"""
datos_cud.py
Base de datos del trámite CUD — requisitos, juntas, beneficios, formularios.
Fuente: Secretaría Nacional de Discapacidad del Ministerio de Salud (ex ANDIS,
argentina.gob.ar/andis) + PDF oficial Ministerio de Transporte.
Juntas evaluadoras: 24 provincias completas — datos oficiales 2024.
Actualizado con la Ley 27.793 (Emergencia Nacional en Discapacidad) y su
Reglamentación, Decreto 84/2026 (Anexo I y Anexo II).
"""

FORMULARIOS = [{'id': 'solicitud_cud',
  'nombre': 'Solicitud de CUD — Formulario online ANDIS',
  'descripcion': 'Formulario principal para iniciar el trámite del CUD. Completá el cuestionario online para saber qué planilla corresponde a tu situación.',
  'url': 'https://www.argentina.gob.ar/cud/consulta-de-requisitos-para-tramitar-el-cud',
  'url_online': 'https://www.argentina.gob.ar/cud/como-obtener-el-certificado-unico-de-discapacidad-cud',
  'formato': 'Formulario online',
  'obligatorio': True},
 {'id': 'declaracion_jurada',
  'nombre': 'Declaración Jurada de Ingresos',
  'descripcion': 'Requerida para solicitar la Pensión No Contributiva por Discapacidad para Protección Social '
                 '(Ley 27.793, reglamentada por el Decreto 84/2026). Se descarga desde el portal de la '
                 'Secretaría Nacional de Discapacidad según el tipo de discapacidad.',
  'url': 'https://www.argentina.gob.ar/salud/senadis/pensiones-informacion-y-tramites',
  'url_online': 'https://www.argentina.gob.ar/andis',
  'formato': 'PDF (disponible en la junta evaluadora)',
  'obligatorio': False},
 {'id': 'autorizacion_tercero',
  'nombre': 'Autorización para tramitar por tercero',
  'descripcion': 'Cuando el trámite lo realiza un familiar, tutor o representante legal. Debe ser manuscrita y firmada por el titular.',
  'url': 'https://www.argentina.gob.ar/cud/como-obtener-el-certificado-unico-de-discapacidad-cud',
  'url_online': None,
  'formato': 'Manuscrita firmada (no requiere formulario oficial)',
  'obligatorio': False}]


REQUISITOS_GENERALES = [{'orden': 1,
  'documento': 'DNI original y fotocopia',
  'detalle': 'Vigente. Para menores: DNI del menor y del adulto responsable.',
  'obligatorio': True},
 {'orden': 2,
  'documento': 'Formulario de solicitud completo',
  'detalle': 'Descargar y completar el formulario oficial de ANDIS antes del turno.',
  'obligatorio': True,
  'url_descarga': 'https://www.argentina.gob.ar/cud/como-obtener-el-certificado-unico-de-discapacidad-cud'},
 {'orden': 3,
  'documento': 'Historia clínica o informe médico actualizado',
  'detalle': 'Emitido por médico matriculado. Diagnóstico, evolución y limitaciones funcionales. '
             'Antigüedad máxima recomendada: 6 meses.',
  'obligatorio': True},
 {'orden': 4,
  'documento': 'Estudios complementarios según tipo de discapacidad',
  'detalle': 'Análisis, imágenes, informes de especialistas según corresponda.',
  'obligatorio': True},
 {'orden': 5,
  'documento': '2 fotos 4x4 fondo blanco',
  'detalle': 'Fotografías recientes del solicitante.',
  'obligatorio': True},
 {'orden': 6,
  'documento': 'Turno previo',
  'detalle': 'Sacar turno online en argentina.gob.ar/cud/consulta-de-requisitos-para-tramitar-el-cud o '
             'llamar al 0800-555-3472 de la Secretaría Nacional de Discapacidad.',
  'obligatorio': True,
  'url': 'https://www.argentina.gob.ar/cud/consulta-de-requisitos-para-tramitar-el-cud'}]


REQUISITOS_POR_TIPO = {'motora': {'nombre': 'Discapacidad motora',
            'descripcion': 'Afecta el sistema neuromuscular o esquelético.',
            'documentos_adicionales': ['Informe neurológico o traumatológico según corresponda',
                                       'Resonancia magnética o radiografías según diagnóstico',
                                       'Informe de kinesiólogo o fisiatra (evaluación funcional)',
                                       'En caso de amputación: informe del cirujano y/o '
                                       'protetista'],
            'especialidades_evaluadoras': ['Neurólogo', 'Traumatólogo', 'Fisiatra'],
            'tip': 'El informe de evaluación funcional es fundamental para la junta evaluadora.'},
 'visual': {'nombre': 'Discapacidad visual',
            'descripcion': 'Pérdida parcial o total de la visión.',
            'documentos_adicionales': ['Informe oftalmológico con agudeza visual y campo visual '
                                       '(perimetría)',
                                       'Fondo de ojo actualizado',
                                       'En baja visión: informe de rehabilitación visual si '
                                       'existe'],
            'especialidades_evaluadoras': ['Oftalmólogo'],
            'tip': 'El campo visual (perimetría) es el estudio más importante para acreditar '
                   'discapacidad visual.'},
 'auditiva': {'nombre': 'Discapacidad auditiva',
              'descripcion': 'Pérdida parcial o total de la audición.',
              'documentos_adicionales': ['Audiometría tonal y vocal reciente (máx. 6 meses)',
                                         'Logoaudiometría',
                                         'Potenciales evocados auditivos en menores o casos '
                                         'complejos',
                                         'Informe del otorrinolaringólogo o audiólogo'],
              'especialidades_evaluadoras': ['Otorrinolaringólogo', 'Audiólogo'],
              'tip': 'La audiometría debe realizarse sin audífonos para determinar el grado real '
                     'de pérdida.'},
 'intelectual': {'nombre': 'Discapacidad intelectual',
                 'descripcion': 'Alteraciones significativas en la función intelectual.',
                 'documentos_adicionales': ['Evaluación psicológica con test de inteligencia '
                                            '(WISC, WAIS según edad)',
                                            'Informe neurológico o neuropediátrico',
                                            'Informe escolar o de institución educativa especial '
                                            'si aplica',
                                            'Para TEA: informe diagnóstico con escala DSM-5 o '
                                            'CIE-11'],
                 'especialidades_evaluadoras': ['Psicólogo',
                                                'Neurólogo/Neuropediatra',
                                                'Psiquiatra'],
                 'tip': 'Para TEA sin compromiso intelectual el CUD puede otorgarse igualmente. '
                        'Documentar las dificultades en la vida cotidiana.'},
 'psicosocial': {'nombre': 'Discapacidad psicosocial (salud mental)',
                 'descripcion': 'Alteraciones en la conducta adaptativa y la salud mental.',
                 'documentos_adicionales': ['Informe psiquiátrico actualizado con diagnóstico '
                                            'DSM-5/CIE-11',
                                            'Historia clínica de internaciones previas si aplica',
                                            'Informe de psicólogo tratante',
                                            'Constancia de tratamiento actual'],
                 'especialidades_evaluadoras': ['Psiquiatra', 'Psicólogo'],
                 'tip': 'El criterio es la limitación funcional en la vida cotidiana, no solo el '
                        'diagnóstico.'},
 'visceral': {'nombre': 'Discapacidad visceral / orgánica',
              'descripcion': 'Afecta órganos internos.',
              'documentos_adicionales': ['Informe del médico especialista en el órgano afectado',
                                         'Estudios de función orgánica actualizados',
                                         'En insuficiencia renal: informe de nefrología',
                                         'Para enfermedades raras: informe de centro de '
                                         'referencia'],
              'especialidades_evaluadoras': ['Especialista del órgano afectado', 'Médico clínico'],
              'tip': 'Para enfermedades raras, el diagnóstico de un centro de referencia nacional '
                     'tiene mayor peso.'}}


