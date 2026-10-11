"""Punto de entrada unico del ETL de SolarBI.

Uso (desde la carpeta que contiene data/):
    python run_etl.py

Flujo: Bronze (CSV crudo) -> reglas de calidad -> silver.lectura_5min
       -> resumen diario -> dwh.fact_energia_dia
La carga es idempotente: usa UPSERT, asi que ejecutarla varias veces
deja los mismos conteos.
"""
import getpass
import os

import pandas as pd
import psycopg

ENTRADA = "data/bronze/telemetria.csv"
COLUMNAS = ["ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"]
INTERVALO_H = 5 / 60  # cada lectura representa 5 minutos

CONEXION = dict(host="localhost", port=5432, dbname="SolarBI", user="postgres")


# ---------------------------------------------------------------- Extract
def extraer():
    """Lee Bronze. El archivo nunca se modifica."""
    return pd.read_csv(ENTRADA, parse_dates=["ts"])


# -------------------------------------------------------------- Transform
def _aplicar_regla(datos, mala):
    return datos[~mala], int(mala.sum())


def transformar(df):
    """Aplica las 3 reglas de calidad. Devuelve (filas_validas, conteos)."""
    conteos = {"leidas": len(df)}

    # Regla 1 - Unicidad
    actual, conteos["duplicado"] = _aplicar_regla(
        df, df.duplicated(subset=["ts", "dispositivo_id"], keep="first")
    )
    # Regla 2 - Completitud
    actual, conteos["dato_faltante"] = _aplicar_regla(
        actual, actual[COLUMNAS].isna().any(axis=1)
    )
    # Regla 3 - Validez (rango fisico de un inversor de 5 kWp)
    en_rango = (
        actual["p_ac_kw"].between(0, 5.0)
        & actual["irradiancia_wm2"].between(0, 1500)
        & actual["temp_modulo_c"].between(-20, 100)
    )
    actual, conteos["fuera_de_rango"] = _aplicar_regla(actual, ~en_rango)

    conteos["validas"] = len(actual)
    conteos["pct_validos"] = round(100 * conteos["validas"] / conteos["leidas"], 2)
    return actual, conteos


def resumen_diario(bronze, silver):
    """Energia por dia y dispositivo, y % de datos validos del dia."""
    leidas_dia = (
        bronze.assign(fecha=bronze["ts"].dt.date)
        .groupby(["fecha", "dispositivo_id"])
        .size()
        .rename("leidas")
    )
    s = silver.assign(
        fecha=silver["ts"].dt.date,
        energia_kwh=silver["p_ac_kw"] * INTERVALO_H,  # kW x 5/60 h = kWh
    )
    diario = s.groupby(["fecha", "dispositivo_id"]).agg(
        energia_kwh=("energia_kwh", "sum"), validas=("ts", "size")
    )
    diario = diario.join(leidas_dia)
    diario["pct_datos_validos"] = (100 * diario["validas"] / diario["leidas"]).round(2)
    diario["energia_kwh"] = diario["energia_kwh"].round(3)
    return diario.reset_index()[
        ["fecha", "dispositivo_id", "energia_kwh", "pct_datos_validos"]
    ]


# ------------------------------------------------------------------- Load
SQL_SILVER = """
INSERT INTO silver.lectura_5min
    (ts, dispositivo_id, p_ac_kw, irradiancia_wm2, temp_modulo_c)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (ts, dispositivo_id) DO UPDATE SET
    p_ac_kw = EXCLUDED.p_ac_kw,
    irradiancia_wm2 = EXCLUDED.irradiancia_wm2,
    temp_modulo_c = EXCLUDED.temp_modulo_c
"""

SQL_FACT = """
INSERT INTO dwh.fact_energia_dia
    (fecha, dispositivo_id, energia_kwh, pct_datos_validos)
VALUES (%s, %s, %s, %s)
ON CONFLICT (fecha, dispositivo_id) DO UPDATE SET
    energia_kwh = EXCLUDED.energia_kwh,
    pct_datos_validos = EXCLUDED.pct_datos_validos
"""


def cargar(silver, diario, password):
    filas_silver = [
        (
            r.ts.to_pydatetime(),
            int(r.dispositivo_id),
            float(r.p_ac_kw),
            float(r.irradiancia_wm2),
            float(r.temp_modulo_c),
        )
        for r in silver.itertuples(index=False)
    ]
    filas_fact = [
        (r.fecha, int(r.dispositivo_id), float(r.energia_kwh), float(r.pct_datos_validos))
        for r in diario.itertuples(index=False)
    ]
    with psycopg.connect(password=password, **CONEXION) as conn:
        with conn.cursor() as cur:
            cur.executemany(SQL_SILVER, filas_silver)
            cur.executemany(SQL_FACT, filas_fact)
            cur.execute("SELECT count(*) FROM silver.lectura_5min")
            n_silver = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM dwh.fact_energia_dia")
            n_fact = cur.fetchone()[0]
    return n_silver, n_fact


# ------------------------------------------------------------------- Main
def main():
    password = os.environ.get("PGPASSWORD") or getpass.getpass(
        "Contrasena de PostgreSQL (usuario postgres): "
    )

    bronze = extraer()
    silver, conteos = transformar(bronze)
    diario = resumen_diario(bronze, silver)

    print("Calidad:", conteos)
    n_silver, n_fact = cargar(silver, diario, password)
    print(f"Filas en silver.lectura_5min:  {n_silver}")
    print(f"Filas en dwh.fact_energia_dia: {n_fact}")


if __name__ == "__main__":
    main()
