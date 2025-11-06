from .models import Secret, Deal, BaseImage
from django.core.cache import cache


def dropdown_list(request):
    """
    Добавляет список всех таинств в контекст шаблона.
    """
    all_secrets = Secret.objects.only('pk', 'name',).order_by(
        'pk'
    )
    all_deal = Deal.objects.only('pk', 'stream',).order_by(
        'pk'
    )
    context = {'all_secrets': all_secrets, 'all_deal': all_deal}
    return context


def site_settings(request):
    data = cache.get('site_settings_ctx')
    if data is None:
        s = BaseImage.objects.filter(name='main').order_by('-id').first()
        url = s.image.url if s and s.image else None
        data = {'HEADER_BG_URL': url}
        cache.set('site_settings_ctx', data, 60 * 60)  # 1 час
    return data