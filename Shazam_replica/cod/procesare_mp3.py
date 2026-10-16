from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import soundfile as sf

from amprente import salveaza_amprenta
from identificare_duplicate import calculeaza_sha256
from baza_date import exista_procesare, salveaza_in_baza


CONFIGURATIE = {
    "versiune_algoritm": 1,
    "durata_fragment_secunde": 1.0,
    "pas_hz": 20,
    "maxime_per_fragment": 10,
}


def proceseaza_piesa(file_path, cale_baza, folder_amprente):
    """
    Returneaza True daca piesa a fost adaugata in catalog.
    Returneaza False daca procesarea exista deja.
    """
    file_path = Path(file_path).resolve()
    configuratie = CONFIGURATIE.copy()

    # VERIFICAREA DUPLICATELOR
    sha256_piesa = calculeaza_sha256(file_path)

    if exista_procesare(cale_baza, sha256_piesa, configuratie):
        return False

    # CITIRE AUDIO
    x, Fs = sf.read(
        file_path,
        dtype="float64",
        always_2d=True,
    )

    if x.shape[0] == 0 or not np.isfinite(x).all():
        raise ValueError("Fisierul nu contine un semnal audio valid.")

    durata_piesa = x.shape[0] / Fs
    x_mono = np.mean(x, axis=1)

    lungime_fragment = int(
        round(Fs * configuratie["durata_fragment_secunde"])
    )
    pas_hz = configuratie["pas_hz"]
    maxime_per_fragment = configuratie["maxime_per_fragment"]

    date_repere = []

    # ANALIZA FRAGMENTELOR
    for inceput in range(0, len(x_mono), lungime_fragment):
        sfarsit = min(inceput + lungime_fragment, len(x_mono))
        fragment = x_mono[inceput:sfarsit]

        timp_fragment = inceput / Fs
        N = len(fragment)

        X = np.fft.rfft(fragment)
        A = np.abs(X) / N

        if N % 2 == 0:
            A[1:-1] *= 2
        else:
            A[1:] *= 2

        f = np.fft.rfftfreq(N, d=1.0 / Fs)

        # Maxime locale.
        conditie_maxime = (
            (A[1:-1] > A[:-2])
            & (A[1:-1] >= A[2:])
        )

        indici_maxime = np.flatnonzero(conditie_maxime) + 1

        ordine = np.argsort(
            -A[indici_maxime],
            kind="stable",
        )

        indici_selectati = indici_maxime[
            ordine[:maxime_per_fragment]
        ]

        frecvente = f[indici_selectati]
        amplitudini = A[indici_selectati]

        categorii = np.floor(
            frecvente / pas_hz + 0.5
        ).astype(int)

        for frecventa, amplitudine, categorie in zip(
            frecvente,
            amplitudini,
            categorii,
        ):
            date_repere.append([
                timp_fragment,
                frecventa,
                amplitudine,
                categorie,
                categorie * pas_hz,
            ])

    # TABELUL REPERELOR
    repere_piesa = pd.DataFrame(
        date_repere,
        columns=[
            "TimpSecunde",
            "FrecventaHz",
            "Amplitudine",
            "Categorie",
            "CentruCategorieHz",
        ],
    )

    if repere_piesa.empty:
        raise ValueError("Nu au fost gasite repere in piesa.")

    # DATELE AMPRENTEI
    amprenta = {
        "nume": file_path.stem,
        "fisierSursa": str(file_path),
        "sha256": sha256_piesa,
        "repere": repere_piesa,
        "Fs": int(Fs),
        "durataSecunde": durata_piesa,
        "lungimeFragment": lungime_fragment,
        "pasHz": pas_hz,
        "maximePerFragment": maxime_per_fragment,
        "configuratie": configuratie,
        "versiuneAlgoritm": configuratie["versiune_algoritm"],
    }

    # CREAREA SI SALVAREA GRAFICULUI
    figura, ax = plt.subplots(figsize=(12, 6))

    try:
        puncte = ax.scatter(
            repere_piesa["TimpSecunde"],
            repere_piesa["FrecventaHz"],
            s=20,
            c=repere_piesa["Amplitudine"],
            cmap="viridis",
        )

        ax.set_xlabel("Timp (secunde)")
        ax.set_ylabel("Frecventa (Hz)")
        ax.set_title(file_path.stem)
        ax.grid(True)

        figura.colorbar(puncte, ax=ax, label="Amplitudine")
        figura.tight_layout()

        salveaza_amprenta(
            amprenta,
            figura,
            folder_amprente,
        )

        return salveaza_in_baza(
            cale_baza,
            amprenta,
            configuratie,
        )

    finally:
        # Inchidem figura inclusiv daca salvarea produce o eroare.
        plt.close(figura)