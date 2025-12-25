from .ResponseBase import ResponseBase

class PersonatorSearchResponse(ResponseBase):

    def __init__(self, version="", transmission_reference="", transmission_results="", total_pages="", total_records="", records=None):
        self.version = version
        self.transmission_reference = transmission_reference
        self.transmission_results = transmission_results
        self.total_pages = total_pages
        self.total_records = total_records
        self.records = records if records is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        cls.data = data
        records = [PersonatorSearchRecord.from_dict(record) for record in data.get("Records", [])]
        return cls(
            version=data.get("Version", ""),
            transmission_reference=data.get("TransmissionReference", ""),
            transmission_results=data.get("TransmissionResults", ""),
            total_pages=data.get("TotalPages", ""),
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

    def set_total_pages(self, total_pages):
        self.total_pages = total_pages

    def set_total_records(self, total_records):
        self.total_records = total_records

    # Getters
    def get_version(self):
        return self.version or ""

    def get_transmission_reference(self):
        return self.transmission_reference or ""

    def get_transmission_results(self):
        return self.transmission_results or ""
    
    def get_total_pages(self):
        return self.total_pages or ""

    def get_total_records(self):
        return self.total_records or ""
    

class PersonatorSearchRecord:
    def __init__(
        self, record_id="", results="", full_name="", first_name="", last_name="", date_of_birth="", date_of_death="", \
            melissa_identity_key="", current_address=None, previous_addresses=None, phone_records=None, email_records=None,
    ):
        self.record_id = record_id
        self.results = results
        self.full_name = full_name
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.date_of_death = date_of_death
        self.melissa_identity_key = melissa_identity_key
        self.current_address = current_address
        self.previous_addresses = previous_addresses or []
        self.phone_records = phone_records or []
        self.email_records = email_records or []

    @classmethod
    def from_dict(cls, data):
        cls.data = data

        return cls(
            record_id=data.get("RecordID", ""),
            results=data.get("Results", ""),
            full_name=data.get("FullName", ""),
            first_name=data.get("FirstName", ""),
            last_name=data.get("LastName", ""),
            date_of_birth=data.get("DateOfBirth", ""),
            date_of_death=data.get("DateOfDeath", ""),
            melissa_identity_key=data.get("MelissaIdentityKey", ""),
            current_address = PersonatorSearchAddress.from_dict(data.get("CurrentAddress", None)),
            previous_addresses = [PersonatorSearchAddress.from_dict(addr) for addr in data.get("PreviousAddresses", [])],
            phone_records = [PersonatorSearchPhone.from_dict(records) for records in data.get("PhoneRecords", [])],
            email_records = data.get("EmailRecords", [])
        )
    
     # Setters
    def set_record_id(self, record_id):
        self.record_id = record_id

    def set_results(self, results):
        self.results = results

    def set_full_name(self, full_name):
        self.full_name = full_name

    def set_first_name(self, first_name):
        self.first_name = first_name

    def set_last_name(self, last_name):
        self.last_name = last_name

    def set_date_of_birth(self, date_of_birth):
        self.date_of_birth = date_of_birth

    def set_date_of_death(self, date_of_death):
        self.date_of_death = date_of_death

    def set_melissa_identity_key(self, melissa_identity_key):
        self.melissa_identity_key = melissa_identity_key

    # Getters
    def get_record_id(self):
        return self.record_id or ""

    def get_results(self):
        return self.results or ""

    def get_full_name(self):
        return self.full_name or ""

    def get_first_name(self):
        return self.first_name or ""

    def get_last_name(self):
        return self.last_name or ""

    def get_date_of_birth(self):
        return self.date_of_birth or ""

    def get_date_of_death(self):
        return self.date_of_death or ""

    def get_melissa_identity_key(self):
        return self.melissa_identity_key or ""


class PersonatorSearchAddress:
    def __init__(
        self, address_line_1="", suite="", city="", state="", postal_code="", plus4="", 
        melissa_address_key="", melissa_address_key_base="", move_date="",
    ):
        self.address_line_1 = address_line_1
        self.suite = suite
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.plus4 = plus4
        self.melissa_address_key = melissa_address_key
        self.melissa_address_key_base = melissa_address_key_base
        self.move_date = move_date

    @classmethod
    def from_dict(cls, data: dict):
        cls.data = data
        return cls(
            address_line_1=data.get("AddressLine1", ""),
            suite=data.get("Suite", ""),
            city=data.get("City", ""),
            state=data.get("State", ""),
            postal_code=data.get("PostalCode", ""),
            plus4=data.get("Plus4", ""),
            melissa_address_key=data.get("MelissaAddressKey", ""),
            melissa_address_key_base=data.get("MelissaAddressKeyBase", ""),
            move_date=data.get("MoveDate", ""),
        )
    
    # Setters
    def set_address_line_1(self, address_line_1):
        self.address_line_1 = address_line_1

    def set_suite(self, suite):
        self.suite = suite

    def set_city(self, city):
        self.city = city

    def set_state(self, state):
        self.state = state

    def set_postal_code(self, postal_code):
        self.postal_code = postal_code

    def set_plus4(self, plus4):
        self.plus4 = plus4

    def set_melissa_address_key(self, melissa_address_key):
        self.melissa_address_key = melissa_address_key

    def set_melissa_address_key_base(self, melissa_address_key_base):
        self.melissa_address_key_base = melissa_address_key_base

    def set_move_date(self, move_date):
        self.move_date = move_date

    # Getters
    def get_address_line_1(self):
        return self.address_line_1 or ""

    def get_suite(self):
        return self.suite or ""

    def get_city(self):
        return self.city or ""

    def get_state(self):
        return self.state or ""

    def get_postal_code(self):
        return self.postal_code or ""

    def get_plus4(self):
        return self.plus4 or ""

    def get_melissa_address_key(self):
        return self.melissa_address_key or ""

    def get_melissa_address_key_base(self):
        return self.melissa_address_key_base or ""

    def get_move_date(self):
        return self.move_date or ""

class PersonatorSearchPhone(ResponseBase):
    def __init__(self, phone_number=""):
        self.phone_number = phone_number

    @classmethod
    def from_dict(cls, data: dict):
        cls.data = data
        return cls(
            phone_number=data.get("PhoneNumber", "")
        )

    # Setter
    def set_phone_number(self, phone_number):
        self.phone_number = phone_number

    # Getter
    def get_phone_number(self):
        return self.phone_number or ""


class PersonatorSearchEmail(ResponseBase):
    def __init__(self, email=""):
        self.email = email
    
    @classmethod
    def from_dict(cls, data: dict):
        cls.data = data
        return cls(
            email=data.get("Email", "")
        )
    # Setter
    def set_email(self, email):
        self.email = email

    # Getter
    def get_email(self):
        return self.email or ""



