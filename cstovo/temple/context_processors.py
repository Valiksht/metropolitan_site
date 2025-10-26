from .models import Secret, Deal


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
