from .ResponseBase import ResponseBase


class PeopleBusinessSearchResponse(ResponseBase):
    def __init__(self, version="", transmission_reference="", total_records="", result_code="", results=None):
        self.version = version
        self.transmission_reference = transmission_reference
        self.result_code = result_code
        self.total_records = total_records
        self.results = results if results is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        cls.data = data
        results = [PeopleBusinessSearchResult.from_dict(result) for result in data.get("Results", [])]
        return cls(
            version=data.get("Version", ""),
            transmission_reference=data.get("TransmissionReference", ""),
            result_code = data.get("ResultCode", ""),
            total_records = data.get("TotalRecords", ""),
            results=results
        )
    
    # Setters
    def set_version(self, version):
        self.version = version

    def set_transmission_reference(self, transmission_reference):
        self.transmission_reference = transmission_reference

    def set_result_code(self, result_code):
        self.result_code = result_code

    def set_total_records(self, total_records):
        self.total_records = total_records

    # Getters
    def get_version(self):
        return self.version if self.version else ""

    def get_transmission_reference(self):
        return self.transmission_reference if self.transmission_reference else ""

    def get_result_code(self):
        return self.result_code if self.result_code else ""

    def get_total_records(self):
        return self.total_records if self.total_records else ""
    

class PeopleBusinessSearchResult:
    def __init__(self, match_level="", address=None, consumer=None, phone=None):
        self.match_level = match_level
        self.address = address
        self.consumer = consumer
        self.phone = phone

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        address = PeopleBusinessSearchAddress.from_dict(data.get('Address')) if 'Address' in data else None
        consumer = PeopleBusinessSearchConsumer.from_dict(data.get('Consumer')) if 'Consumer' in data else None
        phone = PeopleBusinessSearchPhone.from_dict(data.get('Phone')) if 'Phone' in data else None

        return cls(
            match_level=data.get('matchLevel'),
            address=address,
            consumer=consumer,
            phone=phone
        )
    
    # Setters

    def set_match_level(self, match_level):
        self.match_level = match_level

    # Getters

    def get_match_level(self):
        return self.get_match_level if self.get_match_level else ""
    
