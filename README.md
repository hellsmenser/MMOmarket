<div align="center">
  <img src="public/logo.svg" />
  <h1>MMO Market</h1>
  <p>Веб-приложение для мониторинга цен игровых предметов и валюты Lineage 2</p>
  <a href="https://hellsmenser.github.io/MMOMarket-frontend/" target="_blank" style="font-size:18px;font-weight:600;color:#00ff8f;">🌐 Открыть на GitHub Pages</a>
</div>

## О проекте

- Автоматический сбор цен с различных источников
- REST API для получения истории цен и текущих курсов
- Асинхронная обработка и хранение данных
- Интеграция с Telegram для уведомлений
- Гибкая настройка и расширяемость
- Использование Telethon для работы с Telegram
- Предподготовка: ручная настройка Telegram-аккаунта и подписок

## Предподготовка

Перед запуском сервиса необходимо подготовить Telegram-аккаунт, который будет использоваться для сбора данных:

1. **Создайте отдельный Telegram-аккаунт** (рекомендуется не использовать личный аккаунт).
2. **Авторизуйте аккаунт через Telethon**:
   - Получите `api_id` и `api_hash` на https://my.telegram.org.
   - Запустите скрипт авторизации Telethon, следуйте инструкциям для ввода кода подтверждения.
3. **Подпишитесь на нужные каналы и группы**:
   - Найдите каналы/группы, где публикуются цены на интересующие предметы.
   - Вручную подпишитесь на них через Telegram-клиент.
   - Проверьте, что аккаунт видит сообщения и может их читать.
4. **Добавьте аккаунт в приватные чаты, если требуется**.
5. **Проверьте работу Telethon**:
   - Запустите тестовый скрипт для получения сообщений из каналов.
   - Убедитесь, что сообщения успешно читаются.

> Важно: процесс подготовки Telegram-аккаунта и подписок полностью ручной и не автоматизируется средствами проекта. Это связано с ограничениями Telegram и необходимостью ручного подтверждения.

## Технологии

- Python 3.11+
- FastAPI — быстрый и современный веб-фреймворк
- SQLAlchemy — ORM для работы с базой данных
- APScheduler — планировщик задач
- Pydantic — валидация и сериализация данных
- Alembic — миграции базы данных
- Telethon — асинхронная работа с Telegram

## Быстрый старт

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/hellsmenser/MMOMarket.git
   cd MMOMarket
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Запустите миграции:
   ```bash
   alembic upgrade head
   ```
4. Запустите приложение:
   ```bash
   python run.py
   ```

## API

Документация доступна по адресу `/docs` после запуска сервера.

### Примеры эндпоинтов
- `/prices/` — история цен
- `/coin/` — курс игровой валюты
- `/items/` — информация о предметах

## Структура проекта

- `app/` — основной код приложения
  - `api/` — роутеры и обработчики API
  - `core/` — конфигурация, логирование, инициализация
  - `db/` — модели, схемы, CRUD
  - `services/` — бизнес-логика
  - `tasks/` — задачи для планировщика
  - `telegram/` — интеграция с Telegram (Telethon)
  - `utils/` — вспомогательные функции
- `migrations/` — миграции Alembic
- `requirements.txt` — зависимости
- `run.py` — точка входа

## 💡 Контакты и поддержка

- 🌐 Попробовать: [https://hellsmenser.github.io/MMOMarket-frontend/](https://hellsmenser.github.io/MMOMarket-frontend/)
- Telegram: [@hellsmenser](https://t.me/hellsmenser)
- Issues: [GitHub Issues](https://github.com/hellsmenser/MMOMarket-frontend/issues)
- Frontend: [MMO Market frontend](https://github.com/hellsmenser/MMOmarket-frontend)

---

<div align="center">
  <sub>Made with ❤️ for Lineage 2 Community</sub>
</div>

