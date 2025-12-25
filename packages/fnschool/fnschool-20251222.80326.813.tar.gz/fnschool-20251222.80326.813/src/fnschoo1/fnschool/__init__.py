import re

from django.utils.translation import gettext as _

# from django.utils.translation import gettext_lazy as _


def count_chinese_characters(text):
    pattern = re.compile(r"[\u4e00-\u9fa5]")
    chinese_chars = pattern.findall(text)
    return len(chinese_chars)


# The end.
