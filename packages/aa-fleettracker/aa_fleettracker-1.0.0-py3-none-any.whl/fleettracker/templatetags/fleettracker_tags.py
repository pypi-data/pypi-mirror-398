from django import template

register = template.Library()

@register.simple_tag
def corp_logo_url(corporation_id: int, size: int = 32) -> str:
    return f"https://images.evetech.net/corporations/{corporation_id}/logo?size={size}"
