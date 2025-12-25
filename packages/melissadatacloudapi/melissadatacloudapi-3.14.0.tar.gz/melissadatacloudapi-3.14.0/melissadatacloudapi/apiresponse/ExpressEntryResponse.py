from .ResponseBase import ResponseBase

class ExpressEntryResponse(ResponseBase):

    def __init__(self, version="", result_code="", error_string="", results=None):
        self.version = version
        self.result_code = result_code
        self.error_string = error_string
        self.results = results if results is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        cls.data=data
        results = [ExpressEntryRecord.from_dict(result) for result in data.get("Results", [])]
        return cls(
            version=data.get("Version", ""),
            result_code=data.get("ResultCode", ""),
            error_string=data.get("ErrorString", ""),
            results=results
        )

    # Setters
    def set_version(self, version):
        self.version = version

    def set_result_code(self, result_code):
        self.result_code = result_code

    def set_error_string(self, error_string):
        self.error_string = error_string

    # Getters
    def get_version(self):
        return self.version or ""

    def get_result_code(self):
        return self.result_code or ""

    def get_error_string(self):
        return self.error_string or ""
    

class ExpressEntryRecord(ResponseBase):

    def __init__(self, address=None):
        self.address=address

    @classmethod
    def from_dict(cls, data: dict):
        cls.data = data
        return cls(
            address = ExpressEntryAddress.from_dict(data.get("Address", None))
        )

class ExpressEntryAddress(ResponseBase):
    def __init__(self, address_line_1="", city="", city_accepted="", city_not_accepted="", state="",
                 postal_code="", country_subdivision_code="", address_key="", suite_name="", suite_count="",
                 suite_list=None, plus_four=None, mak="", base_mak=""):

        self.address_line_1 = address_line_1
        self.city = city
        self.city_accepted = city_accepted
        self.city_not_accepted = city_not_accepted
        self.state = state
        self.postal_code = postal_code
        self.country_subdivision_code = country_subdivision_code
        self.address_key = address_key
        self.suite_name = suite_name
        self.suite_count = suite_count
        self.suite_list = suite_list or []
        self.plus_four = plus_four or []
        self.mak = mak
        self.base_mak = base_mak

    @classmethod
    def from_dict(cls, data):
        cls.data=data
        return cls(
            address_line_1=data.get("AddressLine1", ""),
            city=data.get("City", ""),
            city_accepted=data.get("CityAccepted", ""),
            city_not_accepted=data.get("CityNotAccepted", ""),
            state=data.get("State", ""),
            postal_code=data.get("PostalCode", ""),
            country_subdivision_code=data.get("CountrySubdivisionCode", ""),
            address_key=data.get("AddressKey", ""),
            suite_name=data.get("SuiteName", ""),
            suite_count=data.get("SuiteCount", ""),
            suite_list=data.get("SuiteList", []),
            plus_four=data.get("PlusFour", []),
            mak=data.get("MAK", ""),
            base_mak=data.get("BaseMAK", "")
        )
    
    # Setters
    def set_address_line_1(self, address_line_1):
        self.address_line_1 = address_line_1

    def set_city(self, city):
        self.city = city

    def set_city_accepted(self, city_accepted):
        self.city_accepted = city_accepted

    def set_city_not_accepted(self, city_not_accepted):
        self.city_not_accepted = city_not_accepted

    def set_state(self, state):
        self.state = state

    def set_postal_code(self, postal_code):
        self.postal_code = postal_code

    def set_country_subdivision_code(self, country_subdivision_code):
        self.country_subdivision_code = country_subdivision_code

    def set_address_key(self, address_key):
        self.address_key = address_key

    def set_suite_name(self, suite_name):
        self.suite_name = suite_name

    def set_suite_count(self, suite_count):
        self.suite_count = suite_count

    def set_mak(self, mak):
        self.mak = mak

    def set_base_mak(self, base_mak):
        self.base_mak = base_mak

    # Getters
    def get_address_line_1(self):
        return self.address_line_1 or ""

    def get_city(self):
        return self.city or ""

    def get_city_accepted(self):
        return self.city_accepted or ""

    def get_city_not_accepted(self):
        return self.city_not_accepted or ""

    def get_state(self):
        return self.state or ""

    def get_postal_code(self):
        return self.postal_code or ""

    def get_country_subdivision_code(self):
        return self.country_subdivision_code or ""

    def get_address_key(self):
        return self.address_key or ""

    def get_suite_name(self):
        return self.suite_name or ""

    def get_suite_count(self):
        return self.suite_count or ""

    def get_mak(self):
        return self.mak or ""

    def get_base_mak(self):
        return self.base_mak or ""

