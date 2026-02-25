from django.contrib import admin, messages
from django.urls import path, reverse
from django.utils.html import format_html
from django import forms
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from .models import BackupLog
from .services import download_backup, restore_backup

class BackupUploadForm(forms.Form):
    # 'file' должно соответствовать name='file' в вашем HTML <input type="file">
    file = forms.FileField(label="Выберите файл бэкапа") 

@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'last_export_at',
    )
    readonly_fields = (
        'name',
        'slug',
        'last_export_at',
        'run_now_button',
    )
    fields = (
        'name',
        'last_export_at',
        'run_now_button',
    )

    # Кнопки в форме изменения объекта
    def run_now_button(self, obj):
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        download_url = reverse(f'admin:{app_label}_{model_name}_download', args=[obj.slug])
        upload_url = reverse(f'admin:{app_label}_{model_name}_upload', args=[obj.slug])
        return format_html(
            '<a class="button" href="{}" style="margin-right:8px">Скачать</a>'
            '<a class="button" href="{}">Загрузить</a>',
            download_url, upload_url
        )
    run_now_button.short_description = 'Резервные копии'
    # Кнопки в списке (дополнительно, удобно)
    def run_now_button_list(self, obj):
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        download_url = reverse(f'admin:{app_label}_{model_name}_download', args=[obj.slug])
        upload_url = reverse(f'admin:{app_label}_{model_name}_upload', args=[obj.slug])
        return format_html(
            '<a class="button" href="{}" style="margin-right:8px">Скачать</a>'
            '<a class="button" href="{}">Загрузить</a>',
            download_url, upload_url
        )
    run_now_button_list.short_description = 'Действия'
    run_now_button_list.allow_tags = True
    # Собственные URL-ы админки
    def get_urls(self):
        urls = super().get_urls()
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        custom = [
            path('<slug:slug>/download/', self.admin_site.admin_view(self.download_view),
                 name=f'{app_label}_{model_name}_download'),
            path('<slug:slug>/upload/', self.admin_site.admin_view(self.upload_view),
                 name=f'{app_label}_{model_name}_upload'),
        ]
        return custom + urls
    # Вью «Скачать»: передаём slug в services.download_backup(slug)
    def download_view(self, request, slug):
        if not request.user.is_superuser:
            return HttpResponseForbidden('Недостаточно прав.')
        try:
            # Ожидается, что download_backup(slug) вернёт HttpResponse с файлом (Streaming/FileResponse)
            return download_backup(slug)
        except Exception as e:
            messages.error(request, f'Ошибка скачивания бэкапа: {e}')
            # назад к списку
            cl = reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')
            return redirect(cl)
    # Вью «Загрузить»: GET — форма, POST — передаём slug и файл в services.restore_backup(slug, file)
    def upload_view(self, request, slug):
        if not request.user.is_superuser:
            return HttpResponseForbidden('Недостаточно прав.')
        if request.method == 'POST' and request.FILES.get('file'):
            up = request.FILES['file']
            try:
                # Реализуйте в services.restore_backup(slug, uploaded_file)
                restore_backup(slug, up)
                messages.success(request, 'Импорт/восстановление выполнено.')
            except Exception as e:
                messages.error(request, f'Ошибка импорта/восстановления: {e}')
            cl = reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')
            return redirect(cl)
        else:
            form = BackupUploadForm()
        context = dict(
            self.admin_site.each_context(request),
            opts=self.model._meta,
            object_slug=slug,
            title='Загрузка архива для восстановления',
            form=form,
        )
        # Простейшая форма без отдельного шаблона — рендерим inline
        return render(request, 'admin/backup_upload.html', context)
