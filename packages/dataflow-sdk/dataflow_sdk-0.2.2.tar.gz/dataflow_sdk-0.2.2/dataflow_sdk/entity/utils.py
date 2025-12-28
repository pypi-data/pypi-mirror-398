import re

DOMAIN_REGEX = re.compile(
    r'^(?:[a-zA-Z0-9]'
    r'(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+'
    r'[a-zA-Z]{2,}$'
)

def is_domain(domain: str) -> bool:
    return bool(DOMAIN_REGEX.match(domain))