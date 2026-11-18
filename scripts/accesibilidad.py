"""
accesibilidad.py — utilidades WCAG 2.1/2.2 AA para los gráficos Chart.js del
Observatorio. Cada endpoint que alimenta un <canvas> debe envolver su payload
con `grafico_accesible()` antes de devolverlo: así el frontend recibe el
aria-label y la tabla alternativa ya armados, sin lógica de accesibilidad
duplicada en JavaScript.
"""
from __future__ import annotations

from html import escape
from typing import Any


def grafico_accesible(
    datos: list[dict[str, Any]],
    titulo: str,
    columna_etiqueta: str,
    columna_valor: str,
    unidad: str = "",
) -> dict[str, str]:
    """
    Construye los metadatos de accesibilidad para un gráfico Chart.js.

    Devuelve:
      - aria_label: resumen textual del gráfico completo (para el atributo
        aria-label del <canvas> que lo renderiza).
      - tabla_html_sr_only: tabla HTML equivalente, pensada para insertarse
        oculta visualmente (clase .sr-only) pero navegable por lectores de
        pantalla y disponible para copiar/exportar.

    Uso en el frontend (templates/index.html):
        <canvas id="graficoTipos" role="img" aria-label="{{ resp.accesibilidad.aria_label }}"></canvas>
        {{ resp.accesibilidad.tabla_html_sr_only | safe }}
    """
    if not datos:
        return {
            "aria_label": f"{titulo}: sin datos disponibles.",
            "tabla_html_sr_only": f'<p class="sr-only">{escape(titulo)}: sin datos disponibles.</p>',
        }

    total = sum(d.get(columna_valor, 0) for d in datos)
    partes = "; ".join(
        f"{d.get(columna_etiqueta, '')}: {d.get(columna_valor, 0)}{unidad}" for d in datos
    )
    aria_label = f"{titulo}. {len(datos)} categorías, total {total}{unidad}. Detalle: {partes}."

    filas = "".join(
        f"<tr><td>{escape(str(d.get(columna_etiqueta, '')))}</td>"
        f"<td>{escape(str(d.get(columna_valor, '')))}{escape(unidad)}</td></tr>"
        for d in datos
    )
    tabla_html = (
        f'<table class="sr-only" aria-label="Tabla de datos de: {escape(titulo)}">'
        f"<caption>{escape(titulo)}</caption>"
        f"<thead><tr><th>{escape(columna_etiqueta.capitalize())}</th>"
        f"<th>Valor{escape(unidad)}</th></tr></thead>"
        f"<tbody>{filas}</tbody></table>"
    )
    return {"aria_label": aria_label, "tabla_html_sr_only": tabla_html}
