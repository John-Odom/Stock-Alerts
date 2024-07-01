from django.urls import path
# from django.urls import 
from . import views

app_name = 'stocks'

urlpatterns = [
    path('', views.stock_index_view, name="stock_index"),
    path('alerts/', views.alerts, name='alerts'),
    path('delete_alert/<int:id>/', views.delete_alert, name='delete_alert'),
    path('<slug:slug>/', views.stock_detail, name='stock_detail'),  # Nested slug pattern under articles/
]