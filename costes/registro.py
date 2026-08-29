import json
from datetime import datetime
from pathlib import Path

RUTA_LOG = Path(__file__).resolve().parent / "uso.jsonl"

PRECIOS_POR_MILLON = {
    "claude-haiku-4-5-20251001": {"entrada": 1.00, "salida": 5.00},
}


def registrar_uso(modelo: str, etiqueta: str, tokens_entrada: int, tokens_salida: int) -> float:
    precios = PRECIOS_POR_MILLON.get(modelo, {"entrada": 0.0, "salida": 0.0})
    coste = (
        tokens_entrada / 1_000_000 * precios["entrada"]
        + tokens_salida / 1_000_000 * precios["salida"]
    )

    with open(RUTA_LOG, "a") as f:
        f.write(
            json.dumps(
                {
                    "fecha": datetime.now().isoformat(),
                    "etiqueta": etiqueta,
                    "modelo": modelo,
                    "tokens_entrada": tokens_entrada,
                    "tokens_salida": tokens_salida,
                    "coste_usd": round(coste, 6),
                }
            )
            + "\n"
        )

    return coste


def resumen_gasto() -> dict:
    if not RUTA_LOG.exists():
        return {"llamadas": 0, "coste_total_usd": 0.0, "por_etiqueta": {}}

    total = 0.0
    llamadas = 0
    por_etiqueta: dict[str, float] = {}

    with open(RUTA_LOG) as f:
        for linea in f:
            registro = json.loads(linea)
            total += registro["coste_usd"]
            llamadas += 1
            por_etiqueta[registro["etiqueta"]] = (
                por_etiqueta.get(registro["etiqueta"], 0.0) + registro["coste_usd"]
            )

    return {
        "llamadas": llamadas,
        "coste_total_usd": round(total, 6),
        "por_etiqueta": {k: round(v, 6) for k, v in por_etiqueta.items()},
    }
