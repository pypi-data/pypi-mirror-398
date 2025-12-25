from .ResponseBase import ResponseBase

class PersonatorConsumerResponse(ResponseBase):
    def __init__(self, version="", transmission_reference="", transmission_results="", total_records="", records=None):
        self.version = version
        self.transmission_reference = transmission_reference
        self.transmission_results = transmission_results
        self.total_records = total_records
        self.records = records if records is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        records = [PersonatorConsumerRecord.from_dict(record) for record in data.get("Records", [])]
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
    
class PersonatorConsumerRecord(ResponseBase):
    def __init__(self, address_delivery_installation="", address_extras="", address_house_number="", address_key="",
                 address_line_1="", address_line_2="", address_lock_box="", address_post_direction="", 
                 address_pre_direction="", address_private_mailbox_name="", address_private_mailbox_range="",
                 address_route_service="", address_street_name="", address_street_suffix="", address_suite_name="",
                 address_suite_number="", address_type_code="", area_code="", cbsacode="", cbsadivision_code="",
                 cbsadivision_level="", cbsadivision_title="", cbsalevel="", cbsatitle="", carrier_route="",
                 census_block="", census_key="", census_tract="", children_age_range="", city="", city_abbreviation="",
                 company_name="", congressional_district="", country_code="", country_name="", county_fips="",
                 county_name="", county_subdivision_code="", county_subdivision_name="", credit_card_user="",
                 date_last_confirmed="", date_of_birth="", date_of_death="", delivery_indicator="", 
                 delivery_point_check_digit="", delivery_point_code="", demographics_gender="", demographics_results="",
                 distance_address_to_ip="", domain_name="", education="", elementary_school_district_code="",
                 elementary_school_district_name="", email_address="", estimated_home_value="", ethnic_code="", 
                 ethnic_group="", gender="", gender2="", household_income="", household_size="", ip_address="",
                 ip_city="", ip_connection_speed="", ip_connection_type="", ip_continent="", 
                 ip_country_abbreviation="", ip_country_name="", ip_domain_name="", ip_isp_name="", 
                 ip_latitude="", ip_longitude="", ip_postal_code="", ip_proxy_description="", ip_proxy_type="",
                 ip_region="", ip_utc="", latitude="", length_of_residence="", longitude="", mailbox_name="",
                 marital_status="", melissa_address_key="", melissa_address_key_base="", melissa_identity_key="",
                 move_date="", name_first="", name_first2="", name_full="", name_last="", name_last2="", name_middle="",
                 name_middle2="", name_prefix="", name_prefix2="", name_suffix="", name_suffix2="", new_area_code="",
                 occupation="", own_rent="", phone_country_code="", phone_country_name="", phone_extension="",
                 phone_number="", phone_prefix="", phone_suffix="", place_code="", place_name="", plus4="",
                 political_party="", postal_code="", presence_of_children="", presence_of_senior="", private_mail_box="",
                 record_id="", results="", salutation="", secondary_school_district_code="", 
                 secondary_school_district_name="", state="", state_district_lower="", state_district_upper="",
                 state_name="", suite="", top_level_domain="", utc="", unified_school_district_code="",
                 unified_school_district_name="", record_extras="", reserved=""):
        self.address_delivery_installation = address_delivery_installation
        self.address_extras = address_extras
        self.address_house_number = address_house_number
        self.address_key = address_key
        self.address_line_1 = address_line_1
        self.address_line_2 = address_line_2
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
        self.address_type_code = address_type_code
        self.area_code = area_code
        self.cbsacode = cbsacode
        self.cbsadivision_code = cbsadivision_code
        self.cbsadivision_level = cbsadivision_level
        self.cbsadivision_title = cbsadivision_title
        self.cbsalevel = cbsalevel
        self.cbsatitle = cbsatitle
        self.carrier_route = carrier_route
        self.census_block = census_block
        self.census_key = census_key
        self.census_tract = census_tract
        self.children_age_range = children_age_range
        self.city = city
        self.city_abbreviation = city_abbreviation
        self.company_name = company_name
        self.congressional_district = congressional_district
        self.country_code = country_code
        self.country_name = country_name
        self.county_fips = county_fips
        self.county_name = county_name
        self.county_subdivision_code = county_subdivision_code
        self.county_subdivision_name = county_subdivision_name
        self.credit_card_user = credit_card_user
        self.date_last_confirmed = date_last_confirmed
        self.date_of_birth = date_of_birth
        self.date_of_death = date_of_death
        self.delivery_indicator = delivery_indicator
        self.delivery_point_check_digit = delivery_point_check_digit
        self.delivery_point_code = delivery_point_code
        self.demographics_gender = demographics_gender
        self.demographics_results = demographics_results
        self.distance_address_to_ip = distance_address_to_ip
        self.domain_name = domain_name
        self.education = education
        self.elementary_school_district_code = elementary_school_district_code
        self.elementary_school_district_name = elementary_school_district_name
        self.email_address = email_address
        self.estimated_home_value = estimated_home_value
        self.ethnic_code = ethnic_code
        self.ethnic_group = ethnic_group
        self.gender = gender
        self.gender2 = gender2
        self.household_income = household_income
        self.household_size = household_size
        self.ip_address = ip_address
        self.ip_city = ip_city
        self.ip_connection_speed = ip_connection_speed
        self.ip_connection_type = ip_connection_type
        self.ip_continent = ip_continent
        self.ip_country_abbreviation = ip_country_abbreviation
        self.ip_country_name = ip_country_name
        self.ip_domain_name = ip_domain_name
        self.ip_isp_name = ip_isp_name
        self.ip_latitude = ip_latitude
        self.ip_longitude = ip_longitude
        self.ip_postal_code = ip_postal_code
        self.ip_proxy_description = ip_proxy_description
        self.ip_proxy_type = ip_proxy_type
        self.ip_region = ip_region
        self.ip_utc = ip_utc
        self.latitude = latitude
        self.length_of_residence = length_of_residence
        self.longitude = longitude
        self.mailbox_name = mailbox_name
        self.marital_status = marital_status
        self.melissa_address_key = melissa_address_key
        self.melissa_address_key_base = melissa_address_key_base
        self.melissa_identity_key = melissa_identity_key
        self.move_date = move_date
        self.name_first = name_first
        self.name_first2 = name_first2
        self.name_full = name_full
        self.name_last = name_last
        self.name_last2 = name_last2
        self.name_middle = name_middle
        self.name_middle2 = name_middle2
        self.name_prefix = name_prefix
        self.name_prefix2 = name_prefix2
        self.name_suffix = name_suffix
        self.name_suffix2 = name_suffix2
        self.new_area_code = new_area_code
        self.occupation = occupation
        self.own_rent = own_rent
        self.phone_country_code = phone_country_code
        self.phone_country_name = phone_country_name
        self.phone_extension = phone_extension
        self.phone_number = phone_number
        self.phone_prefix = phone_prefix
        self.phone_suffix = phone_suffix
        self.place_code = place_code
        self.place_name = place_name
        self.plus4 = plus4
        self.political_party = political_party
        self.postal_code = postal_code
        self.presence_of_children = presence_of_children
        self.presence_of_senior = presence_of_senior
        self.private_mail_box = private_mail_box
        self.record_id = record_id
        self.results = results
        self.salutation = salutation
        self.secondary_school_district_code = secondary_school_district_code
        self.secondary_school_district_name = secondary_school_district_name
        self.state = state
        self.state_district_lower = state_district_lower
        self.state_district_upper = state_district_upper
        self.state_name = state_name
        self.suite = suite
        self.top_level_domain = top_level_domain
        self.utc = utc
        self.unified_school_district_code = unified_school_district_code
        self.unified_school_district_name = unified_school_district_name
        self.record_extras = record_extras
        self.reserved = reserved

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            address_delivery_installation=data.get("AddressDeliveryInstallation", ""),
            address_extras=data.get("AddressExtras", ""),
            address_house_number=data.get("AddressHouseNumber", ""),
            address_key=data.get("AddressKey", ""),
            address_line_1=data.get("AddressLine1", ""),
            address_line_2=data.get("AddressLine2", ""),
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
            address_type_code=data.get("AddressTypeCode", ""),
            area_code=data.get("AreaCode", ""),
            cbsacode=data.get("CBSACode", ""),
            cbsadivision_code=data.get("CBSADivisionCode", ""),
            cbsadivision_level=data.get("CBSADivisionLevel", ""),
            cbsadivision_title=data.get("CBSADivisionTitle", ""),
            cbsalevel=data.get("CBSALevel", ""),
            cbsatitle=data.get("CBSATitle", ""),
            carrier_route=data.get("CarrierRoute", ""),
            census_block=data.get("CensusBlock", ""),
            census_key=data.get("CensusKey", ""),
            census_tract=data.get("CensusTract", ""),
            children_age_range=data.get("ChildrenAgeRange", ""),
            city=data.get("City", ""),
            city_abbreviation=data.get("CityAbbreviation", ""),
            company_name=data.get("CompanyName", ""),
            congressional_district=data.get("CongressionalDistrict", ""),
            country_code=data.get("CountryCode", ""),
            country_name=data.get("CountryName", ""),
            county_fips=data.get("CountyFIPS", ""),
            county_name=data.get("CountyName", ""),
            county_subdivision_code=data.get("CountySubdivisionCode", ""),
            county_subdivision_name=data.get("CountySubdivisionName", ""),
            credit_card_user=data.get("CreditCardUser", ""),
            date_last_confirmed=data.get("DateLastConfirmed", ""),
            date_of_birth=data.get("DateOfBirth", ""),
            date_of_death=data.get("DateOfDeath", ""),
            delivery_indicator=data.get("DeliveryIndicator", ""),
            delivery_point_check_digit=data.get("DeliveryPointCheckDigit", ""),
            delivery_point_code=data.get("DeliveryPointCode", ""),
            demographics_gender=data.get("DemographicsGender", ""),
            demographics_results=data.get("DemographicsResults", ""),
            distance_address_to_ip=data.get("DistanceAddressToIP", ""),
            domain_name=data.get("DomainName", ""),
            education=data.get("Education", ""),
            elementary_school_district_code=data.get("ElementarySchoolDistrictCode", ""),
            elementary_school_district_name=data.get("ElementarySchoolDistrictName", ""),
            email_address=data.get("EmailAddress", ""),
            estimated_home_value=data.get("EstimatedHomeValue", ""),
            ethnic_code=data.get("EthnicCode", ""),
            ethnic_group=data.get("EthnicGroup", ""),
            gender=data.get("Gender", ""),
            gender2=data.get("Gender2", ""),
            household_income=data.get("HouseholdIncome", ""),
            household_size=data.get("HouseholdSize", ""),
            ip_address=data.get("IPAddress", ""),
            ip_city=data.get("IPCity", ""),
            ip_connection_speed=data.get("IPConnectionSpeed", ""),
            ip_connection_type=data.get("IPConnectionType", ""),
            ip_continent=data.get("IPContinent", ""),
            ip_country_abbreviation=data.get("IPCountryAbbreviation", ""),
            ip_country_name=data.get("IPCountryName", ""),
            ip_domain_name=data.get("IPDomainName", ""),
            ip_isp_name=data.get("IPISPName", ""),
            ip_latitude=data.get("IPLatitude", ""),
            ip_longitude=data.get("IPLongitude", ""),
            ip_postal_code=data.get("IPPostalCode", ""),
            ip_proxy_description=data.get("IPProxyDescription", ""),
            ip_proxy_type=data.get("IPProxyType", ""),
            ip_region=data.get("IPRegion", ""),
            ip_utc=data.get("IPUTC", ""),
            latitude=data.get("Latitude", ""),
            length_of_residence=data.get("LengthOfResidence", ""),
            longitude=data.get("Longitude", ""),
            mailbox_name=data.get("MailboxName", ""),
            marital_status=data.get("MaritalStatus", ""),
            melissa_address_key=data.get("MelissaAddressKey", ""),
            melissa_address_key_base=data.get("MelissaAddressKeyBase", ""),
            melissa_identity_key=data.get("MelissaIdentityKey", ""),
            move_date=data.get("MoveDate", ""),
            name_first=data.get("NameFirst", ""),
            name_first2=data.get("NameFirst2", ""),
            name_full=data.get("NameFull", ""),
            name_last=data.get("NameLast", ""),
            name_last2=data.get("NameLast2", ""),
            name_middle=data.get("NameMiddle", ""),
            name_middle2=data.get("NameMiddle2", ""),
            name_prefix=data.get("NamePrefix", ""),
            name_prefix2=data.get("NamePrefix2", ""),
            name_suffix=data.get("NameSuffix", ""),
            name_suffix2=data.get("NameSuffix2", ""),
            new_area_code=data.get("NewAreaCode", ""),
            occupation=data.get("Occupation", ""),
            own_rent=data.get("OwnRent", ""),
            phone_country_code=data.get("PhoneCountryCode", ""),
            phone_country_name=data.get("PhoneCountryName", ""),
            phone_extension=data.get("PhoneExtension", ""),
            phone_number=data.get("PhoneNumber", ""),
            phone_prefix=data.get("PhonePrefix", ""),
            phone_suffix=data.get("PhoneSuffix", ""),
            place_code=data.get("PlaceCode", ""),
            place_name=data.get("PlaceName", ""),
            plus4=data.get("Plus4", ""),
            political_party=data.get("PoliticalParty", ""),
            postal_code=data.get("PostalCode", ""),
            presence_of_children=data.get("PresenceOfChildren", ""),
            presence_of_senior=data.get("PresenceOfSenior", ""),
            private_mail_box=data.get("PrivateMailBox", ""),
            record_id=data.get("RecordID", ""),
            results=data.get("Results", ""),
            salutation=data.get("Salutation", ""),
            secondary_school_district_code=data.get("SecondarySchoolDistrictCode", ""),
            secondary_school_district_name=data.get("SecondarySchoolDistrictName", ""),
            state=data.get("State", ""),
            state_district_lower=data.get("StateDistrictLower", ""),
            state_district_upper=data.get("StateDistrictUpper", ""),
            state_name=data.get("StateName", ""),
            suite=data.get("Suite", ""),
            top_level_domain=data.get("TopLevelDomain", ""),
            utc=data.get("UTC", ""),
            unified_school_district_code=data.get("UnifiedSchoolDistrictCode", ""),
            unified_school_district_name=data.get("UnifiedSchoolDistrictName", ""),
            record_extras=data.get("RecordExtras", ""),
            reserved=data.get("Reserved", "")
        )
    
    # Setters

    def set_address_delivery_installation(self, address_delivery_installation):
        self.address_delivery_installation = address_delivery_installation

    def set_address_extras(self, address_extras):
        self.address_extras = address_extras

    def set_address_house_number(self, address_house_number):
        self.address_house_number = address_house_number

    def set_address_key(self, address_key):
        self.address_key = address_key

    def set_address_line_1(self, address_line_1):
        self.address_line_1 = address_line_1

    def set_address_line_2(self, address_line_2):
        self.address_line_2 = address_line_2

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

    def set_address_type_code(self, address_type_code):
        self.address_type_code = address_type_code

    def set_area_code(self, area_code):
        self.area_code = area_code

    def set_cbsa_code(self, cbsa_code):
        self.cbsa_code = cbsa_code

    def set_cbsa_division_code(self, cbsa_division_code):
        self.cbsa_division_code = cbsa_division_code

    def set_cbsa_division_level(self, cbsa_division_level):
        self.cbsa_division_level = cbsa_division_level

    def set_cbsa_division_title(self, cbsa_division_title):
        self.cbsa_division_title = cbsa_division_title

    def set_cbsa_level(self, cbsa_level):
        self.cbsa_level = cbsa_level

    def set_cbsa_title(self, cbsa_title):
        self.cbsa_title = cbsa_title

    def set_carrier_route(self, carrier_route):
        self.carrier_route = carrier_route

    def set_census_block(self, census_block):
        self.census_block = census_block

    def set_census_key(self, census_key):
        self.census_key = census_key

    def set_census_tract(self, census_tract):
        self.census_tract = census_tract

    def set_children_age_range(self, children_age_range):
        self.children_age_range = children_age_range

    def set_city(self, city):
        self.city = city

    def set_city_abbreviation(self, city_abbreviation):
        self.city_abbreviation = city_abbreviation

    def set_company_name(self, company_name):
        self.company_name = company_name

    def set_congressional_district(self, congressional_district):
        self.congressional_district = congressional_district

    def set_country_code(self, country_code):
        self.country_code = country_code

    def set_country_name(self, country_name):
        self.country_name = country_name

    def set_county_fips(self, county_fips):
        self.county_fips = county_fips

    def set_county_name(self, county_name):
        self.county_name = county_name

    def set_county_subdivision_code(self, county_subdivision_code):
        self.county_subdivision_code = county_subdivision_code

    def set_county_subdivision_name(self, county_subdivision_name):
        self.county_subdivision_name = county_subdivision_name

    def set_credit_card_user(self, credit_card_user):
        self.credit_card_user = credit_card_user

    def set_date_last_confirmed(self, date_last_confirmed):
        self.date_last_confirmed = date_last_confirmed

    def set_date_of_birth(self, date_of_birth):
        self.date_of_birth = date_of_birth

    def set_date_of_death(self, date_of_death):
        self.date_of_death = date_of_death

    def set_delivery_indicator(self, delivery_indicator):
        self.delivery_indicator = delivery_indicator

    def set_delivery_point_check_digit(self, delivery_point_check_digit):
        self.delivery_point_check_digit = delivery_point_check_digit

    def set_delivery_point_code(self, delivery_point_code):
        self.delivery_point_code = delivery_point_code

    def set_demographics_gender(self, demographics_gender):
        self.demographics_gender = demographics_gender

    def set_demographics_results(self, demographics_results):
        self.demographics_results = demographics_results

    def set_distance_address_to_ip(self, distance_address_to_ip):
        self.distance_address_to_ip = distance_address_to_ip

    def set_domain_name(self, domain_name):
        self.domain_name = domain_name

    def set_education(self, education):
        self.education = education

    def set_elementary_school_district_code(self, elementary_school_district_code):
        self.elementary_school_district_code = elementary_school_district_code

    def set_elementary_school_district_name(self, elementary_school_district_name):
        self.elementary_school_district_name = elementary_school_district_name

    def set_email_address(self, email_address):
        self.email_address = email_address

    def set_estimated_home_value(self, estimated_home_value):
        self.estimated_home_value = estimated_home_value

    def set_ethnic_code(self, ethnic_code):
        self.ethnic_code = ethnic_code

    def set_ethnic_group(self, ethnic_group):
        self.ethnic_group = ethnic_group

    def set_gender(self, gender):
        self.gender = gender

    def set_gender2(self, gender2):
        self.gender2 = gender2

    def set_household_income(self, household_income):
        self.household_income = household_income

    def set_household_size(self, household_size):
        self.household_size = household_size

    def set_ip_address(self, ip_address):
        self.ip_address = ip_address

    def set_ip_city(self, ip_city):
        self.ip_city = ip_city

    def set_ip_connection_speed(self, ip_connection_speed):
        self.ip_connection_speed = ip_connection_speed

    def set_ip_connection_type(self, ip_connection_type):
        self.ip_connection_type = ip_connection_type

    def set_ip_continent(self, ip_continent):
        self.ip_continent = ip_continent

    def set_ip_country_abbreviation(self, ip_country_abbreviation):
        self.ip_country_abbreviation = ip_country_abbreviation

    def set_ip_country_name(self, ip_country_name):
        self.ip_country_name = ip_country_name

    def set_ip_domain_name(self, ip_domain_name):
        self.ip_domain_name = ip_domain_name

    def set_ip_isp_name(self, ip_isp_name):
        self.ip_isp_name = ip_isp_name

    def set_ip_latitude(self, ip_latitude):
        self.ip_latitude = ip_latitude

    def set_ip_longitude(self, ip_longitude):
        self.ip_longitude = ip_longitude

    def set_ip_postal_code(self, ip_postal_code):
        self.ip_postal_code = ip_postal_code

    def set_ip_proxy_description(self, ip_proxy_description):
        self.ip_proxy_description = ip_proxy_description

    def set_ip_proxy_type(self, ip_proxy_type):
        self.ip_proxy_type = ip_proxy_type

    def set_ip_region(self, ip_region):
        self.ip_region = ip_region

    def set_ip_utc(self, ip_utc):
        self.ip_utc = ip_utc

    def set_latitude(self, latitude):
        self.latitude = latitude

    def set_length_of_residence(self, length_of_residence):
        self.length_of_residence = length_of_residence

    def set_longitude(self, longitude):
        self.longitude = longitude

    def set_mailbox_name(self, mailbox_name):
        self.mailbox_name = mailbox_name

    def set_marital_status(self, marital_status):
        self.marital_status = marital_status

    def set_melissa_address_key(self, melissa_address_key):
        self.melissa_address_key = melissa_address_key

    def set_melissa_address_key_base(self, melissa_address_key_base):
        self.melissa_address_key_base = melissa_address_key_base

    def set_melissa_identity_key(self, melissa_identity_key):
        self.melissa_identity_key = melissa_identity_key

    def set_move_date(self, move_date):
        self.move_date = move_date

    def set_name_first(self, name_first):
        self.name_first = name_first

    def set_name_first2(self, name_first2):
        self.name_first2 = name_first2

    def set_name_full(self, name_full):
        self.name_full = name_full

    def set_name_last(self, name_last):
        self.name_last = name_last

    def set_name_last2(self, name_last2):
        self.name_last2 = name_last2

    def set_name_middle(self, name_middle):
        self.name_middle = name_middle

    def set_name_middle2(self, name_middle2):
        self.name_middle2 = name_middle2

    def set_name_prefix(self, name_prefix):
        self.name_prefix = name_prefix

    def set_name_prefix2(self, name_prefix2):
        self.name_prefix2 = name_prefix2

    def set_name_suffix(self, name_suffix):
        self.name_suffix = name_suffix

    def set_name_suffix2(self, name_suffix2):
        self.name_suffix2 = name_suffix2

    def set_new_area_code(self, new_area_code):
        self.new_area_code = new_area_code

    def set_occupation(self, occupation):
        self.occupation = occupation

    def set_own_rent(self, own_rent):
        self.own_rent = own_rent

    def set_phone_country_code(self, phone_country_code):
        self.phone_country_code = phone_country_code

    def set_phone_country_name(self, phone_country_name):
        self.phone_country_name = phone_country_name

    def set_phone_extension(self, phone_extension):
        self.phone_extension = phone_extension

    def set_phone_number(self, phone_number):
        self.phone_number = phone_number

    def set_phone_prefix(self, phone_prefix):
        self.phone_prefix = phone_prefix

    def set_phone_suffix(self, phone_suffix):
        self.phone_suffix = phone_suffix

    def set_place_code(self, place_code):
        self.place_code = place_code

    def set_place_name(self, place_name):
        self.place_name = place_name

    def set_plus4(self, plus4):
        self.plus4 = plus4

    def set_political_party(self, political_party):
        self.political_party = political_party

    def set_postal_code(self, postal_code):
        self.postal_code = postal_code

    def set_presence_of_children(self, presence_of_children):
        self.presence_of_children = presence_of_children

    def set_presence_of_senior(self, presence_of_senior):
        self.presence_of_senior = presence_of_senior

    def set_private_mail_box(self, private_mail_box):
        self.private_mail_box = private_mail_box

    def set_record_id(self, record_id):
        self.record_id = record_id

    def set_results(self, results):
        self.results = results

    def set_salutation(self, salutation):
        self.salutation = salutation

    def set_secondary_school_district_code(self, secondary_school_district_code):
        self.secondary_school_district_code = secondary_school_district_code

    def set_secondary_school_district_name(self, secondary_school_district_name):
        self.secondary_school_district_name = secondary_school_district_name

    def set_state(self, state):
        self.state = state

    def set_state_district_lower(self, state_district_lower):
        self.state_district_lower = state_district_lower

    def set_state_district_upper(self, state_district_upper):
        self.state_district_upper = state_district_upper

    def set_state_name(self, state_name):
        self.state_name = state_name

    def set_suite(self, suite):
        self.suite = suite

    def set_top_level_domain(self, top_level_domain):
        self.top_level_domain = top_level_domain

    def set_utc(self, utc):
        self.utc = utc

    def set_unified_school_district_code(self, unified_school_district_code):
        self.unified_school_district_code = unified_school_district_code

    def set_unified_school_district_name(self, unified_school_district_name):
        self.unified_school_district_name = unified_school_district_name

    def set_record_extras(self, record_extras):
        self.record_extras = record_extras

    def set_reserved(self, reserved):
        self.reserved = reserved

    # Getters

    def get_address_delivery_installation(self):
        return self.address_delivery_installation or ""

    def get_address_extras(self):
        return self.address_extras or ""

    def get_address_house_number(self):
        return self.address_house_number or ""

    def get_address_key(self):
        return self.address_key or ""

    def get_address_line_1(self):
        return self.address_line_1 or ""

    def get_address_line_2(self):
        return self.address_line_2 or ""

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

    def get_address_type_code(self):
        return self.address_type_code or ""

    def get_area_code(self):
        return self.area_code or ""

    def get_cbsa_code(self):
        return self.cbsa_code or ""

    def get_cbsa_division_code(self):
        return self.cbsa_division_code or ""

    def get_cbsa_division_level(self):
        return self.cbsa_division_level or ""

    def get_cbsa_division_title(self):
        return self.cbsa_division_title or ""

    def get_cbsa_level(self):
        return self.cbsa_level or ""

    def get_cbsa_title(self):
        return self.cbsa_title or ""

    def get_carrier_route(self):
        return self.carrier_route or ""

    def get_census_block(self):
        return self.census_block or ""

    def get_census_key(self):
        return self.census_key or ""

    def get_census_tract(self):
        return self.census_tract or ""

    def get_children_age_range(self):
        return self.children_age_range or ""

    def get_city(self):
        return self.city or ""

    def get_city_abbreviation(self):
        return self.city_abbreviation or ""

    def get_company_name(self):
        return self.company_name or ""

    def get_congressional_district(self):
        return self.congressional_district or ""

    def get_country_code(self):
        return self.country_code or ""

    def get_country_name(self):
        return self.country_name or ""

    def get_county_fips(self):
        return self.county_fips or ""

    def get_county_name(self):
        return self.county_name or ""

    def get_county_subdivision_code(self):
        return self.county_subdivision_code or ""

    def get_county_subdivision_name(self):
        return self.county_subdivision_name or ""

    def get_credit_card_user(self):
        return self.credit_card_user or ""

    def get_date_last_confirmed(self):
        return self.date_last_confirmed or ""

    def get_date_of_birth(self):
        return self.date_of_birth or ""

    def get_date_of_death(self):
        return self.date_of_death or ""

    def get_delivery_indicator(self):
        return self.delivery_indicator or ""

    def get_delivery_point_check_digit(self):
        return self.delivery_point_check_digit or ""

    def get_delivery_point_code(self):
        return self.delivery_point_code or ""

    def get_demographics_gender(self):
        return self.demographics_gender or ""

    def get_demographics_results(self):
        return self.demographics_results or ""

    def get_distance_address_to_ip(self):
        return self.distance_address_to_ip or ""

    def get_domain_name(self):
        return self.domain_name or ""

    def get_education(self):
        return self.education or ""

    def get_elementary_school_district_code(self):
        return self.elementary_school_district_code or ""

    def get_elementary_school_district_name(self):
        return self.elementary_school_district_name or ""

    def get_email_address(self):
        return self.email_address or ""

    def get_estimated_home_value(self):
        return self.estimated_home_value or ""

    def get_ethnic_code(self):
        return self.ethnic_code or ""

    def get_ethnic_group(self):
        return self.ethnic_group or ""

    def get_gender(self):
        return self.gender or ""

    def get_gender2(self):
        return self.gender2 or ""

    def get_household_income(self):
        return self.household_income or ""

    def get_household_size(self):
        return self.household_size or ""

    def get_ip_address(self):
        return self.ip_address or ""

    def get_ip_city(self):
        return self.ip_city or ""

    def get_ip_connection_speed(self):
        return self.ip_connection_speed or ""

    def get_ip_connection_type(self):
        return self.ip_connection_type or ""

    def get_ip_continent(self):
        return self.ip_continent or ""

    def get_ip_country_abbreviation(self):
        return self.ip_country_abbreviation or ""

    def get_ip_country_name(self):
        return self.ip_country_name or ""

    def get_ip_domain_name(self):
        return self.ip_domain_name or ""

    def get_ip_isp_name(self):
        return self.ip_isp_name or ""

    def get_ip_latitude(self):
        return self.ip_latitude or ""

    def get_ip_longitude(self):
        return self.ip_longitude or ""

    def get_ip_postal_code(self):
        return self.ip_postal_code or ""

    def get_ip_proxy_description(self):
        return self.ip_proxy_description or ""

    def get_ip_proxy_type(self):
        return self.ip_proxy_type or ""

    def get_ip_region(self):
        return self.ip_region or ""

    def get_ip_utc(self):
        return self.ip_utc or ""

    def get_latitude(self):
        return self.latitude or ""

    def get_length_of_residence(self):
        return self.length_of_residence or ""

    def get_longitude(self):
        return self.longitude or ""

    def get_mailbox_name(self):
        return self.mailbox_name or ""

    def get_marital_status(self):
        return self.marital_status or ""

    def get_melissa_address_key(self):
        return self.melissa_address_key or ""

    def get_melissa_address_key_base(self):
        return self.melissa_address_key_base or ""

    def get_melissa_identity_key(self):
        return self.melissa_identity_key or ""

    def get_move_date(self):
        return self.move_date or ""

    def get_name_first(self):
        return self.name_first or ""

    def get_name_first2(self):
        return self.name_first2 or ""

    def get_name_full(self):
        return self.name_full or ""

    def get_name_last(self):
        return self.name_last or ""

    def get_name_last2(self):
        return self.name_last2 or ""

    def get_name_middle(self):
        return self.name_middle or ""

    def get_name_middle2(self):
        return self.name_middle2 or ""

    def get_name_prefix(self):
        return self.name_prefix or ""

    def get_name_prefix2(self):
        return self.name_prefix2 or ""

    def get_name_suffix(self):
        return self.name_suffix or ""

    def get_name_suffix2(self):
        return self.name_suffix2 or ""

    def get_new_area_code(self):
        return self.new_area_code or ""

    def get_occupation(self):
        return self.occupation or ""

    def get_own_rent(self):
        return self.own_rent or ""

    def get_phone_country_code(self):
        return self.phone_country_code or ""

    def get_phone_country_name(self):
        return self.phone_country_name or ""

    def get_phone_extension(self):
        return self.phone_extension or ""

    def get_phone_number(self):
        return self.phone_number or ""

    def get_phone_prefix(self):
        return self.phone_prefix or ""

    def get_phone_suffix(self):
        return self.phone_suffix or ""

    def get_place_code(self):
        return self.place_code or ""

    def get_place_name(self):
        return self.place_name or ""

    def get_plus4(self):
        return self.plus4 or ""

    def get_political_party(self):
        return self.political_party or ""

    def get_postal_code(self):
        return self.postal_code or ""

    def get_presence_of_children(self):
        return self.presence_of_children or ""

    def get_presence_of_senior(self):
        return self.presence_of_senior or ""

    def get_private_mail_box(self):
        return self.private_mail_box or ""

    def get_record_id(self):
        return self.record_id or ""

    def get_results(self):
        return self.results or ""

    def get_salutation(self):
        return self.salutation or ""

    def get_secondary_school_district_code(self):
        return self.secondary_school_district_code or ""

    def get_secondary_school_district_name(self):
        return self.secondary_school_district_name or ""

    def get_state(self):
        return self.state or ""

    def get_state_district_lower(self):
        return self.state_district_lower or ""

    def get_state_district_upper(self):
        return self.state_district_upper or ""

    def get_state_name(self):
        return self.state_name or ""

    def get_suite(self):
        return self.suite or ""

    def get_top_level_domain(self):
        return self.top_level_domain or ""

    def get_utc(self):
        return self.utc or ""

    def get_unified_school_district_code(self):
        return self.unified_school_district_code or ""

    def get_unified_school_district_name(self):
        return self.unified_school_district_name or ""

    def get_record_extras(self):
        return self.record_extras or ""

    def get_reserved(self):
        return self.reserved or ""