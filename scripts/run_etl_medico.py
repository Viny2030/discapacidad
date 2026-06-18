import sys
sys.path.insert(0, '.')
from scripts.etl_medico import run_etl_medico

resultado = run_etl_medico(max_por_query=5)
print('Artículos procesados:', resultado['resumen'].get('total_articulos', 0))
print('Ensayos clínicos:', resultado['resumen'].get('total_ensayos', 0))