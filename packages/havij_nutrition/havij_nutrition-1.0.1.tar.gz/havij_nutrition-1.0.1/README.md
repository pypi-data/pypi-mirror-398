# Nutrition Scanner + Meal Logger (Havij)

Streamlit app that looks up products by barcode via Open Food Facts, logs meals, and tracks daily/weekly nutrition totals.

## Features
- Barcode lookup with nutrition per 100g
- Meal logging with SQLite persistence
- Daily totals and 7-day trends

## Requirements
- Python 3.10+
- Poetry

## Setup
```bash
poetry install
```

## Run
```bash
poetry run streamlit run havij/presentation/streamlit_app.py
```

## Configuration
- `DB_PATH` (optional): path to SQLite file (default: `data/app.sqlite`)

## Tests
```bash
poetry run poe test
```
