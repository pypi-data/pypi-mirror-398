from django.db import models
from django.utils import timezone
from django.conf import settings

class FleetSnapshot(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    label = models.CharField(max_length=120, blank=True, default="")

    commander_character_id = models.BigIntegerField(db_index=True)
    commander_name = models.CharField(max_length=128, blank=True, default="")

    fleet_id = models.BigIntegerField(db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)

    member_count = models.IntegerField(default=0)

    class Meta:
        default_permissions = ()
        ordering = ["-created_at"]
        

    def __str__(self):
        return f"Fleet {self.fleet_id} @ {self.created_at:%Y-%m-%d %H:%M}"


class FleetMemberSnapshot(models.Model):
    fleet_snapshot = models.ForeignKey(
        FleetSnapshot, on_delete=models.CASCADE, related_name="members"
    )

    character_id = models.BigIntegerField(db_index=True)
    character_name = models.CharField(max_length=128, blank=True, default="")
    corporation_id = models.BigIntegerField(db_index=True)
    corporation_name = models.CharField(max_length=128, blank=True, default="")
    alliance_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    ship_type_id = models.IntegerField(null=True, blank=True, db_index=True)
    ship_type_name = models.CharField(max_length=128, blank=True, default="")
    solar_system_id = models.CharField(max_length=128, blank=True, default="")
    role = models.CharField(max_length=64, blank=True, default="")
    role_name = models.CharField(max_length=64, blank=True, default="")

    join_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["fleet_snapshot", "corporation_id"]),
            models.Index(fields=["fleet_snapshot", "ship_type_id"]),
        ]
        default_permissions = ()


class FleetTrackerUserSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.ForeignKey("esi.Token", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"FleetTrackerUserSettings({self.user_id})"
    class Meta:
        default_permissions = ()

class General(models.Model):
    """Meta model for app permissions"""

    class Meta:
        """Meta definitions"""

        managed = False
        default_permissions = ()
        permissions = [
            ("access_fleettracker", "Can access Fleet Tracker"),
            ("take_snapshot", "Can take fleet snapshots"),
        ]
