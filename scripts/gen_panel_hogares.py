"""
gen_panel_hogares.py — genera la pestaña "Hogares" de templates/index.html.

Los hogares salen de HOGARES (abajo, cada uno con su fuente) y los organismos
provinciales para pedir una vacante salen de JUNTAS_POR_PROVINCIA
(scripts/datos_cud.py), así la pestaña CUD y la de Hogares no se contradicen.

Uso:  python -m scripts.gen_panel_hogares
Reemplaza el bloque entre los marcadores HOGARES:INICIO y HOGARES:FIN.
"""
import html
import json
from pathlib import Path

from scripts.datos_cud import JUNTAS_POR_PROVINCIA

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "templates" / "index.html"
INICIO = "<!-- HOGARES:INICIO (generado por scripts/gen_panel_hogares.py) -->"
FIN = "<!-- HOGARES:FIN -->"

GUIA_ORIONE = "https://donorione.org.ar/familia/FAMILIA_ORIONITA_AR-UR-PY.pdf"

# ll: [lat, lon] de OpenStreetMap (Nominatim). aprox=True: el punto es la calle
# o la localidad, no el edificio exacto.
HOGARES = [
    dict(prov="Buenos Aires", nombre="Pequeño Cottolengo Don Orione — Claypole", tipo="cottolengo",
         dir="Av. Lacaze 3963, Claypole (Almirante Brown)", tel="(011) 2206-5500",
         email="cottolengoclaypole@donorione.org.ar",
         nota="Sede más grande del país: unas 415 personas con discapacidad. Hogar con Centro Educativo Terapéutico.",
         ll=[-34.80842, -58.34256], fuente=GUIA_ORIONE, verif="✔ guía oficial de la Obra Don Orione"),
    dict(prov="Buenos Aires", nombre="Pequeño Cottolengo Don Orione — Avellaneda", tipo="cottolengo",
         dir="Manuel Estévez 620, Avellaneda", tel="(011) 4201-9719",
         email="adm.orioneavellaneda@gmail.com", nota="",
         ll=[-34.65326, -58.36455], fuente=GUIA_ORIONE, verif="✔ guía oficial de la Obra Don Orione"),
    dict(prov="Buenos Aires", nombre="Pequeño Cottolengo Don Orione — Los Polvorines", tipo="cottolengo",
         dir="Av. Presidente Illia 4250, Los Polvorines (Malvinas Argentinas)", tel="(011) 4667-2830",
         email="cottolengodorione@yahoo.com.ar", nota="", aprox=True,
         ll=[-34.53149, -58.70310], fuente=GUIA_ORIONE, verif="✔ guía oficial de la Obra Don Orione"),
    dict(prov="Buenos Aires", nombre="Pequeño Cottolengo Don Orione — Mar del Plata", tipo="cottolengo",
         dir="Matheu 3340, Mar del Plata", tel="+54 9 223 573-2846", email="", nota="",
         ll=[-38.01245, -57.56806], fuente=GUIA_ORIONE, verif="✔ guía oficial de la Obra Don Orione"),
    dict(prov="Buenos Aires", nombre="Colonia Nacional Dr. Manuel A. Montes de Oca", tipo="publico",
         dir="Padre Criado Alonso s/n, Torres (Luján)", tel="(02323) 493380 al 387", email="",
         nota="Organismo del Ministerio de Salud de la Nación para personas con discapacidad intelectual "
              "y padecimientos mentales.",
         ll=[-34.42139, -59.14268],
         fuente="https://capacitacion.inap.gob.ar/coordinador/colonia-nacional-dr-manuel-a-montes-de-oca/",
         verif="✔ ficha del INAP (Estado nacional)"),
    dict(prov="Córdoba", nombre="Pequeño Cottolengo Don Orione — Córdoba", tipo="cottolengo",
         dir="B° Santa Isabel 1ª Sección (comunidad: Av. Armada Argentina 2440), Córdoba",
         tel="(0351) 494-0730", email="info@donorionecordoba.com.ar",
         nota="Sede administrativa: 9 de Julio 37, 2° piso, of. 37 — (0351) 422-1518.",
         ll=[-31.47536, -64.23795], fuente=GUIA_ORIONE,
         verif="✔ guía oficial; ⚠ la guía da la dirección de la comunidad, no la puerta del hogar"),
    dict(prov="Córdoba", nombre="Pequeño Cottolengo Don Orione — San Francisco", tipo="cottolengo",
         dir="Juan de Garay 2900, San Francisco", tel="(03564) 42-6577",
         email="cottolengodonorionesf@gmail.com", nota="",
         ll=[-31.41924, -62.09621], fuente=GUIA_ORIONE, verif="✔ guía oficial de la Obra Don Orione"),
    dict(prov="Santa Fe", nombre="Pequeño Cottolengo Don Orione — Rosario", tipo="cottolengo",
         dir="Gorriti 461, Rosario", tel="(0341) 439-9198",
         email="administracionrosario@donorione.org.ar", nota="",
         ll=[-32.92330, -60.67021], fuente=GUIA_ORIONE, verif="✔ guía oficial de la Obra Don Orione"),
    dict(prov="Santa Fe", nombre="Pequeño Cottolengo Don Orione — General Lagos", tipo="cottolengo",
         dir="Ruta 21 km 12, zona rural, General Lagos", tel="(03402) 49-0052",
         email="cottolengolagos@gmail.com", nota="",
         ll=[-33.09951, -60.55469], fuente=GUIA_ORIONE, verif="✔ guía oficial de la Obra Don Orione"),
    dict(prov="Corrientes", nombre="Pequeño Cottolengo Don Orione — Itatí", tipo="cottolengo",
         dir="Obispo Luis María Niella 792, Itatí", tel="(0379) 449-3304",
         email="cottolengoitati@yahoo.com.ar", nota="", aprox=True,
         ll=[-27.26913, -58.24663], fuente=GUIA_ORIONE, verif="✔ guía oficial de la Obra Don Orione"),
    dict(prov="Mendoza", nombre="Pequeño Cottolengo Don Orione — Mendoza", tipo="cottolengo",
         dir="Juan B. Justo 1565, Villa Hipódromo (Godoy Cruz)", tel="(0261) 427-1333",
         email="hdonorionemza@gmail.com", nota="Hogar permanente para personas con discapacidad severa.",
         ll=[-32.90628, -68.86094], fuente=GUIA_ORIONE, verif="✔ guía oficial de la Obra Don Orione"),
    dict(prov="Chaco", nombre="Pequeño Cottolengo Don Orione — Presidencia Roque Sáenz Peña", tipo="cottolengo",
         dir="Av. Las Malvinas y Superiora Palmira, Pres. Roque Sáenz Peña", tel="(0364) 442-1860",
         email="cottolengochaco@yahoo.com.ar", nota="", aprox=True,
         ll=[-26.79097, -60.44129], fuente=GUIA_ORIONE,
         verif="✔ guía oficial; ⚠ el punto del mapa es la ciudad, no el edificio"),
    dict(prov="Tucumán", nombre="Pequeño Cottolengo Don Orione — San Miguel de Tucumán", tipo="cottolengo",
         dir="Av. República del Líbano 2148 (comunidad y parroquia), San Miguel de Tucumán",
         tel="(0381) 424-6879", email="cottotuc@gmail.com", nota="",
         ll=[-26.79876, -65.21434], fuente=GUIA_ORIONE,
         verif="✔ guía oficial; ⚠ la guía da la dirección de la comunidad"),
    dict(prov="Entre Ríos", nombre="Hogar Aprendiendo a Ser", tipo="otro",
         dir="Pedro Londero 2947, Paraná", tel="", email="",
         nota="Hogar privado inaugurado en noviembre de 2026, junto a un Centro de Día; el Iprodi habló de 234 camas.",
         ll=[-31.74243, -60.45904], aprox=True,
         fuente="https://www.elheraldo.com.ar/noticias/interes-general/se-inauguro-el-hogar-aprendiendo-a-ser-una-iniciativa-privada-que-amplia-los-espacios-de-atencion-para-personas-con-discapacidad",
         verif="⚠ nota de prensa; sin teléfono publicado"),
    dict(prov="Jujuy", nombre="Residencia “Nicky” — Asociación Todos Juntos", tipo="otro",
         dir="Salta 1058, San Salvador de Jujuy", tel="(0388) 423-0236", email="",
         nota="Asociación que acompaña a personas con discapacidad intelectual y sus familias desde 1988.",
         ll=[-24.18191, -65.30520], aprox=True, fuente="https://todosjuntosjujuy.org/contacto/",
         verif="✔ sitio oficial de la asociación"),
]

