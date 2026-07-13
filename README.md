# Аналитический пайплайн: продажи детской одежды на маркетплейсах

Учебный end-to-end проект аналитика данных: от генерации сырых данных до
интерактивных дашбордов и отчётов для бизнеса. Все данные синтетические
(3 бренда детской одежды, 5 000 SKU, продажи за 2025 год на Wildberries,
Ozon, Яндекс Маркете и Lamoda).

**Стек:** Python (pandas, Plotly, Faker) · PostgreSQL · Google Sheets + Apps Script

## Архитектура

```
Python (генерация данных)          scripts/generate_*.py
        │
        ▼
CSV  →  PostgreSQL                 sql/01_create_tables.sql, sql/02_load_data.sql
        │
        ▼
SQL-витрины                        sql/03_analytics.sql
  · план/факт по месяцам и брендам
  · юнит-экономика по SKU
  · ТОП SKU по прибыли (оконные функции)
  · ABC-анализ по накопленной выручке
  · эффективность рекламы (ДРР, CPC, CTR, CPO)
        │
        ▼
Дашборды (pandas + Plotly → HTML)  dashboard/*.py
Google Sheets (Apps Script)        отчёты план/факт и юнит-экономика
```

## Дашборды

Оба дашборда — самодостаточные HTML-файлы: собираются Python-скриптом,
открываются двойным кликом, не требуют сервера и интернета.

### План / Факт (`dashboard/plan_fact_dashboard.py`)

- KPI-карточки: план, факт, разрыв, % выполнения;
- столбчатый график факта по месяцам с условным форматированием по статусу
  выполнения плана (≥100% / 80–99% / 50–79% / <50%) и линией плана;
- сводная таблица по брендам;
- тепловая карта «бренд × месяц» — быстро видно проблемные периоды.

### Юнит-экономика (`dashboard/unit_economics_dashboard.py`)

- KPI-карточки: выручка, прибыль, маржинальность, продажи в штуках;
- маржинальность по категориям и выручка/прибыль по брендам;
- ABC-анализ ассортимента;
- ТОП-10 прибыльных и ТОП-10 проблемных SKU;
- **поиск по артикулу и кросс-фильтрация** по всем 4 761 SKU:
  бренд, категория и статус маржи комбинируются, итоги по выборке
  пересчитываются на лету, таблица сортируется по любой колонке.

## Структура проекта

```
scripts/     генерация синтетических данных (Faker + numpy)
data/        сгенерированные CSV и экспорт SQL-витрин
sql/         DDL, загрузка данных, аналитические запросы
dashboard/   Python-скрипты сборки дашбордов и готовые HTML
docs/        регламент обновления, инструкции для пользователей
```

## Как воспроизвести

```bash
# 1. Окружение
python -m venv venv
venv/Scripts/activate          # Windows; на Linux/macOS: source venv/bin/activate
pip install -r requirements.txt

# 2. Генерация данных (опционально — готовые CSV уже в data/)
python scripts/generate_products.py
python scripts/generate_sales.py
python scripts/generate_ads.py
python scripts/generate_plan.py

# 3. SQL-витрины (нужен PostgreSQL)
psql -d marketplace_demo -f sql/01_create_tables.sql
psql -d marketplace_demo -f sql/02_load_data.sql
psql -d marketplace_demo -f sql/03_analytics.sql

# 4. Дашборды
python dashboard/plan_fact_dashboard.py
python dashboard/unit_economics_dashboard.py
```

Результат — `dashboard/plan_fact_dashboard.html` и
`dashboard/unit_economics_dashboard.html`.

## Отчёты в Google Sheets

Витрины также разворачиваются в Google Таблицу тремя листами
(План_Факт, SKU_витрина, Юнит_Экономика): условное форматирование задаётся
правилами Sheets, ТОП/антитоп SKU считаются формулами `QUERY` поверх листа
с данными, обновление — в один клик через собственное меню на Apps Script.

## Документация

- [Регламент обновления дашбордов](docs/reglament_obnovlenie_dashboardov.md) —
  бизнес-процесс от новых данных до публикации;
- [Инструкция по дашбордам](docs/instrukciya_dashboardy.md) —
  для нетехнических пользователей.
