"""
main.py — Módulo CUD Trámite
Puede correr standalone o montarse en el Observatorio principal.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from scripts.api_cud import router as router_cud

app = FastAPI(
    title="CUD — Trámite y Beneficios",
    description="Guía completa del Certificado Único de Discapacidad. Requisitos, formularios, juntas evaluadoras y beneficios.",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router_cud)


@app.get("/", response_class=HTMLResponse)
async def landing():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width,initial-scale=1.0">
      <title>CUD — Certificado Único de Discapacidad</title>
      <style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{font-family:system-ui,sans-serif;background:#f8f9fa;color:#212529}
        header{background:#1a5276;color:white;padding:2rem;text-align:center}
        header h1{font-size:1.8rem;margin-bottom:.5rem}
        .gratuito{background:#d4edda;color:#155724;border-radius:6px;
                  padding:.4rem 1rem;display:inline-block;margin-top:.5rem;font-weight:600}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
              gap:1.2rem;padding:2rem;max-width:1100px;margin:0 auto}
        .card{background:white;border-radius:10px;padding:1.5rem;
              box-shadow:0 1px 4px rgba(0,0,0,.08)}
        .card h2{color:#1a5276;margin-bottom:1rem;font-size:1rem}
        .ep{display:flex;align-items:center;gap:.5rem;padding:.35rem 0;
            border-bottom:1px solid #eee;font-size:.85rem}
        .ep:last-child{border:none}
        .tag{background:#e8f4fd;color:#1a5276;border-radius:4px;
             padding:2px 6px;font-size:.72rem;font-weight:600}
        a{color:#1a5276;text-decoration:none}
        a:hover{text-decoration:underline}
        .cta{text-align:center;padding:0 2rem 2rem;display:flex;gap:1rem;
             justify-content:center;flex-wrap:wrap}
        .btn{padding:.6rem 1.5rem;border-radius:6px;font-size:.9rem;
             display:inline-block;font-weight:600}
        .btn-primary{background:#1a5276;color:white}
        .btn-secondary{background:#27ae60;color:white}
        footer{text-align:center;padding:2rem;color:#888;font-size:.82rem}
      </style>
    </head>
    <body>
      <header>
        <h1>🪪 Certificado Único de Discapacidad</h1>
        <p>Guía completa del trámite · Requisitos · Beneficios · Juntas evaluadoras</p>
        <div class="gratuito">✅ El trámite es completamente GRATUITO</div>
      </header>

      <div class="grid">
        <div class="card">
          <h2>📋 Cómo tramitarlo</h2>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/pasos">/api/cud/pasos</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/requisitos">/api/cud/requisitos</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/requisitos?tipo=motora">/api/cud/requisitos?tipo=motora</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/formularios">/api/cud/formularios</a></div>
        </div>
        <div class="card">
          <h2>📍 Dónde tramitarlo</h2>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/juntas">/api/cud/juntas</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/juntas?provincia=CABA">/api/cud/juntas?provincia=CABA</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/consulta-estado">/api/cud/consulta-estado</a></div>
        </div>
        <div class="card">
          <h2>🎯 Beneficios</h2>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/beneficios">/api/cud/beneficios</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/sube">/api/cud/sube</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/obras-sociales">/api/cud/obras-sociales</a></div>
        </div>
        <div class="card">
          <h2>❓ Preguntas frecuentes</h2>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/faq">/api/cud/faq</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/faq?q=vence">/api/cud/faq?q=vence</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud">/api/cud</a></div>
        </div>
      </div>

      <div class="cta">
        <a href="https://www.argentina.gob.ar/tramites/sacar-turno-cud"
           target="_blank" class="btn btn-secondary">📅 Sacar turno online</a>
        <a href="/docs" class="btn btn-primary">📡 API Docs</a>
      </div>

      <footer>
        Información oficial basada en normativa ANDIS · Ley 22.431 · Ley 24.901<br>
        Para consultas oficiales: <a href="https://www.argentina.gob.ar/andis">argentina.gob.ar/andis</a>
        · 0800-333-ANDIS
      </footer>
    </body>
    </html>
    """


@app.get("/health")
async def health():
    return {"status": "ok", "module": "cud-tramite", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8001)), reload=True)
