-- Загрузка сгенерированных CSV в PostgreSQL.
-- Выполнять через psql из корня проекта (\copy читает файлы на стороне клиента):
--     psql -d marketplace_demo -f sql/02_load_data.sql

TRUNCATE products, sales, advertising, plan;

\copy products FROM 'data/products.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8')

\copy sales FROM 'data/sales.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8')

\copy advertising FROM 'data/advertising.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8')

\copy plan FROM 'data/plan.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8')

-- Контроль загрузки
SELECT 'products' AS table_name, COUNT(*) FROM products
UNION ALL SELECT 'sales', COUNT(*) FROM sales
UNION ALL SELECT 'advertising', COUNT(*) FROM advertising
UNION ALL SELECT 'plan', COUNT(*) FROM plan;
