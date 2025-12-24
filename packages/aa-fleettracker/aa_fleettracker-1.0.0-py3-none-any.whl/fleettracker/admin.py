from django.contrib import admin
from .models import FleetSnapshot, FleetMemberSnapshot

@admin.register(FleetSnapshot)
class FleetSnapshotAdmin(admin.ModelAdmin):
    list_display = ("created_at", "label", "fleet_id", "member_count", "commander_name")
    list_filter = ("created_at",)
    search_fields = ("label", "fleet_id", "commander_name")

@admin.register(FleetMemberSnapshot)
class FleetMemberSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "fleet_snapshot",
        "character_name",
        "corporation_name",
        "ship_type_name",
        "role",
        "solar_system_id",
    )
    list_filter = ("corporation_id", "ship_type_id", "role")
    search_fields = ("character_name", "corporation_name", "ship_type_name")
