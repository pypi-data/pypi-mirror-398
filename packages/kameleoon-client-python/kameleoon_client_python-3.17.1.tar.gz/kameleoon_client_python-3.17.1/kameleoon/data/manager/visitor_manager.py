"""Visitor Manager"""
import collections
import time
from typing import Any, Dict, Iterator, List, Optional
from kameleoon.configuration.custom_data_info import CustomDataInfo
from kameleoon.data import Conversion, CustomData
from kameleoon.data.mapping_identifier import MappingIdentifier
from kameleoon.data.manager.visitor import Visitor
from kameleoon.data.manager.visitor_slot import VisitorSlot
from kameleoon.helpers.scheduler import Scheduler
from kameleoon.logging.kameleoon_logger import KameleoonLogger
from kameleoon.managers.data.data_manager import DataManager


class VisitorManager:
    """Visitor manager"""
    def __init__(
        self, data_manager: DataManager, expiration_period: float, scheduler: Scheduler
    ) -> None:
        KameleoonLogger.debug("CALL: VisitorManager(data_manager, expiration_period: %s, scheduler)",
                              expiration_period)
        self._data_manager = data_manager
        self.__expiration_period = expiration_period
        self._slots: Dict[str, VisitorSlot] = collections.defaultdict(VisitorSlot)
        scheduler.schedule_job("VisitorManager.purge", expiration_period, self.__purge)
        KameleoonLogger.debug("RETURN: VisitorManager(data_manager, expiration_period: %s, scheduler)",
                              expiration_period)

    def __iter__(self) -> Iterator[str]:
        yield from list(self._slots)

    def __len__(self) -> int:
        return len(self._slots)

    def get_visitor(self, visitor_code: str) -> Optional[Visitor]:
        """Retrieves a visitor by their code if it exists, otherwise returns `None`."""
        KameleoonLogger.debug("CALL: VisitorManager.get_visitor(visitor_code: %s)", visitor_code)
        if (slot := self.__try_acquire_slot(visitor_code)) is None:
            visitor = None
        else:
            try:
                if slot.visitor is not None:
                    slot.update_last_activity_time()
                visitor = slot.visitor
            finally:
                slot.lock.release()
        KameleoonLogger.debug("RETURN: VisitorManager.get_visitor(visitor_code: %s) -> (visitor: %s)",
                              visitor_code, visitor)
        return visitor

    def get_or_create_visitor(self, visitor_code: str) -> Visitor:
        """Retrieves an existing visitor or creates a new one if not found."""
        KameleoonLogger.debug("CALL: VisitorManager.get_or_create_visitor(visitor_code: %s)", visitor_code)
        slot = self.__acquire_slot(visitor_code)
        try:
            if slot.visitor is None:
                slot.visitor = Visitor()
            else:
                slot.update_last_activity_time()
            return slot.visitor
        finally:
            slot.lock.release()
            KameleoonLogger.debug("RETURN: VisitorManager.get_or_create_visitor(visitor_code: %s)", visitor_code)

    def add_data(self, visitor_code: str, *args) -> Visitor:
        """
        Adds data to a visitor.

        Handles custom data:
        * marks custom data of the local scope as unsent
        * converts custom data with the mapping identifier index to the mapping identifier
        * maps a visitor by its mapping identifier
        """
        KameleoonLogger.debug("CALL: VisitorManager.add_data(visitor_code: %s, args: %s)", visitor_code, args)
        visitor = self.get_or_create_visitor(visitor_code)
        custom_data_info = self._data_manager.data_file.custom_data_info
        data_to_add: List[Any] = [None] * len(args)
        for i, data in enumerate(args):
            if isinstance(data, CustomData):
                data = self.__process_custom_data(visitor_code, visitor, custom_data_info, data)
            elif isinstance(data, Conversion):
                data = self.__process_conversion(data, custom_data_info)
            data_to_add[i] = data
        visitor.add_data(*data_to_add)
        KameleoonLogger.debug("RETURN: VisitorManager.add_data(visitor_code: %s, args: %s) -> (visitor)",
                              visitor_code, args)
        return visitor

    def __process_custom_data(
        self, visitor_code: str, visitor: Visitor, custom_data_info: CustomDataInfo, custom_data: CustomData
    ) -> Optional[CustomData]:
        """Processes custom data, potentially modifying or mapping it based on certain conditions."""
        if mapped_cd := self.__try_map_custom_data_index_by_name(custom_data, custom_data_info):
            custom_data = mapped_cd
        else:
            KameleoonLogger.error("%s is invalid and will be ignored", custom_data)
            return None
        # We shouldn't send custom data with local only type
        if custom_data_info.is_local_only(custom_data.index):
            custom_data.mark_as_sent()
        # If mappingIdentifier is passed, we should link anonymous visitor with real unique userId.
        # After authorization, customer must be able to continue work with userId, but hash for variation
        # should be calculated based on anonymous visitor code, that's why set MappingIdentifier to visitor.
        if custom_data_info.is_mapping_identifier(custom_data.index) and custom_data.values and custom_data.values[0]:
            visitor.mapping_identifier = visitor_code
            user_id = custom_data.values[0]
            if visitor_code != user_id:
                slot = self.__acquire_slot(user_id)
                try:
                    slot.visitor = visitor.clone()
                finally:
                    slot.lock.release()
                KameleoonLogger.info("Linked anonymous visitor %s with user %s", visitor_code, user_id)
            return MappingIdentifier(custom_data)
        return custom_data

    @staticmethod
    def __process_conversion(conversion: Conversion, cdi: CustomDataInfo) -> Conversion:
        if conversion.metadata:
            metadata = []
            for cd in conversion.metadata:
                mapped_cd = VisitorManager.__try_map_custom_data_index_by_name(cd, cdi)
                if mapped_cd:
                    metadata.append(mapped_cd)
                else:
                    KameleoonLogger.warning("Conversion metadata %s is invalid", cd)
            conversion._metadata = metadata
        return conversion

    @staticmethod
    def __try_map_custom_data_index_by_name(custom_data: CustomData, cdi: CustomDataInfo) -> Optional[CustomData]:
        if custom_data.index != CustomData.UNDEFINED_INDEX:
            return custom_data
        if custom_data.name is None:
            return None
        cd_index = cdi.get_custom_data_index_by_name(custom_data.name)
        return custom_data._named_to_indexed(cd_index) if cd_index is not None else None

    def __purge(self) -> None:
        KameleoonLogger.debug("CALL: VisitorManager.__purge()")
        expired_time = time.time() - self.__expiration_period
        for visitor_code in list(self._slots):
            if slot := self.__try_acquire_slot_once(visitor_code):
                try:
                    if (slot.visitor is None) or (slot.last_activity_time < expired_time):
                        self._slots.pop(visitor_code, None)
                finally:
                    slot.lock.release()
        KameleoonLogger.debug("RETURN: VisitorManager.__purge()")

    def __acquire_slot(self, visitor_code: str) -> VisitorSlot:
        while True:
            slot = self._slots[visitor_code]
            slot.lock.acquire()
            if slot == self._slots.get(visitor_code):
                return slot
            slot.lock.release()

    def __try_acquire_slot(self, visitor_code: str) -> Optional[VisitorSlot]:
        while True:
            slot = self._slots.get(visitor_code)
            if slot is None:
                return None
            slot.lock.acquire()
            if slot == self._slots.get(visitor_code):
                return slot
            slot.lock.release()

    def __try_acquire_slot_once(self, visitor_code: str) -> Optional[VisitorSlot]:
        slot = self._slots.get(visitor_code)
        if slot is None:
            return None
        slot.lock.acquire()
        if slot == self._slots.get(visitor_code):
            return slot
        slot.lock.release()
        return None
