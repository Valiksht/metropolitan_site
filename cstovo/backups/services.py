import json
from django.http import StreamingHttpResponse, FileResponse, HttpResponse
from io import BytesIO
from django.apps import apps
from django.db import transaction
from datetime import datetime, date


class DjangoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)
    
GROUPE = {
     'news': ('News', 'NewsImage'),
     'temple_clergy': ('Clergy', 'Temple', 'TempleClergy'),
     'over': ('Secret', 'GodServes', 'Deal', 'Contact'),
     'base': ('BaseImage',),
     }

LOOKUP_MODEL_PARAMS = {
    'Clergy': ('first_name', 'last_name'),
    'Temple': ('name',),
    'TempleClergy': ('temple_id', 'clergy_id'),
    'News': ('title',), 
    'NewsImage': ('news', 'image'),
    'Secret': ('full_name',), 
    'GodServes': ('name',), 
    'Deal': ('stream',), 
    'Contact': ('phone', 'email'),
    'BaseImage': ('name',),
}
    
KEY_MAP = {
    'NewsImage': {
        'news': ('News', 'news_id'),
    },
    'TempleClergy': {
        'clergy': ('Clergy', 'clergy_id'),
        'temple': ('Temple', 'temple_id'),
    },
}

RELATION_ONLY_MODELS = {
    'TempleClergy',
    'NewsImage',
}

IMAGE_FIELDS = {
    'Clergy': ('image', 'small_image'),
    'Temple': ('image', 'small_image'),  # если есть такая модель, то добавьте 'small_image'
    'News': ('image',),
    'Secret': ('image',),
    'GodServes': ('image',),
    'Deal': ('image',),
    'NewsImage': ('image',),
    'BaseImage': ('image',),   # если есть такая модель
    # добавьте сюда другие модели/поля при необходимости
}

# Реализуйте логику под ваш формат
def download_backup(slug: str):
    """
    Должна вернуть HttpResponse с файлом на скачивание.
    Здесь вы генерируете бэкап (на лету или берёте готовый) для сущности по slug.
    """

    print ('Запуск выгрузки')
    print (slug)
    dump_data = {}
    for model_name in GROUPE[slug]:
        print (model_name)
        try:
            model = apps.get_model(app_label='temple', model_name=model_name)
            objects = list(model.objects.all().values())
            dump_data[model_name] = objects
        except Exception as e:
            dump_data[model_name] = []
            print (e)
    json_data = json.dumps(dump_data, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder)
    buf = BytesIO()
    buf.write(json_data.encode('utf-8'))
    buf.seek(0)
    resp = FileResponse(buf, as_attachment=True, filename=f'{slug}.txt', content_type='application/json')
    return resp


