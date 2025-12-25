from .ResponseBase import ResponseBase

class GlobalPhoneResponse(ResponseBase):
    def __init__(self, version="", transmission_reference="", transmission_results="", total_records="", records=None):
        self.version = version
        self.transmission_reference = transmission_reference
        self.transmission_results = transmission_results
        self.total_records = total_records
        self.records = records if records is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        records = [GlobalPhoneRecord.from_dict(record) for record in data.get("Records", [])]
        return cls(
            version=data.get("Version", ""),
            transmission_reference=data.get("TransmissionReference", ""),
            transmission_results=data.get("TransmissionResults", ""),
            total_records = data.get("TotalRecords", ""),
            records=records
        )
    
    # Setters
    def set_version(self, version):
        self.version = version

    def set_transmission_reference(self, transmission_reference):
        self.transmission_reference = transmission_reference

    def set_transmission_results(self, transmission_results):
        self.transmission_results = transmission_results

    def set_total_records(self, total_records):
        self.total_records = total_records

    # Getters
    def get_version(self):
        return self.version or ""

    def get_transmission_reference(self):
        return self.transmission_reference or ""

    def get_transmission_results(self):
        return self.transmission_results or ""

    def get_total_records(self):
        return self.total_records or ""
    
class GlobalPhoneRecord:
    def __init__(
        self, record_id="", results="", phone_number="", administrative_area="", country_abbreviation="", country_name="", carrier="",
        caller_id="", dst="", international_phone_number="", language="", latitude="", locality="", longitude="", phone_international_prefix="", phone_country_dialing_code="",
        phone_nation_prefix="", phone_national_destination_code="", phone_subscriber_number="", utc="", postal_code="", suggestions="", time_zone_code="", time_zone_name=""
    ):
        self.record_id = record_id
        self.results = results
        self.phone_number = phone_number
        self.administrative_area = administrative_area
        self.country_abbreviation = country_abbreviation
        self.country_name = country_name
        self.carrier = carrier
        self.caller_id = caller_id
        self.dst = dst
        self.international_phone_number = international_phone_number
        self.language = language
        self.latitude = latitude
        self.locality = locality
        self.longitude = longitude
        self.phone_international_prefix = phone_international_prefix
        self.phone_country_dialing_code = phone_country_dialing_code
        self.phone_nation_prefix = phone_nation_prefix
        self.phone_national_destination_code = phone_national_destination_code
        self.phone_subscriber_number = phone_subscriber_number
        self.utc = utc
        self.postal_code = postal_code
        self.suggestions = suggestions
        self.time_zone_code = time_zone_code
        self.time_zone_name = time_zone_name

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            record_id=data.get("RecordID", ""),
            results=data.get("Results", ""),
            phone_number=data.get("PhoneNumber", ""),
            administrative_area=data.get("AdministrativeArea", ""),
            country_abbreviation=data.get("CountryAbbreviation", ""),
            country_name=data.get("CountryName", ""),
            carrier=data.get("Carrier", ""),
            caller_id=data.get("CallerID", ""),
            dst=data.get("DST", ""),
            international_phone_number=data.get("InternationalPhoneNumber", ""),
            language=data.get("Language", ""),
            latitude=data.get("Latitude", ""),
            locality=data.get("Locality", ""),
            longitude=data.get("Longitude", ""),
            phone_international_prefix=data.get("PhoneInternationalPrefix", ""),
            phone_country_dialing_code=data.get("PhoneCountryDialingCode", ""),
            phone_nation_prefix=data.get("PhoneNationPrefix", ""),
            phone_national_destination_code=data.get("PhoneNationalDestinationCode", ""),
            phone_subscriber_number=data.get("PhoneSubscriberNumber", ""),
            utc=data.get("UTC", ""),
            postal_code=data.get("PostalCode", ""),
            suggestions=data.get("Suggestions", ""),
            time_zone_code=data.get("TimeZoneCode", ""),
            time_zone_name=data.get("TimeZoneName", "")
        )
    

    # Setters
    def set_record_id(self, record_id):
        self.record_id = record_id

    def set_results(self, results):
        self.results = results

    def set_phone_number(self, phone_number):
        self.phone_number = phone_number

    def set_administrative_area(self, administrative_area):
        self.administrative_area = administrative_area

    def set_country_abbreviation(self, country_abbreviation):
        self.country_abbreviation = country_abbreviation

    def set_country_name(self, country_name):
        self.country_name = country_name

    def set_carrier(self, carrier):
        self.carrier = carrier

    def set_caller_id(self, caller_id):
        self.caller_id = caller_id

    def set_dst(self, dst):
        self.dst = dst

    def set_international_phone_number(self, international_phone_number):
        self.international_phone_number = international_phone_number

    def set_language(self, language):
        self.language = language

    def set_latitude(self, latitude):
        self.latitude = latitude

    def set_locality(self, locality):
        self.locality = locality

    def set_longitude(self, longitude):
        self.longitude = longitude

    def set_phone_international_prefix(self, phone_international_prefix):
        self.phone_international_prefix = phone_international_prefix

    def set_phone_country_dialing_code(self, phone_country_dialing_code):
        self.phone_country_dialing_code = phone_country_dialing_code

    def set_phone_nation_prefix(self, phone_nation_prefix):
        self.phone_nation_prefix = phone_nation_prefix

    def set_phone_national_destination_code(self, phone_national_destination_code):
        self.phone_national_destination_code = phone_national_destination_code

    def set_phone_subscriber_number(self, phone_subscriber_number):
        self.phone_subscriber_number = phone_subscriber_number

    def set_utc(self, utc):
        self.utc = utc

    def set_postal_code(self, postal_code):
        self.postal_code = postal_code

    def set_suggestions(self, suggestions):
        self.suggestions = suggestions

    def set_time_zone_code(self, time_zone_code):
        self.time_zone_code = time_zone_code

    def set_time_zone_name(self, time_zone_name):
        self.time_zone_name = time_zone_name

    # Getters
    def get_record_id(self):
        return self.record_id or ""

    def get_results(self):
        return self.results or ""

    def get_phone_number(self):
        return self.phone_number or ""

    def get_administrative_area(self):
        return self.administrative_area or ""

    def get_country_abbreviation(self):
        return self.country_abbreviation or ""

    def get_country_name(self):
        return self.country_name or ""

    def get_carrier(self):
        return self.carrier or ""

    def get_caller_id(self):
        return self.caller_id or ""

    def get_dst(self):
        return self.dst or ""

    def get_international_phone_number(self):
        return self.international_phone_number or ""

    def get_language(self):
        return self.language or ""

    def get_latitude(self):
        return self.latitude or ""

    def get_locality(self):
        return self.locality or ""

    def get_longitude(self):
        return self.longitude or ""

    def get_phone_international_prefix(self):
        return self.phone_international_prefix or ""

    def get_phone_country_dialing_code(self):
        return self.phone_country_dialing_code or ""

    def get_phone_nation_prefix(self):
        return self.phone_nation_prefix or ""

    def get_phone_national_destination_code(self):
        return self.phone_national_destination_code or ""

    def get_phone_subscriber_number(self):
        return self.phone_subscriber_number or ""

    def get_utc(self):
        return self.utc or ""

    def get_postal_code(self):
        return self.postal_code or ""

    def get_suggestions(self):
        return self.suggestions or ""

    def get_time_zone_code(self):
        return self.time_zone_code or ""

    def get_time_zone_name(self):
        return self.time_zone_name or ""
