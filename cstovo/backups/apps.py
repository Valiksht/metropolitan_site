from django.apps import AppConfig
from django.db.models.signals import post_migrate


def ensure_defaults(sender, **kwargs):
    Backup = sender.get_model('BackupLog')
    data = [
        {'name': 'Новости', 'slug': 'news', 'last_export_at': ''},
        {
            'name': 'Духовенство и храмы',
            'slug': 'temple_clergy',
            'last_export_at': '',
        },
        {
            'name': 'Таинства, деятельность, богослужения и контакты',
            'slug': 'over',
            'last_export_at': '',
        },
        {'name': 'Базовые изображения', 'slug': 'base', 'last_export_at': ''},
    ]
    for d in data:
        Backup.objects.update_or_create(name = d['name'], slug = d['slug'])


class BackupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backups'
    verbose_name = 'Бэкапы'

    def ready(self):
        post_migrate.connect(ensure_defaults, sender=self)