PASOS_TRAMITE = [{'paso': 1,
  'titulo': 'Reunir la documentación',
  'descripcion': 'Juntá el DNI, formulario completado, informes médicos, estudios y fotos.',
  'duracion_estimada': 'Variable — depende de conseguir turnos médicos',
  'url': None,
  'tip': 'Empezá por pedir el informe a tu médico tratante. Explicale que es para el CUD.'},
 {'paso': 2,
  'titulo': 'Sacar turno en la Junta Evaluadora',
  'descripcion': 'Sacá turno online o llamá al 0800 de tu provincia.',
  'duracion_estimada': '1 a 30 días según provincia',
  'url': 'https://www.argentina.gob.ar/cud/consulta-de-requisitos-para-tramitar-el-cud',
  'tip': 'Sacar el turno mientras juntás los documentos para no perder tiempo.'},
 {'paso': 3,
  'titulo': 'Presentarse a la Junta Evaluadora',
  'descripcion': 'Concurrí en la fecha y hora del turno con TODA la documentación.',
  'duracion_estimada': '1 día (la entrevista dura 30-60 min aprox.)',
  'url': None,
  'tip': 'Llevá copias de todo. Si no podés trasladarte, en muchos casos hay evaluación '
         'domiciliaria.'},
 {'paso': 4,
  'titulo': 'Evaluación interdisciplinaria',
  'descripcion': 'La junta evalúa la documentación y al solicitante. Pueden pedir estudios '
                 'adicionales.',
  'duracion_estimada': 'En el momento o hasta 30 días hábiles',
  'url': None,
  'tip': 'Si te piden estudios adicionales, preguntá exactamente qué necesitan y los plazos.'},
 {'paso': 5,
  'titulo': 'Resolución y emisión del CUD',
  'descripcion': 'Si se aprueba, se emite el CUD físico y/o digital (app Mi Argentina).',
  'duracion_estimada': '30 a 90 días hábiles según provincia',
  'url': 'https://www.argentina.gob.ar/andis',
  'tip': 'Podés consultar el estado en argentina.gob.ar/andis/consultas-publicas con tu DNI.'},
 {'paso': 6,
  'titulo': 'Descargar el CUD digital',
  'descripcion': 'Una vez emitido, el CUD digital está disponible en la app Mi Argentina.',
  'duracion_estimada': 'Inmediato una vez notificado',
  'url': 'https://mi.argentina.gob.ar',
  'tip': 'El CUD digital tiene la misma validez legal que el físico.'}]


BENEFICIOS = [{'categoria': 'Salud',
  'icono': '🏥',
  'beneficios': [{'nombre': 'Cobertura médica integral',
                  'detalle': '100% de cobertura en prestaciones de rehabilitación vinculadas a la '
                             'discapacidad (Ley 24.901).',
                  'normativa': 'Ley 24.901'},
                 {'nombre': 'Medicamentos sin cargo',
                  'detalle': 'Medicamentos relacionados con la discapacidad sin costo.',
                  'normativa': 'Ley 24.901'},
                 {'nombre': 'Prestaciones de apoyo',
                  'detalle': 'Asistente personal, acompañante terapéutico, transporte sanitario.',
                  'normativa': 'Ley 24.901'}]},
 {'categoria': 'Transporte',
  'icono': '🚌',
  'beneficios': [{'nombre': 'Transporte público gratuito',
                  'detalle': '100% de descuento en colectivos, trenes y subtes de todo el país. '
                             'Registrar CUD en SUBE.',
                  'normativa': 'Ley 22.431 / CNRT',
                  'url': 'https://www.argentina.gob.ar/salud/senadis/asociar-el-certificado-unico-de-discapacidad-cud-la-tarjeta-sube'},
                 {'nombre': 'Franquicia aerocomercial',
                  'detalle': 'Descuento en pasajes aéreos de cabotaje para la persona y un '
                             'acompañante.',
                  'normativa': 'Resolución ANAC'}]},
 {'categoria': 'Educación',
  'icono': '📚',
  'beneficios': [{'nombre': 'Educación especial e integrada',
                  'detalle': 'Maestras integradoras y apoyos pedagógicos financiados por la obra '
                             'social.',
                  'normativa': 'Ley 26.206 / Ley 24.901'},
                 {'nombre': 'Ayuda escolar anual',
                  'detalle': 'Asignación familiar especial para hijo con discapacidad (ANSES).',
                  'normativa': 'Ley 24.714',
                  'url': 'https://www.anses.gob.ar/informacion/asignacion-familiar-por-hijo-con-discapacidad'}]},
 {'categoria': 'Trabajo',
  'icono': '💼',
  'beneficios': [{'nombre': 'Cupo laboral en el Estado',
                  'detalle': '4% de los cargos del Estado Nacional deben ser cubiertos por '
                             'personas con discapacidad.',
                  'normativa': 'Ley 22.431 art. 8'},
                 {'nombre': 'Incentivos para empleadores',
                  'detalle': 'Empresas que contraten personas con CUD tienen reducciones en '
                             'contribuciones patronales.',
                  'normativa': 'Ley 22.431'}]},
 {'categoria': 'Impuestos y económico',
  'icono': '💰',
  'beneficios': [{'nombre': 'Exención en Ganancias',
                  'detalle': 'Las personas con CUD pueden estar exentas del impuesto a las '
                             'ganancias.',
                  'normativa': 'Ley 20.628'},
                 {'nombre': 'Pensión No Contributiva por Discapacidad para Protección Social',
                  'detalle': 'Para personas con discapacidad sin obra social ni ingresos suficientes. '
                             'Reemplaza a la ex "pensión por invalidez"; quienes ya cobraban esta última '
                             'pasan de forma automática (conversión de oficio) al nuevo régimen. Los '
                             'criterios de acceso (porcentaje de incapacidad, tope de ingresos) están '
                             'pendientes de acuerdo entre la Secretaría Nacional de Discapacidad y el '
                             'Consejo Federal de Discapacidad.',
                  'normativa': 'Ley 27.793 / Decreto 84/2026 (Anexo I y Anexo II)',
                  'url': 'https://www.argentina.gob.ar/salud/senadis/pensiones-informacion-y-tramites'},
                 {'nombre': 'Moratoria impositiva para prestadores de la Ley 24.901',
                  'detalle': 'Régimen de regularización de deudas impositivas, aduaneras y de la '
                             'seguridad social vencidas al 31/12/2025, con condonación de hasta el '
                             '100% de intereses y de determinadas multas. Lo administra ARCA (ex AFIP) '
                             'sobre la nómina que remite la Secretaría Nacional de Discapacidad.',
                  'normativa': 'Decreto 84/2026, Art. 4° inciso b) Anexo I'},
                 {'nombre': 'Exención en patente de vehículos',
                  'detalle': 'Exención o reducción en el pago de patente del vehículo adaptado.',
                  'normativa': 'Varía por provincia'}]},
 {'categoria': 'Vivienda',
  'icono': '🏠',
  'beneficios': [{'nombre': 'Accesibilidad en viviendas del Estado',
                  'detalle': 'Prioridad en acceso a viviendas sociales accesibles.',
                  'normativa': 'Ley 24.314'}]}]


