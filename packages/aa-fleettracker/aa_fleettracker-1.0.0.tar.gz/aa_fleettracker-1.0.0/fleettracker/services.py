import logging
from django.db import transaction
from django.utils import timezone

from esi.clients import EsiClientProvider
from eveuniverse.models import  EveEntity, EveType

from .models import FleetSnapshot, FleetMemberSnapshot

logger = logging.getLogger(__name__)
esi = EsiClientProvider()

def _get_character_public_info(character_id: int) -> dict:
    # public endpoint, no token needed
    return esi.client.Character.get_characters_character_id(
        character_id=character_id
    ).results()


def _get_corp_ticker(corporation_id: int) -> str:
    try:
        data = esi.client.Corporation.get_corporations_corporation_id(
            corporation_id=corporation_id
        ).results()
        return (data.get("ticker") or "").strip()
    except Exception:
        logger.exception("Failed to fetch corp ticker", extra={"corporation_id": corporation_id})
        return ""



def _resolve_entity_name(entity_id: int) -> str:
    try:
        obj, _ = EveEntity.objects.get_or_create_esi(id=entity_id)
        return obj.name or ""
    except Exception:
        return ""

def _resolve_ship_name(type_id: int) -> str:
    try:
        obj, _ = EveType.objects.get_or_create_esi(id=type_id)
        return obj.name or ""
    except Exception:
        return ""

def take_fleet_snapshot(*, token, commander_character_id: int, commander_name: str = "", label: str = "") -> FleetSnapshot:
    """
    token: django-esi Token (or compatible) that can provide an access token.
    commander_character_id: ID of the FC character taking the snapshot
    """
    # 1) fleet id of the character
    fleet_info = esi.client.Fleets.get_characters_character_id_fleet(
        character_id=commander_character_id,
        token=token.valid_access_token(),
    ).results()

    fleet_id = fleet_info.get("fleet_id")
    if not fleet_id:
        raise RuntimeError("Ta postać nie jest w flocie (ESI nie zwróciło fleet_id).")

    # 2) fleet members
    members = esi.client.Fleets.get_fleets_fleet_id_members(
        fleet_id=fleet_id,
        token=token.valid_access_token(),
    ).results()

    commander_name = _resolve_entity_name(commander_character_id)

    with transaction.atomic():
        snap = FleetSnapshot.objects.create(
            fleet_id=fleet_id,
            commander_character_id=commander_character_id,
            commander_name=commander_name,
            label=label or "",
            created_at=timezone.now(),
            member_count=len(members),
        )

        objs = []
        for m in members:
            char_id = m.get("character_id")
            sys_id = m.get("solar_system_id")
            if not char_id:
                logger.warning("Fleet member without character_id", extra={"member": m, "fleet_id": fleet_id})
                continue

            try:
                char_info = esi.client.Character.get_characters_character_id(
                    character_id=char_id
                ).results()
            except Exception:
                logger.exception("Failed to fetch character info", extra={"character_id": char_id})
                continue

            corp_id = char_info.get("corporation_id")
            alliance_id = char_info.get("alliance_id")
            ticker = _get_corp_ticker(corp_id)
            corp_display = ticker or _resolve_entity_name(corp_id) or str(corp_id)


            if not corp_id:
                logger.warning("Character without corporation_id", extra={"character_id": char_id, "char_info": char_info})
                continue


            objs.append(
                FleetMemberSnapshot(
                    fleet_snapshot=snap,
                    character_id=char_id,
                    character_name=char_info.get("name", "") or _resolve_entity_name(char_id),
                    corporation_id=corp_id,
                    corporation_name=corp_display,
                    alliance_id=alliance_id,
                    ship_type_id=m.get("ship_type_id"),
                    ship_type_name=_resolve_ship_name(m.get("ship_type_id")) if m.get("ship_type_id") else "",
                    solar_system_id=_resolve_entity_name(sys_id),
                    role=m.get("role", "") or "",
                    role_name=m.get("role_name", "") or "",
                    join_time=m.get("join_time"),
                )
            )


        FleetMemberSnapshot.objects.bulk_create(objs, batch_size=1000)

    return snap
