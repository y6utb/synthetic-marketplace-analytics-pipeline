WITH fact_sales AS (

    SELECT
        DATE_TRUNC('month', date)::date AS month,
        brand,
        SUM(revenue) AS fact_revenue

    FROM sales

    GROUP BY 1,2

)

SELECT

    p.month,
    p.brand,

    p.plan_revenue,

    COALESCE(f.fact_revenue,0) AS fact_revenue,

    COALESCE(f.fact_revenue,0) - p.plan_revenue AS gap,

    ROUND(
        COALESCE(f.fact_revenue,0)
        / p.plan_revenue * 100,
        2
    ) AS plan_completion_percent


FROM plan p

LEFT JOIN fact_sales f

    ON p.month = f.month
    AND p.brand = f.brand

ORDER BY
    p.month,
    p.brand;

    WITH unit_economics AS (

    SELECT

        article,

        brand,

        category,

        SUM(qty) AS units_sold,

        SUM(revenue) AS revenue,

        SUM(cost) AS cost,

        SUM(commission) AS commission,

        SUM(logistics) AS logistics,

        SUM(profit) AS profit

    FROM sales

    GROUP BY
        article,
        brand,
        category

)

SELECT

    article,

    brand,

    category,

    units_sold,

    revenue,

    cost,

    commission,

    logistics,

    profit,

    ROUND(
        profit / revenue * 100,
        2
    ) AS margin_percent


FROM unit_economics

ORDER BY profit DESC;

WITH sku_profit AS (

    SELECT

        article,

        brand,

        category,

        SUM(revenue) AS revenue,

        SUM(profit) AS profit

    FROM sales

    GROUP BY
        article,
        brand,
        category

),

ranked_sku AS (

    SELECT

        *,

        RANK() OVER(
            PARTITION BY brand
            ORDER BY profit DESC
        ) AS profit_rank

    FROM sku_profit

)


SELECT *

FROM ranked_sku

WHERE profit_rank <= 10

ORDER BY
    brand,
    profit_rank;

    WITH sku_revenue AS (

    SELECT

        article,

        brand,

        SUM(revenue) AS revenue

    FROM sales

    GROUP BY
        article,
        brand

), revenue_share AS (

    SELECT

        *,

        SUM(revenue) OVER(
            PARTITION BY brand
            ORDER BY revenue DESC
        ) AS cumulative_revenue,

        SUM(revenue) OVER(
            PARTITION BY brand
        ) AS total_brand_revenue


    FROM sku_revenue

)


SELECT

    article,

    brand,

    revenue,

    ROUND(
        cumulative_revenue / total_brand_revenue * 100,
        2
    ) AS cumulative_percent,


    CASE

        WHEN cumulative_revenue / total_brand_revenue <= 0.8
            THEN 'A'

        WHEN cumulative_revenue / total_brand_revenue <= 0.95
            THEN 'B'

        ELSE 'C'

    END AS abc_group


FROM revenue_share


ORDER BY
    brand,
    revenue DESC;

    WITH advertising_metrics AS (

    SELECT

        date,

        marketplace,

        brand,

        SUM(impressions) AS impressions,

        SUM(clicks) AS clicks,

        SUM(orders) AS ad_orders,

        SUM(spend) AS spend


    FROM advertising


    GROUP BY

        date,
        marketplace,
        brand

),

sales_metrics AS (

    SELECT

        date,

        marketplace,

        brand,

        SUM(revenue) AS revenue,


        SUM(qty) AS orders


    FROM sales


    GROUP BY

        date,
        marketplace,
        brand

)


SELECT

    a.date,

    a.marketplace,

    a.brand,


    a.impressions,

    a.clicks,

    a.ad_orders,

    a.spend,


    COALESCE(s.revenue,0) AS revenue,


    ROUND(
        a.spend / NULLIF(s.revenue,0) * 100,
        2
    ) AS drr,


    ROUND(
        a.spend / NULLIF(a.clicks,0),
        2
    ) AS cpc,


    ROUND(
        a.clicks / NULLIF(a.impressions,0) * 100,
        3
    ) AS ctr,


    ROUND(
        a.spend / NULLIF(a.ad_orders,0),
        2
    ) AS cpo


FROM advertising_metrics a


LEFT JOIN sales_metrics s

ON a.date = s.date

AND a.marketplace = s.marketplace

AND a.brand = s.brand;

CREATE VIEW plan_fact AS

WITH fact_sales AS (

    SELECT
        DATE_TRUNC('month', date)::date AS month,
        brand,
        SUM(revenue) AS fact_revenue

    FROM sales

    GROUP BY 1,2

)

SELECT

    p.month,
    p.brand,
    p.plan_revenue,
    COALESCE(f.fact_revenue,0) AS fact_revenue,
    COALESCE(f.fact_revenue,0)-p.plan_revenue AS gap

FROM plan p

LEFT JOIN fact_sales f

ON p.month=f.month
AND p.brand=f.brand;