JUNTAS_POR_PROVINCIA = {'Buenos Aires': {'nombre_organismo': 'Dirección Provincial de Discapacidad — Provincia de Buenos '
                                      'Aires',
                  'url_turno': 'https://www.argentina.gob.ar/andis/juntas-evaluadoras-cud',
                  'telefono': '0800-222-2427',
                  'email': 'discapacidad@gba.gob.ar',
                  'turno_online': True,
                  'tiempo_espera_estimado': '20-45 días',
                  'nota': 'La provincia tiene juntas en todos los municipios. Ver listado completo '
                          'en el portal provincial.',
                  'sedes': [{'nombre': 'Dirección Provincial — La Plata',
                             'direccion': 'Calle 8, esq. 67 Nº 1689, La Plata'},
                            {'nombre': 'Hospital R. Rossi — La Plata',
                             'direccion': 'Calle 37 e/ 116 y 117, La Plata',
                             'telefono': '0221-4822-8821'},
                            {'nombre': 'Hospital San Martín — La Plata',
                             'direccion': 'Calle 69 y 116, La Plata',
                             'telefono': '0221-4211190'},
                            {'nombre': 'Hospital Paroissien — La Matanza',
                             'direccion': 'Ruta 3 km. 21, Isidro Casanova',
                             'telefono': '4669-2828'},
                            {'nombre': 'Hospital Melo — Lanús',
                             'direccion': 'Av. Villa de Luján 3050, Remedios de Escalada',
                             'telefono': '4246-0868'},
                            {'nombre': 'Dirección de Discapacidad — Mar del Plata',
                             'direccion': 'Pescadores 456, Mar del Plata',
                             'telefono': '0223-4803053'},
                            {'nombre': 'Dirección de Discapacidad — Bahía Blanca',
                             'direccion': 'Chiclana 451, Bahía Blanca',
                             'telefono': '0291-5506000'}]},
 'CABA': {'nombre_organismo': 'COPIDIS — Comisión para la Plena Participación e Inclusión de las '
                              'Personas con Discapacidad',
          'url_turno': 'https://buenosaires.gob.ar/tramites/solicitud-del-certificado-unico-de-discapacidad-cud',
          'telefono': '0800-999-2727 opción 3',
          'email': 'discapacidadba@buenosaires.gob.ar',
          'turno_online': True,
          'tiempo_espera_estimado': '15-30 días',
          'nota': 'Las juntas en CABA están distribuidas por tipo de discapacidad.',
          'sedes': [{'nombre': 'IREP — Discapacidad Motora',
                     'direccion': 'Echeverría 955, Belgrano',
                     'telefono': '4781-6071 int. 1083',
                     'tipo': 'motora'},
                    {'nombre': 'Hospital Rocca — Motora y Auditiva',
                     'direccion': 'Segurola 1949, Flores',
                     'telefono': '4630-4728',
                     'tipo': 'motora/auditiva'},
                    {'nombre': 'Hospital Santa Lucía — Visual',
                     'direccion': 'Av. San Juan 2021 y Sarandí, San Cristóbal',
                     'telefono': '4121-3193',
                     'tipo': 'visual'},
                    {'nombre': 'Hospital Álvear — Salud Mental adultos',
                     'direccion': 'Warnes 2630, Agronomía',
                     'telefono': '4521-0983',
                     'tipo': 'psicosocial'},
                    {'nombre': 'Hospital Piñero — Menores de 18 años',
                     'direccion': 'Varela 1307 y Viola, Flores',
                     'telefono': '4631-8601',
                     'tipo': 'todas (menores)'},
                    {'nombre': 'Hospital Penna — Visceral adultos',
                     'direccion': 'Pedro Chutro 3380, Parque Patricios',
                     'telefono': '4911-3030 int. 106',
                     'tipo': 'visceral'}]},
 'Catamarca': {'nombre_organismo': 'Dirección de Asistencia Integral a Personas con Discapacidad',
               'url_turno': 'https://www.catamarca.gov.ar',
               'telefono': '(03833) 437921 / 437913',
               'email': 'discapacidadctca@yahoo.com.ar',
               'turno_online': False,
               'tiempo_espera_estimado': '15-30 días',
               'sedes': [{'nombre': 'Sede Central',
                          'direccion': 'Av. Juan D. Perón 11 esq. Av. Arturo Illia, San Fernando '
                                       'del Valle de Catamarca',
                          'telefono': '(03833) 437921'}]},
 'Chaco': {'nombre_organismo': 'Junta Central Evaluadora — Hospital Julio C. Perrando',
           'url_turno': 'https://www.chaco.gov.ar',
           'telefono': '(03722) 425050 / 442399 / 456446',
           'email': None,
           'turno_online': False,
           'tiempo_espera_estimado': '15-30 días',
           'sedes': [{'nombre': 'Hospital Julio C. Perrando — Resistencia (Junta Central)',
                      'direccion': 'Av. 9 de Julio 1099, Resistencia',
                      'telefono': '(03722) 425050'},
                     {'nombre': 'Hospital General Güemes — Juan José Castelli',
                      'direccion': 'Av. San Martín 1050, Juan José Castelli',
                      'telefono': '(03732) 471006'},
                     {'nombre': 'Hospital 9 de Julio — Las Breñas',
                      'direccion': 'Arbo y Blanco S/N, Las Breñas',
                      'telefono': '(03731) 460034'},
                     {'nombre': 'Hospital 4 de Julio — Presidencia R. Sáenz Peña',
                      'direccion': 'Malvinas Argentinas S/N 1350',
                      'telefono': '(03644) 424568'},
                     {'nombre': 'Hospital Salvador Mazza — Villa Ángela',
                      'direccion': 'Josefa Rosello y Freire, Villa Ángela',
                      'telefono': '(03735) 429065'}]},
 'Chubut': {'nombre_organismo': 'Secretaría de Salud — Dirección de Discapacidad',
            'url_turno': 'https://www.chubut.gov.ar',
            'telefono': '0800 222 8582',
            'email': None,
            'turno_online': False,
            'tiempo_espera_estimado': '15-30 días',
            'sedes': [{'nombre': 'Sede Central — Rawson', 'direccion': 'Moreno 555, Rawson'},
                      {'nombre': 'Hospital Regional — Comodoro Rivadavia',
                       'direccion': 'H. Yrigoyen 950, Comodoro Rivadavia',
                       'telefono': '(0297) 4473563'},
                      {'nombre': 'Hospital Zonal — Esquel',
                       'direccion': 'Roca 145, Esquel',
                       'telefono': '(02945) 451224'},
                      {'nombre': 'Hospital Sub-zonal — Puerto Madryn',
                       'direccion': 'Pujol 247, Puerto Madryn',
                       'telefono': '(02964) 453030'},
                      {'nombre': 'Hospital Sub-zonal — Rawson',
                       'direccion': 'Julio A. Roca 545, Rawson',
                       'telefono': '(02965) 481260'},
                      {'nombre': 'Serv. Rehabilitación Pichi Anul — Trelew',
                       'direccion': 'San Martín 518, Trelew',
                       'telefono': '(02965) 427670'},
                      {'nombre': 'Hospital Trevelin',
                       'direccion': 'Av. San Martín 995, Trevelin',
                       'telefono': '(02965) 480132'}]},
 'Córdoba': {'nombre_organismo': 'Junta Central Evaluadora de Personas — Ministerio de Salud',
             'url_turno': 'https://www.cba.gov.ar/discapacidad',
             'telefono': '(0351) 4341511 / 4688692',
             'email': None,
             'turno_online': True,
             'tiempo_espera_estimado': '15-30 días',
             'sedes': [{'nombre': 'Junta Central Evaluadora',
                        'direccion': 'Av. Vélez Sarsfield 2311, Córdoba Capital',
                        'telefono': '(0351) 4341511'},
                       {'nombre': 'Centro Nacional de Reconocimientos Médicos',
                        'direccion': '9 de Julio 360, Capital',
                        'telefono': '(0351) 421-5304'},
                       {'nombre': 'Hospital de Córdoba',
                        'direccion': 'Av. Patria 656, Barrio Pueyrredón, Capital'},
                       {'nombre': 'Hospital de Niños Santísima Trinidad',
                        'direccion': 'Bajada Pucará S/N, Barrio Crisol'},
                       {'nombre': 'Hospital Regional Dr. Romagosa — Dean Funes',
                        'direccion': 'Colón 247, Dean Funes'},
                       {'nombre': 'Hospital Central San Antonio de Padua — Río Cuarto',
                        'direccion': 'Gral. Mosconi 48, Río Cuarto'},
                       {'nombre': 'Hospital Regional Pasteur — Villa María',
                        'direccion': 'Pasteur Mendoza 2152, Villa María'}]},
 'Corrientes': {'nombre_organismo': 'Junta Central Evaluadora de Personas — Ministerio de Salud',
                'url_turno': 'https://salud.corrientes.gov.ar',
                'telefono': '(03783) 424842',
                'email': None,
                'turno_online': False,
                'tiempo_espera_estimado': '15-30 días',
                'sedes': [{'nombre': 'Junta Central — Corrientes Capital',
                           'direccion': 'Santa Fe 762, Corrientes Capital',
                           'telefono': '(03783) 424842'},
                          {'nombre': 'Instituto Correntino de Ayuda al Lisiado',
                           'direccion': 'San Lorenzo 784, Corrientes',
                           'telefono': '(03783) 424642'},
                          {'nombre': 'Hospital Dr. Camilo Maniagurria — Goya',
                           'direccion': 'Av. Mazzanti 550, Goya',
                           'telefono': '(03777) 422283'}]},
 'Entre Ríos': {'nombre_organismo': 'IPRODICH — Instituto Provincial del Discapacitado de Entre '
                                    'Ríos',
                'url_turno': 'https://www.iprodich.gob.ar',
                'telefono': '(0343) 4208280 / 4208281',
                'email': 'ipdiscapacidad@yahoo.com.ar',
                'turno_online': False,
                'tiempo_espera_estimado': '15-30 días',
                'sedes': [{'nombre': 'IPRODICH — Sede Central Paraná',
                           'direccion': 'Gregoria Matorras de San Martín 861 y Azcuénaga, Paraná',
                           'telefono': '(0343) 4208280'}]},
 'Formosa': {'nombre_organismo': 'Junta Central Evaluadora — Ministerio de Desarrollo Humano',
             'url_turno': 'https://www.formosa.gob.ar',
             'telefono': '(03717) 436446',
             'email': None,
             'turno_online': False,
             'tiempo_espera_estimado': '15-30 días',
             'sedes': [{'nombre': 'Junta Central — Centro de Día',
                        'direccion': 'Junín y Yunká, Formosa Capital',
                        'telefono': '(03717) 436446'},
                       {'nombre': 'Ministerio de Desarrollo Humano',
                        'direccion': 'Santa Fe 1260, Formosa Capital',
                        'telefono': '(03717) 427515'},
                       {'nombre': 'Hospital Dr. Cruz Felipe Arnedo — Clorinda',
                        'direccion': 'San Martín y Los Andes, Clorinda',
                        'telefono': '(03718) 422800'},
                       {'nombre': 'Hospital Laguna Blanca',
                        'direccion': 'Esteban Florentín S/N, Laguna Blanca',
                        'telefono': '(03718) 470020'}]},
 'Jujuy': {'nombre_organismo': 'Departamento Provincial de Rehabilitación — Ministerio de '
                               'Bienestar Social',
           'url_turno': 'https://salud.jujuy.gob.ar',
           'telefono': '(0388) 4234243 / 44221308',
           'email': None,
           'turno_online': False,
           'tiempo_espera_estimado': '15-30 días',
           'sedes': [{'nombre': 'Sede Central — San Salvador de Jujuy',
                      'direccion': 'Independencia 41, San Salvador de Jujuy',
                      'telefono': '(0388) 4234243'}]},
 'La Pampa': {'nombre_organismo': 'Dirección de Discapacidad — Ministerio de Bienestar Social',
              'url_turno': 'https://www.lapampa.gob.ar',
              'telefono': '(02954) 453953',
              'email': None,
              'turno_online': False,
              'tiempo_espera_estimado': '10-20 días',
              'sedes': [{'nombre': 'Dirección de Discapacidad — Santa Rosa',
                         'direccion': 'Av. Julio A. Roca 851, Santa Rosa',
                         'telefono': '(02954) 453953'},
                        {'nombre': 'Centro Abudara — General Pico',
                         'direccion': 'S/C, S/N (ex Hospital Ferroviario), General Pico',
                         'telefono': '(02302) 431994'}]},
 'La Rioja': {'nombre_organismo': 'Juntas Evaluadoras — Ministerio de Salud',
              'url_turno': 'https://salud.larioja.gov.ar',
              'telefono': '(03822) 453552',
              'email': None,
              'turno_online': False,
              'tiempo_espera_estimado': '15-30 días',
              'sedes': [{'nombre': 'Hospital Enrique Vera Barros — La Rioja Capital',
                         'direccion': 'Olta S/N, La Rioja Capital',
                         'telefono': '(03822) 453552'},
                        {'nombre': 'Hospital San Nicolás — Aimogasta',
                         'direccion': 'Casimiro Godoy S/N, Aimogasta',
                         'telefono': '(03827) 429004'},
                        {'nombre': 'Hospital Luis Agote — Chamical',
                         'direccion': 'Constantino Carver esq. El Chacho, Chamical',
                         'telefono': '(03826) 429020'},
                        {'nombre': 'Hospital Luis Pasteur — Chepes',
                         'direccion': 'San Juan 255, Chepes',
                         'telefono': '(03821) 429105'},
                        {'nombre': 'Hospital Eleazar H. Mota — Chilecito',
                         'direccion': 'Cabero 500, Chilecito'}]},
 'Mendoza': {'nombre_organismo': 'Gerencia de Discapacidad — Ministerio de Salud',
             'url_turno': 'https://www.mendoza.gov.ar',
             'telefono': '(0261) 4254780',
             'email': None,
             'turno_online': True,
             'tiempo_espera_estimado': '15-30 días',
             'sedes': [{'nombre': 'Junta Central — Mendoza Capital',
                        'direccion': 'España 922, Mendoza Capital',
                        'telefono': '(0261) 4254780'},
                       {'nombre': 'Gerencia de Discapacidad',
                        'direccion': 'Colón 659, Mendoza Capital',
                        'telefono': '(0261) 4254780 int. 113'},
                       {'nombre': 'Junta — Las Heras',
                        'direccion': 'San Miguel 1457, Las Heras',
                        'telefono': '4378126'},
                       {'nombre': 'Junta — Guaymallén',
                        'direccion': 'Mitre y Godoy Cruz, Guaymallén',
                        'telefono': '4498204'},
                       {'nombre': 'Junta — Maipú',
                        'direccion': 'Barcala 155 e/Pescara y Padre Vázquez, Maipú',
                        'telefono': '4974285'},
                       {'nombre': 'Junta — San Rafael',
                        'direccion': 'Córdoba 156, San Rafael',
                        'telefono': '(0260) 449279'},
                       {'nombre': 'Junta — San Martín',
                        'direccion': 'Almirante Brown y España, San Martín',
                        'telefono': '(0263) 420362'},
                       {'nombre': 'Junta — Tunuyán / San Carlos',
                        'direccion': 'Hospital Regional Dr. A. Scaravelli, Tunuyán',
                        'telefono': '(02622) 411963'},
                       {'nombre': 'Junta — General Alvear',
                        'direccion': 'San Rafael 175, General Alvear',
                        'telefono': '(02625) 425861'},
                       {'nombre': 'Junta — Malargüe',
                        'direccion': 'Vacunatorio Central, Malargüe',
                        'telefono': '(02627) 4710505'}]},
 'Misiones': {'nombre_organismo': 'Dirección de Discapacidad — Ministerio de Salud Pública',
              'url_turno': 'https://salud.misiones.gob.ar',
              'telefono': '(0376) 444082 / 441426',
              'email': 'discapacidad_misiones@hotmail.com',
              'turno_online': False,
              'tiempo_espera_estimado': '10-25 días',
              'sedes': [{'nombre': 'Junta Central — Posadas',
                         'direccion': 'Junín y Tucumán, Posadas',
                         'telefono': '(0376) 444082'},
                        {'nombre': 'Junta Evaluadora — Eldorado',
                         'direccion': 'Calle Mbororé, Eldorado'},
                        {'nombre': 'Hospital SAMIC — Oberá',
                         'direccion': 'Calle Pincén y Federación S/N, Oberá',
                         'telefono': '03755-421226',
                         'email': 'cudzonacentroturuguay@gmail.com'},
                        {'nombre': 'Zona Sur — Leandro N. Alem',
                         'direccion': '25 de Mayo 1076, Leandro N. Alem',
                         'telefono': '03754-533509'},
                        {'nombre': 'Junta — Jardín América',
                         'direccion': 'Fray Bonifacio Ortiz y Ruta Provincial 7, Jardín América',
                         'telefono': '3743-610701'},
                        {'nombre': 'Hospital de Iguazú',
                         'direccion': 'Victoria Aguirre 142, Puerto Iguazú',
                         'telefono': '3755-546269'},
                        {'nombre': 'CIC — Andresito',
                         'direccion': 'Av. Corrientes y Catamarca, Andresito',
                         'telefono': '3757-304839'},
                        {'nombre': 'Junta — San Vicente',
                         'direccion': 'Calle Abel Sínuka 48, San Vicente',
                         'telefono': '3755-546269'},
                        {'nombre': 'Hospital San Antonio — San Antonio',
                         'direccion': 'Av. Andrés Guacurarí 750, San Antonio'}]},
 'Neuquén': {'nombre_organismo': 'JUCAID — Junta Coordinadora para la Atención Integral del '
                                 'Discapacitado',
             'url_turno': 'https://www.neuquen.gov.ar',
             'telefono': '(0299) 4495552',
             'email': None,
             'turno_online': False,
             'tiempo_espera_estimado': '10-20 días',
             'sedes': [{'nombre': 'JUCAID — Neuquén Capital',
                        'direccion': 'Salta 265, Neuquén Capital (CP 8300)',
                        'telefono': '(0299) 4495552'}]},
 'Río Negro': {'nombre_organismo': 'Consejo Provincial del Discapacitado — Junta Central',
               'url_turno': 'https://www.rionegro.gov.ar',
               'telefono': '(02920) 421833',
               'email': None,
               'turno_online': False,
               'tiempo_espera_estimado': '10-20 días',
               'sedes': [{'nombre': 'Consejo Provincial del Discapacitado — Viedma',
                          'direccion': 'Laprida 226, Viedma',
                          'telefono': '(02920) 421833'}]},
 'Salta': {'nombre_organismo': 'Junta Central Evaluadora — Secretaría de Asistencia Médica',
           'url_turno': 'https://www.salta.gov.ar',
           'telefono': '(0387) 4375146 / 4314866',
           'email': None,
           'turno_online': False,
           'tiempo_espera_estimado': '15-30 días',
           'sedes': [{'nombre': 'Junta Central Evaluadora — Salta Capital',
                      'direccion': 'Gral. Güemes 562, Salta Capital',
                      'telefono': '(0387) 4375146'},
                     {'nombre': 'Secretaría de Asistencia Médica',
                      'direccion': 'Lerma 800, Salta Capital',
                      'telefono': '(0387) 4375146'}]},
 'San Juan': {'nombre_organismo': 'Dirección de la Persona con Capacidades Especiales',
              'url_turno': 'https://www.sanjuan.gov.ar',
              'telefono': '(0264) 4216606',
              'email': None,
              'turno_online': False,
              'tiempo_espera_estimado': '15-30 días',
              'sedes': [{'nombre': 'Dirección de la Persona con Capacidades Especiales',
                         'direccion': 'Gral. Acha 534 (s), San Juan Capital',
                         'telefono': '(0264) 4216606'},
                        {'nombre': 'Sub-Junta Médica Evaluadora',
                         'direccion': 'Mendoza 398 (sur), San Juan Capital',
                         'telefono': '(0264) 4226609'}]},
 'San Luis': {'nombre_organismo': 'Centro de Referencia Provincial de Rehabilitación',
              'url_turno': 'https://www.sanluis.gov.ar',
              'telefono': '(02652) 425046 / 431079',
              'email': None,
              'turno_online': False,
              'tiempo_espera_estimado': '10-20 días',
              'sedes': [{'nombre': 'Centro de Referencia Provincial de Rehabilitación',
                         'direccion': 'Ciudad del Rosario y Pasteur, San Luis Capital',
                         'telefono': '(02652) 425046'}]},
 'Santa Cruz': {'nombre_organismo': 'Área de Discapacidad — Subsecretaría de Salud Pública',
                'url_turno': 'https://www.santacruz.gov.ar',
                'telefono': '(02966) 426173 / 420535',
                'email': None,
                'turno_online': False,
                'tiempo_espera_estimado': '10-20 días',
                'sedes': [{'nombre': 'Área de Discapacidad — Río Gallegos',
                           'direccion': 'Salta 55, Río Gallegos',
                           'telefono': '(02966) 426173'}]},
 'Santa Fe': {'nombre_organismo': 'Dirección Provincial de Inclusión de Personas con Discapacidad',
              'url_turno': 'https://www.santafe.gov.ar/discapacidad',
              'telefono': '0800-888-3588',
              'email': None,
              'turno_online': True,
              'tiempo_espera_estimado': '10-25 días',
              'sedes': [{'nombre': 'Junta Central — Santa Fe Capital',
                         'direccion': 'Dr. Zavalla 3361 2° piso, Santa Fe Capital',
                         'telefono': '(0342) 4572481'},
                        {'nombre': 'Dirección Provincial de Rehabilitación',
                         'direccion': 'Bv. Zavalla 3361, Santa Fe',
                         'telefono': '(0342) 4572483'},
                        {'nombre': 'CEMAR — Rosario (2da. Circunscripción)',
                         'direccion': '9 de Julio 325, Rosario',
                         'telefono': '(0341) 4721164'},
                        {'nombre': 'Hospital Granadero Baigorria',
                         'direccion': 'Av. San Martín 1645, Granadero Baigorria',
                         'telefono': '(0341) 4721164'},
                        {'nombre': 'SAMCO Reconquista',
                         'direccion': 'Hipólito Irigoyen 1580, Reconquista',
                         'telefono': '(03482) 420012'},
                        {'nombre': 'SAMCO Rafaela',
                         'direccion': 'Lisandro de la Torre 373, Rafaela',
                         'telefono': '(03492) 421621'},
                        {'nombre': 'Hospital San José — Casilda',
                         'direccion': '9 de Julio 2351, Casilda',
                         'telefono': '(03464) 422382'},
                        {'nombre': 'Hospital Alejandro Gutiérrez — Venado Tuerto',
                         'direccion': 'Gutiérrez 55, Venado Tuerto',
                         'telefono': '(03462) 439098'}]},
 'Santiago del Estero': {'nombre_organismo': 'Dirección Provincial de Discapacidad',
                         'url_turno': 'https://www.santiago.gov.ar',
                         'telefono': '(0385) 4242207',
                         'email': None,
                         'turno_online': False,
                         'tiempo_espera_estimado': '15-30 días',
                         'sedes': [{'nombre': 'Dirección Provincial de Discapacidad',
                                    'direccion': 'Güemes y Misiones, Santiago del Estero Capital',
                                    'telefono': '(0385) 4242207'}]},
 'Tierra del Fuego': {'nombre_organismo': 'Secretaría General de Acción Social — Dirección de '
                                          'Discapacidad',
                      'url_turno': 'https://www.tierradelfuego.gob.ar',
                      'telefono': '(02901) 431159',
                      'email': None,
                      'turno_online': False,
                      'tiempo_espera_estimado': '10-20 días',
                      'sedes': [{'nombre': 'Dirección de Discapacidad — Ushuaia',
                                 'direccion': 'San Martín 450, 1° Piso, Ushuaia',
                                 'telefono': '(02901) 431159'}]},
 'Tucumán': {'nombre_organismo': 'Junta de Evaluación de Discapacidad y Categorización de '
                                 'Prestadores',
             'url_turno': 'https://salud.tucuman.gov.ar',
             'telefono': '(0381) 452-6291 / 6292',
             'email': None,
             'turno_online': False,
             'tiempo_espera_estimado': '15-30 días',
             'sedes': [{'nombre': 'Junta de Evaluación — San Miguel de Tucumán',
                        'direccion': 'Alberdi 416, San Miguel de Tucumán',
                        'telefono': '(0381) 452-6291'}]}}