class PeopleBusinessSearchAddress:
    def __init__(self, address1="", dependent_locality="", locality="", locality_alternates="",
                 administrative_area="", country_code="", country_name="", thoroughfare="",
                 thoroughfare_pre_direction="", thoroughfare_name="", thoroughfare_trailing_type="",
                 thoroughfare_post_direction="", premises="", premise_type="", premise_number="",
                 sub_premises="", sub_premise_type="", sub_premise_number="", postal_code="",
                 postal_code_secondary="", melissa_address_key="", melissa_address_key_base=""):
        self.address1 = address1
        self.dependent_locality = dependent_locality
        self.locality = locality
        self.locality_alternates = locality_alternates
        self.administrative_area = administrative_area
        self.country_code = country_code
        self.country_name = country_name
        self.thoroughfare = thoroughfare
        self.thoroughfare_pre_direction = thoroughfare_pre_direction
        self.thoroughfare_name = thoroughfare_name
        self.thoroughfare_trailing_type = thoroughfare_trailing_type
        self.thoroughfare_post_direction = thoroughfare_post_direction
        self.premises = premises
        self.premise_type = premise_type
        self.premise_number = premise_number
        self.sub_premises = sub_premises
        self.sub_premise_type = sub_premise_type
        self.sub_premise_number = sub_premise_number
        self.postal_code = postal_code
        self.postal_code_secondary = postal_code_secondary
        self.melissa_address_key = melissa_address_key
        self.melissa_address_key_base = melissa_address_key_base

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            address1=data.get('Address1'),
            dependent_locality=data.get('DependentLocality'),
            locality=data.get('Locality'),
            locality_alternates=data.get('LocalityAlternates'),
            administrative_area=data.get('AdministrativeArea'),
            country_code=data.get('CountryCode'),
            country_name=data.get('CountryName'),
            thoroughfare=data.get('Thoroughfare'),
            thoroughfare_pre_direction=data.get('ThoroughfarePreDirection'),
            thoroughfare_name=data.get('ThoroughfareName'),
            thoroughfare_trailing_type=data.get('ThoroughfareTrailingType'),
            thoroughfare_post_direction=data.get('ThoroughfarePostDirection'),
            premises=data.get('Premises'),
            premise_type=data.get('PremiseType'),
            premise_number=data.get('PremiseNumber'),
            sub_premises=data.get('SubPremises'),
            sub_premise_type=data.get('SubPremiseType'),
            sub_premise_number=data.get('SubPremiseNumber'),
            postal_code=data.get('PostalCode'),
            postal_code_secondary=data.get('PostalCodeSecondary'),
            melissa_address_key=data.get('MelissaAddressKey'),
            melissa_address_key_base=data.get('MelissaAddressKeyBase')
        )
    
    class PeopleBusinessSearchAddress:
        def __init__(self):
            self._address1 = None
            self._dependent_locality = None
            self._locality = None
            self._locality_alternates = None
            self._administrative_area = None
            self._country_code = None
            self._country_name = None
            self._thoroughfare = None
            self._thoroughfare_pre_direction = None
            self._thoroughfare_name = None
            self._thoroughfare_trailing_type = None
            self._thoroughfare_post_direction = None
            self._premises = None
            self._premise_type = None
            self._premise_number = None
            self._sub_premises = None
            self._sub_premise_type = None
            self._sub_premise_number = None
            self._postal_code = None
            self._postal_code_secondary = None
            self._melissa_address_key = None
            self._melissa_address_key_base = None

    # Setters
    def set_address1(self, address1):
        self._address1 = address1

    def set_dependent_locality(self, dependent_locality):
        self._dependent_locality = dependent_locality

    def set_locality(self, locality):
        self._locality = locality

    def set_locality_alternates(self, locality_alternates):
        self._locality_alternates = locality_alternates

    def set_administrative_area(self, administrative_area):
        self._administrative_area = administrative_area

    def set_country_code(self, country_code):
        self._country_code = country_code

    def set_country_name(self, country_name):
        self._country_name = country_name

    def set_thoroughfare(self, thoroughfare):
        self._thoroughfare = thoroughfare

    def set_thoroughfare_pre_direction(self, thoroughfare_pre_direction):
        self._thoroughfare_pre_direction = thoroughfare_pre_direction

    def set_thoroughfare_name(self, thoroughfare_name):
        self._thoroughfare_name = thoroughfare_name

    def set_thoroughfare_trailing_type(self, thoroughfare_trailing_type):
        self._thoroughfare_trailing_type = thoroughfare_trailing_type

    def set_thoroughfare_post_direction(self, thoroughfare_post_direction):
        self._thoroughfare_post_direction = thoroughfare_post_direction

    def set_premises(self, premises):
        self._premises = premises

    def set_premise_type(self, premise_type):
        self._premise_type = premise_type

    def set_premise_number(self, premise_number):
        self._premise_number = premise_number

    def set_sub_premises(self, sub_premises):
        self._sub_premises = sub_premises

    def set_sub_premise_type(self, sub_premise_type):
        self._sub_premise_type = sub_premise_type

    def set_sub_premise_number(self, sub_premise_number):
        self._sub_premise_number = sub_premise_number

    def set_postal_code(self, postal_code):
        self._postal_code = postal_code

    def set_postal_code_secondary(self, postal_code_secondary):
        self._postal_code_secondary = postal_code_secondary

    def set_melissa_address_key(self, melissa_address_key):
        self._melissa_address_key = melissa_address_key

    def set_melissa_address_key_base(self, melissa_address_key_base):
        self._melissa_address_key_base = melissa_address_key_base

    # Getters
    def get_address1(self):
        return self._address1 if self._address1 else ""

    def get_dependent_locality(self):
        return self._dependent_locality if self._dependent_locality else ""

    def get_locality(self):
        return self._locality if self._locality else ""

    def get_locality_alternates(self):
        return self._locality_alternates if self._locality_alternates else ""

    def get_administrative_area(self):
        return self._administrative_area if self._administrative_area else ""

    def get_country_code(self):
        return self._country_code if self._country_code else ""

    def get_country_name(self):
        return self._country_name if self._country_name else ""

    def get_thoroughfare(self):
        return self._thoroughfare if self._thoroughfare else ""

    def get_thoroughfare_pre_direction(self):
        return self._thoroughfare_pre_direction if self._thoroughfare_pre_direction else ""

    def get_thoroughfare_name(self):
        return self._thoroughfare_name if self._thoroughfare_name else ""

    def get_thoroughfare_trailing_type(self):
        return self._thoroughfare_trailing_type if self._thoroughfare_trailing_type else ""

    def get_thoroughfare_post_direction(self):
        return self._thoroughfare_post_direction if self._thoroughfare_post_direction else ""

    def get_premises(self):
        return self._premises if self._premises else ""

    def get_premise_type(self):
        return self._premise_type if self._premise_type else ""

    def get_premise_number(self):
        return self._premise_number if self._premise_number else ""

    def get_sub_premises(self):
        return self._sub_premises if self._sub_premises else ""

    def get_sub_premise_type(self):
        return self._sub_premise_type if self._sub_premise_type else ""

    def get_sub_premise_number(self):
        return self._sub_premise_number if self._sub_premise_number else ""

    def get_postal_code(self):
        return self._postal_code if self._postal_code else ""

    def get_postal_code_secondary(self):
        return self._postal_code_secondary if self._postal_code_secondary else ""

    def get_melissa_address_key(self):
        return self._melissa_address_key if self._melissa_address_key else ""

    def get_melissa_address_key_base(self):
        return self._melissa_address_key_base if self._melissa_address_key_base else ""
    
