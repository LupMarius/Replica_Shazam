from io import BytesIO

import av
import numpy as np
import pandas as pd


CONFIGURATIE = {
    "versiune_algoritm": 1,
    "durata_fragment_secunde": 1.0,
    "pas_hz": 20,
    "maxime_per_fragment": 10,
}

COLOANE = [
    "TimpSecunde",
    "FrecventaHz",
    "Amplitudine",
    "Categorie",
    "CentruCategorieHz",
]


def decodeaza_audio(continut, durata_maxima=600):
    bucati = []
    fs = None
    canale = None
    total = 0

    with av.open(BytesIO(continut)) as container:
        if not container.streams.audio:
            raise ValueError("Fisierul nu contine audio.")

        # Convertim valorile in numere reale, cu un rand per canal.
        # Frecventa de esantionare ramane cea a sursei decodate.
        convertor = av.AudioResampler(format="dblp")

        for cadru in container.decode(audio=0):
            if cadru.samples == 0:
                continue

            if not cadru.sample_rate:
                raise ValueError("Frecventa de esantionare invalida.")

            if fs is None:
                fs = cadru.sample_rate
                canale = len(cadru.layout.channels)
            elif (
                cadru.sample_rate != fs
                or len(cadru.layout.channels) != canale
            ):
                raise ValueError("Parametrii audio se schimba.")

            total += cadru.samples

            if total / fs > durata_maxima:
                raise ValueError("Audio depaseste durata permisa.")

            for convertit in convertor.resample(cadru):
                # Media canalelor produce semnalul mono.
                bucati.append(convertit.to_ndarray().mean(axis=0))

        if fs is not None:
            for convertit in convertor.resample(None):
                bucati.append(convertit.to_ndarray().mean(axis=0))

    if not bucati:
        raise ValueError("Nu exista esantioane audio.")

    x_mono = np.concatenate(bucati)

    if x_mono.size == 0 or not np.isfinite(x_mono).all():
        raise ValueError("Semnalul audio este invalid.")

    return x_mono, fs, canale


def extrage_repere(x_mono, fs, configuratie):
    lungime = round(fs * configuratie["durata_fragment_secunde"])
    pas_hz = configuratie["pas_hz"]
    maxim = configuratie["maxime_per_fragment"]
    randuri = []

    for inceput in range(0, len(x_mono), lungime):
        fragment = x_mono[inceput:inceput + lungime]
        n = len(fragment)

        amplitudini = np.abs(np.fft.rfft(fragment)) / n

        if n % 2 == 0:
            amplitudini[1:-1] *= 2
        else:
            amplitudini[1:] *= 2

        frecvente = np.fft.rfftfreq(n, d=1.0 / fs)

        indici = np.flatnonzero(
            (amplitudini[1:-1] > amplitudini[:-2])
            & (amplitudini[1:-1] >= amplitudini[2:])
        ) + 1

        ordine = np.argsort(-amplitudini[indici], kind="stable")

        for indice in indici[ordine[:maxim]]:
            frecventa = frecvente[indice]
            categorie = int(np.floor(frecventa / pas_hz + 0.5))

            randuri.append([
                inceput / fs,
                frecventa,
                amplitudini[indice],
                categorie,
                categorie * pas_hz,
            ])

    return pd.DataFrame(randuri, columns=COLOANE)