# analysis/admin.py

from django.contrib import admin
from .models import YearlyRecord, MonthlyRecord


@admin.register(YearlyRecord)
class YearlyRecordAdmin(admin.ModelAdmin):
    list_display  = ("year", "clinic", "births", "deaths", "proportion_deaths")
    list_filter   = ("clinic",)
    ordering      = ("clinic", "year")


@admin.register(MonthlyRecord)
class MonthlyRecordAdmin(admin.ModelAdmin):
    list_display  = ("date", "births", "deaths", "proportion_deaths", "after_handwashing")
    ordering      = ("date",)