FAQ = [{'pregunta': '¿El trámite del CUD es gratuito?',
  'respuesta': 'Sí, el trámite del CUD es completamente gratuito. Ningún organismo puede cobrar '
               'por la emisión del certificado.'},
 {'pregunta': '¿El CUD vence?',
  'respuesta': 'Desde la Resolución ANDIS 322/2023, el CUD se otorga sin fecha de vencimiento '
               'mientras las condiciones certificantes se mantengan. Los CUD anteriores mantienen '
               'su validez.'},
 {'pregunta': '¿Puedo tramitar el CUD si vivo en el interior del país?',
  'respuesta': 'Sí. Cada provincia tiene su propia Junta Evaluadora. El trámite se realiza en la '
               'jurisdicción donde residís según tu DNI.'},
 {'pregunta': '¿Qué pasa si me rechazan el CUD?',
  'respuesta': 'Podés apelar la resolución dentro de los 30 días hábiles ante la misma Junta o el '
               'organismo provincial. Es recomendable presentar documentación adicional.'},
 {'pregunta': '¿El CUD es lo mismo que la pensión por discapacidad?',
  'respuesta': 'No. El CUD certifica la discapacidad. La Pensión No Contributiva por Discapacidad para '
               'Protección Social (Ley 27.793 / Decreto 84/2026) es una prestación económica diferente '
               'que puede solicitarse con el CUD pero tiene requisitos propios.'},
 {'pregunta': '¿Tengo que volver a tramitar mi pensión por invalidez con la nueva ley?',
  'respuesta': 'No. Si ya cobrabas una pensión no contributiva otorgada antes de la Ley 27.793, la '
               'conversión a la nueva Pensión No Contributiva por Discapacidad para Protección Social es '
               'automática ("de oficio"), a cargo de la Secretaría Nacional de Discapacidad. Mientras se '
               'tramita, seguís cobrando el beneficio que ya tenías (Art. 9° Anexo I, Decreto 84/2026).'},
 {'pregunta': '¿Cambiaron los criterios para certificar el CUD con el Decreto 84/2026?',
  'respuesta': 'Todavía no. El Art. 11 del Anexo I del Decreto 84/2026 establece que la Secretaría '
               'Nacional de Discapacidad dictará nuevos lineamientos de certificación, previa '
               'intervención del Consejo Federal de Discapacidad, pero al momento no modificó los '
               'criterios vigentes de la Resolución ANDIS 322/2023.'},
 {'pregunta': '¿Puedo tener CUD y trabajar?',
  'respuesta': 'Sí. Tener CUD no impide trabajar. El cupo laboral del 4% en el Estado está pensado '
               'para personas con CUD que buscan empleo.'},
 {'pregunta': '¿Mi obra social está obligada a cubrir todo?',
  'respuesta': 'Sí. Bajo la Ley 24.901, obras sociales y prepagas deben cubrir el 100% de las '
               'prestaciones de rehabilitación. Si se niegan, denunciá ante la Superintendencia de '
               'Salud: 0800-222-72583.'},
 {'pregunta': '¿Cómo registro el CUD en la SUBE?',
  'respuesta': 'Online en sube.gob.ar o en una terminal SUBE. Necesitás el número de CUD y el '
               'número de tarjeta SUBE. El descuento del 100% se activa automáticamente.'},
 {'pregunta': '¿El CUD digital tiene la misma validez que el físico?',
  'respuesta': 'Sí. El CUD digital en la app Mi Argentina tiene exactamente la misma validez legal '
               'e incluye código QR para verificación.'},
 {'pregunta': '¿Cuánto tiempo tarda el trámite?',
  'respuesta': 'Entre 30 y 90 días hábiles desde la evaluación según la provincia. CABA y Buenos '
               'Aires suelen tener mayor demanda.'}]

