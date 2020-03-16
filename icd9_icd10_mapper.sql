CREATE TEMPORARY TABLE icdcode_converter
    (
    conversion_id		INTEGER			NOT NULL ,
    icd10			    VARCHAR(50)		NULL ,
    convertion_type		INTEGER			NOT NULL ,
    icd9			    VARCHAR(50)		NULL ,
    PRIMARY KEY (conversion_id)
    )
;

COPY icdcode_converter FROM '~/cse544_project/icdconverter.csv' WITH (FORMAT csv, DELIMITER ',');

CREATE TEMPORARY TABLE update_waiting_1st AS (
    SELECT condition_source_value,
           regexp_replace(condition_source_value, '[0-9]$', '', 'g') AS condition_source_value1,
           concat(condition_source_value, '0') AS condition_source_value2,
           concat(condition_source_value, '9') AS condition_source_value3,
           concat(condition_source_value, '1') AS condition_source_value4,
           row_number() OVER (PARTITION BY condition_source_value) AS r
    FROM condition_occurrence
);
DELETE FROM update_waiting_1st
WHERE r > 1;

CREATE TEMPORARY TABLE tmp_icd1on1converter AS (
    SELECT row_number() OVER (PARTITION BY icd9) AS r, conversion_id, icd9, icd10
    FROM icdcode_converter
    WHERE convertion_type = 1
);
DELETE FROM tmp_icd1on1converter
WHERE r > 1;

CREATE TEMPORARY TABLE tmp_1st_update AS(
    SELECT condition_source_value, condition_source_value1, condition_source_value2,
    condition_source_value3,condition_source_value4,
    converter1.icd10, converter2.icd10 AS icd10_1, converter3.icd10 AS icd10_2,
    converter4.icd10 AS icd10_3, converter5.icd10 AS icd10_4
FROM update_waiting_1st
LEFT JOIN tmp_icd1on1converter converter1 ON condition_source_value = converter1.icd9
LEFT JOIN tmp_icd1on1converter converter2 ON condition_source_value1 = converter2.icd9
LEFT JOIN tmp_icd1on1converter converter3 ON condition_source_value2 = converter3.icd9
LEFT JOIN tmp_icd1on1converter converter4 ON condition_source_value3 = converter4.icd9
LEFT JOIN tmp_icd1on1converter converter5 ON condition_source_value4 = converter5.icd9);

SELECT * FROM tmp_1st_update WHERE icd10_3 IS NOT NULL;

UPDATE tmp_1st_update
SET icd10 = icd10_1
WHERE icd10 IS NULL;

UPDATE tmp_1st_update
SET icd10 = icd10_2
WHERE icd10 IS NULL;

UPDATE tmp_1st_update
SET icd10 = icd10_3
WHERE icd10 IS NULL;

UPDATE tmp_1st_update
SET icd10 = icd10_4
WHERE icd10 IS NULL;

SELECT count(*) FROM tmp_1st_update WHERE icd10 IS NULL;

CREATE TEMPORARY TABLE tmp_icdNon1converter AS (
    SELECT row_number() OVER (PARTITION BY icd9) AS r, conversion_id, icd9, icd10
    FROM icdcode_converter
    WHERE convertion_type = 9
);
DELETE FROM tmp_icdNon1converter
WHERE r > 1;

CREATE TEMPORARY TABLE update_waiting_2nd AS (
    SELECT condition_source_value, condition_source_value1, condition_source_value2,
    condition_source_value3, condition_source_value4
    FROM tmp_1st_update
    WHERE icd10 IS NULL
);

