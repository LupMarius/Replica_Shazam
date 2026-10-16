from pathlib import Path
import json
import hashlib
import numpy as np


def salveaza_amprenta(amprenta, figura, folder_amprente):
    # Cream folderul daca nu exista.
    folder_amprente = Path(folder_amprente)
    folder_amprente.mkdir(parents=True, exist_ok=True)

    nume_piesa = amprenta["nume"]

    config_text = json.dumps(
        amprenta["configuratie"],
        sort_keys=True,
        separators=(",", ":"),
    )

    identificator = hashlib.sha256(
        (amprenta["sha256"] + ":" + config_text).encode("utf-8")
    ).hexdigest()

    cale_date = folder_amprente / f"{identificator}.npz"
    cale_imagine = folder_amprente / f"{identificator}.png"

    # Separam tabelul numeric de informatiile despre piesa.
    repere = amprenta["repere"]

    metadate = {
        cheie: valoare
        for cheie, valoare in amprenta.items()
        if cheie != "repere"
    }

    # Salvam numerele, denumirile coloanelor si metadatele.
    np.savez_compressed(
        cale_date,
        repere=repere.to_numpy(dtype=float),
        coloane=np.array(repere.columns.tolist(), dtype=str),
        metadate=json.dumps(metadate, ensure_ascii=False),
    )

    # Salvam figura primita ca argument.
    figura.savefig(cale_imagine, dpi=150, bbox_inches="tight")

    print(f"Date salvate: {cale_date}")
    print(f"Imagine salvata: {cale_imagine}")

    return cale_date