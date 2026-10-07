# Aleksandar Pavlovic 0093/2022

from django.contrib import admin
from .models import Med

@admin.register(Med)
class MedAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user", #user_id
        "name",
        "surname",
        "level_spec",
        "is_verified",
    )
    list_editable = ("level_spec", "is_verified")

