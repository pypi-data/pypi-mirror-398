import os
from typing import Optional


def get_task_id() -> Optional[str]:
    return os.getenv('BIYAO_FLOW_TASK_ID')


def get_task_site() -> Optional[str]:
    return os.getenv('BIYAO_FLOW_TASK_SITE')


def get_task_type() -> Optional[str]:
    return os.getenv('BIYAO_FLOW_TASK_TYPE')


def get_attr_status(obj, attr):
    if attr is None:
        return False
    value = getattr(obj, attr, -1)
    if value >= 0:
        return True
    else:
        return False
