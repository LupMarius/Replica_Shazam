import base64
import json
from io import BytesIO
from time import perf_counter

import sqlite3
from pathlib import Path

from comparare import compara_repere

import av
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile

from analiza_audio import CONFIGURATIE, decodeaza_audio, extrage_repere


app = FastAPI(title="Recunoastere muzicala")
MAX_OCTETI = 50 * 1024 * 1024

CALE_BAZA = (
    Path(__file__).resolve().parent.parent
    / "date"
    / "catalog.db"
)
@app.get("/api/status")
def status():
    return {"status": "ok"}


@app.post("/api/analizeaza")
def analizeaza_audio(fisier: UploadFile):
    inceput = perf_counter()
    continut = fisier.file.read(MAX_OCTETI + 1)

    if not continut:
        raise HTTPException(400, "Fisierul este gol.")

    if len(continut) > MAX_OCTETI:
        raise HTTPException(413, "Fisierul depaseste 50 MiB.")

    try:
        x_mono, fs, canale = decodeaza_audio(continut)
        repere = extrage_repere(x_mono, fs, CONFIGURATIE)

    except (av.FFmpegError, ValueError) as error:
        raise HTTPException(
            422,
            "Audio invalid, incompatibil sau mai lung de 10 minute.",
        ) from error

    if repere.empty:
        raise HTTPException(422, "Nu au fost gasite repere audio.")

    inceput_comparatie = perf_counter()

    try:
        candidati = compara_repere(
            repere,
            CALE_BAZA,
            CONFIGURATIE,
        )

    except (FileNotFoundError, sqlite3.Error) as error:
        raise HTTPException(
            503,
            "Catalogul nu poate fi citit. Verifica baza de date.",
        ) from error

    except ValueError as error:
        raise HTTPException(422, str(error)) from error

    timp_comparatie_ms = round(
        (perf_counter() - inceput_comparatie) * 1000,
        1,
    )

    metadate = {
        "nume": fisier.filename or "inregistrare",
        "Fs": fs,
        "durataSecunde": len(x_mono) / fs,
        "configuratie": CONFIGURATIE,
    }

    # Construim arhiva NPZ in memorie, fara cale de fisier.
    with BytesIO() as buffer:
        np.savez_compressed(
            buffer,
            repere=repere.to_numpy(dtype=float),
            coloane=np.array(repere.columns.tolist(), dtype=str),
            metadate=json.dumps(metadate, ensure_ascii=False),
        )

        # Base64 permite transportul arhivei binare intr-un raspuns JSON.
        npz_text = base64.b64encode(buffer.getvalue()).decode("ascii")

    return {
        "status": "amprenta_generata",
        "nume_fisier": metadate["nume"],
        "durata_secunde": round(metadate["durataSecunde"], 3),
        "fs": fs,
        "canale": canale,
        "numar_repere": len(repere),
        "amprenta_npz": npz_text,
        "timp_backend_ms": round((perf_counter() - inceput) * 1000, 1),
        "candidati": candidati,
        "timp_comparatie_ms": timp_comparatie_ms,
    }