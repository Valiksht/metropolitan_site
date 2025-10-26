from django.db import models


class Deal(models.Model):
    stream = models.CharField(
        max_length=255, verbose_name='Направление деятельнсти'
    )
    image = models.ImageField(
        upload_to='deal_images',
        null=True,
        blank=True,
        verbose_name='Изображение',
    )
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Деятольеность'
        verbose_name_plural = 'Деятельность'

    def __str__(self):
        return self.stream


class Clergy(models.Model):
    name = models.CharField(max_length=255, verbose_name='ФИО')
    post = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Епархиальные послушания',
    )
    description = models.TextField(
        null=True, blank=True, verbose_name='Места служения'
    )
    image = models.ImageField(
        upload_to='clergy_images',
        null=True,
        blank=True,
        verbose_name='Изображение',
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Духовенство'
        verbose_name_plural = 'Духовенство'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse('temple:duhovenstvo_detail', args=[str(self.id)])


class Temple(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название храма')
    description = models.TextField(verbose_name='История')
    image = models.ImageField(
        upload_to='temple_images',
        null=True,
        blank=True,
        verbose_name='Изображение храма',
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
    clergy = models.ManyToManyField(
        Clergy,
        through='TempleClergy',
        related_name='temple',
        verbose_name='Свещенослужители',
    )
    # Добавить инфу кто кто он в этом храме
    shcool = models.ForeignKey(
        Deal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='temple',
        verbose_name='Воскресная школа',
    )

    class Meta:
        verbose_name = 'Храм'
        verbose_name_plural = 'Храмы'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse('temple:temple_detail', args=[str(self.id)])


class TempleClergy(models.Model):
    temple = models.ForeignKey(
        Temple, on_delete=models.CASCADE, related_name='temple_clergy'
    )
    clergy = models.ForeignKey(Clergy, on_delete=models.CASCADE)
    post = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Должность'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')


class Secret(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название таинства')
    full_name = models.CharField(
        max_length=255, verbose_name='Полное название таинства'
    )
    description = models.TextField(verbose_name='Описание таинства')
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
    name = models.CharField(max_length=255, verbose_name='Имя')
    phone = models.CharField(max_length=50, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')
    message = models.TextField(null=True, verbose_name='Описание')
    location = models.TextField(
        max_length=255, null=True, blank=True, verbose_name='Код карты из конструктора карт'
    )

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'

    def __str__(self):
        return self.name


class News(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    image = models.ImageField(
        upload_to='news_images',
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
        from django.urls import reverse

        return reverse('temple:news_detail', args=[str(self.id)])


class NewsImage(models.Model):
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
    TYPE_IMAGE = (
        ('main', 'Главное изображение'),
        ('logo', 'Логотип'),
        ('base_temple', 'Базовое изображение храма'),
        ('base_clergy', 'Базовое изображение духовенства'),
    )

    def upload_to(instance, filename):
        ext = filename.split('.')[-1]
        return f'base_images/{instance.name}.{ext}'

    name = models.CharField(max_length=50, choices=TYPE_IMAGE, unique=True)
    image = models.ImageField(upload_to=upload_to)

    class Meta:
        verbose_name = 'Базовое изображение'
        verbose_name_plural = 'Базовые изображения'
