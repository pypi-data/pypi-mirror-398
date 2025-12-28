# AGENTS.md

Інструкції для AI-агентів при роботі з Python проєктами.

## Менеджер пакетів

Завжди використовуй **uv** для всіх операцій з пакетами:

```bash
# Створення проєкту
uv init my-project

# Додавання залежностей
uv add requests pytest

# Додавання dev-залежностей
uv add --dev mypy ruff

# Встановлення залежностей
uv sync

# Запуск скриптів
uv run python main.py
uv run pytest
```

## Версіонування

Використовуй **semantic versioning** (MAJOR.MINOR.PATCH):

- **MAJOR** — несумісні зміни API (1.0.0 → 2.0.0)
- **MINOR** — нова функціональність, сумісна зі старою (1.0.0 → 1.1.0)
- **PATCH** — виправлення помилок (1.0.0 → 1.0.1)

```toml
# pyproject.toml
[project]
version = "1.2.3"
```

## Тестування

Використовуй **pytest**:

```bash
# Запуск тестів
uv run pytest

# З покриттям коду
uv run pytest --cov=src --cov-report=html

# Конкретний тест
uv run pytest tests/test_main.py::test_function
```

Структура тестів:

```python
# tests/test_main.py
import pytest
from src.main import add

def test_add():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, 1) == 0

@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

## Перевірка типів

Використовуй **mypy**:

```bash
# Перевірка типів
uv run mypy src/

# З конфігурацією
uv run mypy --strict src/
```

Анотації типів:

```python
def greet(name: str, times: int = 1) -> str:
    return (name + "! ") * times

from typing import List, Dict, Optional

def process_items(items: List[str]) -> Dict[str, int]:
    return {item: len(item) for item in items}

def find_user(user_id: int) -> Optional[str]:
    return "Alice" if user_id == 1 else None
```



## Контрольний список

Перед комітом:
- [ ] `uv run pytest` — всі тести проходять
- [ ] `uv run mypy src/` — немає помилок типів
