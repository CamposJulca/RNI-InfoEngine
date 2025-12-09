import re
from django import template

register = template.Library()

@register.filter
def regex_match(value, pattern):
    """
    Retorna True si el texto hace match con el patrón regex.
    """
    if value is None:
        return False
    return re.match(pattern, str(value)) is not None
