# GitHub и развёртывание

## Перед публикацией

Выполните в PowerShell:

```powershell
cd C:\Users\АННА\Desktop\Agent007\travel-smm-ai-bot
powershell -ExecutionPolicy Bypass -File .\run_tests.ps1
git check-ignore .env
```

Ожидается `34 passed`, а вторая команда должна вывести `.env`. Если `.env` не игнорируется, не продолжайте публикацию.

## Создание отдельного репозитория GitHub без GitHub CLI

1. Войдите на `github.com` и нажмите **New repository**.
2. Назовите репозиторий `travel-smm-ai-bot`.
3. Выберите Public или Private по требованиям курса.
4. Не добавляйте через сайт README, `.gitignore` и лицензию — они уже есть локально.
5. Нажмите **Create repository** и скопируйте HTTPS-адрес.

Затем выполните в каталоге проекта:

```powershell
git init -b main
git add .
git status
git commit -m "Build Travel SMM AI Assistant MVP"
git remote add origin https://github.com/ВАШ_ЛОГИН/travel-smm-ai-bot.git
git push -u origin main
```

Перед `git commit` убедитесь, что в списке нет `.env`, базы `.db` и `.venv`. Команду `git push` выполняйте только после создания своего репозитория и проверки файлов.

## Проверка Docker локально

Docker — желательный, но не обязательный элемент проекта. После запуска Docker Desktop:

```powershell
docker build -t travel-smm-ai-bot .
docker run --rm --env-file .env -v ${PWD}\data:/app/data travel-smm-ai-bot
```

Ожидается запуск long polling. Контейнер остановится по `Ctrl+C`. `.env` не копируется в образ благодаря `.dockerignore`.

## Выбор платформы

Для бота требуется постоянно работающий Python-процесс или контейнер с исходящим доступом к Telegram/OpenAI и постоянным диском для SQLite. Подойдут платформы с background worker или VPS. Перед выбором необходимо отдельно проверить актуальные тарифы, ограничения long polling, хранение диска и правила обработки секретов.

Развёртывание не выполнено автоматически: платформа не выбрана, внешние аккаунты и разрешение пользователя не предоставлены.

## Переменные на платформе

Добавьте в защищённые настройки сервиса:

- `MOCK_MODE`;
- `TELEGRAM_BOT_TOKEN`;
- `ADMIN_TELEGRAM_ID`;
- `TARGET_CHANNEL_ID`;
- `OPENAI_API_KEY` — только для реального режима;
- модели и путь базы при необходимости.

Не загружайте файл `.env` в GitHub.

## Финальная проверка после развёртывания

1. `/start` доступен администратору.
2. Посторонний ID заблокирован.
3. Мок-режим проходит весь сценарий.
4. Отказ на подтверждении не публикует материал.
5. Подтверждение публикует только в тестовый канал.
6. После перезапуска черновик сохраняется.
7. В логах нет токенов и полных чувствительных ответов.
