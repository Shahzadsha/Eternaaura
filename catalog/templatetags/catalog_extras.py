from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def split(value, delimiter=","):
    return [v.strip() for v in value.split(delimiter)]


@register.filter
def render_stars(value):
    """
    Accurately renders 1 to 5 star ratings with gold filled stars (★)
    and muted un-filled stars for remaining points.
    """
    try:
        rating = float(value or 0)
    except (TypeError, ValueError):
        rating = 0.0
    rating = max(0.0, min(5.0, rating))
    full_stars = int(round(rating))

    stars_html = ""
    for i in range(1, 6):
        if i <= full_stars:
            stars_html += '<span class="text-gold">★</span>'
        else:
            stars_html += '<span class="text-ink/20">★</span>'
    return mark_safe(stars_html)