# ── SUBE_INFO ─────────────────────────────────────────────────────────────────
# Registro del CUD en la tarjeta SUBE para transporte público gratuito.
# Fuente: Ministerio de Transporte / SUBE — sube.gob.ar
# Normativa: Ley 22.431 art. 22 / Resolución CNRT 1018/2018
SUBE_INFO = {
    'titulo': 'Registro del CUD en la tarjeta SUBE',
    'descripcion': (
        'El registro del CUD en la tarjeta SUBE es un trámite OBLIGATORIO e independiente '
        'del CUD. Sin este paso el descuento en transporte público NO se activa aunque '
        'ya tengas el CUD en mano.'
    ),
    'beneficio': {
        'descuento': '100%',
        'medios': ['colectivo', 'tren', 'subte', 'premetro'],
        'alcance': 'Todo el país (red SUBE nacional)',
        'acompanante': (
            'El titular puede viajar con un acompañante con el mismo descuento '
            'cuando lo necesite por razón de su discapacidad (acreditar con CUD).'
        ),
        'normativa': 'Ley 22.431 art. 22 / Resolución CNRT 1018/2018',
    },
    'requisitos': [
        'Tener el CUD otorgado (número de CUD o DNI vinculado)',
        'Tarjeta SUBE registrada a nombre del titular (no puede ser una SUBE anónima)',
        'Número de tarjeta SUBE (impreso en el reverso, 16 dígitos)',
        'Cuenta en argentina.gob.ar para el trámite online (opcional — también se puede hacer presencialmente)',
    ],
    'canales': [
        {
            'canal': 'Online — sube.gob.ar',
            'url': 'https://www.sube.gob.ar',
            'pasos': [
                'Ingresá a sube.gob.ar',
                'Iniciá sesión con tu cuenta de argentina.gob.ar (podés crearla gratis)',
                'Seleccioná "Registrar beneficio por discapacidad"',
                'Ingresá el número de CUD y el número de SUBE (16 dígitos del reverso)',
                'Confirmá los datos y enviá el formulario',
                'El descuento se activa en la próxima carga o uso de la tarjeta (24-48 hs)',
            ],
        },
        {
            'canal': 'Trámite oficial Argentina.gob.ar',
            'url': 'https://www.argentina.gob.ar/salud/senadis/asociar-el-certificado-unico-de-discapacidad-cud-la-tarjeta-sube',
            'pasos': [
                'Ingresá al trámite oficial en argentina.gob.ar',
                'Completá el formulario con datos del CUD y la SUBE',
                'El sistema vincula el beneficio automáticamente',
            ],
        },
        {
            'canal': 'Terminal SUBE (presencial)',
            'url': None,
            'pasos': [
                'Acercate a cualquier terminal SUBE habilitada (kioscos, supermercados, Correo Argentino)',
                'Apoyá la tarjeta SUBE en el lector',
                'Seleccioná la opción "Beneficios por discapacidad"',
                'Seguí las instrucciones en pantalla ingresando tu número de CUD',
                'El descuento queda registrado en la tarjeta al instante',
            ],
        },
        {
            'canal': 'Centro de atención ANDIS',
            'url': 'https://www.argentina.gob.ar/turnos',
            'pasos': [
                'Sacá turno en ANDIS',
                'Presentá DNI y tarjeta SUBE',
                'El agente realiza el registro durante la atención',
            ],
        },
    ],
    'activacion': {
        'online': '24 a 48 horas después del registro',
        'terminal': 'Inmediata',
        'centro_andis': 'Inmediata durante la atención',
        'nota': (
            'Si el descuento no se activa luego de 72 hs del registro online, '
            'llamar a la línea SUBE: 0800-777-7823 (gratuito, lun-vie 8-20 hs).'
        ),
    },
    'renovacion': (
        'Como el CUD ya no vence (Resolución ANDIS 322/2023), el beneficio SUBE '
        'tampoco vence. Solo deberás actualizarlo si cambiás de tarjeta SUBE.'
    ),
    'sube_perdida_o_robo': {
        'pasos': [
            'Bloqueá la SUBE en sube.gob.ar o llamando al 0800-777-7823',
            'Solicitá una nueva tarjeta SUBE registrada',
            'Repetí el registro del beneficio por discapacidad con la nueva tarjeta',
        ],
        'nota': 'El saldo y el beneficio de discapacidad se transfieren a la nueva tarjeta.',
    },
    'contacto': {
        'telefono': '0800-777-7823',
        'horario': 'Lunes a viernes de 8 a 20 hs',
        'gratuito': True,
        'web': 'https://www.sube.gob.ar',
    },
    'preguntas_frecuentes': [
        {
            'pregunta': '¿Puedo usar la SUBE de otra persona para el descuento?',
            'respuesta': (
                'No. El beneficio se vincula a UNA tarjeta SUBE registrada a nombre del titular. '
                'El uso de la tarjeta de otra persona implica la pérdida del beneficio.'
            ),
        },
        {
            'pregunta': '¿El descuento aplica a cualquier colectivo del país?',
            'respuesta': (
                'Sí, en todos los servicios de transporte público que operen con SUBE: '
                'colectivos urbanos e interurbanos, trenes del AMBA y subte de CABA. '
                'Para servicios de larga distancia consultá con la empresa de transporte.'
            ),
        },
        {
            'pregunta': '¿Qué pasa si ya tengo SUBE pero no está registrada?',
            'respuesta': (
                'Primero tenés que registrar la tarjeta a tu nombre en sube.gob.ar. '
                'Una SUBE anónima no puede recibir el beneficio de discapacidad.'
            ),
        },
        {
            'pregunta': '¿El acompañante también viaja gratis?',
            'respuesta': (
                'Sí, cuando la persona con discapacidad necesita asistencia para viajar, '
                'un acompañante también viaja sin cargo. El titular debe presentar el CUD '
                'al chofer o guarda si se lo solicitan.'
            ),
        },
    ],
}

