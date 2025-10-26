from django.urls import path
from . import views

app_name = 'temple'

urlpatterns = [
    path('', views.HomePage.as_view(), name='homepage'),
    path('news/', views.NewsListView.as_view(), name='news'),
    path('news/<int:pk>/', views.NewsDetailView.as_view(), name='news_detail'),
    path('duhovenstvo/', views.ClergyListView.as_view(), name='clergy'),
    path(
        'duhovenstvo/<int:pk>/',
        views.ClergyDetailView.as_view(),
        name='clergy_detail',
    ),
    path('temple/', views.TempleListView.as_view(), name='temple'),
    path(
        'temple/<int:pk>/',
        views.TempleDetailView.as_view(),
        name='temple_detail',
    ),
    path('deal/', views.DealView.as_view(), name='deal'),
    path('deal/<int:pk>/', views.DealDetailView.as_view(), name='deal_detail'),
    path('secret/', views.SecretView.as_view(), name='secret'),
    path('secret/<int:pk>/', views.SecretDetailView.as_view(), name='secret_detail'),
    path('godserves/', views.GodServesView.as_view(), name='godserves'),
    path('contact/', views.ContactView.as_view(), name='contact'),
]
