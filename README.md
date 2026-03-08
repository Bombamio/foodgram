## Описание проекта

**Foodgram** — это веб-приложение для публикации и обмена рецептами.
Пользователи могут создавать рецепты, подписываться на авторов, добавлять рецепты в избранное и формировать список покупок.

Основные возможности проекта:

* регистрация и авторизация пользователей
* создание, редактирование и удаление рецептов
* добавление рецептов в избранное
* подписка на авторов
* формирование списка покупок
* скачивание списка покупок в виде файла
* фильтрация рецептов по тегам
* загрузка изображений рецептов
* API для взаимодействия фронтенда и бекенда

Проект реализован с использованием **Django REST Framework** и разворачивается в **Docker-контейнерах**.

---

# Стек технологий

### Backend

* Python 3.12
* Django
* Django REST Framework
* Djoser
* PostgreSQL
* Gunicorn

### Infrastructure

* Docker
* Docker Compose
* Nginx

### Дополнительно

* JWT-аутентификация
* Django Filters

---

# Как развернуть проект на сервере

### 1. Клонировать репозиторий

```bash
git clone https://github.com/Bombamio/foodgram.git
cd foodgram
```

---

### 2. Создать файл `.env`

Пример:

```env
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432

SECRET_KEY=django_secret_key
DEBUG=False
ALLOWED_HOSTS=your_domain,127.0.0.1
```

---

### 3. Запустить контейнеры

```bash
docker compose up -d --build
```

---

### 4. Выполнить миграции

```bash
docker compose exec backend python manage.py migrate
```

---

### 5. Создать суперпользователя

```bash
docker compose exec backend python manage.py createsuperuser
```

---

### 6. Собрать статику

```bash
docker compose exec backend python manage.py collectstatic
```

---

После этого проект будет доступен по адресу:

```
http://your_domain
```

---

# Запуск проекта локально (без Docker)

### 1. Клонировать репозиторий

```bash
git clone https://github.com/your_username/foodgram.git
cd foodgram/backend
```

---

### 2. Создать виртуальное окружение

```bash
python -m venv venv
```

Активировать:

Linux / MacOS

```bash
source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

---

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

---

### 4. Выполнить миграции

```bash
python manage.py migrate
```

---

### 5. Запустить сервер

```bash
python manage.py runserver
```

---

# Документация API

После запуска проекта документация будет доступна по адресу:

```
http://localhost/api/docs/
```

---

# Ссылка на развернутый проект

```
https://your_domain
```

---

# Автор

Евсей Илья

GitHub:
https://github.com/Bombamio
