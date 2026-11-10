"""
gen_panel_manual.py — genera la pestaña "Manual" (ES/EN) de templates/index.html.

Incluye el manual de uso en español e inglés y dos grafos SVG, con nombre en
todos los nodos (criterio del ecosistema):
  1. Funcionamiento: fuentes -> procesos automáticos -> datos guardados -> API -> pantallas.
  2. Uso: qué necesitás -> pestaña -> qué encontrás (los nodos de pestaña abren esa pestaña).

Uso:  python -m scripts.gen_panel_manual
Reemplaza el bloque entre los marcadores MANUAL:INICIO y MANUAL:FIN.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "templates" / "index.html"
INICIO = "<!-- MANUAL:INICIO (generado por scripts/gen_panel_manual.py) -->"
FIN = "<!-- MANUAL:FIN -->"
LANGS = ("es", "en")

# ── Grafo 1: funcionamiento ────────────────────────────────────────────────
_W, _H = 180, 58
# (id, x, y, ancho, alto, tipo)
FLOW_NODES = [
    ("pubmed", 20, 20, _W, _H, "input"),
    ("ctgov", 20, 95, _W, _H, "input"),
    ("mymemory", 20, 170, _W, _H, "input"),
    ("datosgob", 20, 245, _W, _H, "input"),
    ("georef", 20, 320, _W, _H, "input"),
    ("normas", 20, 395, _W, _H, "input"),
    ("etl_med", 230, 95, _W, _H, "process"),
    ("sched", 230, 188, _W, _H, "control"),
    ("etl_est", 230, 282, _W, _H, "process"),
    ("revision", 230, 395, _W, _H, "process"),
    ("cache", 440, 95, _W, _H, "store"),
    ("csv", 440, 282, _W, _H, "store"),
    ("curados", 440, 395, _W, _H, "store"),
    ("health", 650, 95, _W, _H, "control"),
    ("api", 650, 188, _W, _H, "endpoint"),
    ("sitio", 860, 132, _W, _H, "output"),
    ("docs", 860, 245, _W, _H, "output"),
    ("forms", 860, 320, _W, _H, "input"),
    ("email", 860, 395, _W, _H, "output"),
]
FLOW_EDGES = [
    "M200 49 L215 49 L215 110 L230 110",
    "M200 124 L230 124",
    "M200 199 L215 199 L215 138 L230 138",
    "M200 274 L215 274 L215 300 L230 300",
    "M200 349 L215 349 L215 322 L230 322",
    "M200 424 L230 424",
    "M320 188 L320 153",
    "M320 246 L320 282",
    "M410 124 L440 124",
    "M410 311 L440 311",
    "M410 424 L440 424",
    "M620 124 L635 124 L635 207 L650 207",
    "M620 311 L635 311 L635 227 L650 227",
    "M620 424 L640 424 L640 240 L650 240",
    "M740 153 L740 188",
    "M830 207 L845 207 L845 161 L860 161",
    "M830 227 L845 227 L845 274 L860 274",
    "M950 378 L950 395",
]
FLOW_VIEWBOX = (1060, 470)

# ── Grafo 2: uso ───────────────────────────────────────────────────────────
# (clave, pestaña a abrir); el texto de cada fila está en GRAPH_TEXT[lang]["uso"]
USO_FILAS = [
    ("cud", "cud"), ("sube", "cud"), ("beneficios", "calculadora"), ("pension", "pensiones"),
    ("condicion", "condiciones"), ("tratamiento", "tratamientos"), ("hogar", "hogares"),
    ("trabajo", "laboral"), ("mayores", "mayores"), ("senas", "senas"), ("datos", "estadistico"),
    ("caba", "gcba"), ("dev", "docs"),
]
_UX, _UW, _UH, _USTEP = (20, 380, 690), (300, 230, 310), 44, 52
USO_VIEWBOX = (1020, 20 + _USTEP * len(USO_FILAS))

GRAPH_TEXT = {
    "es": {
        "flow": {
            "pubmed": ("PubMed", ["artículos; también en vivo"]),
            "ctgov": ("ClinicalTrials.gov", ["ensayos que reclutan"]),
            "mymemory": ("MyMemory", ["traducción de resúmenes"]),
            "datosgob": ("ANDIS · INDEC", ["informe oficial CUD, población"]),
            "georef": ("GeoRef", ["provincias y comunas"]),
            "normas": ("Normas y guías oficiales", ["leyes, ANDIS, Don Orione"]),
            "etl_med": ("ETL médico", ["GitHub Actions, miércoles"]),
            "sched": ("Programador interno", ["cada 15 días, en el servidor"]),
            "etl_est": ("Scraper + ETL estadístico", ["GitHub Actions, lunes"]),
            "revision": ("Revisión manual", ["fuente y verificación"]),
            "cache": ("Caché médica", ["etl_medico_cache.json", "traducciones_es.json"]),
            "csv": ("Datos estadísticos", ["data/processed/*.csv"]),
            "curados": ("Datos curados", ["datos_cud.py, generadores"]),
            "health": ("Controles", ["diario y frescura mensual"]),
            "api": ("API FastAPI", ["/api/cud, /api/provincias…"]),
            "sitio": ("Sitio web", ["pestañas y mapas"]),
            "docs": ("API Docs", ["/docs, datos abiertos"]),
            "forms": ("Formularios", ["contacto y encuesta"]),
            "email": ("Correo del equipo", ["no se guarda en el sitio"]),
        },
        "legend_flow": {"input": "Fuente o entrada", "control": "Control", "process": "Proceso",
                        "store": "Dato guardado", "endpoint": "API", "output": "Lo que ves"},
        "uso": {
            "cud": ("Sacar o renovar el CUD", "CUD", "requisitos, pasos y junta de tu provincia"),
            "sube": ("Viajar gratis", "CUD → SUBE", "vincular el CUD con la tarjeta SUBE"),
            "beneficios": ("Saber qué me corresponde", "Calculadora", "beneficios según tu situación"),
            "pension": ("Cobrar una pensión", "Pensiones", "PNC por discapacidad: requisitos"),
            "condicion": ("Entender una condición", "Condiciones", "TEA, epilepsia, visual y 10 más"),
            "tratamiento": ("Tratamientos e investigación", "Tratamientos · Médico", "PubMed, ensayos, vanguardia"),
            "hogar": ("Buscar un hogar", "Hogares", "mapa y direcciones por provincia"),
            "trabajo": ("Conseguir trabajo", "Inclusión Laboral", "cupo laboral y leyes provinciales"),
            "mayores": ("Persona mayor", "Adultos Mayores", "CUD, derechos y recursos 65+"),
            "senas": ("Lengua de señas", "Lengua de Señas", "LSA, Ley 27.710 y cursos"),
            "datos": ("Ver datos o comparar", "Estadístico · Comparador", "CUD por provincia y tipo"),
            "caba": ("Vivo en CABA", "GCBA · Comuna_07", "escuelas, salud y la Comuna 7"),
            "dev": ("Usar los datos en mi app", "API Docs", "endpoints abiertos en JSON"),
        },
        "legend_uso": {"input": "Qué necesitás", "output": "Pestaña (tocala para abrirla)", "signal": "Qué encontrás"},
        "aria_flow": "Grafo de funcionamiento: de las fuentes oficiales y científicas a las pestañas del sitio",
        "aria_uso": "Grafo de uso: qué necesitás, qué pestaña abrir y qué vas a encontrar",
    },
    "en": {
        "flow": {
            "pubmed": ("PubMed", ["articles; also live"]),
            "ctgov": ("ClinicalTrials.gov", ["recruiting trials"]),
            "mymemory": ("MyMemory", ["abstract translation"]),
            "datosgob": ("ANDIS · INDEC", ["official CUD report, population"]),
            "georef": ("GeoRef", ["provinces and comunas"]),
            "normas": ("Laws and official guides", ["statutes, ANDIS, Don Orione"]),
            "etl_med": ("Medical ETL", ["GitHub Actions, Wednesdays"]),
            "sched": ("Internal scheduler", ["every 15 days, on the server"]),
            "etl_est": ("Scraper + statistics ETL", ["GitHub Actions, Mondays"]),
            "revision": ("Manual review", ["source and verification"]),
            "cache": ("Medical cache", ["etl_medico_cache.json", "traducciones_es.json"]),
            "csv": ("Statistics data", ["data/processed/*.csv"]),
            "curados": ("Curated data", ["datos_cud.py, generators"]),
            "health": ("Checks", ["daily and monthly freshness"]),
            "api": ("FastAPI API", ["/api/cud, /api/provincias…"]),
            "sitio": ("Website", ["tabs and maps"]),
            "docs": ("API Docs", ["/docs, open data"]),
            "forms": ("Forms", ["contact and survey"]),
            "email": ("Team mailbox", ["not stored on the site"]),
        },
        "legend_flow": {"input": "Source or input", "control": "Control", "process": "Process",
                        "store": "Stored data", "endpoint": "API", "output": "What you see"},
        "uso": {
            "cud": ("Get or renew the CUD", "CUD", "requirements, steps, your province's board"),
            "sube": ("Travel for free", "CUD → SUBE", "link the CUD to the SUBE card"),
            "beneficios": ("Know what I'm entitled to", "Calculadora", "benefits for your situation"),
            "pension": ("Receive a pension", "Pensiones", "disability pension: requirements"),
            "condicion": ("Understand a condition", "Condiciones", "autism, epilepsy, vision and 10 more"),
            "tratamiento": ("Treatments and research", "Tratamientos · Médico", "PubMed, trials, cutting edge"),
            "hogar": ("Find a residential home", "Hogares", "map and addresses by province"),
            "trabajo": ("Find a job", "Inclusión Laboral", "job quotas and provincial laws"),
            "mayores": ("Older person", "Adultos Mayores", "CUD, rights and resources 65+"),
            "senas": ("Sign language", "Lengua de Señas", "LSA, Law 27,710 and courses"),
            "datos": ("See or compare data", "Estadístico · Comparador", "CUD by province and type"),
            "caba": ("I live in Buenos Aires City", "GCBA · Comuna_07", "schools, health and Comuna 7"),
            "dev": ("Use the data in my app", "API Docs", "open JSON endpoints"),
        },
        "legend_uso": {"input": "What you need", "output": "Tab (tap it to open)", "signal": "What you get"},
        "aria_flow": "Operation graph: from official and scientific sources to the site's tabs",
        "aria_uso": "Usage graph: what you need, which tab to open and what you will find",
    },
}


def _node(node_id, x, y, w, h, kind, title, lines, ir=None):
    cx = x + w / 2
    total = 16 + 14 * len(lines)
    base = y + (h - total) / 2 + 13
    attrs = f' data-ir="{ir}" tabindex="0" role="button"' if ir else ""
    out = [f'<g class="mn-node {kind}" data-node="{node_id}"{attrs}>',
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>',
           f'<text class="t" x="{cx:g}" y="{base:g}">{escape(title)}</text>']
    out += [f'<text class="s" x="{cx:g}" y="{base + 16 + 14 * i:g}">{escape(t)}</text>' for i, t in enumerate(lines)]
    out.append("</g>")
    return "".join(out)


def _svg(viewbox, aria, marker, edges, nodes_svg):
    w, h = viewbox
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}" role="img" aria-label="{escape(aria)}">'
            f'<defs><marker id="{marker}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path class="mn-arrow" d="M0 0 L10 5 L0 10 z"/></marker></defs>'
            + "".join(f'<path class="mn-edge" d="{d}" marker-end="url(#{marker})"/>' for d in edges)
            + "".join(nodes_svg) + "</svg>")


def grafo_funcionamiento(lang):
    t = GRAPH_TEXT[lang]["flow"]
    nodes = [_node(n, x, y, w, h, k, *t[n]) for n, x, y, w, h, k in FLOW_NODES]
    return _svg(FLOW_VIEWBOX, GRAPH_TEXT[lang]["aria_flow"], f"mn-af-{lang}", FLOW_EDGES, nodes)


def grafo_uso(lang):
    t = GRAPH_TEXT[lang]["uso"]
    nodes, edges = [], []
    for i, (clave, pestana) in enumerate(USO_FILAS):
        y = 10 + _USTEP * i
        necesidad, tab, resultado = t[clave]
        nodes.append(_node(f"{clave}-n", _UX[0], y, _UW[0], _UH, "input", necesidad, []))
        nodes.append(_node(f"{clave}-p", _UX[1], y, _UW[1], _UH, "output", tab, [], ir=pestana))
        nodes.append(_node(f"{clave}-r", _UX[2], y, _UW[2], _UH, "signal", resultado, []))
        cy = y + _UH / 2
        edges.append(f"M{_UX[0] + _UW[0]} {cy:g} L{_UX[1]} {cy:g}")
        edges.append(f"M{_UX[1] + _UW[1]} {cy:g} L{_UX[2]} {cy:g}")
    return _svg(USO_VIEWBOX, GRAPH_TEXT[lang]["aria_uso"], f"mn-au-{lang}", edges, nodes)


def leyenda(items):
    return '<ul class="mn-legend">' + "".join(
        f'<li><span class="mn-sw {k}"></span>{escape(v)}</li>' for k, v in items.items()) + "</ul>"


CSS = """
    #panel-manual .mn-lang{display:flex;gap:.5rem;margin:.4rem 0 1rem}
    #panel-manual .mn-lang button{border:1px solid #1d5d8c;background:#fff;color:#1d5d8c;border-radius:999px;padding:.35rem 1rem;font-weight:600;cursor:pointer}
    #panel-manual .mn-lang button[aria-pressed="true"]{background:#1d5d8c;color:#fff}
    #panel-manual .mn-graph{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid #cfe5f6;border-radius:8px;background:#fbfdff;padding:.5rem;margin:.6rem 0}
    #panel-manual .mn-graph svg{display:block;max-width:100%;min-width:640px;height:auto}
    #panel-manual .mn-node rect{stroke-width:1.4}
    #panel-manual .mn-node .t{font:600 13px system-ui,sans-serif;text-anchor:middle;fill:#1c2430}
    #panel-manual .mn-node .s{font:11px system-ui,sans-serif;text-anchor:middle;fill:#4a5562}
    #panel-manual .mn-node[data-ir]{cursor:pointer}
    #panel-manual .mn-node[data-ir]:hover rect,#panel-manual .mn-node[data-ir]:focus rect{stroke-width:2.6}
    #panel-manual .mn-node[data-ir]:focus{outline:none}
    #panel-manual .mn-edge{fill:none;stroke:#7a8794;stroke-width:1.4}
    #panel-manual .mn-arrow{fill:#7a8794}
    #panel-manual .input rect,#panel-manual .mn-sw.input{fill:#e8eefc;stroke:#3b5fc4}
    #panel-manual .control rect,#panel-manual .mn-sw.control{fill:#fdeee3;stroke:#bf6a24}
    #panel-manual .process rect,#panel-manual .mn-sw.process{fill:#eef1f5;stroke:#66717f}
    #panel-manual .store rect,#panel-manual .mn-sw.store{fill:#e3f4ea;stroke:#2c8050}
    #panel-manual .endpoint rect,#panel-manual .mn-sw.endpoint{fill:#e9e8fb;stroke:#5a50c2}
    #panel-manual .output rect,#panel-manual .mn-sw.output{fill:#fbf3d6;stroke:#94790f}
    #panel-manual .signal rect,#panel-manual .mn-sw.signal{fill:#fde8ec;stroke:#b83a55}
    #panel-manual .mn-legend{display:flex;flex-wrap:wrap;gap:.4rem 1rem;list-style:none;padding:0;margin:.3rem 0;font-size:.82rem}
    #panel-manual .mn-sw{display:inline-block;width:14px;height:14px;border:1.4px solid;border-radius:3px;margin-right:.35rem;vertical-align:-2px}
    #panel-manual .mn-tabla td:first-child{white-space:nowrap;font-weight:600}
