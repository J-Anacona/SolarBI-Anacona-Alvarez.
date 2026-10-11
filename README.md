# SolarBI 

Monitoreo de los datos crudos a dos tableros, uno en Power BI y otro en Grafana, sobre la misma base de datos PostgreSQL.

Integrantes: Jhon Herney Anacona Ortega y Miguel Angel Pardo Alvarez
Curso y grupo:Inteligencia de Negocios 
Institución: Institución Universitaria Pascual Bravo

## Descripción

Se construyó un flujo de datos completo con tres capas:

- Bronze: telemetría cruda de un inversor de 5 kWp, simulada durante 3 días con lecturas cada 5 minutos y anomalías inyectadas.
- Silver: lecturas limpias tras aplicar tres reglas de calidad (duplicados, datos faltantes y rango físico válido).
- Gold: resumen diario de energía por dispositivo, cargado en PostgreSQL de forma idempotente con UPSERT.

Sobre esa base se construyeron dos visualizaciones: un informe en **Power BI** (medidas DAX) y un dashboard operativo en **Grafana**.


## Estructura del repositorio

```
├── README.md
├── .gitignore
├── docs/       PDF de la consulta
├── data/
│   ├── bronze/ datos crudos
│   └── silver/ datos limpios y reporte de calidad
├── etl/        simulador.py, limpiar.py, run_etl.py
├── sql/        creación de tablas y plantillas de carga
├── powerbi/    informe de Power BI (.pbix)
└── grafana/    dashboard exportado (dashboard.json)
```

## Pasos para reproducir

**Requisitos:** Python 3, PostgreSQL, Power BI Desktop y Grafana OSS.

1. **Instalar las librerías de Python:**
```
   pip install pandas "psycopg[binary]"
```
2. **Crear la base de datos** `SolarBI` en PostgreSQL y ejecutar `sql/crear_tablas.sql`.
3. **Datos Bronze:** el archivo `data/bronze/telemetria.csv` ya está incluido. Si se vuelve a ejecutar `etl/simulador.py` se generan datos distintos, porque usa azar.
4. **Ejecutar el ETL** desde la raíz del repositorio. Pide la contraseña de PostgreSQL, o la toma de la variable de entorno `PGPASSWORD`:
```
   python etl/run_etl.py
```
   Ejecutarlo más de una vez no duplica filas: la carga es idempotente.
5. **Power BI:** abrir `powerbi/SolarBI.pbix`. Si pide credenciales, usar el servidor `localhost` y la base `SolarBI`.
6. **Grafana:** conectar PostgreSQL como data source (`localhost:5432`, base `SolarBI`) e importar `grafana/dashboard.json`. Los datos son del 5 al 7 de octubre de 2026, por lo que hay que ajustar el rango de tiempo.

## Seguridad

No se suben contraseñas ni cadenas de conexión. El ETL pide la contraseña al ejecutarse o la lee de la variable de entorno `PGPASSWORD`.

