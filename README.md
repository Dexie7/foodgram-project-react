# YaMDb Final
![YaMDb workflow](https://github.com/dexie7/foodgram-project-react/actions/workflows/yamdb_workflow.yml/badge.svg)
## О проекте:

Сайт Foodgram, «Продуктовый помощник». На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.
## Начало работы

Для запуска проекта на локальной машине в целях разработки и тестирования.

### Предварительная подготовка

#### Публичный IP
158.160.6.7

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

### Установка проекта (на примере Linux)

- Создайте папку для проекта YaMDb `mkdir foodgram` и перейдите в нее `cd foodgram`
- Склонируйте этот репозиторий в текущую папку `git@github.com:Dexie7/foodgram-project-react.git`.
- Создайте файл `.env` командой `touch .env` и добавьте в него переменные окружения для работы с базой данных:
```sh
DB_NAME=postgres # имя базы данных
POSTGRES_USER=postgres # логин для подключения к базе данных
POSTGRES_PASSWORD=postgres # пароль для подключения к БД (установите свой)
DB_HOST=db # название сервиса (контейнер в котором будет развернута БД)
DB_PORT=5432 # порт для подключения к БД
SECRET_KEY=... # секретный ключ
DEBUG = True # данную опцию следует добавить для отладки
```
- Запустите docker-compose `sudo docker-compose up -d` 
- Примените миграции `sudo docker-compose exec web python manage.py migrate`
- Соберите статику `sudo docker-compose exec web python manage.py collectstatic --no-input`
- Создайте суперпользователя Django `sudo docker-compose exec web python manage.py createsuperuser --email 'admin@yamdb.com'`


![](https://img.shields.io/pypi/pyversions/p5?logo=python&logoColor=yellow&style=for-the-badge)
![](https://img.shields.io/badge/Django-2.2.16-blue)
![](https://img.shields.io/badge/DRF-3.12.4-lightblue)