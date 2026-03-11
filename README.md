# Turbine Wear Forecast

Каркас desktop-приложения для прогнозирования стачивания деталей турбин.

## Требования
- Python 3.12+

## Установка (venv + pip)
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e .[dev]
```

## Запуск приложения
```bash
turbine-forecast
```

## Проверка качества
```bash
ruff check .
black --check .
mypy src
pytest
```
