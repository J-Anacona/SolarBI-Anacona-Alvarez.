-- SolarBI Pascual - Creacion de esquemas y tablas en PostgreSQL
-- Base de datos: SolarBI
-- Se ejecuta una sola vez (es seguro repetirlo: usa IF NOT EXISTS).

CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS dwh;

-- Capa Silver: lecturas limpias cada 5 minutos
CREATE TABLE IF NOT EXISTS silver.lectura_5min (
    ts               timestamp     NOT NULL,
    dispositivo_id   integer       NOT NULL,
    p_ac_kw          numeric(8,3)  NOT NULL,
    irradiancia_wm2  numeric(8,1)  NOT NULL,
    temp_modulo_c    numeric(5,1)  NOT NULL,
    PRIMARY KEY (ts, dispositivo_id)
);

-- Capa Gold: resumen diario de energia por dispositivo
CREATE TABLE IF NOT EXISTS dwh.fact_energia_dia (
    fecha              date          NOT NULL,
    dispositivo_id     integer       NOT NULL,
    energia_kwh        numeric(10,3) NOT NULL,
    pct_datos_validos  numeric(5,2)  NOT NULL,
    PRIMARY KEY (fecha, dispositivo_id)
);
