from django.contrib import admin
from django.utils.html import format_html, mark_safe

from .models import (
    Temple,
    Clergy,
    TempleClergy,
    Deal,
    Secret,
    GodServes,
    Contact,
    News,
    NewsImage,
    BaseImage,
)


class TempleClergyInline(admin.TabularInline):
    model = TempleClergy
    extra = 1
    verbose_name = "Священнослужитель"
    verbose_name_plural = "Священнослужители"


@admin.register(Clergy)
class ClergyAdmin(admin.ModelAdmin):
    readonly_fields = ['image_preview']
    list_display = (
        'custom_fio',
        'get_temples_list',
    )
    list_filter = ('runk',)
    fields = (
        'runk',
        'first_name',
        'last_name',
        'post',
        'image',
        'image_preview',
        'order',
    )
    exclude = ('small_image',)

    def custom_fio(self, obj):
        runk_display = obj.get_runk_display()
        return f'{runk_display} {obj.first_name} {obj.last_name}'

    custom_fio.short_description = 'ФИО'

    def get_temples_list(self, obj):
        # Формируем список храмов
        return format_html(
            ',<br> '.join(
                f'<a href="/admin/temple/temple/{temple.id}/change/">{temple.name}</a>'
                for temple in obj.temple.all()
            )
        )

    get_temples_list.short_description = 'Храмы'

    def get_ordering(self, request):
        return ['last_name', 'first_name']

    def get_form(self, request, obj=..., change=..., **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.base_fields['order'].help_text = (
            'Заполнить если нужно вывести свещенослужителя выше в списке. '
            'Чем больше число, тем выше в списке.',
        )
        return form

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="max-height: 200px; max-width: 200px;">'
            )
        return "Загрузите изображение"

    image_preview.short_description = 'Превью изображения'


@admin.register(Temple)
class TempleAdmin(admin.ModelAdmin):
    readonly_fields = ['image_preview']
    fields = (
        'name',
        'status',
        'description',
        'image',
        'image_preview',
        'schedule',
        'location',
        'phone',
        'map',
        'order',
        'shcool',
    )
    list_display = ('name', 'order')
    list_editable = ('order',)
    list_filter = ('status',)
    search_fields = ('name',)
    inlines = (TempleClergyInline,)

    def get_people_list(self, obj):
        # Формируем список служителей
        return format_html(
            ',<br> '.join(
                f'<a href="/admin/temple/clergy/{person.id}/change/">{person.first_name} {person.last_name}</a>'
                for person in obj.clergy.all()
            )
        )

    get_people_list.short_description = 'Священнослужители'

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="max-height: 200px; max-width: 200px;">'
            )
        return "Загрузите изображение"

    image_preview.short_description = 'Превью изображения'


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('stream',)
    list_filter = ('stream',)


@admin.register(Secret)
class SecretAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)


@admin.register(GodServes)
class GodServesAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message')
    list_filter = ('name',)


class NewsImageInLine(admin.TabularInline):
    model = NewsImage
    extra = 1
    fields = ('image',)


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    readonly_fields = ['image_preview']
    list_display = (
        'title',
        'on_main',
    )
    list_filter = ('title', 'on_main')
    list_editable = ('on_main',)
    fields = (
        'title',
        'date',
        'description',
        'image',
        'image_preview',
        'stream',
        'on_main',
    )
    inlines = (NewsImageInLine,)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="max-height: 200px; max-width: 200px;">'
            )
        return "Загрузите изображение"

    image_preview.short_description = 'Превью изображения'


@admin.register(BaseImage)
class BaseImageAdmin(admin.ModelAdmin):
    readonly_fields = ['image_preview']
    list_display = ('name', 'image')
    list_filter = ('name',)
    fields = ('name', 'image', 'image_preview')

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="max-height: 200px; max-width: 200px;">'
            )
        return "Загрузите изображение"

    image_preview.short_description = 'Превью изображения'
