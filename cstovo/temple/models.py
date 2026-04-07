import os

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.db.models.functions import Lower
from django_ckeditor_5.fields import CKEditor5Field

from .serves import compress_image


class Clergy(models.Model):
    """Модель священнослужителей"""

    CLERGY_RANK = (
        ('deacon', 'Дьякон'),
        ('priest', 'Иерей'),
        ('archpriest', 'Протоиерей'),
        ('bishop', 'Епископ'),
    )
    CLERGY_RANK_DICT = dict(CLERGY_RANK)
    runk = models.CharField(
        max_length=255,
        choices=CLERGY_RANK,
        default='deacon',
        verbose_name='Сан',
    )
    first_name = models.CharField(
        max_length=255, default='Имя', verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=255, default='Фамилия', verbose_name='Фамилия'
    )
    post = models.TextField(
        null=True, blank=True, verbose_name='Епархиальные послушания'
    )
    image = models.ImageField(
        upload_to='clergy_images',
        null=True,
        blank=True,
        verbose_name='Изображение',
    )
    small_image = models.ImageField(
        upload_to='clergy_samll_images',
        null=True,
        blank=True,
        verbose_name='Маленькое изображение',
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок',
    )

    class Meta:
        verbose_name = 'Духовенство'
        verbose_name_plural = 'Духовенство'

    @property
    def rank_display(self):
        return self.CLERGY_RANK_DICT.get(self.runk, self.runk)

    def __str__(self):
        return f'{self.rank_display} {self.first_name} {self.last_name}'

    def get_absolute_url(self):
        return reverse('temple:clergy_detail', args=[str(self.id)])

    def save(self, *args, **kwargs):
        image_changed = False
        if self.pk:
            old = type(self).objects.filter(pk=self.pk).only('image').first()
            if old and old.image != self.image:
                image_changed = True
        else:
            image_changed = bool(self.image)
        super().save(*args, **kwargs)
        if self.image and (image_changed or not self.small_image):
            base_name = os.path.splitext(os.path.basename(self.image.name))[0]
            thumb_name = f'clergy_images/small/small_{base_name}.jpg'
            thumb_content = compress_image(self.image)
            self.small_image.save(thumb_name, thumb_content, save=False)
            type(self).objects.filter(pk=self.pk).update(
                small_image=self.small_image.name
            )
     

class Deal(models.Model):
    """Модель направлений деятельности"""

    stream = models.CharField(
        max_length=255, verbose_name='Направление деятельнсти'
    )
    short_stream = models.CharField(
        max_length=255,
        default='Деятельность',
        verbose_name='Краткое названиенаправление деятельнсти',
    )
    image = models.ImageField(
        upload_to='deal_images',
        null=True,
        blank=True,
        verbose_name='Изображение',
    )
    description = CKEditor5Field(verbose_name='Описание', config_name='default')
    curator = models.ForeignKey(
        Clergy,
        on_delete=models.CASCADE,
        related_name='deals',
        verbose_name='Куратор из духовенства',
        null=True,
        blank=True,
    )
    curator_2 = models.ForeignKey(
        Clergy,
        on_delete=models.CASCADE,
        related_name='deals_2',
        verbose_name='Куратор из духовенства 2',
        null=True,
        blank=True,
    )
    sv_curator_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Фамилия и Имя светского куратора',
    )
    sv_curator_post = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Должность светского куратора',
    )
    sv_curator_image = models.ImageField(
        upload_to='curator_images',
        null=True,
        blank=True,
        verbose_name='Изображение светского куратора',
    )
    sv_curator_url = models.URLField(
        max_length=255,
        verbose_name='Ссылка на сайт или страницу светского куратора',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Деятельность'
        verbose_name_plural = 'Деятельность'

    def __str__(self):
        return self.stream


class Temple(models.Model):
    """Модель храмов"""

    STATUS_TEMPLE = (
        ('active', 'Действующие'),
        ('restoring', 'Восстанавливающиеся'),
        ('under_construction', 'Строящиеся'),
        ('destroyed', 'Разрушенные'),
    )

    name = models.CharField(max_length=255, verbose_name='Название храма')
    description = CKEditor5Field(verbose_name='История', null=True, blank=True, config_name='default')
    image = models.ImageField(
        upload_to='temple_images',
        null=True,
        blank=True,
        verbose_name='Изображение храма',
    )
    small_image = models.ImageField(
        upload_to='temple_images',
        null=True,
        blank=True,
        verbose_name='Маленькое изображение храма',
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    schedule = models.TextField(
        null=True, blank=True, verbose_name='Расписание'
    )
    location = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Адрес'
    )
    phone = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Телефон'
    )
    map = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='Код карты из конструктора карт',
    )
    clergy = models.ManyToManyField(
        Clergy,
        through='TempleClergy',
        related_name='temple',
        verbose_name='Свещенослужители',
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_TEMPLE,
        default='active',
        verbose_name='Статус',
    )
    shcool = models.ForeignKey(
        Deal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='temple',
        verbose_name='Воскресная школа',
    )

    class Meta:
        ordering = (Lower('name'),)
        verbose_name = 'Храм'
        verbose_name_plural = 'Храмы'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('temple:temple_detail', args=[str(self.id)])

    def save(self, *args, **kwargs):
        image_changed = False
        if self.pk:
            old = type(self).objects.filter(pk=self.pk).only('image').first()
            if old and old.image != self.image:
                image_changed = True
        else:
            image_changed = bool(self.image)
    #     status_rank = {
    #         'active': 1,
    #         'restoring': 2,
    #         'under_construction': 3,
    #         'destroyed': 4,
    #     }
    #     self.order = status_rank.get(self.status, 5)
        super().save(*args, **kwargs)

        if self.image and (image_changed or not self.small_image):
            base_name = os.path.splitext(os.path.basename(self.image.name))[0]
            thumb_name = f'clergy_images/small/small_{base_name}.jpg'
            thumb_content = compress_image(self.image)
            self.small_image.save(thumb_name, thumb_content, save=False)
            type(self).objects.filter(pk=self.pk).update(
                small_image=self.small_image.name
            )