PROVINCIAS = sorted(JUNTAS_POR_PROVINCIA, key=lambda p: (p != "Buenos Aires", p != "CABA", p))


def e(s):
    return html.escape(str(s or ""), quote=True)


def fila_provincia(prov):
    org = JUNTAS_POR_PROVINCIA[prov]
    propios = [h for h in HOGARES if h["prov"] == prov]
    if propios:
        lista = "<ul class=\"ls-lista\" style=\"margin:0 0 0 1rem\">" + "".join(
            f"<li><strong>{e(h['nombre'])}</strong><br>{e(h['dir'])}"
            + (f" &middot; {e(h['tel'])}" if h["tel"] else "")
            + f"<br><span class=\"muted\">{e(h['verif'])}</span></li>" for h in propios) + "</ul>"
    else:
        lista = ("<span class=\"muted\">Sin hogar verificado todav&iacute;a en este listado. "
                 "Pedí la n&oacute;mina de hogares habilitados al organismo de la columna siguiente.</span>")
    url = org.get("url_turno") or ""
    organismo = e(org["nombre_organismo"])
    if url:
        organismo = f"<a href=\"{e(url)}\" target=\"_blank\" rel=\"noopener\">{organismo}</a>"
    return (f"<tr data-prov=\"{e(prov)}\"><th scope=\"row\">{e(prov)}</th><td>{lista}</td>"
            f"<td>{organismo}<br>{e(org.get('telefono'))}</td></tr>")


