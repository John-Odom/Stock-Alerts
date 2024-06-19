from django.urls import path
# from django.urls import 
from . import views

app_name = 'stocks'

urlpatterns = [
    path('', views.stock_index_view, name="stock_index"),
    path('<slug:slug>/', views.stock_detail, name='stock_detail'),  # Nested slug pattern under articles/
]