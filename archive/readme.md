# archive — código archivado

## etl_medico_backup.py (archivado 2026-06-30)

Era una copia de respaldo de `scripts/etl_medico.py`, ligeramente más vieja
(le falta la función `_fetch_scielo_original` que sí tiene la versión actual).

Confirmado antes de archivar:

- Ningún archivo del repo lo importa (`grep -rln "etl_medico_backup" .` → vacío).
- No corre en ningún workflow de `.github/workflows/`.
- No se usa en producción (`main.py` solo importa `scripts.etl_medico`, no el backup).

Se conserva acá por las dudas en vez de borrarlo directo. Si nadie lo
necesita en un tiempo, se puede eliminar esta carpeta sin riesgo.