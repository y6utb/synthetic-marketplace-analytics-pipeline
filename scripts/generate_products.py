from faker import Faker
import pandas as pd
import random

# ----------------------------
# Настройки
# ----------------------------

fake = Faker("ru_RU")

NUM_PRODUCTS = 5000

# ----------------------------
# Справочники
# ----------------------------

brands = [
    "ДетиНосят",
    "ДетиПоносят",
    "ДетиНеВыносят"
]

suppliers = [
    "ООО Текстиль Плюс",
    "ООО Детский Мир",
    "Fashion Group",
    "Kids Factory",
    "Happy Textile"
]

categories = {
    "Футболки": [
        "Футболка хлопковая",
        "Футболка оверсайз",
        "Футболка базовая"
    ],

    "Худи": [
        "Худи утепленное",
        "Худи на молнии",
        "Худи оверсайз"
    ],

    "Комбинезоны": [
        "Комбинезон демисезонный",
        "Комбинезон утепленный",
        "Комбинезон хлопковый"
    ],

    "Куртки": [
        "Куртка зимняя",
        "Куртка демисезонная",
        "Куртка мембранная"
    ],

    "Штаны": [
        "Брюки спортивные",
        "Джоггеры",
        "Штаны утепленные"
    ],

    "Пижамы": [
        "Пижама хлопковая",
        "Пижама с принтом"
    ]
}

colors = [
    "Черный",
    "Белый",
    "Синий",
    "Красный",
    "Бежевый",
    "Серый",
    "Зеленый",
    "Розовый"
]

sizes = [
    "80",
    "86",
    "92",
    "98",
    "104",
    "110",
    "116",
    "122",
    "128",
    "134",
    "140"
]

genders = [
    "Мальчики",
    "Девочки",
    "Унисекс"
]

seasons = [
    "Весна",
    "Лето",
    "Осень",
    "Зима"
]

collections = [
    "Basic",
    "Premium",
    "Sport",
    "Casual",
    "New"
]

# ----------------------------
# Генерация
# ----------------------------

products = []

for sku in range(1, NUM_PRODUCTS + 1):

    category = random.choice(list(categories.keys()))

    product = random.choice(categories[category])

    season = random.choice(seasons)

    gender = random.choice(genders)

    color = random.choice(colors)

    size = random.choice(sizes)

    brand = random.choice(brands)

    supplier = random.choice(suppliers)

    cost = random.randint(300, 4000)

    markup = random.uniform(2.2, 3.5)

    retail_price = round(cost * markup, -1)

    commission = random.choice([10, 12, 15, 18, 20])

    logistics = random.randint(50, 250)

    storage = random.randint(5, 40)

    weight = random.randint(150, 1200)

    article = f"{brand[:3].upper()}-{sku:06}"

    sku_name = f"{product} {color.lower()}"

    products.append({

        "sku_id": sku,

        "article": article,

        "sku_name": sku_name,

        "category": category,

        "brand": brand,

        "supplier": supplier,

        "collection": random.choice(collections),

        "gender": gender,

        "season": season,

        "color": color,

        "size": size,

        "cost_price": cost,

        "retail_price": retail_price,

        "commission_percent": commission,

        "logistics_cost": logistics,

        "storage_cost": storage,

        "weight_g": weight

    })

# ----------------------------
# DataFrame
# ----------------------------

df = pd.DataFrame(products)

# ----------------------------
# Сохранение
# ----------------------------

df.to_csv(
    "data/products.csv",
    sep=";",
    index=False,
    encoding="utf-8-sig"
)

print("=" * 60)
print("Products успешно созданы!")
print("=" * 60)
print(df.head())
print()
print(f"Всего товаров: {len(df)}")