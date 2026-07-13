import pandas as pd
import random
import numpy as np


NUM_ROWS = 20000


dates = pd.date_range(
    "2025-01-01",
    "2025-12-31"
)


brands = [
    "ДетиНосят",
    "ДетиПоносят",
    "ДетиНеВыносят"
]


marketplaces = [
    "Wildberries",
    "Ozon",
    "Яндекс Маркет",
    "Lamoda"
]


campaign_types = [
    "Продвижение карточки",
    "Авто-реклама",
    "Поиск",
    "Каталог",
    "Брендовая реклама"
]


ads = []


for i in range(NUM_ROWS):

    impressions = random.randint(
        1000,
        200000
    )

    ctr = random.uniform(
        0.01,
        0.08
    )

    clicks = int(
        impressions * ctr
    )


    cpc = random.randint(
        10,
        80
    )

    spend = clicks * cpc


    conversion = random.uniform(
        0.03,
        0.15
    )

    orders = max(
        1,
        int(clicks * conversion)
    )


    ads.append({

        "date": random.choice(dates),

        "marketplace": random.choice(
            marketplaces
        ),

        "brand": random.choice(
            brands
        ),

        "campaign_type": random.choice(
            campaign_types
        ),

        "impressions": impressions,

        "clicks": clicks,

        "orders": orders,

        "spend": spend

    })


df = pd.DataFrame(ads)


df.to_csv(
    "data/advertising.csv",
    sep=";",
    index=False,
    encoding="utf-8-sig"
)


print(df.head())
print()
print(f"Строк создано: {len(df)}")