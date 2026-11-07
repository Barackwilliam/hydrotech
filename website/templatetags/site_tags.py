from django import template
from django.utils.html import format_html_join

from .. import i18n

register = template.Library()


@register.simple_tag(takes_context=True)
def tr(context, obj, field):
    """{% tr service "title" %} -> service.title_sw or service.title_en, by the visitor's language."""
    return i18n.pick(obj, field, context.get("lang", i18n.DEFAULT))


@register.simple_tag(takes_context=True)
def tr_paragraphs(context, obj, field):
    """Each line of the text becomes its own <p> (the admin help text promises that)."""
    text = i18n.pick(obj, field, context.get("lang", i18n.DEFAULT))
    return format_html_join("\n", "<p>{}</p>", ((line.strip(),) for line in text.splitlines() if line.strip()))


@register.simple_tag(takes_context=True)
def tr_lines(context, obj, field):
    """Each non-empty line of a text field, for step lists."""
    text = i18n.pick(obj, field, context.get("lang", i18n.DEFAULT))
    return [line.strip(" -•\t") for line in text.splitlines() if line.strip(" -•\t")]


@register.inclusion_tag("website/_icon.html")
def icon(name, size=28):
    return {"name": name, "size": size}


@register.filter
def initials_color(name):
    palette = ["#0b5ea8", "#c96a1b", "#147a6e", "#7a3fa0", "#2c4a6b"]
    return palette[sum(map(ord, name or "")) % len(palette)]
