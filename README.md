# YaMDb Final
![Foodgram workflow](https://github.com/dexie7/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)
## О проекте:

Автор: Пермяков Е.Г.
Сайт Foodgram, «Продуктовый помощник». На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.
## Начало работы

Для запуска проекта на локальной машине в целях разработки и тестирования.

### Предварительная подготовка

#### Публичный IP
- IP: 158.160.14.99
- данные админа:
    - логин: admin
    - пароль: admin
- пользователи:
    - логин: test@yandex.ru
    - пароль: test34543test

#### Установка Docker
Установите Docker, используя инструкции с официального сайта:
- для [Windows и MacOS](https://www.docker.com/products/docker-desktop) 
- для [Linux](https://docs.docker.com/engine/install/ubuntu/). Установите [Docker Compose](https://docs.docker.com/compose/install/)

### Подготовка сервера

- Войдите на свой удаленный сервер в облаке `ssh [имя пользователя]@[ip-адрес]`
- Остановите службу nginx `sudo systemctl stop nginx`
- Установите docker `sudo apt install docker.io`
- Установите docker-compose `sudo curl -L "https://github.com/docker/compose/releases/download/1.26.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose`
- Затем необходимо задать правильные разрешения, чтобы сделать команду docker-compose исполняемой `sudo chmod +x /usr/local/bin/docker-compose` 
- Скопируйте файлы docker-compose.yaml и nginx/default.conf из вашего проекта на сервер в home/<ваш_username>/docker-compose.yaml и home/<ваш_username>/nginx/default.conf соответственно. Используя следующую команду `scp [путь к файлу] [имя пользователя]@[имя сервера/ip-адрес]:[путь к файлу]`

### Запуск проекта (на примере Linux) в контейнерах Docker

- Создайте папку для проекта `mkdir foodgram-project-react` и перейдите в нее `cd foodgram-project-react`
- Склонируйте этот репозиторий в текущую папку `git@github.com:Dexie7/foodgram-project-react.git`.
-Перейдите в папку `cd foodgram-project-react/infra`
- Создайте файл `.env` при помощи команды ниже:
```
echo 'SECRET_KEY=super-secret
ALLOWED_HOSTS=*
DEBUG=0
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
' > .env
```
- Запустите docker-compose `sudo docker-compose up -d` 
- Примените миграции `sudo docker-compose exec backend python manage.py migrate`
- Соберите статику `sudo docker-compose exec backend python manage.py collectstatic --no-input`
- Создайте суперпользователя Django `sudo docker-compose exec backend python manage.py createsuperuser'`
- Заполните БД подготовленными данными при первом запуске
```
sudo docker-compose cp ../data/ingredients.json backend:/app/ingredients.json 
sudo docker-compose exec backend python manage.py importingredients ingredients.json
sudo docker-compose exec backend rm ingredients.json
```
#### Результат

Будет запущен весь проект.

Frontend - http://localhost/

Админка - http://localhost/secure_zone/


### Deploy на сервер

При пуше в ветку master выполняется автоматическое разворачивание проекта на сервере (после всех тестов). Единственно, необходимо создать суперпользователя используя команду выше

#### Результат

Будет запущен весь проект.

Рецепты - http://158.160.14.99/recipes

Админка - http://158.160.14.99/secure_zone/


![](https://img.shields.io/pypi/pyversions/p5?logo=python&logoColor=yellow&style=for-the-badge)
![](https://img.shields.io/badge/Django-2.2.16-blue)
![](https://img.shields.io/badge/DRF-3.12.4-lightblue)