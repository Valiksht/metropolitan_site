from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Prefetch, Count
from django.views.generic import TemplateView, ListView, DetailView
from django.utils import timezone

from .models import (
    BaseImage,
    News,
    NewsImage,
    Temple,
    Status,
    Clergy,
    Contact,
    Deal,
    Secret,
    GodServes,
    TempleClergy,
)


class HomePage(TemplateView):
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
    model = News
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'
    # Добавить пагинацию.
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-date')
        queryset = queryset.annotate(
            num_images=Count('images') # Добавляем поле num_images, которое подсчитывает связанные NewsImage
        )
        return queryset


class NewsDetailView(DetailView):
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
    model = Temple
    template_name = 'temple/temple_list.html'
    context_object_name = 'temple_list'

    def get_queryset(self):
        qs = super().get_queryset().select_related('status').order_by('order', 'name')
        status_id = self.request.GET.get('status', 'all')
        if status_id != 'all':
            qs = qs.filter(status_id=status_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Храмы'
        try:
            base_image = BaseImage.objects.get(name='base_temple')
            context['base_temple'] = base_image
        except Exception as e:
            # Обработка других возможных исключений
            print(f"Произошла ошибка при получении базового изображения: {e}")
            context['base_temple'] = None
        try:
            context['all_statuses'] = Status.objects.all().order_by('order') # Переименовал status_list в all_statuses
        except Exception as e:
            print(f"Произошла ошибка при получении статусов: {e}")
            context['all_statuses'] = [] # Передаем пустой список, если ошибка
        # Передаем имя выбранного статуса в контекст, чтобы пометить активную радиокнопку
        context['selected_status_name'] = self.request.GET.get('status', 'all')
        return context


class TempleDetailView(DetailView):
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
    model = Clergy
    template_name = 'clergy/clergy_list.html'
    context_object_name = 'clergy_list'

    # def get_queryset(self):
    #     return (
    #         Clergy.objects
    #         .only('id', 'first_name', 'last_name', 'post', 'order', 'small_image')  # добавьте то, что реально нужно в списке
    #         .order_by('order', 'id')
    #     )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Духовенство'
        return context


class ClergyDetailView(DetailView):
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
                    ).order_by('order',),
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
    model = Deal
    template_name = 'deal/deal.html'
    context_object_name = 'deal_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Деятельность'
        return context


class DealDetailView(DetailView):
    model = Deal
    template_name = 'deal/deal_detail.html'
    context_object_name = 'deal'


class SecretView(ListView):
    model = Secret
    template_name = 'secret/secret.html'
    context_object_name = 'secret_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Тайна'
        return context


class SecretDetailView(DetailView):
    model = Secret
    template_name = 'secret/secret_detail.html'
    context_object_name = 'secret'


class GodServesView(ListView):
    model = GodServes
    template_name = 'god_serves/god_serves.html'
    context_object_name = 'godserves_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Богослужения'
        return context


class ContactView(ListView):
    model = Contact
    template_name = 'contact/contact.html'
    context_object_name = 'contact_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Контакты'
        return context
