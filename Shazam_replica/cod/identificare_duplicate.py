import hashlib
from pathlib import Path


def calculeaza_sha256(file_path):
    file_path = Path(file_path)

    # Initializam calculul SHA-256.
    hash_fisier = hashlib.sha256()

    # Citim fisierul binar in blocuri de cate 1 MB.
    with file_path.open("rb") as fisier:
        while True:
            bloc = fisier.read(1024 * 1024)

            # Un bloc gol inseamna ca am ajuns la final.
            if not bloc:
                break

            hash_fisier.update(bloc)

    # Returnam semnatura sub forma de text.
    return hash_fisier.hexdigest()