def restore_backup(slug: str, uploaded_file):
    """
    Принимает slug и загруженный файл (InMemoryUploadedFile / TemporaryUploadedFile).
    Реализуйте разбор и восстановление данных по вашему формату.
    Ничего не возвращает, в случае ошибки — бросает исключение.
    """
    # Пример (заглушка): просто читаем файл
    print ('Завыск загрузки')
    print(f'Slug: {slug}')
    print(f'File: {uploaded_file}')
    
    try:
        uploaded_file.seek(0)
        json_data = json.loads(uploaded_file.read().decode('utf-8'))
    except Exception as er:
        print(er)
        return er
    
    print(len(json_data))


    group_model_names = GROUPE[slug]

    total_count = 0
    created_count = 0
    duplicate_count = 0

    created_map = {model_name: {} for model_name in group_model_names}

    # ---------------------- ФАЗА 1: создание/обновление "основных" моделей без учёта внешних ключей ----------------------
    for model_name in group_model_names:
        print(f'Загрузка модели {model_name}')
        if model_name in RELATION_ONLY_MODELS:
            continue
        Model = apps.get_model(app_label='temple', model_name=model_name)
        model_items = json_data.get(model_name, [])
        lookup_fields = LOOKUP_MODEL_PARAMS.get(model_name, ())
        for item in model_items:
            total_count += 1
            fields = item.copy()          # копируем все поля из item
            old_id = fields.pop('id', None)  # вытаскиваем id и убираем его из fields
            fk_config = KEY_MAP.get(model_name, {})
            for fk_field, (target_model_name, json_fk_key) in fk_config.items():
                if target_model_name not in group_model_names:
                    fields.pop(fk_field, None)
                    fields.pop(json_fk_key, None)
            for img_field in IMAGE_FIELDS.get(model_name, ()):
                fields.pop(img_field, None)
            # тут удалить поле с фото
            lookup_kwargs = {}
            for lf in lookup_fields:
                if lf in fields:
                    lookup_kwargs[lf] = fields[lf]
            if lookup_kwargs:
                obj, created = Model.objects.update_or_create(
                    defaults=fields,
                    **lookup_kwargs,
                )
            else:
                obj = Model.objects.create(**fields)  # Просто создаём новый объект с указанными полями
                created = True  # Помечаем, что объект был создан
            if created:  # Если объект был создан как новый
                created_count += 1  # Увеличиваем счётчик созданных объектов
            else:  # Иначе объект уже существовал и был обновлён
                duplicate_count += 1  # Увеличиваем счётчик "дублирующих" (обновлённых) объектов
            if old_id is not None:  # Если в JSON был указан старый ID
                created_map[model_name][old_id] = obj.pk  # Сохраняем сопоставление старого ID к новому первичному ключу в базе
        print(total_count, created_count, duplicate_count)
    # ---------------------- ФАЗА 2: привязка внешних ключей и создание relation‑only моделей ----------------------
    # Сначала обновляем FK у "основных" моделей внутри группы
    print('Обновление FK у "основных" моделей внутри группы')
    for model_name in group_model_names:  # Снова итерируемся по именам моделей группы
        if model_name in RELATION_ONLY_MODELS:  # Пропускаем relation‑only модели на этом шаге
            continue  # Переходим к следующей модели
        Model = apps.get_model(app_label='temple', model_name=model_name)  # Получаем класс модели по имени
        model_items = json_data.get(model_name, [])  # Получаем список элементов из backup_data для этой модели
        fk_config = KEY_MAP.get(model_name, {})  # Получаем конфигурацию FK для текущей модели (если она есть)
        if not fk_config:  # Если для модели нет описанных внешних ключей
            continue  # Переходим к следующей модели
        for item in model_items:  # Итерируемся по каждой записи из бэкапа для текущей модели
            old_id = item.get('id')  # Забираем старый ID объекта
            if old_id is None:  # Если старого ID нет
                continue  # Ничего сделать не можем – переходим к следующей записи
            new_pk = created_map[model_name].get(old_id)  # Получаем новый PK в базе по старому ID
            if new_pk is None:  # Если объект по этому старому ID не был создан/обновлён
                continue  # Пропускаем – возможно, он не попал под условия или был пропущен
            obj = Model.objects.get(pk=new_pk)  # Загружаем объект из базы по новому PK
            updated = False  # Флаг – меняли ли мы хоть одно FK поле у объекта
            for fk_field, (target_model_name, json_fk_key) in fk_config.items():  # Итерируемся по каждому описанному FK полю
                if target_model_name not in group_model_names:  # Если целевая модель не входит в текущую группу
                    continue  # Пропускаем – FK на другие группы не заполняем
                old_target_id = item.get(json_fk_key)  # Забираем старый ID связанного объекта из JSON
                if not old_target_id:  # Если старый ID пустой или отсутствует
                    continue  # Нечего связывать – переходим к следующему полю
                new_target_pk = created_map[target_model_name].get(old_target_id)  # Ищем новый PK целевой модели по старому ID
                if not new_target_pk:  # Если целевой объект ещё не был создан/обновлён в этой группе
                    continue  # Не можем установить связь – пропускаем
                setattr(obj, f"{fk_field}_id", new_target_pk)  # Устанавливаем значение FK поля через *_id, чтобы избежать лишних запросов
                updated = True  # Помечаем, что объект был изменён
            if updated:  # Если хотя бы одно FK поле было обновлено
                obj.save()  # Сохраняем изменения в базе
    # Теперь создаём/обновляем relation‑only модели (например, through‑таблицы) – внутри группы
        print(total_count, created_count, duplicate_count)
    print('Создание/обновление relation-only моделей внутри группы')
    for model_name in group_model_names:  # Итерируемся по именам моделей группы
        if model_name not in RELATION_ONLY_MODELS:  # Нас интересуют только relation‑only модели
            continue  # Пропускаем все остальные модели
        Model = apps.get_model(app_label='temple', model_name=model_name)  # Получаем класс relation‑only модели по имени
        model_items = json_data.get(model_name, [])  # Получаем список элементов из backup_data для этой relation‑only модели
        fk_config = KEY_MAP.get(model_name, {})  # Получаем конфигурацию FK для этой модели
        lookup_fields = LOOKUP_MODEL_PARAMS.get(model_name, ())  # Получаем набор полей, по которым ищем уникальную связку
        for item in model_items:  # Итерируемся по каждой записи relation‑only модели из бэкапа
            total_count += 1  # Увеличиваем общий счётчик обработанных записей (relation‑only тоже считаем)
            fields = item.copy()              # копируем все поля из объекта
            old_id = fields.pop('id', None)   # при желании можно сохранить старый id
            for img_field in IMAGE_FIELDS.get(model_name, ()):
                fields.pop(img_field, None)
            # Преобразуем FK‑поля по карте старых/новых ID, но только если целевая модель внутри текущей группы
            for fk_field, (target_model_name, json_fk_key) in fk_config.items():  # Итерируемся по описанию FK полей
                if target_model_name not in group_model_names:  # Если целевая модель принадлежит другой группе
                    fields.pop(fk_field, None)  # Убираем FK поле – оставляем связь пустой
                    fields.pop(json_fk_key, None)  # Убираем старый ID из полей JSON, если есть
                    continue  # Переходим к следующему FK полю
                old_target_id = item.get(json_fk_key)  # Получаем старый ID связанного объекта
                if not old_target_id:  # Если старый ID не задан
                    fields.pop(fk_field, None)  # Убираем FK поле, чтобы не ставить некорректное значение
                    continue  # Переходим к следующему FK полю
                new_target_pk = created_map[target_model_name].get(old_target_id)  # Ищем новый PK для связанного объекта
                if not new_target_pk:  # Если целевой объект в этой группе ещё не создан/не найден
                    fields.pop(fk_field, None)  # Убираем FK поле – связь установить нельзя
                    continue  # Переходим к следующему FK полю
                fields[fk_field + "_id"] = new_target_pk  # Явно задаём поле *_id новым PK (чтобы не тянуть объект из базы)
            # Формируем условия поиска для relation‑only модели (чтобы не дублировать связки)
            lookup_kwargs = {}  # Инициализируем словарь условий поиска
            for lf in lookup_fields:  # Проходим по уникальным полям relation‑only модели
                if lf in fields:  # Если поле присутствует в данных
                    lookup_kwargs[lf] = fields[lf]  # Добавляем его в словарь поиска
            if lookup_kwargs:  # Если заданы поля для поиска
                obj, created = Model.objects.get_or_create(  # Пытаемся найти или создать relation‑only запись
                    defaults=fields,  # Если не найдена – создадим с этими полями
                    **lookup_kwargs,  # Условия поиска существующей записи
                )  # Завершаем вызов get_or_create
                if not created:  # Если запись уже существовала
                    # При необходимости можно обновить дополнительные поля – тогда используйте update_or_create.
                    pass  # Здесь ничего не делаем, оставляем как есть
            else:  # Если уникальные поля для поиска не заданы
                obj = Model.objects.create(**fields)  # Создаём новую relation‑only запись
                created = True  # Помечаем, что запись была создана
            if created:  # Если создана новая запись relation‑only
                created_count += 1  # Увеличиваем счётчик созданных
            else:  # Иначе запись уже существовала
                duplicate_count += 1  # Увеличиваем счётчик "дублей"
            if old_id is not None:
                created_map[model_name][old_id] = obj.pk
    print(total_count, created_count, duplicate_count)
    return total_count, created_count, duplicate_count