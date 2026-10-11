import os
import pandas as pd

ENTRADA = "data/bronze/telemetria.csv"
SALIDA = "data/silver/telemetria_silver.csv"
RECHAZADAS = "data/silver/telemetria_rechazadas.csv"
REPORTE = "data/silver/reporte_calidad.csv"

COLUMNAS = ["ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"]

os.makedirs("data/silver", exist_ok=True)

# Bronze solo se lee, nunca se modifica
df = pd.read_csv(ENTRADA, parse_dates=["ts"])
leidas = len(df)


def aplicar_regla(datos, nombre, mala):
    """Separa las filas que incumplen la regla y deja las que pasan."""
    rechazadas = datos[mala].copy()
    rechazadas["regla"] = nombre
    return datos[~mala], rechazadas


# Regla 1 - Unicidad: una sola fila por (ts, dispositivo_id)
actual, rech_dup = aplicar_regla(
    df, "duplicado", df.duplicated(subset=["ts", "dispositivo_id"], keep="first")
)

# Regla 2 - Completitud: ninguna columna puede estar vacia
actual, rech_falt = aplicar_regla(
    actual, "dato_faltante", actual[COLUMNAS].isna().any(axis=1)
)

# Regla 3 - Validez: rango fisico (inversor de 5 kWp)
en_rango = (
    actual["p_ac_kw"].between(0, 5.0)
    & actual["irradiancia_wm2"].between(0, 1500)
    & actual["temp_modulo_c"].between(-20, 100)
)
actual, rech_rango = aplicar_regla(actual, "fuera_de_rango", ~en_rango)

validas = len(actual)
pct_validos = round(100 * validas / leidas, 2)

actual.to_csv(SALIDA, index=False)
pd.concat([rech_dup, rech_falt, rech_rango]).to_csv(RECHAZADAS, index=False)

reporte = pd.DataFrame(
    {
        "concepto": [
            "filas_leidas",
            "rechazadas_duplicado",
            "rechazadas_dato_faltante",
            "rechazadas_fuera_de_rango",
            "filas_validas",
            "porcentaje_datos_validos",
        ],
        "valor": pd.Series(
            [
                leidas,
                len(rech_dup),
                len(rech_falt),
                len(rech_rango),
                validas,
                pct_validos,
            ],
            dtype=object,
        ),
    }
)
reporte.to_csv(REPORTE, index=False)
print(reporte.to_string(index=False))
