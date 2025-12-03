from django.http import StreamingHttpResponse, FileResponse, HttpResponse

# Реализуйте логику под ваш формат
def download_backup(slug: str):
    """
    Должна вернуть HttpResponse с файлом на скачивание.
    Здесь вы генерируете бэкап (на лету или берёте готовый) для сущности по slug.
    """

    groupe = {
         'news': ['news', 'newsimage'],
         'temple_clergy': ['temple', 'clergy', 'templeimage', 'clergyimage'],
         'over': ['over', 'overimage'],
         'base': ['base', 'baseimage'],
         }
    # Пример (заглушка): вернуть пустой текстовый файл
    from io import BytesIO
    buf = BytesIO(b'backup placeholder for slug=' + slug.encode('utf-8'))
    resp = FileResponse(buf, as_attachment=True, filename=f'{slug}.txt')
    return resp
def restore_backup(slug: str, uploaded_file):
    """
    Принимает slug и загруженный файл (InMemoryUploadedFile / TemporaryUploadedFile).
    Реализуйте разбор и восстановление данных по вашему формату.
    Ничего не возвращает, в случае ошибки — бросает исключение.
    """
    # Пример (заглушка): просто читаем файл
    for _ in uploaded_file.chunks():
        pass
    # Ваша логика восстановления...
    return