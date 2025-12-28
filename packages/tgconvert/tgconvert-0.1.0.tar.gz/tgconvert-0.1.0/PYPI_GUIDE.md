# Руководство по публикации на PyPI

Это полное руководство по публикации библиотеки `tgconvert` на Python Package Index (PyPI).

## 📋 Содержание

1. [Подготовка к публикации](#подготовка-к-публикации)
2. [Регистрация на PyPI](#регистрация-на-pypi)
3. [Создание пакета](#создание-пакета)
4. [Тестирование на TestPyPI](#тестирование-на-testpypi)
5. [Публикация на PyPI](#публикация-на-pypi)
6. [Обновление версий](#обновление-версий)
7. [Автоматизация с GitHub Actions](#автоматизация-с-github-actions)

## 🎯 Подготовка к публикации

### 1. Проверьте структуру проекта

Убедитесь, что ваш проект имеет правильную структуру:

```
tgconvert/
├── tgconvert/          # Основной пакет
│   ├── __init__.py
│   ├── base.py
│   ├── converter.py
│   ├── cli.py
│   └── formats/
│       ├── __init__.py
│       ├── telethon.py
│       ├── pyrogram.py
│       ├── tdata.py
│       └── authkey.py
├── tests/              # Тесты (опционально)
├── README.md           # Документация
├── LICENSE             # Лицензия
├── pyproject.toml      # Конфигурация пакета
└── setup.py           # Установочный скрипт
```

### 2. Создайте LICENSE файл

```bash
# MIT License рекомендуется
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
```

### 3. Создайте .gitignore

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Telegram sessions
*.session
tdata/
*.txt
EOF
```

### 4. Установите необходимые инструменты

```bash
pip install --upgrade pip
pip install build twine
```

## 🔐 Регистрация на PyPI

### 1. Создайте аккаунты

1. **TestPyPI** (для тестирования): https://test.pypi.org/account/register/
2. **PyPI** (реальный): https://pypi.org/account/register/

### 2. Настройте API токены

#### Создание API токена на PyPI:

1. Войдите в аккаунт на https://pypi.org
2. Перейдите в Account Settings → API tokens
3. Нажмите "Add API token"
4. Введите имя токена (например, "tgconvert-upload")
5. Выберите scope:
   - Для первой публикации: "Entire account"
   - После первой публикации: создайте токен только для вашего проекта
6. Скопируйте токен (начинается с `pypi-`)

#### Сохраните токены в ~/.pypirc:

```bash
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-ваш_токен_здесь

[testpypi]
username = __token__
password = pypi-ваш_тестовый_токен_здесь
repository = https://test.pypi.org/legacy/
EOF

# Защитите файл
chmod 600 ~/.pypirc
```

## 📦 Создание пакета

### 1. Проверьте версию

Убедитесь, что версия в `tgconvert/__init__.py` и `pyproject.toml` совпадают:

```python
# tgconvert/__init__.py
__version__ = "0.1.0"
```

```toml
# pyproject.toml
[project]
version = "0.1.0"
```

### 2. Соберите пакет

```bash
# Очистите предыдущие сборки
rm -rf build/ dist/ *.egg-info

# Соберите пакет
python -m build
```

Это создаст два файла в папке `dist/`:
- `tgconvert-0.1.0.tar.gz` (source distribution)
- `tgconvert-0.1.0-py3-none-any.whl` (built distribution)

### 3. Проверьте пакет

```bash
# Проверьте описание
twine check dist/*

# Должно вывести: Checking distribution dist/...: PASSED
```

## 🧪 Тестирование на TestPyPI

### 1. Загрузите на TestPyPI

```bash
twine upload --repository testpypi dist/*
```

### 2. Установите и протестируйте

```bash
# Создайте виртуальное окружение для теста
python -m venv test_env
source test_env/bin/activate  # Linux/Mac
# или
test_env\Scripts\activate  # Windows

# Установите из TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ tgconvert

# Протестируйте
tgconvert --version
tgconvert --list-formats

# Протестируйте в Python
python -c "from tgconvert import SessionConverter; print('OK')"

# Очистите
deactivate
rm -rf test_env
```

## 🚀 Публикация на PyPI

### 1. Финальная проверка

Перед публикацией убедитесь:

- ✅ Все тесты проходят
- ✅ README.md полный и корректный
- ✅ Версия правильная
- ✅ Лицензия добавлена
- ✅ Тестирование на TestPyPI успешно

### 2. Загрузите на PyPI

```bash
twine upload dist/*
```

### 3. Проверьте публикацию

Ваш пакет будет доступен по адресу:
```
https://pypi.org/project/tgconvert/
```

### 4. Установите из PyPI

```bash
pip install tgconvert
```

## 🔄 Обновление версий

### Семантическое версионирование

Используйте формат `MAJOR.MINOR.PATCH`:

- **MAJOR**: Несовместимые изменения API
- **MINOR**: Новая функциональность (обратно совместимая)
- **PATCH**: Исправления багов

### Процесс обновления

1. **Обновите версию** в обоих местах:
   ```python
   # tgconvert/__init__.py
   __version__ = "0.2.0"
   ```
   
   ```toml
   # pyproject.toml
   version = "0.2.0"
   ```

2. **Обновите CHANGELOG.md** (создайте если нет):
   ```markdown
   # Changelog
   
   ## [0.2.0] - 2025-12-24
   ### Added
   - Поддержка новых форматов
   
   ### Fixed
   - Исправлена ошибка при конвертации tdata
   
   ## [0.1.0] - 2025-12-24
   ### Added
   - Начальный релиз
   ```

3. **Создайте git tag**:
   ```bash
   git add .
   git commit -m "Release version 0.2.0"
   git tag v0.2.0
   git push origin main --tags
   ```

4. **Соберите и загрузите**:
   ```bash
   rm -rf build/ dist/ *.egg-info
   python -m build
   twine check dist/*
   twine upload dist/*
   ```

## 🤖 Автоматизация с GitHub Actions

### Создайте .github/workflows/publish.yml

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Check package
      run: twine check dist/*
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

### Настройка GitHub Secrets

1. Перейдите в Settings → Secrets and variables → Actions
2. Нажмите "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: ваш PyPI API токен
5. Сохраните

### Использование

Теперь при создании нового Release на GitHub пакет автоматически опубликуется на PyPI:

```bash
# Создайте релиз через GitHub UI или:
gh release create v0.2.0 --title "Version 0.2.0" --notes "Release notes"
```

## 📊 Мониторинг и метрики

### PyPI Statistics

После публикации вы можете отслеживать:
- Количество загрузок
- Популярные версии Python
- География пользователей

Используйте: https://pypistats.org/packages/tgconvert

### Badges для README

Добавьте красивые badges в README.md:

```markdown
[![PyPI version](https://badge.fury.io/py/tgconvert.svg)](https://badge.fury.io/py/tgconvert)
[![Downloads](https://pepy.tech/badge/tgconvert)](https://pepy.tech/project/tgconvert)
[![Python Version](https://img.shields.io/pypi/pyversions/tgconvert)](https://pypi.org/project/tgconvert/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

## ⚠️ Частые проблемы

### Проблема: "Package already exists"

**Решение**: Вы не можете повторно загрузить ту же версию. Увеличьте версию.

### Проблема: "Invalid username or password"

**Решение**: 
- Убедитесь что используете `__token__` как username
- Проверьте что токен начинается с `pypi-`
- Создайте новый токен если старый не работает

### Проблема: "twine: command not found"

**Решение**: 
```bash
pip install --upgrade twine
```

### Проблема: Импорт не работает после установки

**Решение**: Проверьте что `__init__.py` правильно экспортирует классы:
```python
from .converter import SessionConverter
__all__ = ["SessionConverter"]
```

## 📚 Полезные ссылки

- **PyPI Guide**: https://packaging.python.org/tutorials/packaging-projects/
- **Setuptools Documentation**: https://setuptools.pypa.io/
- **Twine Documentation**: https://twine.readthedocs.io/
- **PEP 517**: https://peps.python.org/pep-0517/
- **PEP 518**: https://peps.python.org/pep-0518/

## ✅ Чек-лист перед публикацией

- [ ] Все тесты проходят
- [ ] README.md завершён
- [ ] LICENSE добавлен
- [ ] Версии обновлены
- [ ] .gitignore настроен
- [ ] Зависимости указаны
- [ ] Описание информативное
- [ ] Keywords добавлены
- [ ] Classifiers правильные
- [ ] Протестировано на TestPyPI
- [ ] Git tags созданы
- [ ] GitHub репозиторий публичный

---

Поздравляем! Теперь ваша библиотека доступна всему миру! 🎉
