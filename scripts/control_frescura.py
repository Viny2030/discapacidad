"""
control_frescura.py — controla que los datos y las secciones del sitio estén al día.

Revisa cuatro cosas y escribe un informe en Markdown:
  1. Si la página oficial de ANDIS publica un informe (PDF) distinto del que
     tenemos guardado: eso significa que el scraper no lo pudo cargar.
  2. Si producción muestra la misma fecha y total que el repositorio
     (detecta un despliegue que no tomó los datos nuevos).
  3. Que ninguna sección escrita a mano (data/fuentes.json) lleve más de 12 meses sin revisión.
  4. La antigüedad del informe oficial (solo informativo: depende del Estado).

Sale con código 1 si 1, 2 o 3 fallan, para que el workflow abra un issue.
Hace 2 pedidos HTTP en total.

Uso:  python -m scripts.control_frescura [--sitio https://discapacidad.viny2030.com.ar]
"""
from __future__ import annotations

import sys
from datetime import date

import requests

from scripts.scraper_andis import PAGINA, USER_AGENT, buscar_pdf, cargar_guardado

SITIO = "https://discapacidad.viny2030.com.ar"


def meses_desde(iso: str, hoy: date | None = None) -> int:
    hoy = hoy or date.today()
    a, m = int(iso[:4]), int(iso[5:7])
    return (hoy.year - a) * 12 + (hoy.month - m)


def controlar(sitio: str = SITIO) -> tuple[bool, list[str]]:
    guardado = cargar_guardado().get("oficial", {})
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    ok, lineas = True, ["## Control de frescura de datos estadísticos", ""]

    try:
        pdf_publicado = buscar_pdf(s.get(PAGINA, timeout=30).text)
        if pdf_publicado == guardado.get("fuente_pdf"):
            lineas.append(f"- ✅ El informe guardado es el que publica ANDIS: {pdf_publicado}")
        else:
            ok = False
            lineas.append(f"- ❌ ANDIS publica un informe que no está cargado: {pdf_publicado} "
                          f"(guardado: {guardado.get('fuente_pdf')}). Correr el workflow «ETL Estadístico semanal».")
    except Exception as e:  # noqa: BLE001 — se informa cualquier error de red o de formato
        ok = False
        lineas.append(f"- ❌ No se pudo leer la página oficial de ANDIS: {e}")

    try:
        prod = s.get(f"{sitio}/api/resumen", timeout=30).json()
        if (prod.get("fecha_datos"), prod.get("total_cud_vigentes")) == (guardado.get("fecha_corte"), guardado.get("total_cud_vigentes")):
            lineas.append(f"- ✅ Producción muestra el mismo corte que el repositorio ({prod.get('fecha_datos')}).")
        else:
            ok = False
            lineas.append(f"- ❌ Producción muestra {prod.get('fecha_datos')} / {prod.get('total_cud_vigentes')} y el "
                          f"repositorio {guardado.get('fecha_corte')} / {guardado.get('total_cud_vigentes')}: revisar el despliegue.")
    except Exception as e:  # noqa: BLE001
        ok = False
        lineas.append(f"- ❌ No se pudo consultar {sitio}/api/resumen: {e}")

    from scripts.api_fuentes import listar_fuentes
    vencidas = [f for f in listar_fuentes() if f.get("tipo") == "contenido" and f["antiguedad"]["meses"] > 12]
    if vencidas:
        ok = False
        for f in vencidas:
            lineas.append(f"- ❌ «{f['seccion']}» lleva {f['antiguedad']['meses']} meses sin revisión: revisarla y "
                          "actualizar su fecha en data/fuentes.json.")
    else:
        lineas.append("- ✅ Todas las secciones escritas a mano se revisaron en los últimos 12 meses.")

    if guardado.get("fecha_corte"):
        edad = meses_desde(guardado["fecha_corte"])
        lineas.append(f"- ℹ️ El último informe oficial es de {guardado['fecha_corte'][:7]} ({edad} meses). "
                      "Su antigüedad depende de lo que publique el Estado; el sitio lo aclara en la pestaña Estadístico.")
    return ok, lineas


if __name__ == "__main__":
    sitio = sys.argv[sys.argv.index("--sitio") + 1] if "--sitio" in sys.argv else SITIO
    ok, lineas = controlar(sitio)
    print("\n".join(lineas))
    sys.exit(0 if ok else 1)