class PeopleBusinessSearchConsumer:
    def __init__(self, full_name="", first_name="", middle_name="", last_name="", suffix="", other_full_names="", melissa_identity_key=""):
        self.full_name = full_name
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.suffix = suffix
        self.other_full_names = other_full_names
        self.melissa_identity_key = melissa_identity_key

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            full_name=data.get("FullName", ""),
            first_name=data.get("FirstName", ""),
            middle_name=data.get("MiddleName", ""),
            last_name=data.get("LastName", ""),
            suffix=data.get("Suffix", ""),
            other_full_names=data.get("OtherFullNames", ""),
            melissa_identity_key=data.get("MelissaIdentityKey", "")
        )
    

    # Setters
    
    def set_full_name(self, full_name):
        self.full_name = full_name

    def set_first_name(self, first_name):
        self.first_name = first_name

    def set_middle_name(self, middle_name):
        self.middle_name = middle_name

    def set_last_name(self, last_name):
        self.last_name = last_name

    def set_suffix(self, suffix):
        self.suffix = suffix

    def set_other_full_names(self, other_full_names):
        self.other_full_names = other_full_names

    def set_melissa_identity_key(self, melissa_identity_key):
        self.melissa_identity_key = melissa_identity_key

    # Getters

    def get_full_name(self):
        return self.full_name or ""

    def get_first_name(self):
        return self.first_name or ""

    def get_middle_name(self):
        return self.middle_name or ""

    def get_last_name(self):
        return self.last_name or ""

    def get_suffix(self):
        return self.suffix or ""

    def get_other_full_names(self):
        return self.other_full_names or ""

    def get_melissa_identity_key(self):
        return self.melissa_identity_key or ""

class PeopleBusinessSearchPhone:
    def __init__(self, phone="", other_phones=""):
        self.phone = phone
        self.other_phones = other_phones

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            phone=data.get("Phone", ""),
            other_phones=data.get("OtherPhones", "")
        )
    
    
    # Setter methods
    
    def set_phone(self, phone):
        self.phone = phone

    def set_other_phones(self, other_phones):
        self.other_phones = other_phones

    # Getter methods
    
    def get_phone(self):
        return self.phone or ""

    def get_other_phones(self):
        return self.other_phones or ""


    