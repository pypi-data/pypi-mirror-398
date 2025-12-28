"""Remote visitor data filter"""


class RemoteVisitorDataFilter:
    """Remote visitor data filter"""

    # pylint: disable=R0913
    def __init__(
        self,
        previous_visit_amount=1,
        current_visit=True,
        custom_data=True,
        page_views=False,
        geolocation=False,
        device=False,
        browser=False,
        operating_system=False,
        conversions=False,
        experiments=False,
        kcs=False,
        visitor_code=True,
        cbs=False,
        personalization=False,
    ) -> None:
        self._previous_visit_amount = previous_visit_amount
        self._current_visit = current_visit
        self._custom_data = custom_data
        self._page_views = page_views
        self._geolocation = geolocation
        self._device = device
        self._browser = browser
        self._operating_system = operating_system
        self._conversions = conversions
        self._experiments = experiments
        self._kcs = kcs
        self._visitor_code = visitor_code
        self._cbs = cbs
        self._personalization = personalization

    @property
    def previous_visit_amount(self) -> int:
        """Number of previous visits to retrieve data from. Number between 1 and 25"""
        return self._previous_visit_amount

    @property
    def current_visit(self) -> bool:
        """True if current visit data will be retrieved"""
        return self._current_visit

    @property
    def custom_data(self) -> bool:
        """True if custom data will be retrieved"""
        return self._custom_data

    @property
    def page_views(self) -> bool:
        """True if page data will be retrieved"""
        return self._page_views

    @property
    def geolocation(self) -> bool:
        """True if geolocation data will be retrieved"""
        return self._geolocation

    @property
    def device(self) -> bool:
        """True if device data will be retrieved"""
        return self._device

    @property
    def browser(self) -> bool:
        """True if browser data will be retrieved"""
        return self._browser

    @property
    def operating_system(self) -> bool:
        """True if operating system data will be retrieved"""
        return self._operating_system

    @property
    def conversions(self) -> bool:
        """True if conversion data will be retrieved"""
        return self._conversions

    @property
    def experiments(self) -> bool:
        """True if experiment data will be retrieved"""
        return self._experiments

    @property
    def kcs(self) -> bool:
        """True if KCS heat data will be retrieved"""
        return self._kcs

    @property
    def visitor_code(self) -> bool:
        """True if the `visitorCode` from the most recent visit will be retrieved and used for the current visit"""
        return self._visitor_code

    @property
    def cbs(self) -> bool:
        """True if CBS data will be retrieved"""
        return self._cbs

    @property
    def personalization(self) -> bool:
        """True if personalization data will be retrieved"""
        return self._personalization

    def __str__(self) -> str:
        return (
            f"RemoteVisitorDataFilter{{previous_visit_amount:{self._previous_visit_amount},"
            f"current_visit:{self._current_visit},custom_data:{self._custom_data},"
            f"page_views:{self._page_views}, geolocation:{self._geolocation},"
            f"device:{self._device},browser:{self._browser},"
            f"operating_system:{self._operating_system},conversions:{self._conversions},"
            f"experiments:{self._experiments},kcs:{self._kcs},visitor_code:{self._visitor_code}}},cbs:{self._cbs},"
            f"personalization:{self._personalization}"
        )
