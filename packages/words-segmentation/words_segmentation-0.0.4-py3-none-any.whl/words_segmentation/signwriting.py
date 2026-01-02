import re

from signwriting.formats.swu import re_swu


def segment_signwriting(text: str) -> list[str]:
    return re.findall(re_swu['sign'], text)
