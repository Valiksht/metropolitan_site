from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, ListView, TemplateView
from django.db.models.functions import Lower

from .models import (
    BaseImage,
    Clergy,
    Contact,
    Deal,
    GodServes,
    News,
    NewsImage,
    Secret,
    Temple,
    TempleClergy,
)


class HomePage(TemplateView):
    """Функия главной страницы"""

    template_name = 'homepage/main.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['base_image'] = BaseImage.objects.get(name='main')
        except BaseImage.DoesNotExist:
            context['base_image'] = None
        main_news = News.objects.filter(
            on_main=True, date__lte=timezone.now()
        ).order_by('-date')
        context['main_news_list'] = main_news
        all_news = News.objects.filter(
            on_main=False, date__lte=timezone.now()
        ).order_by('-date')[:8]
        context['all_news_list'] = all_news
        return context


class NewsListView(ListView):
    """Функция списка новостей"""

    model = News
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'
    # Добавить пагинацию.
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-date')
        queryset = queryset.annotate(
            num_images=Count(
                'images'
            )  # Добавляем поле num_images, которое подсчитывает связанные NewsImage
        )
        return queryset


class NewsDetailView(DetailView):
    """Функция детальной страницы новости"""

    model = News
    template_name = 'news/news_detail.html'
    context_object_name = 'news'

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-date')
        queryset = queryset.prefetch_related(
            Prefetch(
                'images',
                queryset=NewsImage.objects.all().order_by('pk'),
                to_attr='gallery_images',
            ),
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            news_object = context[self.context_object_name]
            context['news_gallery'] = news_object.gallery_images
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            context['news_gallery'] = None
        return context


class TempleListView(ListView):
    """Функция списка храмов"""

    model = Temple
    template_name = 'temple/temple_list.html'
    context_object_name = 'temple_list'

    def get_queryset(self):
        qs = super().get_queryset().order_by('order', Lower('name'))
        status_value = self.request.GET.get('status', 'all')
        allowed_values = {value for value, _ in Temple.STATUS_TEMPLE}
        if status_value in allowed_values:
            qs = qs.filter(status=status_value)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Храмы'
        try:
            context['base_temple'] = BaseImage.objects.get(name='base_temple')
        except BaseImage.DoesNotExist:
            context['base_temple'] = None
        # список фильтров берём из choices
        context['status_choices'] = Temple.STATUS_TEMPLE
        context['selected_status'] = self.request.GET.get('status', 'all')
        return context


class TempleDetailView(DetailView):
    """Функция детальной страницы храма"""

    model = Temple
    template_name = 'temple/temple_detail.html'
    context_object_name = 'temple'

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch(
                    'temple_clergy',
                    queryset=TempleClergy.objects.select_related(
                        'clergy'
                    ).order_by('order', 'clergy__last_name'),
                    to_attr='clergy_in_temple',
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        temple_object = context[self.context_object_name]
        context['title'] = temple_object.name
        context['clergy_in_temple'] = temple_object.clergy_in_temple
        try:
            base_image = BaseImage.objects.get(name='base_temple')
            context['base_temple'] = base_image
        except Exception as e:
            # Обработка других возможных исключений
            print(f"Произошла ошибка при получении базового изображения: {e}")
            context['base_temple'] = None
        return context


class ClergyListView(ListView):
    """Функция списка духовенства"""

    model = Clergy
    template_name = 'clergy/clergy_list.html'
    context_object_name = 'clergy_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Духовенство'
        return context


class ClergyDetailView(DetailView):
    """Функция детальной страницы духовенства"""

    model = Clergy
    template_name = 'clergy/clergy_detail.html'
    context_object_name = 'clergy'

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch(
                    'clergy_temple',
                    queryset=TempleClergy.objects.select_related(
                        'temple'
                    ).order_by(
                        'order',
                    ),
                    to_attr='temple_list',
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clergy_object = context[self.context_object_name]
        context['title'] = clergy_object.last_name
        context['temple_list'] = clergy_object.temple_list
        context['post_list'] = [
            line.strip()
            for line in clergy_object.post.split('\n')
            if line.strip()
        ]
        return context


class DealView(ListView):
    """Функция списка направлений деятельности"""

    model = Deal
    template_name = 'deal/deal.html'
    context_object_name = 'deal_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Деятельность'
        return context


class DealDetailView(DetailView):
    """Функция детальной страницы направления деятельности"""

    model = Deal
    template_name = 'deal/deal_detail.html'
    context_object_name = 'deal'


class SecretView(ListView):
    """Функция списка таинств"""

    model = Secret
    template_name = 'secret/secret.html'
    context_object_name = 'secret_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Тайна'
        return context


class SecretDetailView(DetailView):
    """Функция детальной страницы таинств"""

    model = Secret
    template_name = 'secret/secret_detail.html'
    context_object_name = 'secret'


class GodServesView(ListView):
    """Функция списка богослужений"""

    model = GodServes
    template_name = 'god_serves/god_serves.html'
    context_object_name = 'godserves_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Богослужения'
        return context


class ContactView(ListView):
    """Функция списка контактов"""

    model = Contact
    template_name = 'contact/contact.html'
    context_object_name = 'contact_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Контакты'
        return context


SEARCH_CONFIG = [
    {
        'label': 'Свещенослужители',
        'model': Clergy,
        'fields': [
            'first_name',
            'last_name',
            'post',
        ],  # по каким полям искать
        'limit': 50,  # ограничение результатов на секцию
    },
    {
        'label': 'Новости',
        'model': News,
        'fields': ['title', 'description'],
        'limit': 20,
    },
    {
        'label': 'Храмы',
        'model': Temple,
        'fields': ['name', 'description'],
        'limit': 20,
    },
    {
        'label': 'Таинства',
        'model': Secret,
        'fields': ['full_name', 'description'],
        'limit': 20,
    },
    {
        'label': 'Деятельность',
        'model': Deal,
        'fields': ['stream', 'description', 'sv_curator_name'],
        'limit': 20,
    },
]


def _filter_qs(model, fields, query: str):
    qs = model.objects.all()
    q = (query or '').strip()
    if not q:
        return qs.none()
    # разбиваем по словам: все слова должны встретиться (AND),
    # по полям — соответствие в любом из полей (OR)
    terms = [t for t in q.split() if t]
    for term in terms:
        part = Q()
        for f in fields:
            part |= Q(**{f'{f}__icontains': term})
        qs = qs.filter(part)
    return qs.distinct()


@require_GET
def unified_search(request):
    q = request.GET.get('q', '').strip()
    sections = []
    total = 0
    for cfg in SEARCH_CONFIG:
        qs = _filter_qs(cfg['model'], cfg['fields'], q)
        items = list(qs[: cfg.get('limit', 20)])
        total += len(items)
        sections.append(
            {
                'label': cfg['label'],
                'items': items,
            }
        )
    context = {
        'q': q,
        'sections': sections,
        'total': total,
    }
    return render(request, 'search/search.html', context)


class SearchListView(ListView):
    """Функция списка поиска"""

    model = Temple
    template_name = 'search/search.html'
    context_object_name = 'objects'
    paginate_by = 20
    search_param = 'q'
    search_fields = [
        'name',
    ]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get(self.search_param, '').strip()
        if not q:
            return (
                qs.none()
            )  # без запроса ничего не показываем (или верните qs)
        terms = [t for t in q.split() if t]
        for term in terms:
            part = Q()
            for field in self.search_fields:
                part |= Q(**{f'{field}__icontains': term})
            qs = qs.filter(part)
        return qs.distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get(self.search_param, '').strip()
        return ctx
