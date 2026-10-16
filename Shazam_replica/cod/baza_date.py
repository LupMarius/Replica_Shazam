import json
import sqlite3

from contextlib import closing
from pathlib import Path


def configuratie_text(configuratie):
    """Transforma parametrii intr-un text cu ordine stabila."""
    return json.dumps(
        configuratie,
        sort_keys=True,
        separators=(",", ":"),
    )


def initializeaza_baza(cale_baza):
    cale_baza = Path(cale_baza)
    cale_baza.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(cale_baza)) as conexiune:
        conexiune.execute("PRAGMA foreign_keys = ON")

        conexiune.executescript("""
            CREATE TABLE IF NOT EXISTS piese (
                id INTEGER PRIMARY KEY,
                sha256 TEXT NOT NULL,
                configuratie TEXT NOT NULL,
                nume TEXT NOT NULL,
                fisier_sursa TEXT NOT NULL,
                durata_secunde REAL NOT NULL,
                fs INTEGER NOT NULL,

                UNIQUE (sha256, configuratie)
            );

            CREATE TABLE IF NOT EXISTS repere (
                id INTEGER PRIMARY KEY,
                piesa_id INTEGER NOT NULL,
                timp_secunde REAL NOT NULL,
                frecventa_hz REAL NOT NULL,
                amplitudine REAL NOT NULL,
                categorie INTEGER NOT NULL,

                FOREIGN KEY (piesa_id)
                    REFERENCES piese(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_repere_piesa
                ON repere(piesa_id);

            CREATE INDEX IF NOT EXISTS idx_repere_categorie
                ON repere(categorie);
        """)


def exista_procesare(cale_baza, sha256, configuratie):
    with closing(sqlite3.connect(cale_baza)) as conexiune:
        rezultat = conexiune.execute(
            """
            SELECT id
            FROM piese
            WHERE sha256 = ? AND configuratie = ?
            """,
            (sha256, configuratie_text(configuratie)),
        ).fetchone()

    return rezultat is not None


def salveaza_in_baza(cale_baza, amprenta, configuratie):
    coloane = [
        "TimpSecunde",
        "FrecventaHz",
        "Amplitudine",
        "Categorie",
    ]

    repere = amprenta["repere"]

    if repere.empty:
        raise ValueError("Nu putem salva o amprenta fara repere.")

    with closing(sqlite3.connect(cale_baza)) as conexiune:
        conexiune.execute("PRAGMA foreign_keys = ON")

        # Tranzactie: piesa si reperele se salveaza impreuna.
        # Daca apare o eroare, modificarile sunt anulate.
        with conexiune:
            cursor = conexiune.execute(
                """
                INSERT INTO piese (
                    sha256,
                    configuratie,
                    nume,
                    fisier_sursa,
                    durata_secunde,
                    fs
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (sha256, configuratie) DO NOTHING
                """,
                (
                    amprenta["sha256"],
                    configuratie_text(configuratie),
                    amprenta["nume"],
                    amprenta["fisierSursa"],
                    float(amprenta["durataSecunde"]),
                    int(amprenta["Fs"]),
                ),
            )

            # Protectie suplimentara impotriva duplicatelor.
            if cursor.rowcount == 0:
                return False

            piesa_id = cursor.lastrowid

            randuri = [
                (
                    piesa_id,
                    float(timp),
                    float(frecventa),
                    float(amplitudine),
                    int(categorie),
                )
                for timp, frecventa, amplitudine, categorie
                in repere[coloane].itertuples(index=False, name=None)
            ]

            conexiune.executemany(
                """
                INSERT INTO repere (
                    piesa_id,
                    timp_secunde,
                    frecventa_hz,
                    amplitudine,
                    categorie
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                randuri,
            )

    return True