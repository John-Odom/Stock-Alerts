from django.contrib import admin
from .models import Article
# from django_celery_beat.models import PeriodicTask, IntervalSchedule

admin.site.register(Article)# admin.py
# admin.site.register(IntervalSchedule)
# admin.site.register(PeriodicTask)