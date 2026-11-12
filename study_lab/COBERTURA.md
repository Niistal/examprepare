# Cobertura de estudio — Big_Data/main

Fuente local contrastada con el remoto: `Niistal/Big_Data`, `main`, commit `5e716edf42e0d1097b5ad2fb911755d97ba3865d`.

Los 80 microcasos y 16 lecciones cubren las áreas enumeradas abajo. La cobertura es por conceptos y ejemplos representativos: no equivale a resolver cada ejercicio o detalle de todos los PDF. No se usa una Erronka como referencia principal.

| Materia | Casos | Temas de los casos |
|---|---:|---|
| AA Programazioa | 27 | FastAPI, Git · MLOps, Git · arquitectura, Hugging Face · interpretación, LangChain · flujos, NumPy, NumPy · álgebra, Pandas · análisis, Pandas · archivos, Pandas · combinación, Pandas · limpieza, Pandas · selección, Python · entorno, Python · funciones, Python · fundamentos, Python · serialización, RAG · teoría aplicada, Scikit-Learn, Scikit-Learn · regresión, Scikit-Learn · validación, Streamlit, Visualización, Visualización · Seaborn |
| Sistemas ML | 11 | Clasificación, KNN, Orange · EDA, Orange · metodología, Preprocesamiento · tipos, Regresión lineal, SVM, Validación, Validación · K-Fold, Árboles y bosques |
| AA Ereduak | 11 | AI Act, Fairness, Fundamentos · paradigmas, Lógica difusa, Métricas, Privacidad · auditoría, Privacidad · membership inference, Sesgo · empleo, Sesgos, Ética |
| BD Sistemak | 12 | Arquitectura, Ciclo de datos · arquitectura, Data Lake, ETL · ELT, Elasticsearch · Docker, Elasticsearch · Query DSL, Elasticsearch · agregación, Elasticsearch · mapping, Faker · datos, Formatos · analítica, Kibana · KQL, Logstash |
| BD Aplikatua | 12 | Kafka Connect, Kafka · Python, Kafka · conceptos, Kafka · offsets, NiFi · atributos, NiFi · avanzado, NiFi · básico, NiFi · colas y errores, NiFi · filtrado, Series temporales · ventanas, Streaming · capas |

## Evidencia por caso

Cada caso registra la ruta y sección de contraste. `verified` cubre ruta/tema, no la autoría ni la ejecución de todos los servicios. Los archivos de solución del repo pueden estar asistidos por IA. Las lecciones son explicaciones propias de estudio sobre los mismos conceptos; NotebookLM es apoyo derivado.

