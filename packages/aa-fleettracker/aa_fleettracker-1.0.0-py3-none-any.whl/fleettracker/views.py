from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from esi.models import Token
from esi.decorators import token_required

from .forms import TakeSnapshotForm
from .models import FleetSnapshot, FleetMemberSnapshot, FleetTrackerUserSettings
from .services import take_fleet_snapshot

SCOPE_FLEET_READ = "esi-fleets.read_fleet.v1"

def _get_main_character_id(request) -> int:
    # AA standard: request.user.profile.main_character
    mc = getattr(getattr(request.user, "profile", None), "main_character", None)
    if not mc:
        raise RuntimeError("Main character missing on user profile.")
    return mc.character_id

def _get_token_for_character(character_id: int) -> Token:
    # take any token that has the required scope
    token = Token.objects.filter(character_id=character_id, scopes__name=SCOPE_FLEET_READ).first()
    if not token:
        raise RuntimeError(f"No ESI token with scope: {SCOPE_FLEET_READ}")
    return token

@login_required
@permission_required("fleettracker.take_snapshot", raise_exception=True)
@token_required(scopes=SCOPE_FLEET_READ, new=True)
def connect_fc_token(request, token):
    FleetTrackerUserSettings.objects.update_or_create(
        user=request.user, defaults={"token": token}
    )
    messages.success(request, f"FC token connected for: {getattr(token, 'character_name', token.character_id)}")
    return redirect("fleettracker:dashboard")

@login_required
@permission_required("fleettracker.access_fleettracker", raise_exception=True)
def dashboard(request):
    form = TakeSnapshotForm()
    snaps = list(FleetSnapshot.objects.all()[:10])

    # aggregate per snapshot for the corporation breakdown
    for s in snaps:
        s.corp_rows = (
            FleetMemberSnapshot.objects
            .filter(fleet_snapshot=s)
            .values("corporation_id", "corporation_name")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")
        )

    return render(request, "fleettracker/dashboard.html", {"snaps": snaps, "form": form})

@login_required
@permission_required("fleettracker.take_snapshot", raise_exception=True)
@require_POST
def snapshot_now(request):
    label = (request.POST.get("label") or "").strip()

    settings_obj, _ = FleetTrackerUserSettings.objects.get_or_create(user=request.user)
    if not settings_obj.token:
        messages.warning(request, "Connect FC token first (LOG IN with EVE Online).")
        return redirect("fleettracker:connect_fc_token")

    token = settings_obj.token

    try:
        snap = take_fleet_snapshot(
            token=token,
            commander_character_id=token.character_id,
            commander_name=getattr(token, "character_name", "") or "",
            label=label,
        )
        messages.success(request, f"Snapshot saved: {snap.member_count} members.")
    except Exception as e:
        messages.error(request, f"Failed to take snapshot: {e}")

    return redirect("fleettracker:dashboard")


def fleet_detail(request, snapshot_id: int):
    snap = get_object_or_404(FleetSnapshot, pk=snapshot_id)

    # GET param: corp
    corp_param = (request.GET.get("corp") or "").strip()
    selected_corp_id = None
    try:
        if corp_param:
            selected_corp_id = int(corp_param)
    except ValueError:
        selected_corp_id = None

    base_qs = FleetMemberSnapshot.objects.filter(fleet_snapshot=snap)

    # list of corporations for the dropdown (always from the entire fleet)
    corp_options = (
        base_qs.values("corporation_id", "corporation_name")
        .annotate(cnt=Count("id"))
        .order_by("corporation_name")
    )

    # filtered queryset (members plus ship stats)
    filtered_qs = base_qs
    if selected_corp_id:
        filtered_qs = filtered_qs.filter(corporation_id=selected_corp_id)

    # stats "By Corporation" — here you have two choices:
    # A) always show the full fleet breakdown (regardless of the filter)
    corp_rows = (
        base_qs.values("corporation_id", "corporation_name")
        .annotate(cnt=Count("id"))
        .order_by("-cnt")
    )

    ship_rows = (
        filtered_qs.values("ship_type_id", "ship_type_name")
        .annotate(cnt=Count("id"))
        .order_by("-cnt")
    )

    members = filtered_qs.order_by("corporation_name", "character_name")

    # number of members in the current view (after applying the filter)
    filtered_count = filtered_qs.count()

    return render(
        request,
        "fleettracker/fleet_detail.html",
        {
            "snap": snap,
            "corp_rows": corp_rows,
            "ship_rows": ship_rows,
            "members": members,
            "corp_options": corp_options,
            "selected_corp_id": selected_corp_id,
            "filtered_count": filtered_count,
        },
    )
