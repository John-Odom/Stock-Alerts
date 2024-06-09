from django.urls import path
# from django.urls import 
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings

app_name = 'articles'

urlpatterns = [
    path('articles/', views.article_list, name='article_list'),  # This would be your article list view
    path('articles/create', views.article_create, name='create'),
    path('articles/<slug:slug>/', views.article_detail, name='detail'),  # Nested slug pattern under articles/
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)