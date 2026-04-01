# ⛏️ Minecraft State Bot — Инструкция по запуску

## 📊 Шаг 1: Создай Google Таблицу

Создай таблицу и назови её `MinecraftStateBot` (или своё название).

Создай **5 листов** с такими шапками (первая строка):

| Лист | Шапка (через запятую) |
|---|---|
| `users` | `telegram_id, username, nickname, role, reputation` |
| `tasks` | `id, title, description, resource, quantity, deadline, status` |
| `reports` | `id, telegram_id, username, resource, quantity, photo_id, status` |
| `warehouse` | `resource_name, count` |
| `warns` | `telegram_id, username, reason` |

---

## ☁️ Шаг 2: Google Cloud Console

1. Зайди на [console.cloud.google.com](https://console.cloud.google.com)
2. Создай проект → включи **Google Drive API** и **Google Sheets API**
3. Создай **Service Account** → скачай JSON-ключ
4. Открой таблицу → поделись ею с `email` из JSON-файла (права: **Редактор**)

---

## 🚀 Шаг 3: Деплой на Render

В настройках Render → **Environment Variables** добавь:

| Переменная | Значение |
|---|---|
| `BOT_TOKEN` | Токен из @BotFather |
| `ADMIN_ID` | Твой Telegram ID (число) |
| `SHEET_NAME` | Название твоей таблицы |
| `GOOGLE_CREDS_JSON` | Весь текст JSON-файла (вставь как есть) |

**Start Command:** `python main.py`

---

## 📁 Структура файлов

```
minecraft_bot/
├── config.py
├── main.py
├── requirements.txt
├── database/
│   └── sheets.py        # Вся логика Google Sheets
├── handlers/
│   ├── user.py          # Хендлеры игроков
│   └── admin.py         # Хендлеры админа
├── keyboards/
│   └── menus.py         # Все кнопки
└── states/
    └── states.py        # FSM-состояния
```

---

## ✨ Функционал

**Игрок:** регистрация по нику → задачи → сдача отчёта с фото → склад → статистика → профиль с репутацией и варнами

**Админ:** объявления всем → создание задач (FSM 5 шагов) → удаление задач → выдача варнов (кик при 3) → ручное редактирование склада → просмотр и принятие/отклонение отчётов → авто-начисление репутации и склада
