import sqlite3
from collections import defaultdict
from contextlib import closing
from pathlib import Path

from baza_date import configuratie_text

def numara_potriviri_frecvente(
    frecvente_interogare,
    frecvente_referinta,
    toleranta_hz=3.0,
):
    a = sorted(frecvente_interogare)
    b = sorted(frecvente_referinta)

    i = 0
    j = 0
    potriviri = 0

    while i < len(a) and j < len(b):
        if abs(a[i] - b[j]) <= toleranta_hz:
            potriviri += 1

            # Ambele repere sunt consumate.
            i += 1
            j += 1

        elif a[i] < b[j]:
            i += 1

        else:
            j += 1

    return potriviri


def compara_repere(repere, cale_baza, configuratie, limita=3):
    if configuratie["durata_fragment_secunde"] != 1.0:
        raise ValueError(
            "Aceasta comparatie foloseste fragmente de o secunda."
        )

    # Eliminam categoriile repetate in aceeasi secunda.
    interogare = defaultdict(set)

    interogare = defaultdict(set)

    for timp, frecventa in repere[
        ["TimpSecunde", "FrecventaHz"]
    ].itertuples(index=False, name=None):
        interogare[int(round(timp))].add(float(frecventa))

    if len(interogare) < 3:
        raise ValueError(
            "Sunt necesare cel putin 3 fragmente cu repere. "
            "Incearca o inregistrare de 10-15 secunde."
        )

    cale_baza = Path(cale_baza).resolve()

    if not cale_baza.is_file():
        raise FileNotFoundError("Catalogul SQLite nu exista.")

    catalog = {}

    # Baza este deschisa exclusiv pentru citire.
    with closing(sqlite3.connect(
        cale_baza.as_uri() + "?mode=ro",
        uri=True,
    )) as conexiune:
        randuri = conexiune.execute(
            """
            SELECT p.id, p.nume, r.timp_secunde, r.frecventa_hz
            FROM piese AS p
            JOIN repere AS r ON r.piesa_id = p.id
            WHERE p.configuratie = ?
            """,
            (configuratie_text(configuratie),),
        )

        for piesa_id, nume, timp, frecventa in randuri:
            if piesa_id not in catalog:
                catalog[piesa_id] = {
                    "nume": nume,
                    "secunde": defaultdict(set),
                }

            catalog[piesa_id]["secunde"][int(round(timp))].add(
                float(frecventa)
            )

    if not catalog:
        raise ValueError(
            "Catalogul nu contine repere cu aceasta configuratie."
        )

    rezultate = []
    numar_fragmente = len(interogare)
    prima_secunda = min(interogare)
    ultima_secunda = max(interogare)

    for piesa_id, piesa in catalog.items():
        secunde = piesa["secunde"]
        cel_mai_bun = None

        # Incercam toate aliniamentele care pot avea suprapunere.
        for decalaj in range(
            min(secunde) - ultima_secunda,
            max(secunde) - prima_secunda + 1,
        ):
            suma = 0.0
            fragmente_comune = 0

            for timp, frecvente in interogare.items():
                referinta = secunde.get(timp + decalaj)

                if not referinta:
                    continue

                comune = numara_potriviri_frecvente(
                    frecvente,
                    referinta,
                    toleranta_hz=3.0,
                )

                if comune:
                    total_distinct = (
                            len(frecvente) + len(referinta) - comune
                    )

                    scor_fragment = comune / total_distinct
                    suma += scor_fragment
                    fragmente_comune += 1

            # Fragmentele fara potrivire contribuie cu zero.
            scor = suma / numar_fragmente

            if scor > 0 and (
                cel_mai_bun is None
                or scor > cel_mai_bun["scor"]
            ):
                cel_mai_bun = {
                    "piesa_id": piesa_id,
                    "nume": piesa["nume"],
                    "scor": scor,
                    "decalaj_secunde": decalaj,
                    "fragmente_cu_repere_comune": fragmente_comune,
                    "fragmente_analizate": numar_fragmente,
                }

        if cel_mai_bun is not None:
            rezultate.append(cel_mai_bun)

    rezultate.sort(
        key=lambda rezultat: (-rezultat["scor"], rezultat["piesa_id"])
    )

    rezultate = rezultate[:limita]

    for rezultat in rezultate:
        rezultat["scor"] = round(rezultat["scor"], 4)

    return rezultate