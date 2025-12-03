from django.db import models

class BackupLog(models.Model):
    """Модель логов резервного копирования"""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    last_export_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        verbose_name = 'Резервная копия'
        verbose_name_plural = 'Резервные копии'

    def __str__(self):
        return f"{self.name}: {self.last_export_at or '—'}"