| Caso | Objetivo | Fuente |
|---|---|---|
| P01 | Validador de NIF con funciones | `05_AA_Programazioa/1_Python_Lengoaiak/ariketak/1_Oinarriak_eta_JSON/README.md` |
| P02 | Guardar y cargar un catálogo JSON | `05_AA_Programazioa/1_Python_Lengoaiak/5073_1_Lengoaiak_Ariketak.ipynb` |
| P03 | Comprehension, filtro y lambda | `05_AA_Programazioa/1_Python_Lengoaiak/ariketak/3_Datu_Egiturak_eta_Funtzioak/README.md` |
| P04 | Preparar proyecto reproducible | `05_AA_Programazioa/1_Python_Lengoaiak/ariketak/2_Inguruneak_eta_Tresnak/README.md` |
| P05 | Máscaras booleanas y axis | `05_AA_Programazioa/2_Datu_Zientzia/ariketak/1_NumPy/README.md` |
| P06 | Broadcasting y z-score | `05_AA_Programazioa/2_Datu_Zientzia/ariketak/1_NumPy/README.md` |
| P07 | Limpiar un CSV de ventas | `05_AA_Programazioa/2_Datu_Zientzia/ariketak/2_Pandas/README.md` |
| P08 | GroupBy: agg frente a transform | `05_AA_Programazioa/2_Datu_Zientzia/ariketak/2_Pandas/README.md` |
| P09 | Merge left y registros huérfanos | `05_AA_Programazioa/2_Datu_Zientzia/ariketak/2_Pandas/README.md` |
| P10 | Figura con 2 gráficas | `05_AA_Programazioa/2_Datu_Zientzia/ariketak/3_Bistaratzea/README.md` |
| P11 | Pipeline sin fuga de datos | `05_AA_Programazioa/3_AA_Frameworka/ariketak/1_Scikit_Learn/README.md` |
| P12 | Métricas de clasificación manual | `05_AA_Programazioa/3_AA_Frameworka/ariketak/1_Scikit_Learn/README.md` |
| P13 | API REST con validación | `05_AA_Programazioa/3_AA_Frameworka/ariketak/3_FastAPI_eta_Pydantic/README.md` |
| P14 | Mini dashboard de datos | `05_AA_Programazioa/3_AA_Frameworka/ariketak/4_Streamlit/README.md` |
| P15 | Diseñar RAG con fuentes | `05_AA_Programazioa/3_AA_Frameworka/ariketak/6_RAG_eta_Bektore_Dendak/README.md` |
| P16 | Versionado Git, DVC y MLflow | `05_AA_Programazioa/4_Git_eta_Lan_Fluxuak/ariketak/2_MLOps_DVC_MLflow_Pipeline/README.md` |
| P17 | Concatenar CSV trimestrales | `05_AA_Programazioa/2_Datu_Zientzia/ariketak/2_Pandas/README.md` |
| P18 | Preprocesar columnas heterogéneas | `05_AA_Programazioa/3_AA_Frameworka/ariketak/1_Scikit_Learn/README.md` |
| M01 | Análisis inicial de goles en Orange | `04_Ikaskuntza_Automatikorako_Sistemak/1_Datuak_eta_Aurreprozesamendua/Ariketa_Datuak_interpretatzea.md` |
| M02 | Regresión con datos incorporados | `04_Ikaskuntza_Automatikorako_Sistemak/2_Ikasketa_Gainbegiratua/Ariketa_Erregresio_Lineala.md` |
| M03 | Logística frente a regresión | `04_Ikaskuntza_Automatikorako_Sistemak/2_Ikasketa_Gainbegiratua/Ariketa_Erregresio_Logistikoa.md` |
| M04 | Comparar k=1, 3, 5 en Wine | `04_Ikaskuntza_Automatikorako_Sistemak/2_Ikasketa_Gainbegiratua/Ariketa_KNN.md` |
| M05 | Árbol vs Random Forest | `04_Ikaskuntza_Automatikorako_Sistemak/2_Ikasketa_Gainbegiratua/Ariketa_Decision_Tree_eta_Random_Forest_Ebazpena.md` |
| M06 | SVM lineal vs RBF | `04_Ikaskuntza_Automatikorako_Sistemak/2_Ikasketa_Gainbegiratua/Ariketa_SVM_Ebazpena.md` |
| M07 | Detectar leakage en este código | `04_Ikaskuntza_Automatikorako_Sistemak/3_Balidazio_Metodologia/README.md` |
| M08 | Confusión y métricas con un caso | `04_Ikaskuntza_Automatikorako_Sistemak/3_Balidazio_Metodologia/README.md` |
| M09 | Diseñar un flujo de evaluación Orange | `04_Ikaskuntza_Automatikorako_Sistemak/README.md` |
| E01 | Sesgo de selección en cámaras CNC | `03_AA_Ereduak/ariketak/1_Alborapenak_Bias/README.md` |
| E02 | Disparate impact: selección laboral | `03_AA_Ereduak/ariketak/2_Fairness_eta_Metrikak/README.md` |
| E03 | FPR y FNR en un sistema de riesgo | `03_AA_Ereduak/ariketak/1_Alborapenak_Bias/README.md` |
| E04 | Clasificar riesgos de sistemas de IA | `03_AA_Ereduak/ariketak/4_AI_Act_Sailkapena/README.md` |
| E05 | Auditoría ALTAI de reconocimiento facial | `03_AA_Ereduak/ariketak/3_Auditoria_eta_Etika/README.md` |
| E06 | Regular velocidad de ventilador con fuzzy logic | `NotebookLM_Material_Estudio/03_AA_Ereduak/Guias_de_Estudio/Guia_Estudio_03_AA_Ereduak.md` |
| E07 | Auditar un filtro automatizado de CV | `03_AA_Ereduak/ariketak/5_CV_Iragazkia_Proiektu_Integratzailea/README.md` |
| E08 | Prompt injection como problema de modelo | `03_AA_Ereduak/3_Etika_eta_Legea/1.1_prompt_injection_diseinua_soluzioa.ipynb` |
| S01 | 7 V y escenario de sensores | `06_BD_Sistemak/1_Big_Data_Sarrera/Ariketak_01_01_Ebazpena.md` |
| S02 | Elegir ETL o ELT para CSV | `06_BD_Sistemak/ariketak/3_ETL_eta_Formatuak/README.md` |
| S03 | Arrancar Elastic Stack local | `06_BD_Sistemak/3_Elastic_Stack/compose.yaml` |
| S04 | Buscar productos caros en un índice | `06_BD_Sistemak/ariketak/5_Elasticsearch_eta_Kibana/Ariketa_5_3_Query_DSL.py` |
| S05 | Ventas por categoría | `06_BD_Sistemak/ariketak/5_Elasticsearch_eta_Kibana/Ariketa_5_4_Agregazioak.py` |
| S06 | Filtrar logs en Discover | `06_BD_Sistemak/ariketak/5_Elasticsearch_eta_Kibana/Ariketa_5_5_Discover_KQL.py` |
| S07 | Pipeline grok, date y mutate | `06_BD_Sistemak/3_Elastic_Stack/grok-date.conf` |
| S08 | Generar registros sintéticos | `06_BD_Sistemak/ariketak/4_Faker_Datu_Sintetikoak/README.md` |
| S09 | Warehouse, Lake y Lakehouse | `06_BD_Sistemak/ariketak/3_ETL_eta_Formatuak/README.md` |
| A01 | Pipeline CSV: GetFile a PutFile | `NotebookLM_Material_Estudio/07_BD_Aplikatua/Guias_de_Estudio/Guia_Estudio_07_BD_Aplikatua.md` |
| A02 | Filtrar ventas por importe | `07_BD_Aplikatua/1_Apache_NiFi_Oinarrizkoa/salmentak.csv` |
| A03 | Diferencia atributos, contenido y lineage | `NotebookLM_Material_Estudio/07_BD_Aplikatua/Guias_de_Estudio/Guia_Estudio_07_BD_Aplikatua.md` |
| A04 | MariaDB hacia MongoDB | `07_BD_Aplikatua/2_Apache_NiFi_Aurreratua/06_ariketa_mariadb_mongodb/README.md` |
| A05 | Producer, topic, partitions y consumer group | `07_BD_Aplikatua/3_Apache_Kafka/0-kasua-kafka-kaixo/README.md` |
| A06 | Producer JSON de sensores | `07_BD_Aplikatua/3_Apache_Kafka/1-kasua-kafka-python/README.md` |
| A07 | Consumer y decodificación | `07_BD_Aplikatua/3_Apache_Kafka/1-kasua-kafka-python/README.md` |
| A08 | AEMET: Bronze, Silver y Gold | `07_BD_Aplikatua/3_Apache_Kafka/4-kasua-kafka-aemet/Ariketa_Kafka_Aurreratua_AEMET_Ebazpena.md` |
| A09 | CDC MySQL hacia MongoDB | `07_BD_Aplikatua/3_Apache_Kafka/3-kasua-kafka-connect/README.md` |
| P19 | Formatos y punto de entrada | `05_AA_Programazioa/Apuntes_Estudio_Programazioa.md` |
| P20 | Elemento a elemento o producto matricial | `05_AA_Programazioa/Apuntes_Estudio_Programazioa.md` |
| P21 | loc, iloc y transform | `05_AA_Programazioa/Apuntes_Estudio_Programazioa.md` |
| P22 | Elegir y exportar gráficos | `05_AA_Programazioa/Apuntes_Estudio_Programazioa.md` |
| P23 | Baseline, MAE y R² | `05_AA_Programazioa/Apuntes_Estudio_Programazioa.md` |
| P24 | Ajuste pequeño sin contaminar test | `05_AA_Programazioa/Apuntes_Estudio_Programazioa.md` |
| P25 | Tokens y confianza sin descargar modelos | `05_AA_Programazioa/Apuntes_Estudio_Programazioa.md` |
| P26 | Cadena, memoria y RAG sobre papel | `05_AA_Programazioa/Apuntes_Estudio_Programazioa.md` |
| P27 | Resolver un conflicto y elegir despliegue | `05_AA_Programazioa/Apuntes_Estudio_Programazioa.md` |
| M10 | Auditar datos antes de entrenar | `04_Ikaskuntza_Automatikorako_Sistemak/ariketak/1_Datuak_eta_Aurreprozesamendua/README.md` |
| M11 | Elegir particiones y detectar sobreajuste | `04_Ikaskuntza_Automatikorako_Sistemak/3_Balidazio_Metodologia/README.md` |
| E09 | Elegir reglas, aprendizaje o generación | `NotebookLM_Material_Estudio/03_AA_Ereduak/Guias_de_Estudio/Guia_Estudio_03_AA_Ereduak.md` |
| E10 | Minimizar datos de una app educativa | `03_AA_Ereduak/3_Etika_eta_Legea/3.1_privacy_by_design_auditoria_soluzioa.ipynb` |
| E11 | Interpretar confianza sin confundirla con prueba | `03_AA_Ereduak/3_Etika_eta_Legea/1.2_kide_inferentzia_soluzioa.ipynb` |
| S10 | Definir tipos antes de buscar | `06_BD_Sistemak/ariketak/5_Elasticsearch_eta_Kibana/Ariketa_5_2_Cluster_Mapping.py` |
| S11 | Seguir un evento del sensor al panel | `06_BD_Sistemak/ariketak/2_Bizi_Zikloa_eta_Arkitektura/README.md` |
| S12 | Elegir CSV, JSON o Parquet | `06_BD_Sistemak/ariketak/3_ETL_eta_Formatuak/README.md` |
| A10 | Reiniciar un consumidor sin duplicar el efecto | `07_BD_Aplikatua/ariketak/3_Kafka_Streaming/README.md` |
| A11 | Evitar que un destino lento bloquee sin control | `07_BD_Aplikatua/ariketak/1_NiFi_Oinarrizkoa_Kasuak_1_4/README.md` |
| A12 | Ordenar antes de calcular una media móvil | `07_BD_Aplikatua/ariketak/4_Denbora_Serieak/Ariketa_4_1_Denbora_Serieak.py` |

## Ruta principal ampliada según guía aportada

P28: CSV entero y comprensión de columnas. P29: limpieza Pandas. P30: groupby y distribución de clases. P31: cinco pasos y Pipeline sin fuga. P32: balanced, report y matriz. P33: BaseModel y field_validator. P34: integración con datos diferentes. Todos incluyen dataset completo, imports, criterios, ayuda, solución contrastada y descarga de notebook de inicio. Fuente académica: apuntes de Programazioa y ejercicio de clases desbalanceadas, main verificado. La estructura 3+7 procede del texto aportado por el propietario.
