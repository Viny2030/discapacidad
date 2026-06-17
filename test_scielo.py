from scripts.etl_medico import fetch_scielo, run_etl_medico

# Test 1: SciELO deshabilitado
r = fetch_scielo('motora', 'motor disability', max_results=5)
assert r == [], f'fetch_scielo deberia retornar [] pero retorno {r}'
print('OK fetch_scielo deshabilitado — sin llamadas HTTP')

# Test 2: ETL sin errores SciELO
resultado = run_etl_medico(max_por_query=1)
resumen = resultado['resumen']
assert resumen['total_scielo'] == 0
assert resumen['total_articulos'] > 0
assert resumen['total_ensayos'] > 0
print(f'OK ETL completo')
print(f'   Articulos : {resumen["total_articulos"]}')
print(f'   Ensayos   : {resumen["total_ensayos"]}')
print(f'   SciELO    : {resumen["total_scielo"]}')
print('Sin errores SciELO 404')