def panel():
    opciones = "".join(f"<option value=\"{e(p)}\">{e(p)}</option>" for p in PROVINCIAS)
    filas = "\n".join(fila_provincia(p) for p in PROVINCIAS)
    datos = json.dumps(HOGARES, ensure_ascii=False).replace("</", "<\\/")
    n_cotto = sum(h["tipo"] == "cottolengo" for h in HOGARES)
    return f"""{INICIO}
  <div class="panel" id="panel-hogares" aria-labelledby="ho-titulo">
    <div class="wrap wrap-wide">

      <div class="card">
        <h2 id="ho-titulo">Hogares para personas con discapacidad &mdash; provincia por provincia</h2>
        <p>
          Un <strong>hogar</strong> es una prestaci&oacute;n residencial para personas con discapacidad que no pueden vivir
          con su familia o necesitan apoyos las 24 horas. Est&aacute; incluida en el
          <a href="https://www.argentina.gob.ar/normativa/nacional/ley-24901-47677/texto" target="_blank" rel="noopener">Sistema de Prestaciones B&aacute;sicas (Ley 24.901)</a>:
          con <strong>CUD</strong>, la obra social, la prepaga o el programa Incluir Salud deben cubrirla si el equipo tratante la indica
          y el hogar est&aacute; inscripto en el Registro Nacional de Prestadores.
        </p>
        <p>
          Los <strong>Peque&ntilde;os Cottolengos Don Orione</strong> son la red m&aacute;s conocida: {n_cotto} sedes en el pa&iacute;s
          con hogar permanente para personas con discapacidad severa. Tambi&eacute;n listamos otros hogares cuya direcci&oacute;n
          pudimos confirmar en una fuente p&uacute;blica.
        </p>
        <div class="disclaimer">
          Este listado <strong>no es exhaustivo</strong>: no existe un padr&oacute;n nacional p&uacute;blico de hogares con direcci&oacute;n.
          Antes de ir, llam&aacute; para confirmar vacantes, edades y tipo de discapacidad que reciben.
          La columna <em>Verificaci&oacute;n</em> indica de d&oacute;nde sale cada dato (✔ fuente oficial &middot; ⚠ dato parcial).
          &iquest;Conoc&eacute;s un hogar que falta? Escribinos desde el formulario de contacto de la portada.
        </div>
      </div>

      <div class="card">
        <h3>Mapa de hogares</h3>
        <div style="display:flex;gap:.8rem;flex-wrap:wrap;align-items:center;margin-bottom:.6rem">
          <label for="ho-prov">Provincia:</label>
          <select id="ho-prov"><option value="">Todo el pa&iacute;s</option>{opciones}</select>
          <span class="muted"><span style="color:#1d5d8c">&#9679;</span> Peque&ntilde;o Cottolengo
            &nbsp; <span style="color:#b35c00">&#9679;</span> otro hogar o instituci&oacute;n</span>
        </div>
        <div id="ho-mapa" class="map-container" style="height:440px" role="img"
             aria-label="Mapa de Argentina con los hogares listados. Los mismos datos están en la lista y la tabla siguientes."></div>
        <p class="muted" style="font-size:.78rem">Puntos ubicados con OpenStreetMap. Los marcados como &laquo;ubicaci&oacute;n aproximada&raquo; se&ntilde;alan la calle o la ciudad, no el edificio.</p>
        <div id="ho-lista" aria-live="polite"></div>
      </div>

      <div class="card" id="ho-provincias">
        <h3>Las 24 jurisdicciones: hogares y d&oacute;nde pedir una vacante</h3>
        <p>
          Para ingresar a un hogar suele hacer falta: CUD vigente, indicaci&oacute;n del m&eacute;dico o equipo tratante,
          informe social y la autorizaci&oacute;n de la obra social o del programa provincial. Si no ten&eacute;s cobertura,
          el pedido se hace al organismo provincial de discapacidad.
        </p>
        <div class="am-table-wrap">
          <table class="tbl il-prov" id="ho-tabla">
            <caption class="muted" style="text-align:left">Organismos tomados de la pesta&ntilde;a CUD de este sitio.</caption>
            <thead><tr><th scope="col">Jurisdicci&oacute;n</th><th scope="col">Hogares listados</th><th scope="col">Organismo provincial (vacantes y orientaci&oacute;n)</th></tr></thead>
            <tbody>
{filas}
            </tbody>
          </table>
        </div>
        <h3>Si la cobertura se niega o demora</h3>
        <ul class="ls-lista">
          <li>Ped&iacute; la negativa <strong>por escrito</strong> y reclam&aacute; ante la
            <a href="https://www.argentina.gob.ar/sssalud" target="_blank" rel="noopener">Superintendencia de Servicios de Salud</a> (0800-222-72583).</li>
          <li>La Defensor&iacute;a del Pueblo de tu provincia o municipio puede intervenir sin costo.</li>
          <li>Ante urgencia, un amparo de salud suele resolverse en d&iacute;as; consult&aacute; a la defensor&iacute;a oficial.</li>
        </ul>
        <p class="muted" style="font-size:.78rem">Fuentes: <a href="{GUIA_ORIONE}" target="_blank" rel="noopener">Gu&iacute;a de la Familia Orionita (Argentina, Uruguay y Paraguay)</a>,
          <a href="https://donorione.org.ar/cottolengo-de-claypole/" target="_blank" rel="noopener">Cottolengo de Claypole</a> y las fuentes de cada fila. Revisado el 10/11/2026.</p>
      </div>

    </div>
  </div>
  <script>
    const HOGARES = {datos};
    let hoMapa = null, hoCapa = null;
    function hoDibujar() {{
      const prov = document.getElementById('ho-prov').value;
      const lista = HOGARES.filter(h => !prov || h.prov === prov);
      document.querySelectorAll('#ho-tabla tbody tr').forEach(tr => {{
        tr.style.display = !prov || tr.dataset.prov === prov ? '' : 'none';
      }});
      document.getElementById('ho-lista').innerHTML = lista.length
        ? '<div class="list-items">' + lista.map(h =>
            '<div class="list-item"><strong>' + escapeHtml(h.nombre) + '</strong><br>' +
            escapeHtml(h.dir) + ' &middot; ' + escapeHtml(h.prov) +
            (h.tel ? '<br>Tel.: ' + escapeHtml(h.tel) : '') +
            (h.email ? ' &middot; ' + escapeHtml(h.email) : '') +
            (h.nota ? '<br><span class="muted">' + escapeHtml(h.nota) + '</span>' : '') +
            '<br><a href="https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(h.dir + ', ' + h.prov + ', Argentina') +
            '" target="_blank" rel="noopener">C&oacute;mo llegar</a> &middot; <a href="' + h.fuente + '" target="_blank" rel="noopener">Fuente</a></div>'
          ).join('') + '</div>'
        : '<p class="muted">Todav&iacute;a no listamos hogares verificados en esta provincia. Consult&aacute; al organismo provincial de la tabla.</p>';
      if (!window.L) return;
      if (!hoMapa) {{
        hoMapa = L.map('ho-mapa', {{ scrollWheelZoom: false }}).setView([-38.5, -63.5], 4);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
          attribution: '&copy; OpenStreetMap', maxZoom: 18,
        }}).addTo(hoMapa);
      }}
      setTimeout(() => hoMapa.invalidateSize(), 50);
      if (hoCapa) hoCapa.remove();
      hoCapa = L.layerGroup().addTo(hoMapa);
      const puntos = lista.map(h => {{
        L.circleMarker(h.ll, {{
          radius: 8, weight: 1, fillOpacity: 0.9, color: '#ffffff',
          fillColor: h.tipo === 'cottolengo' ? '#1d5d8c' : '#b35c00',
        }}).bindPopup('<strong>' + escapeHtml(h.nombre) + '</strong><br>' + escapeHtml(h.dir) +
          (h.tel ? '<br>Tel.: ' + escapeHtml(h.tel) : '') +
          (h.aprox ? '<br><em>Ubicaci&oacute;n aproximada</em>' : '')).addTo(hoCapa);
        return h.ll;
      }});
      if (puntos.length > 1) hoMapa.fitBounds(puntos, {{ padding: [30, 30], maxZoom: 12 }});
      else if (puntos.length === 1) hoMapa.setView(puntos[0], 13);
      else hoMapa.setView([-38.5, -63.5], 4);
    }}
    function initHogares() {{
      document.getElementById('ho-prov').addEventListener('change', hoDibujar);
      hoDibujar();
    }}
  </script>
{FIN}"""


def main():
    texto = INDEX.read_bytes().decode("utf-8")  # sin traducir saltos: se respeta CRLF/LF del archivo
    bloque = panel()
    if "\r\n" in texto:
        bloque = bloque.replace("\n", "\r\n")
    if INICIO in texto:
        a = texto.index(INICIO)
        b = texto.index(FIN) + len(FIN)
        texto = texto[:a] + bloque + texto[b:]
    else:
        ancla = "  <!-- ====================== COMUNA_07 ====================== -->"
        salto = "\r\n" if "\r\n" in texto else "\n"
        texto = texto.replace(ancla, bloque + salto * 2 + ancla, 1)
    INDEX.write_bytes(texto.encode("utf-8"))
    print(f"Pestaña Hogares: {len(HOGARES)} hogares, {len(PROVINCIAS)} jurisdicciones")


if __name__ == "__main__":
    main()
