from __future__ import annotations


def cmd_subject(subject_prefix: str, command: str) -> str:
    return f"{subject_prefix}.playlist.cmd.{command}"


CMD_CATALOG_REFRESH = "catalog_refresh"
CMD_QUEUE_APPLY = "queue_apply"
CMD_BLESSED_ADD = "blessed_add"
CMD_BLESSED_REMOVE = "blessed_remove"
CMD_BLESSED_LIST = "blessed_list"
