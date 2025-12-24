from django.urls import path
from . import views

app_name = "fleettracker"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("snapshot/", views.snapshot_now, name="snapshot_now"),
    path("fleet/<int:snapshot_id>/", views.fleet_detail, name="fleet_detail"),
    path("connect/", views.connect_fc_token, name="connect_fc_token"),

]