# ── PLAN_TEA_INFO ────────────────────────────────────────────────────────────
# Plan Nacional del Trastorno del Espectro Autista (TEA).
# Fuente: Resolución 1115/2026 (RESOL-2026-1115-APN-MS), Ministerio de Salud
# (BO 24/08/2026), y su marco normativo (Ley 27.043, Decreto Reglamentario
# 777/2019, Resolución 2641/2019, Resolución 3050/2025).
PLAN_TEA_INFO = {
    'titulo': 'Plan Nacional del Trastorno del Espectro Autista (TEA)',
    'normativa': 'Resolución 1115/2026 (RESOL-2026-1115-APN-MS) — Ministerio de Salud',
    'fecha_resolucion': '21/08/2026',
    'fecha_publicacion_bo': '24/08/2026',
    'boletin_oficial_url': 'https://www.boletinoficial.gob.ar/detalleAviso/primera/346272/20260824',
    'autoridad_aplicacion': (
        'Dirección Nacional de Abordaje Integral de Salud Mental — Subsecretaría de Institutos '
        'y Fiscalización, Secretaría de Gestión Sanitaria (Ministerio de Salud)'
    ),
    'organismos_intervinientes': [
        'Dirección Nacional de Abordaje por Curso de Vida',
        'Dirección Nacional de Calidad y Desarrollo del Talento en Salud',
        'Secretaría Nacional de Discapacidad',
    ],
    'descripcion': (
        'El Plan Nacional del TEA fija la referencia técnica a nivel nacional sobre los '
        'principales trastornos neurológicos asociados a la salud mental, para el trabajo '
        'conjunto con las jurisdicciones locales, organismos públicos y privados y la '
        'comunidad del campo de la Salud Mental.'
    ),
    'objetivo_general': (
        'Impulsar la mejora continua en la calidad de la atención, el tratamiento, la '
        'rehabilitación, recuperación y continuidad de cuidados destinados a las personas '
        'con TEA y sus familias, promoviendo el diagnóstico y la detección temprana, la '
        'intervención oportuna y el acceso a tratamientos adecuados, en concordancia con '
        'los estándares clínicos nacionales e internacionales vigentes.'
    ),
    'perspectiva': (
        'El TEA se reconoce desde una perspectiva del neurodesarrollo, como una condición '
        'que se configura en el curso del desarrollo y que debe comprenderse en relación '
        'con las trayectorias evolutivas de las personas (Decreto Reglamentario 777/2019).'
    ),
    'ejes': [
        {
            'numero': 1,
            'nombre': 'Promoción y prevención',
            'descripcion': 'Campañas nacionales de sensibilización y reducción del estigma.',
        },
        {
            'numero': 2,
            'nombre': 'Formación de recursos humanos',
            'descripcion': 'Capacitación en detección temprana y abordaje interdisciplinario, '
                            'en línea con el Programa Nacional de Formación en Salud Mental '
                            '(Resolución 3050/2025).',
        },
        {
            'numero': 3,
            'nombre': 'Apoyo integral',
            'descripcion': 'Atención psicológica, psiquiátrica y social a las personas con '
                            'TEA y sus familias.',
        },
        {
            'numero': 4,
            'nombre': 'Investigación e innovación',
            'descripcion': 'Estudios epidemiológicos y sistemas de información sobre TEA.',
        },
        {
            'numero': 5,
            'nombre': 'Coordinación intersectorial',
            'descripcion': 'Articulación entre salud, educación y otros sectores, y con las '
                            'jurisdicciones locales.',
        },
        {
            'numero': 6,
            'nombre': 'Diagnóstico epidemiológico',
            'descripcion': 'Vigilancia y mapeo de la situación nacional del TEA.',
        },
    ],
    'financiamiento': (
        'El dictado e implementación de la medida no implica erogación presupuestaria '
        'alguna para la jurisdicción (Arts. 2° y 3°, Resolución 1115/2026): se desarrolla '
        'en el marco de los recursos y programas ya existentes del Ministerio de Salud.'
    ),
    'relacion_con_cud': (
        'El TEA no es, por sí solo, un tipo de discapacidad separado en el trámite del CUD: '
        'se evalúa dentro de la categoría "intelectual" (ver /api/cud/requisitos?tipo=intelectual). '
        'El informe diagnóstico con escala DSM-5 o CIE-11 es la documentación habitualmente '
        'requerida, y el CUD puede otorgarse aunque no haya compromiso intelectual asociado, '
        'documentando las dificultades en la vida cotidiana.'
    ),
    'marco_normativo': [
        {
            'norma': 'Ley 27.043',
            'descripcion': 'Declara de Interés Nacional el abordaje integral e interdisciplinario '
                            'de las personas con Trastornos del Espectro Autista (TEA).',
            'url': 'https://www.argentina.gob.ar/normativa/nacional/ley-27043-240452',
        },
        {
            'norma': 'Decreto Reglamentario 777/2019',
            'descripcion': 'Reglamenta la Ley 27.043 y establece la perspectiva del '
                            'neurodesarrollo para comprender el TEA.',
            'url': 'https://www.argentina.gob.ar/normativa/nacional/decreto-777-2019-331886',
        },
        {
            'norma': 'Resolución 2641/2019 (Ministerio de Salud)',
            'descripcion': 'Aprueba el Consenso sobre Diagnóstico y Tratamiento de Personas '
                            'con Trastorno del Espectro Autista.',
            'url': 'https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-2641-2019-330297',
        },
        {
            'norma': 'Resolución 3050/2025 (Ministerio de Salud)',
            'descripcion': 'Aprueba el Programa Nacional de Formación en Salud Mental, marco '
                            'en el que se inscribe la formación prevista por el Plan TEA.',
            'url': None,
        },
        {
            'norma': 'Resolución 1115/2026 (Ministerio de Salud)',
            'descripcion': 'Aprueba el Plan Nacional del Trastorno del Espectro Autista (TEA).',
            'url': 'https://www.boletinoficial.gob.ar/detalleAviso/primera/346272/20260824',
        },
    ],
    'links_oficiales': [
        {
            'nombre': 'Resolución 1115/2026 — Boletín Oficial',
            'url': 'https://www.boletinoficial.gob.ar/detalleAviso/primera/346272/20260824',
        },
        {
            'nombre': 'Ley 27.043 — Argentina.gob.ar',
            'url': 'https://www.argentina.gob.ar/normativa/nacional/ley-27043-240452',
        },
        {
            'nombre': 'Decreto Reglamentario 777/2019 — Argentina.gob.ar',
            'url': 'https://www.argentina.gob.ar/normativa/nacional/decreto-777-2019-331886',
        },
        {
            'nombre': 'Resolución 2641/2019 — Consenso Diagnóstico y Tratamiento TEA',
            'url': 'https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-2641-2019-330297',
        },
    ],
    'nota': (
        'El Anexo I con el detalle técnico completo del Plan (IF-2026-79614776-APN-DNAISM#MS) '
        'se publica en la edición web del Boletín Oficial (boletinoficial.gob.ar) y todavía no '
        'está disponible como texto consolidado en argentina.gob.ar/normativa.'
    ),
}

