import sys
import json
sys.path.insert(0, '.')
from scripts.etl_estadistico import run_etl_estadistico

resultado = run_etl_estadistico()
print(json.dumps(resultado['resumen'], indent=2, ensure_ascii=False))