class TempleClergy(models.Model):
    """Модель связи храма и священнослужителя"""

    temple = models.ForeignKey(
        Temple, on_delete=models.CASCADE, related_name='temple_clergy'
    )
    clergy = models.ForeignKey(
        Clergy,
        on_delete=models.CASCADE,
        verbose_name='Священнослужитель',
        related_name='clergy_temple',
    )
    post = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Должность'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')


class Secret(models.Model):
    """Модель таинств"""

    name = models.CharField(max_length=255, verbose_name='Название таинства')
    full_name = models.CharField(
        max_length=255, verbose_name='Полное название таинства'
    )
    description = CKEditor5Field(verbose_name='Описание', config_name='default')
    image = models.ImageField(
        upload_to='secret_images',
        null=True,
        blank=True,
        verbose_name='Изображение таинства',
    )

    class Meta:
        verbose_name = 'Таинство'
        verbose_name_plural = 'Таинства'

    def __str__(self):
        return self.name


class GodServes(models.Model):
    """Модель богослужения"""

    name = models.CharField(
        max_length=255, verbose_name='Название богослужения'
    )
    image = models.ImageField(
        upload_to='god_serves_images',
        null=True,
        blank=True,
        verbose_name='Изображение расписания богослужения',
    )

    class Meta:
        verbose_name = 'Богослужение'
        verbose_name_plural = 'Богослужения'

    def __str__(self):
        return self.name


class Contact(models.Model):
    """Модель контактов"""

    name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Имя')
    phone = models.CharField(max_length=50, null=True, blank=True, verbose_name='Телефон')
    email = models.EmailField(null=True, blank=True, verbose_name='Email')
    message = models.TextField(null=True, blank=True, verbose_name='Описание')
    location = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='Код карты из конструктора карт',
    )

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'

    def __str__(self):
        return str(self.pk)


class News(models.Model):
    """Модель новостей"""

    title = models.CharField(max_length=255, verbose_name='Заголовок')
    description = CKEditor5Field(verbose_name='Описание', config_name='default')
    image = models.ImageField(
        upload_to='news_images',
        null=True,
        blank=True,
        verbose_name='Обложка (изображение)',
    )
    small_image = models.ImageField(
        upload_to='news_images/small',
        null=True,
        blank=True,
        verbose_name='Обложка (изображение)',
    )
    date = models.DateTimeField(verbose_name='Дата публикации')
    stream = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='news',
        verbose_name='Направление деятельности',
    )
    on_main = models.BooleanField(
        default=False, verbose_name='Главная новость'
    )

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-date']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('temple:news_detail', args=[str(self.id)])

    def save(self, *args, **kwargs):
        image_changed = False
        if self.pk:
            old = type(self).objects.filter(pk=self.pk).only('image').first()
            if old and old.image != self.image:
                image_changed = True
        else:
            image_changed = bool(self.image)
        super().save(*args, **kwargs)

        if self.image and (image_changed or not self.small_image):
            base_name = os.path.splitext(os.path.basename(self.image.name))[0]
            thumb_name = f'clergy_images/small/small_{base_name}.jpg'
            thumb_content = compress_image(self.image)
            self.small_image.save(thumb_name, thumb_content, save=False)
            type(self).objects.filter(pk=self.pk).update(
                small_image=self.small_image.name
            )


class NewsImage(models.Model):
    """Модель дополнительных изображений новостей"""

    news = models.ForeignKey(
        News, on_delete=models.CASCADE, related_name='images'
    )
    image = models.ImageField(
        upload_to='news_images',
    )

    class Meta:
        verbose_name = 'Изображение новости'
        verbose_name_plural = 'Изображения новостей'

    def __str__(self):
        return f'Изображение для новости {self.news.title}'


class BaseImage(models.Model):
    """Модель базовых изображений"""

    TYPE_IMAGE = (
        ('main', 'Главное изображение'),
        ('logo', 'Логотип'),
        ('base_temple', 'Базовое изображение храма'),
        ('base_clergy', 'Базовое изображение духовенства'),
    )

    def upload_to(instance, filename):
        ext = filename.split('.')[-1]
        return f'base_images/{instance.name}.{ext}'

    name = models.CharField(max_length=50, choices=TYPE_IMAGE, unique=True, verbose_name='Тип изображения')
    image = models.ImageField(upload_to=upload_to, verbose_name='Изображение')

    class Meta:
        verbose_name = 'Базовое изображение'
        verbose_name_plural = 'Базовые изображения'
