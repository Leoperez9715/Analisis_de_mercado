-- Normalización campo ciudad
SELECT *,
  CASE
    WHEN REGEXP_CONTAINS(LOWER(ciudad), r'bogot[aá]') THEN 'BOGOTÁ'
    ELSE UPPER(TRIM(ciudad))
  END AS ciudad_homogeneizada
FROM `pruebaep-461015.datos_mercado_inmobiliario.dataset_prueba_data`;

-- Actualización campo ciudad
UPDATE `pruebaep-461015.datos_mercado_inmobiliario.dataset_prueba_data`
SET ciudad = 
  CASE
    WHEN REGEXP_CONTAINS(LOWER(ciudad), r'bogot[aá]') THEN 'BOGOTÁ'
    ELSE UPPER(TRIM(ciudad))
  END
WHERE TRUE;

-- Verificar filas repetidas en su totalidad
SELECT 
  codigo_web,
  id,
  nombre_publicacion,  
  COUNT(DISTINCT last_edited) AS versiones,
  COUNT(*) AS repeticiones
FROM `pruebaep-461015.datos_mercado_inmobiliario.dataset_prueba_data`
GROUP BY codigo_web, id, nombre_publicacion
HAVING COUNT(*) > 1 AND COUNT(DISTINCT last_edited) > 1;


-- Creación de la tabla con los datos normalizados y filas unicas. 
DROP TABLE IF EXISTS `pruebaep-461015.datos_mercado_inmobiliario.dataset_prueba_data_no_duplicados`;

CREATE OR REPLACE TABLE `pruebaep-461015.datos_mercado_inmobiliario.dataset_prueba_data_no_duplicados` AS
SELECT *
FROM (
  SELECT *,
         ROW_NUMBER() OVER (
           PARTITION BY codigo_web, id, nombre_publicacion
           ORDER BY last_edited asc -- puedes cambiar esto si no tienes fecha
         ) AS fila
  FROM `pruebaep-461015.datos_mercado_inmobiliario.dataset_prueba_data`
)
WHERE fila = 1;

-- Exportar datos 
EXPORT DATA
  OPTIONS (
    uri = 'gs://datos_mercado/datos_prueba_técnica_normalizados_*.csv',
    format = 'CSV',
    overwrite = true,
    header = true,
    field_delimiter = ','
  )
AS
SELECT *
FROM `pruebaep-461015.datos_mercado_inmobiliario.datos_sin_duplicados`;


