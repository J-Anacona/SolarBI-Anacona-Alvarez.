-- SolarBI Pascual - Cargas en PostgreSQL (UPSERT idempotente)


INSERT INTO silver.lectura_5min
    (ts, dispositivo_id, p_ac_kw, irradiancia_wm2, temp_modulo_c)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (ts, dispositivo_id) DO UPDATE SET
    p_ac_kw = EXCLUDED.p_ac_kw,
    irradiancia_wm2 = EXCLUDED.irradiancia_wm2,
    temp_modulo_c = EXCLUDED.temp_modulo_c;

INSERT INTO dwh.fact_energia_dia
    (fecha, dispositivo_id, energia_kwh, pct_datos_validos)
VALUES (%s, %s, %s, %s)
ON CONFLICT (fecha, dispositivo_id) DO UPDATE SET
    energia_kwh = EXCLUDED.energia_kwh,
    pct_datos_validos = EXCLUDED.pct_datos_validos;
