# Quick Start Guide

Быстрое начало работы с tgconvert.

## Установка

```bash
pip install tgconvert
```

## Основные команды

### CLI

```bash
# Показать версию
tgconvert --version

# Список форматов
tgconvert --list-formats

# Информация о сессии
tgconvert -i session.session --info

# Конвертация
tgconvert -i input.session -o output.session -of pyrogram
```

### Python

```python
from tgconvert import SessionConverter

converter = SessionConverter()

# Простая конвертация
converter.convert(
    input_path="session.session",
    output_path="output.session",
    output_format="pyrogram"
)
```

## Форматы

| Формат | Описание | Пример |
|--------|----------|--------|
| telethon | Telethon .session | `session.session` |
| pyrogram | Pyrogram .session | `session.session` |
| tdata | Telegram Desktop | `tdata/` |
| authkey | hex:dc_id | `abc123...ff:2` |

## Примеры

### Telethon → Pyrogram

```bash
tgconvert -i telethon.session -o pyrogram.session -of pyrogram
```

### Любой → tdata

```bash
tgconvert -i session.session -o ./tdata/ -of tdata
```

### Auth key → Session

```bash
tgconvert -i "aabbcc...ff:2" -o session.session -of telethon
```

### Получить информацию

```bash
tgconvert -i session.session --info --json
```

## Программное использование

```python
from tgconvert import SessionConverter, SessionData

converter = SessionConverter()

# Загрузить сессию
session = converter.load("session.session")

# Изменить
session.dc_id = 2

# Сохранить в разных форматах
converter.save(session, "tele.session", "telethon")
converter.save(session, "pyro.session", "pyrogram")
converter.save(session, "tdata/", "tdata")
converter.save(session, "key.txt", "authkey")
```

## Обработка ошибок

```python
try:
    converter.convert(
        input_path="session.session",
        output_path="output.session",
        output_format="pyrogram"
    )
except ValueError as e:
    print(f"Ошибка: {e}")
except FileNotFoundError:
    print("Файл не найден")
```

## Полезные советы

1. **Безопасность**: Никогда не делитесь файлами сессий
2. **Backup**: Делайте резервные копии перед конвертацией
3. **Тестирование**: Сначала протестируйте на тестовых сессиях
4. **Форматы**: Используйте auto-detection для удобства

## Дополнительно

Полная документация: [README.md](README.md)
Публикация на PyPI: [PYPI_GUIDE.md](PYPI_GUIDE.md)