# ── MUSICOTERAPIA_INFO ──────────────────────────────────────────────────────
# Organizaciones profesionales, evidencia científica y recursos sonoros de
# musicoterapia, organizados por tipo de discapacidad/técnica clínica.
MUSICOTERAPIA_INFO = {
    'titulo': 'Musicoterapia — Organizaciones, Evidencia y Recursos Sonoros',
    'descripcion': (
        'La musicoterapia es una disciplina clínica que utiliza intervenciones sonoras y '
        'musicales estructuradas —con base en evidencia— para el abordaje de necesidades '
        'motrices, comunicacionales, cognitivas y sensoriales en personas con discapacidad. '
        'Esta sección reúne organizaciones profesionales de referencia, evidencia científica '
        'y recursos sonoros funcionales organizados según la técnica y el tipo de discapacidad '
        'a la que se aplican.'
    ),
    'organizaciones_profesionales': [
        {
            'nombre': 'World Federation of Music Therapy (WFMT)',
            'url': 'https://www.wfmt.info',
            'descripcion': 'Información global, comités clínicos y directrices internacionales.',
        },
        {
            'nombre': 'Asociación Argentina de Musicoterapia (ASAM)',
            'url': 'https://musicoterapia.org.ar',
            'descripcion': 'Padrón de profesionales matriculados y marco normativo local.',
        },
        {
            'nombre': 'American Music Therapy Association (AMTA)',
            'url': 'https://www.musictherapy.org',
            'descripcion': 'Guías clínicas, fichas informativas por diagnóstico y estándares de práctica.',
        },
    ],
    'evidencia_cientifica': [
        {
            'nombre': 'PubMed — Musicoterapia Neurológica (NMT)',
            'url': 'https://pubmed.ncbi.nlm.nih.gov/?term=Neurologic+Music+Therapy',
            'descripcion': 'Ensayos clínicos y revisiones sobre rehabilitación motora y cognitiva.',
        },
        {
            'nombre': 'PubMed — Terapia de Entonación Melódica (MIT)',
            'url': 'https://pubmed.ncbi.nlm.nih.gov/?term=Melodic+Intonation+Therapy',
            'descripcion': 'Estudios de recuperación del habla, afasias y apraxias.',
        },
        {
            'nombre': 'SciELO — Musicoterapia en Iberoamérica',
            'url': 'https://search.scielo.org/?q=musicoterapia+discapacidad',
            'descripcion': 'Investigaciones y estudios de caso en español y portugués sobre '
                            'neurodesarrollo y discapacidad.',
        },
    ],
    # Recursos sonoros 100% YouTube (sin Spotify: requiere cuenta paga para playlists
    # completas), organizados por los mismos 6 tipos de discapacidad que usa el resto
    # de la plataforma (ver REQUISITOS_POR_TIPO), cada uno con varias técnicas/temas
    # musicales aplicables. Los recursos "YouTube (búsqueda)" apuntan a una búsqueda
    # curada en vez de un video puntual, para no depender de que un único video
    # puntual seguido siga disponible.
    'recursos_por_discapacidad': [
        {
            'tipo_discapacidad': 'motora',
            'nombre': 'Discapacidad motora',
            'tecnicas': [
                {
                    'nombre': 'Estimulación Auditiva Rítmica (RAS) — marcha y coordinación',
                    'descripcion': 'Pistas con pulso isócrono a BPM fijo, usadas en '
                                    'reentrenamiento de la marcha y coordinación motriz.',
                    'recursos': [
                        {'nombre': 'Metrónomo con música estructurada a 60 BPM', 'tipo': 'YouTube',
                         'url': 'https://www.youtube.com/watch?v=kQW8Spw744M'},
                        {'nombre': 'Patrón rítmico isócrono a 80 BPM para entrenamiento de paso', 'tipo': 'YouTube',
                         'url': 'https://www.youtube.com/watch?v=y2hKk-lQ_a4'},
                        {'nombre': 'Ritmo constante a 100 BPM para coordinación motriz', 'tipo': 'YouTube',
                         'url': 'https://www.youtube.com/watch?v=G6P8c3W6r4g'},
                        {'nombre': 'Búsqueda — Rhythmic Auditory Stimulation / metrónomo por BPM', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=Rhythmic+Auditory+Stimulation+metronome+bpm'},
                    ],
                },
                {
                    'nombre': 'Percusión activa — motricidad fina y miembros superiores',
                    'descripcion': 'Ejercicios de tocar tambor/percusión guiados por video, usados '
                                    'en rehabilitación de manos, brazos y motricidad fina.',
                    'recursos': [
                        {'nombre': 'Búsqueda — ejercicios de percusión para rehabilitación de manos', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=drum+therapy+hand+rehabilitation+exercises'},
                        {'nombre': 'Búsqueda — Active Music Therapy motricidad fina', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=active+music+therapy+fine+motor+skills'},
                    ],
                },
                {
                    'nombre': 'Terapia de Entonación Melódica (MIT) — habla post-ACV, afasias y apraxias',
                    'descripcion': 'Usa el canto y la entonación melódica para facilitar la '
                                    'recuperación del habla tras un ACV u otra lesión neurológica.',
                    'recursos': [
                        {'nombre': 'PubMed — evidencia clínica de MIT', 'tipo': 'Evidencia científica',
                         'url': 'https://pubmed.ncbi.nlm.nih.gov/?term=Melodic+Intonation+Therapy'},
                        {'nombre': 'Búsqueda — Melodic Intonation Therapy ejercicios en video', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=Melodic+Intonation+Therapy+exercises+aphasia'},
                    ],
                },
            ],
        },
        {
            'tipo_discapacidad': 'visual',
            'nombre': 'Discapacidad visual',
            'tecnicas': [
                {
                    'nombre': 'Orientación y movilidad guiadas por audio',
                    'descripcion': 'Señales sonoras espaciales y ejercicios rítmicos que refuerzan '
                                    'la orientación y la movilidad independiente.',
                    'recursos': [
                        {'nombre': 'Búsqueda — audio orientation and mobility training blind', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=audio+orientation+and+mobility+training+blind'},
                    ],
                },
                {
                    'nombre': 'Percusión y canto — desarrollo espacial auditivo (método Orff)',
                    'descripcion': 'Actividades de percusión corporal e instrumental (Orff-Schulwerk) '
                                    'usadas para desarrollar la discriminación y ubicación sonora.',
                    'recursos': [
                        {'nombre': 'Búsqueda — Orff Schulwerk música para discapacidad visual', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=Orff+Schulwerk+music+therapy+visually+impaired'},
                    ],
                },
            ],
        },
        {
            'tipo_discapacidad': 'auditiva',
            'nombre': 'Discapacidad auditiva',
            'tecnicas': [
                {
                    'nombre': 'Musicoterapia vibroacústica — percepción por vibración',
                    'descripcion': 'Uso de graves fuertes y superficies vibrátiles (no percepción '
                                    'auditiva) para que la música se sienta como vibración corporal.',
                    'recursos': [
                        {'nombre': 'Búsqueda — vibroacoustic therapy deaf hard of hearing', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=vibroacoustic+therapy+deaf+hard+of+hearing'},
                        {'nombre': 'Búsqueda — música con subwoofer / bajos para sentir el ritmo', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=feel+the+bass+vibration+music+deaf'},
                    ],
                },
                {
                    'nombre': 'Música interpretada en Lengua de Señas Argentina (LSA)',
                    'descripcion': 'Canciones interpretadas en LSA, que combinan ritmo visual y '
                                    'vibración con el componente comunitario/cultural de la música.',
                    'recursos': [
                        {'nombre': 'Búsqueda — canciones en Lengua de Señas Argentina', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=canciones+en+lengua+de+se%C3%B1as+argentina'},
                    ],
                },
            ],
        },
        {
            'tipo_discapacidad': 'intelectual',
            'nombre': 'Discapacidad intelectual (incluye TEA — ver también Plan Nacional TEA)',
            'tecnicas': [
                {
                    'nombre': 'Música de baja estimulación — regulación sensorial (TEA)',
                    'descripcion': 'Ambientes sonoros continuos, sin cambios bruscos ni percusión '
                                    'marcada, diseñados para modular sobrecargas sensoriales.',
                    'recursos': [
                        {'nombre': 'Sesión continua de baja estimulación para reducción de sobrecarga sensorial',
                         'tipo': 'YouTube', 'url': 'https://www.youtube.com/watch?v=WPni755-Krg'},
                        {'nombre': 'Paisaje sonoro suave sin percusión para calma y foco',
                         'tipo': 'YouTube', 'url': 'https://www.youtube.com/watch?v=1ZYbU82GVz4'},
                        {'nombre': 'Búsqueda — Low stimulation music / sensory regulation autismo', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=Low+stimulation+music+sensory+autism'},
                    ],
                },
                {
                    'nombre': 'Canciones estructuradas y repetitivas — aprendizaje y rutinas',
                    'descripcion': 'Canciones con estructura predecible (repetición, secuencia '
                                    'clara) usadas para reforzar rutinas, vocabulario y transiciones.',
                    'recursos': [
                        {'nombre': 'Búsqueda — canciones estructuradas para rutinas y aprendizaje', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=structured+songs+routines+special+education'},
                    ],
                },
            ],
        },
        {
            'tipo_discapacidad': 'psicosocial',
            'nombre': 'Discapacidad psicosocial (salud mental)',
            'tecnicas': [
                {
                    'nombre': 'Música para regulación emocional y ansiedad',
                    'descripcion': 'Pistas de tempo estable y sin sobresaltos usadas como apoyo '
                                    'para bajar niveles de ansiedad y regular el estado de ánimo.',
                    'recursos': [
                        {'nombre': 'Búsqueda — música para ansiedad y regulación emocional', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=music+for+anxiety+and+emotional+regulation'},
                        {'nombre': 'Búsqueda — Deep Focus / música de enfoque sin letra', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=deep+focus+music+no+lyrics'},
                        {'nombre': 'Búsqueda — Peaceful Piano / piano relajante', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=peaceful+piano+relaxing+music'},
                    ],
                },
                {
                    'nombre': 'Mindfulness sonoro y respiración guiada con música',
                    'descripcion': 'Sesiones de respiración pautada por música, usadas como '
                                    'herramienta de autorregulación en crisis de ansiedad o estrés.',
                    'recursos': [
                        {'nombre': 'Búsqueda — mindfulness sonoro respiración guiada', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=guided+breathing+music+mindfulness'},
                    ],
                },
            ],
        },
        {
            'tipo_discapacidad': 'visceral',
            'nombre': 'Discapacidad visceral (enfermedades no evidentes: cardíacas, respiratorias, oncológicas, inmunológicas)',
            'tecnicas': [
                {
                    'nombre': 'Música para manejo del dolor crónico y reducción de estrés',
                    'descripcion': 'Usada como coadyuvante no farmacológico en dolor crónico y '
                                    'contextos oncológicos, junto al tratamiento médico indicado.',
                    'recursos': [
                        {'nombre': 'Búsqueda — music therapy chronic pain management', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=music+therapy+chronic+pain+management'},
                        {'nombre': 'Búsqueda — sound healing / cuencos tibetanos para dolor y estrés', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=sound+healing+singing+bowls+pain+stress'},
                    ],
                },
                {
                    'nombre': 'Respiración guiada con música — condiciones respiratorias y cardíacas',
                    'descripcion': 'Ejercicios de respiración pautados musicalmente, usados como '
                                    'apoyo (no reemplazo) en rehabilitación respiratoria y cardíaca.',
                    'recursos': [
                        {'nombre': 'Búsqueda — breathing exercises music pulmonary rehabilitation', 'tipo': 'YouTube (búsqueda)',
                         'url': 'https://www.youtube.com/results?search_query=breathing+exercises+music+pulmonary+rehabilitation'},
                    ],
                },
            ],
        },
    ],
    'bancos_audio_libres': [
        {
            'nombre': 'Free Music Archive — Ambient / Minimalista',
            'url': 'https://freemusicarchive.org/genre/Ambient/',
            'descripcion': 'Pistas libres de derechos para uso terapéutico propio.',
        },
        {
            'nombre': 'Incompetech',
            'url': 'https://incompetech.com/music/royalty-free/music.html',
            'descripcion': 'Pistas libres de derechos filtrables por BPM exacto, útiles para '
                            'ejercicios motores con tempo controlado.',
        },
    ],
    'nota': (
        'Los recursos externos (YouTube, bancos de audio libres de derechos) son de terceros y se listan '
        'a título orientativo: no reemplazan la indicación de un/a musicoterapeuta matriculado/a. '
        'Verificar siempre la vigencia de los enlaces, ya que el contenido de plataformas de '
        'terceros puede modificarse o discontinuarse.'
    ),
}
