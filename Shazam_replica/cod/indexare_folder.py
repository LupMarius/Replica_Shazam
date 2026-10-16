from pathlib import Path

from baza_date import initializeaza_baza
from procesare_mp3 import proceseaza_piesa


def indexeaza_folder():
    folder_proiect = Path(__file__).resolve().parent.parent

    folder_muzica = folder_proiect / "muzica"
    folder_amprente = folder_proiect / "amprente"
    cale_baza = folder_proiect / "date" / "catalog.db"

    if not folder_muzica.is_dir():
        raise FileNotFoundError(
            f"Folderul de muzica nu exista: {folder_muzica}"
        )

    initializeaza_baza(cale_baza)

    # Selectam MP3-urile direct din folder.
    # Acceptam atat extensia .mp3, cat si .MP3.
    fisiere = sorted(
        (
            fisier
            for fisier in folder_muzica.iterdir()
            if fisier.is_file()
            and fisier.suffix.lower() == ".mp3"
        ),
        key=lambda fisier: fisier.name.lower(),
    )

    if not fisiere:
        print("Nu exista fisiere MP3 in folderul de muzica.")
        return

    procesate = 0
    existente = 0
    erori = 0

    for numar, file_path in enumerate(fisiere, start=1):
        print(f"\n[{numar}/{len(fisiere)}] {file_path.name}")

        try:
            adaugata = proceseaza_piesa(
                file_path,
                cale_baza,
                folder_amprente,
            )

            if adaugata:
                procesate += 1
                print("Procesata si adaugata in catalog.")
            else:
                existente += 1
                print("Exista deja. Trecem la urmatoarea piesa.")

        except Exception as eroare:
            erori += 1
            print(f"Eroare: {eroare}")

    print("\nIndexare terminata.")
    print(f"Piese noi procesate: {procesate}")
    print(f"Procesari deja existente: {existente}")
    print(f"Erori: {erori}")
    print(f"Baza de date: {cale_baza}")


if __name__ == "__main__":
    indexeaza_folder()