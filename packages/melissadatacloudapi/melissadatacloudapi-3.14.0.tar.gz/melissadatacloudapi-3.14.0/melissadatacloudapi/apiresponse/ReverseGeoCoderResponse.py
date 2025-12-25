from .ResponseBase import ResponseBase

class ReverseGeoCoderResponse(ResponseBase):

    def __init__(self, version="", transmission_results="", transmission_reference="", results="", total_records="", records=None):
        self.version = version
        self.transmission_reference = transmission_reference
        self.transmission_results = transmission_results
        self.results = results
        self.total_records = total_records
        self.records = records if records is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        cls.data = data
        records = [ReverseGeoCoderRecord.from_dict(record) for record in data.get("Records", [])]
        return cls(
            version=data.get("Version", ""),
            transmission_reference=data.get("TransmissionReference", ""),
            transmission_results=data.get("TransmissionResults", ""),
            results=data.get("Results", ""),
            total_records=data.get("TotalRecords", ""),
            records=records
        )

     # Setters
    def set_version(self, version):
        self.version = version

    def set_transmission_reference(self, transmission_reference):
        self.transmission_reference = transmission_reference

    def set_transmission_results(self, transmission_results):
        self.transmission_results = transmission_results

    def set_results(self, results):
        self.results = results

    def set_total_records(self, total_records):
        self.total_records = total_records

    def set_records(self, records):
        self.records = records

    # Getters
    def get_version(self):
        return self.version or ""

    def get_transmission_reference(self):
        return self.transmission_reference or ""

    def get_transmission_results(self):
        return self.transmission_results or ""

    def get_results(self):
        return self.results or ""

    def get_total_records(self):
        return self.total_records or ""

    def get_records(self):
        return self.records or []
    
class ReverseGeoCoderRecord(ResponseBase):
    def __init__(self, address_line_1="", suite_name="", suite_count="", city="", state="", postal_code="", address_key="", latitude="", 
                 longitude="", distance="", melissa_address_key="", melissa_address_key_base="", carrier_route="", laitude="", record_id=""):
        # For doLookup endpoint
        self.address_line_1 = address_line_1
        self.suite_name = suite_name
        self.suite_count = suite_count
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.address_key = address_key
        self.latitude = latitude
        self.longitude = longitude
        self.distance = distance
        self.melissa_address_key = melissa_address_key
        self.melissa_address_key_base = melissa_address_key_base

        # For doLookupPostalCodes endpoint
        self.carrier_route = carrier_route
        self.laitude = laitude

        # For doLookupFromList
        self.record_id = record_id

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            address_line_1=data.get("AddressLine1", ""),
            suite_name=data.get("SuiteName", ""),
            suite_count=data.get("SuiteCount", ""),
            city=data.get("City", ""),
            state=data.get("State", ""),
            postal_code=data.get("PostalCode", ""),
            address_key=data.get("AddressKey", ""),
            latitude=data.get("Latitude", ""),
            longitude=data.get("Longitude", ""),
            distance=data.get("Distance", ""),
            melissa_address_key=data.get("MelissaAddressKey", ""),
            melissa_address_key_base=data.get("MelissaAddressKeyBase", ""),
            carrier_route=data.get("CarrierRoute", ""),
            laitude=data.get("Laitude", ""),
            record_id=data.get("RecordID", "")
        )
    
    # Setters
    def set_address_line_1(self, address_line_1):
        self.address_line_1 = address_line_1

    def set_suite_name(self, suite_name):
        self.suite_name = suite_name

    def set_suite_count(self, suite_count):
        self.suite_count = suite_count

    def set_city(self, city):
        self.city = city

    def set_state(self, state):
        self.state = state

    def set_postal_code(self, postal_code):
        self.postal_code = postal_code

    def set_address_key(self, address_key):
        self.address_key = address_key

    def set_latitude(self, latitude):
        self.latitude = latitude

    def set_longitude(self, longitude):
        self.longitude = longitude

    def set_distance(self, distance):
        self.distance = distance

    def set_melissa_address_key(self, melissa_address_key):
        self.melissa_address_key = melissa_address_key

    def set_melissa_address_key_base(self, melissa_address_key_base):
        self.melissa_address_key_base = melissa_address_key_base

    def set_carrier_route(self, carrier_route):
        self.carrier_route = carrier_route

    def set_laitude(self, laitude):
        self.laitude = laitude

    def set_record_id(self, record_id):
        self.record_id = record_id

    # Getters
    def get_address_line_1(self):
        return self.address_line_1 or ""

    def get_suite_name(self):
        return self.suite_name or ""

    def get_suite_count(self):
        return self.suite_count or ""

    def get_city(self):
        return self.city or ""

    def get_state(self):
        return self.state or ""

    def get_postal_code(self):
        return self.postal_code or ""

    def get_address_key(self):
        return self.address_key or ""

    def get_latitude(self):
        return self.latitude or ""

    def get_longitude(self):
        return self.longitude or ""

    def get_distance(self):
        return self.distance or ""

    def get_melissa_address_key(self):
        return self.melissa_address_key or ""

    def get_melissa_address_key_base(self):
        return self.melissa_address_key_base or ""

    def get_carrier_route(self):
        return self.carrier_route or ""

    def get_laitude(self):
        return self.laitude or ""

    def get_record_id(self):
        return self.record_id or ""



