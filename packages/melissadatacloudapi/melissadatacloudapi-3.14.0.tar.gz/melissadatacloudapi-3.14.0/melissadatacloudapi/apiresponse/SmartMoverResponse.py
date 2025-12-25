from .ResponseBase import ResponseBase

class SmartMoverResponse(ResponseBase):
    def __init__(self, version="", transmission_reference="", transmission_results="", total_records="", cass_report_link="", nco_report_link="", records=None):
        self.version = version
        self.transmission_reference = transmission_reference
        self.transmission_results = transmission_results
        self.total_records = total_records
        self.cass_report_link = cass_report_link
        self.nco_report_link = nco_report_link
        self.records = records if records is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        cls.data = data
        records = [SmartMoverRecord.from_dict(record) for record in data.get("Records", [])]
        return cls(
            version=data.get("Version", ""),
            transmission_reference=data.get("TransmissionReference", ""),
            transmission_results=data.get("TransmissionResults", ""),
            total_records = data.get("TotalRecords", ""),
            cass_report_link = data.get("CASSReportLink", ""),
            nco_report_link = data.get("NCOReportLink", ""),
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

    def set_cass_report_link(self, cass_report_link):
        self.cass_report_link = cass_report_link

    def set_ncoa_report_link(self, ncoa_report_link):
        self.ncoa_report_link = ncoa_report_link

    # Getters 
    def get_version(self):
        return self.version or ""

    def get_transmission_reference(self):
        return self.transmission_reference or ""

    def get_transmission_results(self):
        return self.transmission_results or ""

    def get_total_records(self):
        return self.total_records or ""

    def get_cass_report_link(self):
        return self.cass_report_link or ""

    def get_ncoa_report_link(self):
        return self.ncoa_report_link or ""
    
class SmartMoverRecord:
    def __init__(
        self, address_extras="", address_key="", address_line_1="", address_line_2="", address_type_code="", base_melissa_address_key="", carrier_route="", 
        city="", city_abbreviation="", company_name="", country_code="", country_name="", delivery_indicator="", delivery_point_check_digit="", 
        delivery_point_code="", melissa_address_key="", move_effective_date="", move_type_code="", postal_code="", record_id="", results="", 
        state="", state_name="", urbanization="", name_first="", name_full="", name_last="", name_middle="", name_prefix="", name_suffix="", 
        original_address_line_1="", original_address_line_2="", original_city="", original_city_abbreviation="", original_country_code="", 
        original_plus4="", original_postal_code="", original_private_mailbox="", original_results="", original_state="", original_state_name="", 
        original_suite="", original_urbanization="", address_delivery_installation="", address_house_number="", address_lock_box="", 
        address_post_direction="", address_pre_direction="", address_private_mailbox_name="", address_private_mailbox_range="", 
        address_route_service="", address_street_name="", address_street_suffix="", address_suite_name="", address_suite_number="", 
        standardized_address_line_1="", standardized_address_line_2="", standardized_base_melissa_address_key="", standardized_carrier_route="", 
        standardized_city="", standardized_city_abbreviation="", standardized_country_code="", standardized_delivery_indicator="", 
        standardized_delivery_point_check_digit="", standardized_delivery_point_code="", standardized_melissa_address_key="", 
        standardized_plus4="", standardized_postal_code="", standardized_private_mailbox="", standardized_results="", standardized_state="", 
        standardized_state_name="", standardized_suite="", standardized_urbanization="", dpv_foot_notes="", move_return_code="", plus4="", 
        private_mailbox="", suite="",
    ):
        self.address_extras = address_extras
        self.address_key = address_key
        self.address_line_1 = address_line_1
        self.address_line_2 = address_line_2
        self.address_type_code = address_type_code
        self.base_melissa_address_key = base_melissa_address_key
        self.carrier_route = carrier_route
        self.city = city
        self.city_abbreviation = city_abbreviation
        self.company_name = company_name
        self.country_code = country_code
        self.country_name = country_name
        self.delivery_indicator = delivery_indicator
        self.delivery_point_check_digit = delivery_point_check_digit
        self.delivery_point_code = delivery_point_code
        self.melissa_address_key = melissa_address_key
        self.move_effective_date = move_effective_date
        self.move_type_code = move_type_code
        self.postal_code = postal_code
        self.record_id = record_id
        self.results = results
        self.state = state
        self.state_name = state_name
        self.urbanization = urbanization
        self.name_first = name_first
        self.name_full = name_full
        self.name_last = name_last
        self.name_middle = name_middle
        self.name_prefix = name_prefix
        self.name_suffix = name_suffix
        self.original_address_line_1 = original_address_line_1
        self.original_address_line_2 = original_address_line_2
        self.original_city = original_city
        self.original_city_abbreviation = original_city_abbreviation
        self.original_country_code = original_country_code
        self.original_plus4 = original_plus4
        self.original_postal_code = original_postal_code
        self.original_private_mailbox = original_private_mailbox
        self.original_results = original_results
        self.original_state = original_state
        self.original_state_name = original_state_name
        self.original_suite = original_suite
        self.original_urbanization = original_urbanization
        self.address_delivery_installation = address_delivery_installation
        self.address_house_number = address_house_number
        self.address_lock_box = address_lock_box
        self.address_post_direction = address_post_direction
        self.address_pre_direction = address_pre_direction
        self.address_private_mailbox_name = address_private_mailbox_name
        self.address_private_mailbox_range = address_private_mailbox_range
        self.address_route_service = address_route_service
        self.address_street_name = address_street_name
        self.address_street_suffix = address_street_suffix
        self.address_suite_name = address_suite_name
        self.address_suite_number = address_suite_number
        self.standardized_address_line_1 = standardized_address_line_1
        self.standardized_address_line_2 = standardized_address_line_2
        self.standardized_base_melissa_address_key = standardized_base_melissa_address_key
        self.standardized_carrier_route = standardized_carrier_route
        self.standardized_city = standardized_city
        self.standardized_city_abbreviation = standardized_city_abbreviation
        self.standardized_country_code = standardized_country_code
        self.standardized_delivery_indicator = standardized_delivery_indicator
        self.standardized_delivery_point_check_digit = standardized_delivery_point_check_digit
        self.standardized_delivery_point_code = standardized_delivery_point_code
        self.standardized_melissa_address_key = standardized_melissa_address_key
        self.standardized_plus4 = standardized_plus4
        self.standardized_postal_code = standardized_postal_code
        self.standardized_private_mailbox = standardized_private_mailbox
        self.standardized_results = standardized_results
        self.standardized_state = standardized_state
        self.standardized_state_name = standardized_state_name
        self.standardized_suite = standardized_suite
        self.standardized_urbanization = standardized_urbanization
        self.dpv_foot_notes = dpv_foot_notes
        self.move_return_code = move_return_code
        self.plus4 = plus4
        self.private_mailbox = private_mailbox
        self.suite = suite

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            address_extras=data.get("AddressExtras", ""),
            address_key=data.get("AddressKey", ""),
            address_line_1=data.get("AddressLine1", ""),
            address_line_2=data.get("AddressLine2", ""),
            address_type_code=data.get("AddressTypeCode", ""),
            base_melissa_address_key=data.get("BaseMelissaAddressKey", ""),
            carrier_route=data.get("CarrierRoute", ""),
            city=data.get("City", ""),
            city_abbreviation=data.get("CityAbbreviation", ""),
            company_name=data.get("CompanyName", ""),
            country_code=data.get("CountryCode", ""),
            country_name=data.get("CountryName", ""),
            delivery_indicator=data.get("DeliveryIndicator", ""),
            delivery_point_check_digit=data.get("DeliveryPointCheckDigit", ""),
            delivery_point_code=data.get("DeliveryPointCode", ""),
            melissa_address_key=data.get("MelissaAddressKey", ""),
            move_effective_date=data.get("MoveEffectiveDate", ""),
            move_type_code=data.get("MoveTypeCode", ""),
            postal_code=data.get("PostalCode", ""),
            record_id=data.get("RecordID", ""),
            results=data.get("Results", ""),
            state=data.get("State", ""),
            state_name=data.get("StateName", ""),
            urbanization=data.get("Urbanization", ""),
            name_first=data.get("NameFirst", ""),
            name_full=data.get("NameFull", ""),
            name_last=data.get("NameLast", ""),
            name_middle=data.get("NameMiddle", ""),
            name_prefix=data.get("NamePrefix", ""),
            name_suffix=data.get("NameSuffix", ""),
            original_address_line_1=data.get("OriginalAddressLine1", ""),
            original_address_line_2=data.get("OriginalAddressLine2", ""),
            original_city=data.get("OriginalCity", ""),
            original_city_abbreviation=data.get("OriginalCityAbbreviation", ""),
            original_country_code=data.get("OriginalCountryCode", ""),
            original_plus4=data.get("OriginalPlus4", ""),
            original_postal_code=data.get("OriginalPostalCode", ""),
            original_private_mailbox=data.get("OriginalPrivateMailbox", ""),
            original_results=data.get("OriginalResults", ""),
            original_state=data.get("OriginalState", ""),
            original_state_name=data.get("OriginalStateName", ""),
            original_suite=data.get("OriginalSuite", ""),
            original_urbanization=data.get("OriginalUrbanization", ""),
            address_delivery_installation=data.get("AddressDeliveryInstallation", ""),
            address_house_number=data.get("AddressHouseNumber", ""),
            address_lock_box=data.get("AddressLockBox", ""),
            address_post_direction=data.get("AddressPostDirection", ""),
            address_pre_direction=data.get("AddressPreDirection", ""),
            address_private_mailbox_name=data.get("AddressPrivateMailboxName", ""),
            address_private_mailbox_range=data.get("AddressPrivateMailboxRange", ""),
            address_route_service=data.get("AddressRouteService", ""),
            address_street_name=data.get("AddressStreetName", ""),
            address_street_suffix=data.get("AddressStreetSuffix", ""),
            address_suite_name=data.get("AddressSuiteName", ""),
            address_suite_number=data.get("AddressSuiteNumber", ""),
            standardized_address_line_1=data.get("StandardizedAddressLine1", ""),
            standardized_address_line_2=data.get("StandardizedAddressLine2", ""),
            standardized_base_melissa_address_key=data.get("StandardizedBaseMelissaAddressKey", ""),
            standardized_carrier_route=data.get("StandardizedCarrierRoute", ""),
            standardized_city=data.get("StandardizedCity", ""),
            standardized_city_abbreviation=data.get("StandardizedCityAbbreviation", ""),
            standardized_country_code=data.get("StandardizedCountryCode", ""),
            standardized_delivery_indicator=data.get("StandardizedDeliveryIndicator", ""),
            standardized_delivery_point_check_digit=data.get("StandardizedDeliveryPointCheckDigit", ""),
            standardized_delivery_point_code=data.get("StandardizedDeliveryPointCode", ""),
            standardized_melissa_address_key=data.get("StandardizedMelissaAddressKey", ""),
            standardized_plus4=data.get("StandardizedPlus4", ""),
            standardized_postal_code=data.get("StandardizedPostalCode", ""),
            standardized_private_mailbox=data.get("StandardizedPrivateMailbox", ""),
            standardized_results=data.get("StandardizedResults", ""),
            standardized_state=data.get("StandardizedState", ""),
            standardized_state_name=data.get("StandardizedStateName", ""),
            standardized_suite=data.get("StandardizedSuite", ""),
            standardized_urbanization=data.get("StandardizedUrbanization", ""),
            dpv_foot_notes=data.get("DPVFootNotes", ""),
            move_return_code=data.get("MoveReturnCode", ""),
            plus4=data.get("Plus4", ""),
            private_mailbox=data.get("PrivateMailbox", ""),
            suite=data.get("Suite", ""),
        )
    
    # Setters
    def set_address_extras(self, address_extras):
        self.address_extras = address_extras

    def set_address_key(self, address_key):
        self.address_key = address_key

    def set_address_line_1(self, address_line_1):
        self.address_line_1 = address_line_1

    def set_address_line_2(self, address_line_2):
        self.address_line_2 = address_line_2

    def set_address_type_code(self, address_type_code):
        self.address_type_code = address_type_code

    def set_base_melissa_address_key(self, base_melissa_address_key):
        self.base_melissa_address_key = base_melissa_address_key

    def set_carrier_route(self, carrier_route):
        self.carrier_route = carrier_route

    def set_city(self, city):
        self.city = city

    def set_city_abbreviation(self, city_abbreviation):
        self.city_abbreviation = city_abbreviation

    def set_company_name(self, company_name):
        self.company_name = company_name

    def set_country_code(self, country_code):
        self.country_code = country_code

    def set_country_name(self, country_name):
        self.country_name = country_name

    def set_delivery_indicator(self, delivery_indicator):
        self.delivery_indicator = delivery_indicator

    def set_delivery_point_check_digit(self, delivery_point_check_digit):
        self.delivery_point_check_digit = delivery_point_check_digit

    def set_delivery_point_code(self, delivery_point_code):
        self.delivery_point_code = delivery_point_code

    def set_melissa_address_key(self, melissa_address_key):
        self.melissa_address_key = melissa_address_key

    def set_move_effective_date(self, move_effective_date):
        self.move_effective_date = move_effective_date

    def set_move_type_code(self, move_type_code):
        self.move_type_code = move_type_code

    def set_postal_code(self, postal_code):
        self.postal_code = postal_code

    def set_record_id(self, record_id):
        self.record_id = record_id

    def set_results(self, results):
        self.results = results

    def set_state(self, state):
        self.state = state

    def set_state_name(self, state_name):
        self.state_name = state_name

    def set_urbanization(self, urbanization):
        self.urbanization = urbanization

    def set_name_first(self, name_first):
        self.name_first = name_first

    def set_name_full(self, name_full):
        self.name_full = name_full

    def set_name_last(self, name_last):
        self.name_last = name_last

    def set_name_middle(self, name_middle):
        self.name_middle = name_middle

    def set_name_prefix(self, name_prefix):
        self.name_prefix = name_prefix

    def set_name_suffix(self, name_suffix):
        self.name_suffix = name_suffix

    def set_original_address_line_1(self, original_address_line_1):
        self.original_address_line_1 = original_address_line_1

    def set_original_address_line_2(self, original_address_line_2):
        self.original_address_line_2 = original_address_line_2

    def set_original_city(self, original_city):
        self.original_city = original_city

    def set_original_city_abbreviation(self, original_city_abbreviation):
        self.original_city_abbreviation = original_city_abbreviation

    def set_original_country_code(self, original_country_code):
        self.original_country_code = original_country_code

    def set_original_plus4(self, original_plus4):
        self.original_plus4 = original_plus4

    def set_original_postal_code(self, original_postal_code):
        self.original_postal_code = original_postal_code

    def set_original_private_mailbox(self, original_private_mailbox):
        self.original_private_mailbox = original_private_mailbox

    def set_original_results(self, original_results):
        self.original_results = original_results

    def set_original_state(self, original_state):
        self.original_state = original_state

    def set_original_state_name(self, original_state_name):
        self.original_state_name = original_state_name

    def set_original_suite(self, original_suite):
        self.original_suite = original_suite

    def set_original_urbanization(self, original_urbanization):
        self.original_urbanization = original_urbanization

    def set_address_delivery_installation(self, address_delivery_installation):
        self.address_delivery_installation = address_delivery_installation

    def set_address_house_number(self, address_house_number):
        self.address_house_number = address_house_number

    def set_address_lock_box(self, address_lock_box):
        self.address_lock_box = address_lock_box

    def set_address_post_direction(self, address_post_direction):
        self.address_post_direction = address_post_direction

    def set_address_pre_direction(self, address_pre_direction):
        self.address_pre_direction = address_pre_direction

    def set_address_private_mailbox_name(self, address_private_mailbox_name):
        self.address_private_mailbox_name = address_private_mailbox_name

    def set_address_private_mailbox_range(self, address_private_mailbox_range):
        self.address_private_mailbox_range = address_private_mailbox_range

    def set_address_route_service(self, address_route_service):
        self.address_route_service = address_route_service

    def set_address_street_name(self, address_street_name):
        self.address_street_name = address_street_name

    def set_address_street_suffix(self, address_street_suffix):
        self.address_street_suffix = address_street_suffix

    def set_address_suite_name(self, address_suite_name):
        self.address_suite_name = address_suite_name

    def set_address_suite_number(self, address_suite_number):
        self.address_suite_number = address_suite_number

    def set_standardized_address_line_1(self, standardized_address_line_1):
        self.standardized_address_line_1 = standardized_address_line_1

    def set_standardized_address_line_2(self, standardized_address_line_2):
        self.standardized_address_line_2 = standardized_address_line_2

    def set_standardized_base_melissa_address_key(self, standardized_base_melissa_address_key):
        self.standardized_base_melissa_address_key = standardized_base_melissa_address_key

    def set_standardized_carrier_route(self, standardized_carrier_route):
        self.standardized_carrier_route = standardized_carrier_route

    def set_standardized_city(self, standardized_city):
        self.standardized_city = standardized_city

    def set_standardized_city_abbreviation(self, standardized_city_abbreviation):
        self.standardized_city_abbreviation = standardized_city_abbreviation

    def set_standardized_country_code(self, standardized_country_code):
        self.standardized_country_code = standardized_country_code

    def set_standardized_delivery_indicator(self, standardized_delivery_indicator):
        self.standardized_delivery_indicator = standardized_delivery_indicator

    def set_standardized_delivery_point_check_digit(self, standardized_delivery_point_check_digit):
        self.standardized_delivery_point_check_digit = standardized_delivery_point_check_digit

    def set_standardized_delivery_point_code(self, standardized_delivery_point_code):
        self.standardized_delivery_point_code = standardized_delivery_point_code

    def set_standardized_melissa_address_key(self, standardized_melissa_address_key):
        self.standardized_melissa_address_key = standardized_melissa_address_key

    def set_standardized_plus4(self, standardized_plus4):
        self.standardized_plus4 = standardized_plus4

    def set_standardized_postal_code(self, standardized_postal_code):
        self.standardized_postal_code = standardized_postal_code

    def set_standardized_private_mailbox(self, standardized_private_mailbox):
        self.standardized_private_mailbox = standardized_private_mailbox

    def set_standardized_results(self, standardized_results):
        self.standardized_results = standardized_results

    def set_standardized_state(self, standardized_state):
        self.standardized_state = standardized_state

    def set_standardized_state_name(self, standardized_state_name):
        self.standardized_state_name = standardized_state_name

    def set_standardized_suite(self, standardized_suite):
        self.standardized_suite = standardized_suite

    def set_standardized_urbanization(self, standardized_urbanization):
        self.standardized_urbanization = standardized_urbanization

    def set_dpv_foot_notes(self, dpv_foot_notes):
        self.dpv_foot_notes = dpv_foot_notes

    def set_move_return_code(self, move_return_code):
        self.move_return_code = move_return_code

    def set_plus4(self, plus4):
        self.plus4 = plus4

    def set_private_mailbox(self, private_mailbox):
        self.private_mailbox = private_mailbox

    def set_suite(self, suite):
        self.suite = suite

    # Getters
    def get_address_extras(self):
        return self.address_extras or ""

    def get_address_key(self):
        return self.address_key or ""

    def get_address_line_1(self):
        return self.address_line_1 or ""

    def get_address_line_2(self):
        return self.address_line_2 or ""

    def get_address_type_code(self):
        return self.address_type_code or ""

    def get_base_melissa_address_key(self):
        return self.base_melissa_address_key or ""

    def get_carrier_route(self):
        return self.carrier_route or ""

    def get_city(self):
        return self.city or ""

    def get_city_abbreviation(self):
        return self.city_abbreviation or ""

    def get_company_name(self):
        return self.company_name or ""

    def get_country_code(self):
        return self.country_code or ""

    def get_country_name(self):
        return self.country_name or ""

    def get_delivery_indicator(self):
        return self.delivery_indicator or ""

    def get_delivery_point_check_digit(self):
        return self.delivery_point_check_digit or ""

    def get_delivery_point_code(self):
        return self.delivery_point_code or ""

    def get_melissa_address_key(self):
        return self.melissa_address_key or ""

    def get_move_effective_date(self):
        return self.move_effective_date or ""

    def get_move_type_code(self):
        return self.move_type_code or ""

    def get_postal_code(self):
        return self.postal_code or ""

    def get_record_id(self):
        return self.record_id or ""

    def get_results(self):
        return self.results or ""

    def get_state(self):
        return self.state or ""

    def get_state_name(self):
        return self.state_name or ""

    def get_urbanization(self):
        return self.urbanization or ""

    def get_name_first(self):
        return self.name_first or ""

    def get_name_full(self):
        return self.name_full or ""

    def get_name_last(self):
        return self.name_last or ""

    def get_name_middle(self):
        return self.name_middle or ""

    def get_name_prefix(self):
        return self.name_prefix or ""

    def get_name_suffix(self):
        return self.name_suffix or ""

    def get_original_address_line_1(self):
        return self.original_address_line_1 or ""

    def get_original_address_line_2(self):
        return self.original_address_line_2 or ""

    def get_original_city(self):
        return self.original_city or ""

    def get_original_city_abbreviation(self):
        return self.original_city_abbreviation or ""

    def get_original_country_code(self):
        return self.original_country_code or ""

    def get_original_plus4(self):
        return self.original_plus4 or ""

    def get_original_postal_code(self):
        return self.original_postal_code or ""

    def get_original_private_mailbox(self):
        return self.original_private_mailbox or ""

    def get_original_results(self):
        return self.original_results or ""

    def get_original_state(self):
        return self.original_state or ""

    def get_original_state_name(self):
        return self.original_state_name or ""

    def get_original_suite(self):
        return self.original_suite or ""

    def get_original_urbanization(self):
        return self.original_urbanization or ""

    def get_address_delivery_installation(self):
        return self.address_delivery_installation or ""

    def get_address_house_number(self):
        return self.address_house_number or ""

    def get_address_lock_box(self):
        return self.address_lock_box or ""

    def get_address_post_direction(self):
        return self.address_post_direction or ""

    def get_address_pre_direction(self):
        return self.address_pre_direction or ""

    def get_address_private_mailbox_name(self):
        return self.address_private_mailbox_name or ""

    def get_address_private_mailbox_range(self):
        return self.address_private_mailbox_range or ""

    def get_address_route_service(self):
        return self.address_route_service or ""

    def get_address_street_name(self):
        return self.address_street_name or ""

    def get_address_street_suffix(self):
        return self.address_street_suffix or ""

    def get_address_suite_name(self):
        return self.address_suite_name or ""

    def get_address_suite_number(self):
        return self.address_suite_number or ""

    def get_standardized_address_line_1(self):
        return self.standardized_address_line_1 or ""

    def get_standardized_address_line_2(self):
        return self.standardized_address_line_2 or ""

    def get_standardized_base_melissa_address_key(self):
        return self.standardized_base_melissa_address_key or ""

    def get_standardized_carrier_route(self):
        return self.standardized_carrier_route or ""

    def get_standardized_city(self):
        return self.standardized_city or ""

    def get_standardized_city_abbreviation(self):
        return self.standardized_city_abbreviation or ""

    def get_standardized_country_code(self):
        return self.standardized_country_code or ""

    def get_standardized_delivery_indicator(self):
        return self.standardized_delivery_indicator or ""

    def get_standardized_delivery_point_check_digit(self):
        return self.standardized_delivery_point_check_digit or ""

    def get_standardized_delivery_point_code(self):
        return self.standardized_delivery_point_code or ""

    def get_standardized_melissa_address_key(self):
        return self.standardized_melissa_address_key or ""

    def get_standardized_plus4(self):
        return self.standardized_plus4 or ""

    def get_standardized_postal_code(self):
        return self.standardized_postal_code or ""

    def get_standardized_private_mailbox(self):
        return self.standardized_private_mailbox or ""

    def get_standardized_results(self):
        return self.standardized_results or ""

    def get_standardized_state(self):
        return self.standardized_state or ""

    def get_standardized_state_name(self):
        return self.standardized_state_name or ""

    def get_standardized_suite(self):
        return self.standardized_suite or ""

    def get_standardized_urbanization(self):
        return self.standardized_urbanization or ""

    def get_dpv_foot_notes(self):
        return self.dpv_foot_notes or ""

    def get_move_return_code(self):
        return self.move_return_code or ""

    def get_plus4(self):
        return self.plus4 or ""

    def get_private_mailbox(self):
        return self.private_mailbox or ""

    def get_suite(self):
        return self.suite or ""




    