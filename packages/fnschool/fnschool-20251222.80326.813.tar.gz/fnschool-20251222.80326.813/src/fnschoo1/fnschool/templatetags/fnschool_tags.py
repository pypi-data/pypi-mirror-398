from urllib.parse import urlencode

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    query = context["request"].GET.copy()

    for key, value in kwargs.items():
        if value is None:
            if key in query:
                del query[key]
        else:
            query[key] = value

    return urlencode(query)


@register.simple_tag
def multiply(a, b, *args):
    result = float(a) * float(b)
    for arg in args:
        result *= float(arg)
    return result