"""

# Manual: (pestaña, texto) por idioma. Los nombres de pestaña quedan como en el menú.
MANUAL_TABS = {
    "es": [
        ("Inicio", "Resumen del sitio y accesos directos a cada sección."),
        ("CUD", "Qué es el Certificado Único de Discapacidad, requisitos, formularios, pasos, la junta evaluadora de cada provincia, beneficios, cómo vincularlo con la SUBE y preguntas frecuentes."),
        ("Medico", "Artículos científicos recientes de PubMed (con resumen en español) y ensayos clínicos que reclutan pacientes. Podés buscar por tema."),
        ("Estadistico", "CUD vigentes por provincia, por tipo de discapacidad y su evolución, con mapa del país y de las comunas de CABA."),
        ("Vanguardia", "Tratamientos nuevos o experimentales, con nivel de evidencia y aviso médico."),
        ("Calculadora", "Respondé unas preguntas y ves los beneficios que te pueden corresponder."),
        ("Pensiones", "La pensión no contributiva por discapacidad (PNC-PS, Decreto 84/2026): requisitos de referencia, cómo pedirla y causas de suspensión."),
        ("Condiciones", "Trece subpestañas (TEA, lenguaje, dislexia, hipoacusia, epilepsia, poco frecuentes, salud mental, visual, diabetes, celiaquía, fibrosis quística, cáncer infantil y trasplante) con derechos y guía práctica. Las marcadas con * esperan revisión profesional."),
        ("Tratamientos", "Musicoterapia, tratamientos visuales, otras terapias y tratamientos experimentales, con sus fuentes."),
        ("Comparador", "Elegí dos provincias y comparás prestaciones, cupo laboral y juntas lado a lado."),
        ("About (EN)", "Presentación del proyecto en inglés."),
        ("GCBA", "Escuelas de educación especial y centros de salud de la Ciudad de Buenos Aires, con mapas."),
        ("Adultos Mayores", "CUD y derechos de las personas de 65 años o más, tipologías, mapa provincial, calculadora y recursos."),
        ("Lengua de Señas", "Lengua de Señas Argentina (Ley 27.710) y recursos de otros países."),
        ("Inclusión Laboral", "Cupo de empleo público, estímulos para empresas privadas y leyes de cada provincia, con su verificación."),
        ("Hogares", "Hogares para personas con discapacidad (Pequeños Cottolengos y otros) con mapa, direcciones y el organismo de cada provincia para pedir vacante."),
        ("Manual", "Esta guía, en español e inglés, con los dos grafos."),
        ("Comuna_07", "Relevamiento vecinal de la Comuna 7 de CABA y su encuesta."),
    ],
    "en": [
        ("Inicio", "Site overview and shortcuts to every section."),
        ("CUD", "What the Single Disability Certificate (CUD) is: requirements, forms, steps, the assessment board in each province, benefits, how to link it to the SUBE transit card, and FAQs."),
        ("Medico", "Recent PubMed articles (with a Spanish summary) and clinical trials that are recruiting. You can search by topic."),
        ("Estadistico", "Active CUDs by province, by type of disability and over time, with maps of the country and of Buenos Aires City's comunas."),
        ("Vanguardia", "New or experimental treatments, with level of evidence and a medical notice."),
        ("Calculadora", "Answer a few questions to see the benefits you may be entitled to."),
        ("Pensiones", "The non-contributory disability pension (PNC-PS, Decree 84/2026): reference requirements, how to apply and grounds for suspension."),
        ("Condiciones", "Thirteen sub-tabs (autism, language, dyslexia, hearing loss, epilepsy, rare diseases, mental health, vision, diabetes, celiac disease, cystic fibrosis, childhood cancer and transplants) with rights and practical guidance. Those marked * await professional review."),
        ("Tratamientos", "Music therapy, vision treatments, other therapies and experimental treatments, with their sources."),
        ("Comparador", "Pick two provinces and compare benefits, job quotas and assessment boards side by side."),
        ("About (EN)", "Project presentation in English."),
        ("GCBA", "Special-education schools and health centres in Buenos Aires City, with maps."),
        ("Adultos Mayores", "CUD and rights for people aged 65 and over, typologies, provincial map, calculator and resources."),
        ("Lengua de Señas", "Argentine Sign Language (Law 27,710) and resources from other countries."),
        ("Inclusión Laboral", "Public-sector job quotas, incentives for private employers and each province's laws, with verification."),
        ("Hogares", "Residential homes for people with disabilities (Pequeños Cottolengos and others) with a map, addresses and each province's agency for requesting a place."),
        ("Manual", "This guide, in Spanish and English, with both graphs."),
        ("Comuna_07", "Neighbourhood survey of Comuna 7 in Buenos Aires City."),
    ],
}

TEXTOS = {
    "es": {
        "titulo": "Manual de uso del Observatorio de Discapacidad",
        "intro": "Esta guía explica cómo moverte por el sitio, qué hay en cada pestaña y de dónde salen los datos. "
                 "El sitio es un <strong>proyecto independiente, sin vínculo con organismos del Estado</strong>: "
                 "reúne información oficial y científica, pero no reemplaza a un profesional ni al trámite oficial.",
        "nav_t": "Cómo navegar",
        "nav": [
            "El <strong>menú de arriba</strong> tiene una pestaña por tema; en el celular ocupa dos filas, ninguna queda oculta.",
            "El botón <strong>«Escuchar esta página»</strong> (abajo a la izquierda) lee en voz alta la sección abierta.",
            "El botón de <strong>sobre</strong> (abajo a la derecha) abre el formulario de contacto.",
            "En los mapas, tocá un punto para ver sus datos. Las tablas que no entran en la pantalla se deslizan de costado.",
            "<strong>API Docs</strong> (al final del menú) muestra los datos abiertos en formato JSON para desarrolladores.",
            "En <strong>Inicio</strong>, la tabla <strong>«Fuentes y antigüedad de los datos»</strong> dice de dónde sale cada sección y qué tan reciente es; el pie de página tiene un enlace directo.",
        ],
        "uso_t": "Grafo de uso: ¿qué necesitás?",
        "uso_p": "Buscá tu necesidad a la izquierda y seguí la flecha. <strong>Tocá la pestaña del medio para abrirla.</strong>",
        "tabs_t": "Qué hay en cada pestaña",
        "col": ("Pestaña", "Para qué sirve"),
        "func_t": "Grafo de funcionamiento: de dónde salen los datos",
        "func_p": "Los procesos automáticos actualizan la evidencia médica cada miércoles y las estadísticas cada lunes; "
                  "el servidor además los repite cada 15 días, un control diario verifica que el sitio responda y uno mensual que los datos estén al día. "
                  "Las leyes, guías y direcciones se cargan a mano, cada una con su fuente.",
        "priv_t": "Privacidad y avisos",
        "priv": [
            "Los formularios de contacto y de encuesta se envían por correo al equipo; el sitio no los guarda en una base de datos.",
            "Se usan estadísticas de visitas de Google Analytics.",
            "La información es educativa: ante una decisión médica o legal, consultá a un profesional y al organismo oficial.",
            "¿Encontraste un error o un dato desactualizado? Avisanos desde el formulario de contacto.",
        ],
    },
    "en": {
        "titulo": "Disability Observatory user guide",
        "intro": "This guide explains how to move around the site, what each tab contains and where the data come from. "
                 "The site is an <strong>independent project, not affiliated with any government agency</strong>: "
                 "it gathers official and scientific information, but it does not replace a professional or the official procedure. "
                 "Most of the site is in Spanish; tab names are kept as they appear in the menu.",
        "nav_t": "How to navigate",
        "nav": [
            "The <strong>top menu</strong> has one tab per topic; on a phone it wraps onto two rows, so no tab is hidden.",
            "The <strong>«Escuchar esta página»</strong> button (bottom left) reads the open section aloud (in Spanish).",
            "The <strong>envelope</strong> button (bottom right) opens the contact form.",
            "On the maps, tap a point to see its details. Tables wider than the screen scroll sideways.",
            "<strong>API Docs</strong> (end of the menu) exposes the open data as JSON for developers.",
            "On <strong>Inicio</strong>, the <strong>«Fuentes y antigüedad de los datos»</strong> table shows where each section comes from and how recent it is; the footer links straight to it.",
        ],
        "uso_t": "Usage graph: what do you need?",
        "uso_p": "Find your need on the left and follow the arrow. <strong>Tap the tab in the middle to open it.</strong>",
        "tabs_t": "What each tab contains",
        "col": ("Tab", "What it is for"),
        "func_t": "Operation graph: where the data come from",
        "func_p": "Automated jobs refresh the medical evidence every Wednesday and the statistics every Monday; "
                  "the server also reruns them every 15 days, a daily check confirms the site responds and a monthly one that the data are current. "
                  "Laws, guides and addresses are entered by hand, each with its source.",
        "priv_t": "Privacy and notices",
        "priv": [
            "Contact and survey forms are emailed to the team; the site does not store them in a database.",
            "Visit statistics are collected with Google Analytics.",
            "The information is educational: for a medical or legal decision, consult a professional and the official agency.",
            "Found an error or outdated data? Tell us through the contact form.",
        ],
    },
}


def bloque_idioma(lang):
    tx = TEXTOS[lang]
    filas = "".join(f"<tr><td>{escape(t)}</td><td>{escape(d)}</td></tr>" for t, d in MANUAL_TABS[lang])
    li = lambda xs: "".join(f"<li>{x}</li>" for x in xs)  # noqa: E731 — textos propios con HTML controlado
    hidden = "" if lang == "es" else " hidden"
    return f"""      <div class="mn-idioma" lang="{lang}" data-lang="{lang}"{hidden}>
        <div class="card">
          <h2>{escape(tx["titulo"])}</h2>
          <p>{tx["intro"]}</p>
          <h3>{escape(tx["nav_t"])}</h3>
          <ul class="ls-lista">{li(tx["nav"])}</ul>
        </div>
        <div class="card">
          <h3>{escape(tx["uso_t"])}</h3>
          <p>{tx["uso_p"]}</p>
          {leyenda(GRAPH_TEXT[lang]["legend_uso"])}
          <div class="mn-graph">{grafo_uso(lang)}</div>
        </div>
        <div class="card">
          <h3>{escape(tx["tabs_t"])}</h3>
          <div class="am-table-wrap"><table class="tbl mn-tabla">
            <thead><tr><th scope="col">{escape(tx["col"][0])}</th><th scope="col">{escape(tx["col"][1])}</th></tr></thead>
            <tbody>{filas}</tbody>
          </table></div>
        </div>
        <div class="card">
          <h3>{escape(tx["func_t"])}</h3>
          <p>{escape(tx["func_p"])}</p>
          {leyenda(GRAPH_TEXT[lang]["legend_flow"])}
          <div class="mn-graph">{grafo_funcionamiento(lang)}</div>
        </div>
        <div class="card">
          <h3>{escape(tx["priv_t"])}</h3>
          <ul class="ls-lista">{li(tx["priv"])}</ul>
        </div>
      </div>"""


def panel():
    return f"""{INICIO}
  <div class="panel" id="panel-manual" aria-label="Manual / User guide">
    <style>{CSS}    </style>
    <div class="wrap wrap-wide">
      <div class="mn-lang" role="group" aria-label="Idioma / Language">
        <button type="button" data-set-lang="es" aria-pressed="true">Español</button>
        <button type="button" data-set-lang="en" aria-pressed="false">English</button>
      </div>
{bloque_idioma("es")}
{bloque_idioma("en")}
    </div>
  </div>
  <script>
    function mnIdioma(lang) {{
      document.querySelectorAll('#panel-manual .mn-idioma').forEach(d => {{ d.hidden = d.dataset.lang !== lang; }});
      document.querySelectorAll('#panel-manual [data-set-lang]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.setLang === lang)));
      try {{ localStorage.setItem('manual-lang', lang); }} catch (e) {{}}
    }}
    function mnIr(destino) {{
      if (destino === 'docs') {{ window.open('/docs', '_blank', 'noopener'); return; }}
      switchTab(destino);
    }}
    function initManual() {{
      document.querySelectorAll('#panel-manual [data-set-lang]').forEach(b => b.addEventListener('click', () => mnIdioma(b.dataset.setLang)));
      document.querySelectorAll('#panel-manual [data-ir]').forEach(n => {{
        n.addEventListener('click', () => mnIr(n.dataset.ir));
        n.addEventListener('keydown', ev => {{ if (ev.key === 'Enter' || ev.key === ' ') {{ ev.preventDefault(); mnIr(n.dataset.ir); }} }});
      }});
      let lang = 'es';
      try {{ lang = localStorage.getItem('manual-lang') || 'es'; }} catch (e) {{}}
      mnIdioma(lang === 'en' ? 'en' : 'es');
    }}
  </script>
{FIN}"""


def main():
    texto = INDEX.read_bytes().decode("utf-8")
    bloque = panel()
    if INICIO in texto:
        a, b = texto.index(INICIO), texto.index(FIN) + len(FIN)
        texto = texto[:a] + bloque + texto[b:]
    else:
        ancla = "  <!-- ====================== COMUNA_07 ====================== -->"
        texto = texto.replace(ancla, bloque + "\n\n" + ancla, 1)
    INDEX.write_bytes(texto.encode("utf-8"))
    print(f"Pestaña Manual: {len(FLOW_NODES)} nodos de funcionamiento, {3 * len(USO_FILAS)} de uso, ES/EN")


if __name__ == "__main__":
    main()
