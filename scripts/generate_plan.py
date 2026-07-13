import pandas as pd
import random


months = pd.date_range(
    "2025-01-01",
    "2025-12-01",
    freq="MS"
)


brands = [
    "ДетиНосят",
    "ДетиПоносят",
    "ДетиНеВыносят"
]


plans = []


for month in months:

    for brand in brands:

        plans.append({

            "month": month,

            "brand": brand,

            "plan_revenue": random.randint(
                50000000,
                300000000
            )

        })


df = pd.DataFrame(plans)


df.to_csv(
    "data/plan.csv",
    sep=";",
    index=False,
    encoding="utf-8-sig"
)


print(df.head())
print()
print(f"Строк создано: {len(df)}")