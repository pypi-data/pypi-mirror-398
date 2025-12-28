"""Custom data info"""

from typing import Optional, Dict, Union, Any, List

from kameleoon.logging.kameleoon_logger import KameleoonLogger


class CustomDataInfo:
    """Custom data info"""

    SCOPE_VISITOR = "VISITOR"

    def __init__(
        self, custom_data: Optional[List[Dict[str, Union[str, int, Any]]]]
    ) -> None:
        super().__init__()
        self.__mapping_identifier_index = None
        self.__local_only = set()
        self.__visitor_scope = set()
        self.__custom_data_index_by_id = {}
        self.__custom_data_index_by_name = {}
        if custom_data is not None:
            for data in custom_data:
                index = data.get("index")
                if index is not None:
                    index = int(index)
                    if data.get("localOnly"):
                        self.__local_only.add(index)
                    if data.get("scope") == self.SCOPE_VISITOR:
                        self.__visitor_scope.add(index)
                    if (id_ := data.get("id")) is not None:
                        self.__custom_data_index_by_id[id_] = index
                    if (name := data.get("name")) is not None:
                        self.__custom_data_index_by_name[name] = index
                    if data.get("isMappingIdentifier"):
                        if bool(self.__mapping_identifier_index is not None):
                            KameleoonLogger.warning(
                                "More than one mapping identifier is set. Undefined behavior may occur" +
                                " on cross-device reconciliation."
                            )
                        self.__mapping_identifier_index = index

    def is_local_only(self, index: int) -> bool:
        """Check for local only"""
        return index in self.__local_only

    def is_mapping_identifier(self, index: int) -> bool:
        """Check for mapping identifier"""
        return self.__mapping_identifier_index == index

    def is_visitor_scope(self, index: int) -> bool:
        """Check for visitor scope"""
        return index in self.__visitor_scope

    @property
    def mapping_identifier_index(self) -> Optional[int]:
        """Take mapping identifier index"""
        return self.__mapping_identifier_index

    def get_custom_data_index_by_id(self, custom_data_id: int) -> Optional[int]:
        """Get corresponding custom data index by custom data id"""
        return self.__custom_data_index_by_id.get(custom_data_id)

    def get_custom_data_index_by_name(self, custom_data_name: str) -> Optional[int]:
        """Get corresponding custom data index by custom data name"""
        return self.__custom_data_index_by_name.get(custom_data_name)
