from django.contrib import admin
from django.db.models.functions import Length

from .models import Entry


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "value", "value_length", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("value", "category")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(value_length=Length("value"))

    def value_length(self, obj):
        return obj.value_length

    value_length.admin_order_field = "value_length"
    value_length.short_description = "Value length"
