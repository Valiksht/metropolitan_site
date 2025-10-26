from django.contrib import admin
from django.utils.html import format_html

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

class ClergyAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
        'get_temples_list',
    )
    list_filter = ('name',)

    def get_temples_list(self, obj):
        # Формируем список храмов
        return format_html(
            ',<br> '.join(f'<a href="/admin/temple/temple/{temple.id}/change/">{temple.name}</a>' 
                          for temple in obj.temple.all())
        )
    get_temples_list.short_description = 'Храмы'


class TempleAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_people_list')
    list_filter = ('name',)
    inlines = (TempleClergyInline,)

    def get_people_list(self, obj):
        # Формируем список служителей
        return format_html(
            ',<br> '.join(f'<a href="/admin/temple/clergy/{person.id}/change/">{person.name}</a>' 
                          for person in obj.clergy.all())
        )
    get_people_list.short_description = 'Священнослужители'


class DealAdmin(admin.ModelAdmin):
    list_display = ('stream',)
    list_filter = ('stream',)


class SecretAdmin(admin.ModelAdmin):
    list_display = ('name', )
    list_filter = ('name',)


class GodServesAdmin(admin.ModelAdmin):
    list_display = ('name', )
    list_filter = ('name',)


class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message')
    list_filter = ('name',)

class NewsImageInLine(admin.TabularInline):
    model = NewsImage
    extra = 1
    fields = ('image',)


class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'on_main',)
    list_filter = ('title', 'on_main')
    list_editable = ('on_main',)
    inlines = (NewsImageInLine,)


class BaseImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'image')
    list_filter = ('name',)


admin.site.register(Temple, TempleAdmin)
admin.site.register(Clergy, ClergyAdmin)
admin.site.register(Deal, DealAdmin)
admin.site.register(Secret, SecretAdmin)
admin.site.register(GodServes, GodServesAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(News, NewsAdmin)
admin.site.register(BaseImage, BaseImageAdmin)
