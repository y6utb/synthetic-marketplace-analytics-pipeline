CREATE TABLE products (
    sku_id INT,
    article VARCHAR(50),
    sku_name VARCHAR(255),
    category VARCHAR(100),
    brand VARCHAR(100),
    supplier VARCHAR(100),
    collection VARCHAR(100),
    gender VARCHAR(50),
    season VARCHAR(50),
    color VARCHAR(50),
    size VARCHAR(20),
    cost_price NUMERIC,
    retail_price NUMERIC,
    commission_percent NUMERIC,
    logistics_cost NUMERIC,
    storage_cost NUMERIC,
    weight_g INT
);

CREATE TABLE sales (
    date DATE,
    sku_id INT,
    article VARCHAR(50),
    brand VARCHAR(100),
    category VARCHAR(100),
    marketplace VARCHAR(100),
    qty INT,
    price NUMERIC,
    discount_percent NUMERIC,
    revenue NUMERIC,
    cost NUMERIC,
    commission NUMERIC,
    logistics NUMERIC,
    profit NUMERIC
);

CREATE TABLE advertising (
    date DATE,
    marketplace VARCHAR(100),
    brand VARCHAR(100),
    campaign_type VARCHAR(100),
    impressions INT,
    clicks INT,
    orders INT,
    spend NUMERIC
);

CREATE TABLE plan (
    month DATE,
    brand VARCHAR(100),
    plan_revenue NUMERIC
);