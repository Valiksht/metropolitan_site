# cstovo/backups/groups.py
from django.apps import apps

# Группы:
# 1) (Clergy, Temple, TempleClergy)
# 2) (Deal, Secret, GodServes, Contact)
# 3) (News, NewsImage)
# 4) (BaseImage)
#
# Пояснения по выбранным полям:
# - date_field: реальные поля даты в ваших моделях — есть только у News (date).
# - unique_fields: стабильные идентификаторы для дедупликации между базами.
#   При их наличии при импорте дубликаты пропускаются.
# - media_fields: File/Image-поля, чьи файлы нужно включать в архив.
#
# При необходимости скорректируйте unique_fields под вашу предметную логику.

GROUPS = {
    # Группа 1: Духовенство / Храмы / Связи
    "group_clergy_temple": {
        "title": "Выгрузка: Духовенство, храмы и связи",
        "models": [
            {
                "model": "temple.Clergy",
                "date_field": None,
                # Идентифицируем священнослужителя по сану + имени + фамилии
                "unique_fields": ["runk", "first_name", "last_name"],
                # Оба изображения включаем. small_image может быть производным, но пригодится для быстрого развёртывания
                "media_fields": ["image", "small_image"],
            },
            {
                "model": "temple.Temple",
                "date_field": None,
                # Храм идентифицируем по названию + адресу (location может быть пустым; при пустом будет считаться без него)
                "unique_fields": ["name", "location"],
                "media_fields": ["image", "small_image"],
            },
            {
                "model": "temple.TempleClergy",
                "date_field": None,
                # Связь храм–священнослужитель. Используем стабильные поля, а не PK:
                # - храм: name + location
                # - клирик: runk + first_name + last_name
                "unique_fields": [
                    "temple__name", "temple__location",
                    "clergy__runk", "clergy__first_name", "clergy__last_name",
                ],
                "media_fields": [],
            },
        ],
    },

    # Группа 2: Деятельность, таинства, богослужения, контакты
    "group_deals_misc": {
        "title": "Выгрузка: Деятельность, таинства, богослужения, контакты",
        "models": [
            {
                "model": "temple.Deal",
                "date_field": None,
                # Направление деятельности — по названию
                "unique_fields": ["stream"],
                "media_fields": ["image", "sv_curator_image"],
            },
            {
                "model": "temple.Secret",
                "date_field": None,
                # Таинство — по имени
                "unique_fields": ["name"],
                "media_fields": ["image"],
            },
            {
                "model": "temple.GodServes",
                "date_field": None,
                # Богослужение — по названию
                "unique_fields": ["name"],
                "media_fields": ["image"],
            },
            {
                "model": "temple.Contact",
                "date_field": None,
                # Контакт — считаем уникальным по email + телефон
                "unique_fields": ["email", "phone"],
                "media_fields": [],
            },
        ],
    },

    # Группа 3: Новости и изображения новостей
    "group_news": {
        "title": "Выгрузка: Новости",
        "models": [
            {
                "model": "temple.News",
                # Реальное поле даты есть здесь: date — его используем для фильтра «Дата до»
                "date_field": "date",
                # Уникальность новости — заголовок + дата публикации
                "unique_fields": ["title", "date"],
                "media_fields": ["image", "small_image"],
            },
            {
                "model": "temple.NewsImage",
                "date_field": None,
                # Привязка к новости через стабильные поля + сам путь файла
                "unique_fields": ["news__title", "news__date", "image"],
                "media_fields": ["image"],
            },
        ],
    },

    # Группа 4: Базовые изображения
    "group_base_images": {
        "title": "Выгрузка: Базовые изображения",
        "models": [
            {
                "model": "temple.BaseImage",
                "date_field": None,
                # В модели name уже уникален — используем его
                "unique_fields": ["name"],
                "media_fields": ["image"],
            },
        ],
    },
}


def get_model(model_path: str):
    app_label, model_name = model_path.split(".")
    return apps.get_model(app_label, model_name)