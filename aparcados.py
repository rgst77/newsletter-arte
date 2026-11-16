"""Autores del catálogo aparcados por no tener (aún) imágenes libres.

  python aparcados.py            lista quiénes son, desde cuándo y cuándo se reintentan solos
  python aparcados.py comprobar  vuelve a buscar imágenes de cada uno (gratis, sin IA) y libera
                                 a los que ya tengan: entran en la rotación en su turno
"""
import sys
from datetime import datetime, timedelta

from herramientas.catalogo import DIAS_APARCADO, RUTA_OMITIDOS, cargar_catalogo, cargar_enviados, registros_aparcados


def _pendientes_aparcados() -> list[dict]:
    publicados = {r.nombre for r in cargar_enviados()}
    return [r for n, r in sorted(registros_aparcados().items()) if r.get("estado", "aparcado") == "aparcado" and n not in publicados]


def listar() -> None:
    aparcados = _pendientes_aparcados()
    print(f"{len(aparcados)} autores aparcados por falta de imágenes libres (siguen en el catálogo, no se pierden):\n")
    for r in sorted(aparcados, key=lambda r: (r["siglo"], r["nombre"])):
        desde = datetime.fromisoformat(r["fecha"])
        reintento = desde + timedelta(days=DIAS_APARCADO)
        estado = "reintento automático ya posible" if reintento <= datetime.now() else f"reintento automático desde {reintento:%Y-%m-%d}"
        print(f"- {r['nombre']} ({r['disciplina']}, {r['siglo']}) — aparcado el {desde:%Y-%m-%d}; {estado}")


def comprobar() -> None:
    import json

    from agentes.imagenes import elegir_imagenes

    liberados = 0
    for r in _pendientes_aparcados():
        encontradas = len(elegir_imagenes(r["nombre"], r["disciplina"], [], 3))
        if encontradas:
            historial = json.loads(RUTA_OMITIDOS.read_text(encoding="utf-8"))
            historial.append({**r, "estado": "liberado", "motivo": "ya hay imágenes libres", "fecha": datetime.now().isoformat()})
            RUTA_OMITIDOS.write_text(json.dumps(historial, ensure_ascii=False, indent=2), encoding="utf-8")
            liberados += 1
            print(f"LIBERADO  {r['nombre']}: {encontradas} imágenes libres encontradas; entra en la rotación en su turno ({r['siglo']})")
        else:
            print(f"sigue sin imágenes  {r['nombre']}")
    print(f"\n{liberados} liberado(s).")


if __name__ == "__main__":
    comprobar() if sys.argv[1:] == ["comprobar"] else listar()
