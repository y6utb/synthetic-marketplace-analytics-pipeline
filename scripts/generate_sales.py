import pandas as pd
import numpy as np
import random
from datetime import datetime


# ----------------------------
# Настройки
# ----------------------------

NUM_SALES = 100000

START_DATE = "2025-01-01"
END_DATE = "2025-12-31"


# ----------------------------
# Загружаем товары
# ----------------------------

products = pd.read_csv(
    "data/products.csv",
    sep=";"
)

# ----------------------------
# Настройки маркетплейсов
# ----------------------------

marketplaces = [
    "Wildberries",
    "Ozon",
    "Яндекс Маркет",
    "Lamoda"
]

marketplace_weights = [
    0.6,
    0.25,
    0.1,
    0.05
]


# ----------------------------
# Генерация продаж
# ----------------------------

sales = []


# создаем веса популярности товаров
# чтобы часть SKU продавалась чаще

products["popularity"] = np.random.exponential(
    scale=1,
    size=len(products)
)

products["popularity"] = (
    products["popularity"] /
    products["popularity"].sum()
)


for i in range(NUM_SALES):

    product = products.sample(
        1,
        weights="popularity"
    ).iloc[0]


    date = pd.to_datetime(
        np.random.choice(
            pd.date_range(
                START_DATE,
                END_DATE
            )
        )
    )


    qty = random.randint(1, 5)


    # сезонность
    month = date.month

    if month in [11, 12]:
        qty = qty * random.randint(1, 3)


    discount = random.choice(
        [0, 5, 10, 15, 20, 30]
    )


    sale_price = round(
        product["retail_price"] *
        (1 - discount / 100),
        -1
    )


    revenue = qty * sale_price


    cost = qty * product["cost_price"]


    commission = (
        revenue *
        product["commission_percent"] /
        100
    )


    logistics = (
        qty *
        product["logistics_cost"]
    )


    profit = (
        revenue
        - cost
        - commission
        - logistics
    )


    sales.append({

        "date": date,

        "sku_id": product["sku_id"],

        "article": product["article"],

        "brand": product["brand"],

        "category": product["category"],

        "marketplace": np.random.choice(
            marketplaces,
            p=marketplace_weights
        ),

        "qty": qty,

        "price": sale_price,

        "discount_percent": discount,

        "revenue": revenue,

        "cost": cost,

        "commission": round(
            commission,
            2
        ),

        "logistics": logistics,

        "profit": round(
            profit,
            2
        )

    })


# ----------------------------
# DataFrame
# ----------------------------

df = pd.DataFrame(sales)


# сортировка

df = df.sort_values(
    "date"
)


# сохранение

df.to_csv(
    "data/sales.csv",
    sep=";",
    index=False,
    encoding="utf-8-sig"
)


print("=" * 50)
print("Sales успешно созданы")
print("=" * 50)

print(df.head())

print()

print(
    f"Количество продаж: {len(df)}"
)

print(
    f"Выручка: {df['revenue'].sum():,.0f}"
)

print(
    f"Прибыль: {df['profit'].sum():,.0f}"
)