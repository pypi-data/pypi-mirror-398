from typing import Optional, Dict, Any


class Committable:
    """Committable object for bulkload operations."""

    class Type:
        LOCAL_FILE = "LOCAL_FILE"
        TABLE_VOLUME = "TABLE_VOLUME"
        USER_DEFINED = "USER_DEFINED"

    def __init__(self, committable_type: str, path: str, dst_path: Optional[str] = None,
                 user_defined_sql: Optional[str] = None, conf: Optional[Dict[str, Any]] = None):
        self._type = committable_type
        self._path = path
        # transform some infos to user defined sql.
        # such as file path and dst table volume path.
        self._dst_path = dst_path
        self._user_defined_sql = user_defined_sql
        self._conf = conf or {}

    def get_type(self) -> str:
        return self._type

    def get_path(self) -> str:
        return self._path

    def get_dst_path(self) -> Optional[str]:
        return self._dst_path

    def set_dst_path(self, dst_path: str):
        self._dst_path = dst_path

    def get_user_defined_sql(self) -> Optional[str]:
        return self._user_defined_sql

    def get_conf(self) -> Dict[str, Any]:
        return self._conf

    def set_conf(self, conf: Dict[str, Any]):
        self._conf = conf

    def __repr__(self):
        return f"Committable(type={self._type}, path={self._path}, dst_path={self._dst_path}, user_defined_sql={self._user_defined_sql}, conf={self._conf})"
