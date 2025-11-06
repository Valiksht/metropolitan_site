from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import BaseImage

@receiver([post_save, post_delete], sender=BaseImage)
def clear_site_settings_cache(*args, **kwargs):
    cache.delete('site_settings_ctx')