CREATE TEMPORARY TABLE tmp_2nd_update AS(
    SELECT condition_source_value, condition_source_value1, condition_source_value2,
    condition_source_value3,condition_source_value4,
    converter1.icd10, converter2.icd10 AS icd10_1, converter3.icd10 AS icd10_2,
    converter4.icd10 AS icd10_3, converter5.icd10 AS icd10_4
FROM update_waiting_2nd
LEFT JOIN tmp_icdNon1converter converter1 ON condition_source_value = converter1.icd9
LEFT JOIN tmp_icdNon1converter converter2 ON condition_source_value1 = converter2.icd9
LEFT JOIN tmp_icdNon1converter converter3 ON condition_source_value2 = converter3.icd9
LEFT JOIN tmp_icdNon1converter converter4 ON condition_source_value3 = converter4.icd9
LEFT JOIN tmp_icdNon1converter converter5 ON condition_source_value4 = converter5.icd9);

UPDATE tmp_2nd_update
SET icd10 = icd10_1
WHERE icd10 IS NULL;

UPDATE tmp_2nd_update
SET icd10 = icd10_2
WHERE icd10 IS NULL;

UPDATE tmp_2nd_update
SET icd10 = icd10_3
WHERE icd10 IS NULL;

UPDATE tmp_2nd_update
SET icd10 = icd10_4
WHERE icd10 IS NULL;

SELECT count(*) FROM tmp_2nd_update WHERE icd10 IS NULL;

CREATE TEMPORARY TABLE tmp_icd1onNconverter AS (
    SELECT row_number() OVER (PARTITION BY icd9) AS r, conversion_id, icd9, icd10
    FROM icdcode_converter
    WHERE convertion_type = 10
);
DELETE FROM tmp_icd1onNconverter
WHERE r > 1;

CREATE TEMPORARY TABLE update_waiting_3rd AS (
    SELECT condition_source_value, condition_source_value1, condition_source_value2,
    condition_source_value3, condition_source_value4
    FROM tmp_2nd_update
    WHERE icd10 IS NULL
);

CREATE TEMPORARY TABLE tmp_3rd_update AS(
    SELECT condition_source_value, condition_source_value1, condition_source_value2,
    condition_source_value3, condition_source_value4,
    converter1.icd10, converter2.icd10 AS icd10_1, converter3.icd10 AS icd10_2,
    converter4.icd10 AS icd10_3, converter5.icd10 AS icd10_4
FROM update_waiting_3rd
LEFT JOIN tmp_icd1onNconverter converter1 ON condition_source_value = converter1.icd9
LEFT JOIN tmp_icd1onNconverter converter2 ON condition_source_value1 = converter2.icd9
LEFT JOIN tmp_icd1onNconverter converter3 ON condition_source_value2 = converter3.icd9
LEFT JOIN tmp_icd1onNconverter converter4 ON condition_source_value3 = converter4.icd9
LEFT JOIN tmp_icd1onNconverter converter5 ON condition_source_value4 = converter5.icd9);

UPDATE tmp_3rd_update
SET icd10 = icd10_1
WHERE icd10 IS NULL;

UPDATE tmp_3rd_update
SET icd10 = icd10_2
WHERE icd10 IS NULL;

UPDATE tmp_3rd_update
SET icd10 = icd10_3
WHERE icd10 IS NULL;

UPDATE tmp_3rd_update
SET icd10 = icd10_4
WHERE icd10 IS NULL;

SELECT * FROM tmp_3rd_update WHERE icd10 IS NULL;

UPDATE tmp_1st_update up1
SET icd10 = up2.icd10
FROM tmp_2nd_update up2
WHERE up1.icd10 IS NULL AND up1.condition_source_value = up2.condition_source_value;

UPDATE tmp_1st_update up1
SET icd10 = up3.icd10
FROM tmp_3rd_update up3
WHERE up1.icd10 IS NULL AND up1.condition_source_value = up3.condition_source_value;

SELECT condition_source_value, icd10 FROM tmp_1st_update WHERE icd10 IS NULL;

CREATE TABLE icd9_icd10_mapper AS (
    SELECT DISTINCT condition_source_concept_id, up1.condition_source_value, icd10
    FROM tmp_1st_update up1
    INNER JOIN condition_occurrence co
    ON up1.condition_source_value = co.condition_source_value
);