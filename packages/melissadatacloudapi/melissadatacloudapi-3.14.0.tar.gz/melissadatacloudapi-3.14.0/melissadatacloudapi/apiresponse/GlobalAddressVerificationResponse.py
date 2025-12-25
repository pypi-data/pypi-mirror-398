from typing import List, Optional
from .ResponseBase import ResponseBase

class GlobalAddressVerificationResponse(ResponseBase):
    def __init__(self, 
                 version = "", 
                 transmission_reference = "", 
                 transmission_results = "", 
                 total_records = "", 
                 records: list = None):
        self.version = version
        self.transmission_reference = transmission_reference
        self.transmission_results = transmission_results
        self.total_records = total_records
        self.records = records if records is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        records = [GlobalAddressVerificationRecord.from_dict(record) for record in data.get("Records", [])]
        cls.data = data
        return cls(
            version=data.get("Version", ""),
            transmission_reference=data.get("TransmissionReference", ""),
            transmission_results=data.get("TransmissionResults", ""),
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
    

class GlobalAddressVerificationRecord(ResponseBase):
    def __init__( self, record_id="", results="", formatted_address="", organization="", address_line_1="", address_line_2="", address_line_3="", 
                 address_line_4="", address_line_5="", address_line_6="", address_line_7="", address_line_8="", sub_premises="", double_dependent_locality="", 
                 dependent_locality="", locality="", sub_administrative_area="", administrative_area="", postal_code="", postal_code_type="", 
                 address_type="", address_key="", sub_national_area="", country_name="", country_iso3166_1_alpha2="", country_iso3166_1_alpha3="", 
                 country_iso3166_1_numeric="", country_subdivision_code="", thoroughfare="", thoroughfare_pre_direction="", thoroughfare_leading_type="", 
                 thoroughfare_name="", thoroughfare_trailing_type="", thoroughfare_post_direction="", dependent_thoroughfare="", 
                 dependent_thoroughfare_pre_direction="", dependent_thoroughfare_leading_type="", dependent_thoroughfare_name="", 
                 dependent_thoroughfare_trailing_type="", dependent_thoroughfare_post_direction="", building="", premises_type="", 
                 premises_number="", sub_premises_type="", sub_premises_number="", post_box="", latitude="", longitude="", delivery_indicator="", 
                 melissa_address_key="", melissa_address_key_base="", post_office_location="", sub_premise_level="", sub_premise_level_type="", 
                 sub_premise_level_number="", sub_building="", sub_building_type="", sub_building_number="", utc="", dst="", delivery_point_suffix="", 
                 census_key="", extras = None
    ):
        self.record_id = record_id
        self.results = results
        self.formatted_address = formatted_address
        self.organization = organization
        self.address_line_1 = address_line_1
        self.address_line_2 = address_line_2
        self.address_line_3 = address_line_3
        self.address_line_4 = address_line_4
        self.address_line_5 = address_line_5
        self.address_line_6 = address_line_6
        self.address_line_7 = address_line_7
        self.address_line_8 = address_line_8
        self.sub_premises = sub_premises
        self.double_dependent_locality = double_dependent_locality
        self.dependent_locality = dependent_locality
        self.locality = locality
        self.sub_administrative_area = sub_administrative_area
        self.administrative_area = administrative_area
        self.postal_code = postal_code
        self.postal_code_type = postal_code_type
        self.address_type = address_type
        self.address_key = address_key
        self.sub_national_area = sub_national_area
        self.country_name = country_name
        self.country_iso3166_1_alpha2 = country_iso3166_1_alpha2
        self.country_iso3166_1_alpha3 = country_iso3166_1_alpha3
        self.country_iso3166_1_numeric = country_iso3166_1_numeric
        self.country_subdivision_code = country_subdivision_code
        self.thoroughfare = thoroughfare
        self.thoroughfare_pre_direction = thoroughfare_pre_direction
        self.thoroughfare_leading_type = thoroughfare_leading_type
        self.thoroughfare_name = thoroughfare_name
        self.thoroughfare_trailing_type = thoroughfare_trailing_type
        self.thoroughfare_post_direction = thoroughfare_post_direction
        self.dependent_thoroughfare = dependent_thoroughfare
        self.dependent_thoroughfare_pre_direction = dependent_thoroughfare_pre_direction
        self.dependent_thoroughfare_leading_type = dependent_thoroughfare_leading_type
        self.dependent_thoroughfare_name = dependent_thoroughfare_name
        self.dependent_thoroughfare_trailing_type = dependent_thoroughfare_trailing_type
        self.dependent_thoroughfare_post_direction = dependent_thoroughfare_post_direction
        self.building = building
        self.premises_type = premises_type
        self.premises_number = premises_number
        self.sub_premises_type = sub_premises_type
        self.sub_premises_number = sub_premises_number
        self.post_box = post_box
        self.latitude = latitude
        self.longitude = longitude
        self.delivery_indicator = delivery_indicator
        self.melissa_address_key = melissa_address_key
        self.melissa_address_key_base = melissa_address_key_base
        self.post_office_location = post_office_location
        self.sub_premise_level = sub_premise_level
        self.sub_premise_level_type = sub_premise_level_type
        self.sub_premise_level_number = sub_premise_level_number
        self.sub_building = sub_building
        self.sub_building_type = sub_building_type
        self.sub_building_number = sub_building_number
        self.utc = utc
        self.dst = dst
        self.delivery_point_suffix = delivery_point_suffix
        self.census_key = census_key
        self.extras = extras

    @classmethod
    def from_dict(cls, data: dict):
        cls.data = data
        return cls(
            record_id = data.get("RecordID", ""),
            results = data.get("Results", ""),
            formatted_address = data.get("FormattedAddress", ""),
            organization = data.get("Organization", ""),
            address_line_1 = data.get("AddressLine1", ""),
            address_line_2 = data.get("AddressLine2", ""),
            address_line_3 = data.get("AddressLine3", ""),
            address_line_4 = data.get("AddressLine4", ""),
            address_line_5 = data.get("AddressLine5", ""),
            address_line_6 = data.get("AddressLine6", ""),
            address_line_7 = data.get("AddressLine7", ""),
            address_line_8 = data.get("AddressLine8", ""),
            sub_premises = data.get("SubPremises", ""),
            double_dependent_locality = data.get("DoubleDependentLocality", ""),
            dependent_locality = data.get("DependentLocality", ""),
            locality = data.get("Locality", ""),
            sub_administrative_area = data.get("SubAdministrativeArea", ""),
            administrative_area = data.get("AdministrativeArea", ""),
            postal_code = data.get("PostalCode", ""),
            postal_code_type = data.get("PostalCodeType", ""),
            address_type = data.get("AddressType", ""),
            address_key = data.get("AddressKey", ""),
            sub_national_area = data.get("SubNationalArea", ""),
            country_name = data.get("CountryName", ""),
            country_iso3166_1_alpha2 = data.get("CountryISO3166_1_Alpha2", ""),
            country_iso3166_1_alpha3 = data.get("CountryISO3166_1_Alpha3", ""),
            country_iso3166_1_numeric = data.get("CountryISO3166_1_Numeric", ""),
            country_subdivision_code = data.get("CountrySubdivisionCode", ""),
            thoroughfare = data.get("Thoroughfare", ""),
            thoroughfare_pre_direction = data.get("ThoroughfarePreDirection", ""),
            thoroughfare_leading_type = data.get("ThoroughfareLeadingType", ""),
            thoroughfare_name = data.get("ThoroughfareName", ""),
            thoroughfare_trailing_type = data.get("ThoroughfareTrailingType", ""),
            thoroughfare_post_direction = data.get("ThoroughfarePostDirection", ""),
            dependent_thoroughfare = data.get("DependentThoroughfare", ""),
            dependent_thoroughfare_pre_direction = data.get("DependentThoroughfarePreDirection", ""),
            dependent_thoroughfare_leading_type = data.get("DependentThoroughfareLeadingType", ""),
            dependent_thoroughfare_name = data.get("DependentThoroughfareName", ""),
            dependent_thoroughfare_trailing_type = data.get("DependentThoroughfareTrailingType", ""),
            dependent_thoroughfare_post_direction = data.get("DependentThoroughfarePostDirection", ""),
            building = data.get("Building", ""),
            premises_type = data.get("PremisesType", ""),
            premises_number = data.get("PremisesNumber", ""),
            sub_premises_type = data.get("SubPremisesType", ""),
            sub_premises_number = data.get("SubPremisesNumber", ""),
            post_box = data.get("PostBox", ""),
            latitude = data.get("Latitude", ""),
            longitude = data.get("Longitude", ""),
            delivery_indicator = data.get("DeliveryIndicator", ""),
            melissa_address_key = data.get("MelissaAddressKey", ""),
            melissa_address_key_base = data.get("MelissaAddressKeyBase", ""),
            post_office_location = data.get("PostOfficeLocation", ""),
            sub_premise_level = data.get("SubPremiseLevel", ""),
            sub_premise_level_type = data.get("SubPremiseLevelType", ""),
            sub_premise_level_number = data.get("SubPremiseLevelNumber", ""),
            sub_building = data.get("SubBuilding", ""),
            sub_building_type = data.get("SubBuildingType", ""),
            sub_building_number = data.get("SubBuildingNumber", ""),
            utc = data.get("UTC", ""),
            dst = data.get("DST", ""),
            delivery_point_suffix = data.get("DeliveryPointSuffix", ""),
            census_key = data.get("CensusKey", ""),
            extras = GlobalAddressVerificationExtras.from_dict(data.get("Extras", None))
        )
    
    # Setters
    def set_record_id(self, record_id):
        self.record_id = record_id

    def set_results(self, results):
        self.results = results

    def set_formatted_address(self, formatted_address):
        self.formatted_address = formatted_address

    def set_organization(self, organization):
        self.organization = organization

    def set_address_line_1(self, address_line_1):
        self.address_line_1 = address_line_1

    def set_address_line_2(self, address_line_2):
        self.address_line_2 = address_line_2

    def set_address_line_3(self, address_line_3):
        self.address_line_3 = address_line_3

    def set_address_line_4(self, address_line_4):
        self.address_line_4 = address_line_4

    def set_address_line_5(self, address_line_5):
        self.address_line_5 = address_line_5

    def set_address_line_6(self, address_line_6):
        self.address_line_6 = address_line_6

    def set_address_line_7(self, address_line_7):
        self.address_line_7 = address_line_7

    def set_address_line_8(self, address_line_8):
        self.address_line_8 = address_line_8

    def set_sub_premises(self, sub_premises):
        self.sub_premises = sub_premises

    def set_double_dependent_locality(self, double_dependent_locality):
        self.double_dependent_locality = double_dependent_locality

    def set_dependent_locality(self, dependent_locality):
        self.dependent_locality = dependent_locality

    def set_locality(self, locality):
        self.locality = locality

    def set_sub_administrative_area(self, sub_administrative_area):
        self.sub_administrative_area = sub_administrative_area

    def set_administrative_area(self, administrative_area):
        self.administrative_area = administrative_area

    def set_postal_code(self, postal_code):
        self.postal_code = postal_code

    def set_postal_code_type(self, postal_code_type):
        self.postal_code_type = postal_code_type

    def set_address_type(self, address_type):
        self.address_type = address_type

    def set_address_key(self, address_key):
        self.address_key = address_key

    def set_sub_national_area(self, sub_national_area):
        self.sub_national_area = sub_national_area

    def set_country_name(self, country_name):
        self.country_name = country_name

    def set_country_iso3166_1_alpha2(self, country_iso3166_1_alpha2):
        self.country_iso3166_1_alpha2 = country_iso3166_1_alpha2

    def set_country_iso3166_1_alpha3(self, country_iso3166_1_alpha3):
        self.country_iso3166_1_alpha3 = country_iso3166_1_alpha3

    def set_country_iso3166_1_numeric(self, country_iso3166_1_numeric):
        self.country_iso3166_1_numeric = country_iso3166_1_numeric

    def set_country_subdivision_code(self, country_subdivision_code):
        self.country_subdivision_code = country_subdivision_code

    def set_thoroughfare(self, thoroughfare):
        self.thoroughfare = thoroughfare

    def set_thoroughfare_pre_direction(self, thoroughfare_pre_direction):
        self.thoroughfare_pre_direction = thoroughfare_pre_direction

    def set_thoroughfare_leading_type(self, thoroughfare_leading_type):
        self.thoroughfare_leading_type = thoroughfare_leading_type

    def set_thoroughfare_name(self, thoroughfare_name):
        self.thoroughfare_name = thoroughfare_name

    def set_thoroughfare_trailing_type(self, thoroughfare_trailing_type):
        self.thoroughfare_trailing_type = thoroughfare_trailing_type

    def set_thoroughfare_post_direction(self, thoroughfare_post_direction):
        self.thoroughfare_post_direction = thoroughfare_post_direction

    def set_dependent_thoroughfare(self, dependent_thoroughfare):
        self.dependent_thoroughfare = dependent_thoroughfare

    def set_dependent_thoroughfare_pre_direction(self, dependent_thoroughfare_pre_direction):
        self.dependent_thoroughfare_pre_direction = dependent_thoroughfare_pre_direction

    def set_dependent_thoroughfare_leading_type(self, dependent_thoroughfare_leading_type):
        self.dependent_thoroughfare_leading_type = dependent_thoroughfare_leading_type

    def set_dependent_thoroughfare_name(self, dependent_thoroughfare_name):
        self.dependent_thoroughfare_name = dependent_thoroughfare_name

    def set_dependent_thoroughfare_trailing_type(self, dependent_thoroughfare_trailing_type):
        self.dependent_thoroughfare_trailing_type = dependent_thoroughfare_trailing_type

    def set_dependent_thoroughfare_post_direction(self, dependent_thoroughfare_post_direction):
        self.dependent_thoroughfare_post_direction = dependent_thoroughfare_post_direction

    def set_building(self, building):
        self.building = building

    def set_premises_type(self, premises_type):
        self.premises_type = premises_type

    def set_premises_number(self, premises_number):
        self.premises_number = premises_number

    def set_sub_premises_type(self, sub_premises_type):
        self.sub_premises_type = sub_premises_type

    def set_sub_premises_number(self, sub_premises_number):
        self.sub_premises_number = sub_premises_number

    def set_post_box(self, post_box):
        self.post_box = post_box

    def set_latitude(self, latitude):
        self.latitude = latitude

    def set_longitude(self, longitude):
        self.longitude = longitude

    def set_delivery_indicator(self, delivery_indicator):
        self.delivery_indicator = delivery_indicator

    def set_melissa_address_key(self, melissa_address_key):
        self.melissa_address_key = melissa_address_key

    def set_melissa_address_key_base(self, melissa_address_key_base):
        self.melissa_address_key_base = melissa_address_key_base

    def set_post_office_location(self, post_office_location):
        self.post_office_location = post_office_location

    def set_sub_premise_level(self, sub_premise_level):
        self.sub_premise_level = sub_premise_level

    def set_sub_premise_level_type(self, sub_premise_level_type):
        self.sub_premise_level_type = sub_premise_level_type

    def set_sub_premise_level_number(self, sub_premise_level_number):
        self.sub_premise_level_number = sub_premise_level_number

    def set_sub_building(self, sub_building):
        self.sub_building = sub_building

    def set_sub_building_type(self, sub_building_type):
        self.sub_building_type = sub_building_type

    def set_sub_building_number(self, sub_building_number):
        self.sub_building_number = sub_building_number

    def set_utc(self, utc):
        self.utc = utc

    def set_dst(self, dst):
        self.dst = dst

    def set_delivery_point_suffix(self, delivery_point):
        self.delivery_point_suffix = delivery_point

    def set_census_key(self, census_key):
        self.census_key = census_key

    # Getters

    def get_record_id(self):
        return self.record_id or ""

    def get_results(self):
        return self.results or ""

    def get_formatted_address(self):
        return self.formatted_address or ""

    def get_organization(self):
        return self.organization or ""

    def get_address_line_1(self):
        return self.address_line_1 or ""

    def get_address_line_2(self):
        return self.address_line_2 or ""

    def get_address_line_3(self):
        return self.address_line_3 or ""

    def get_address_line_4(self):
        return self.address_line_4 or ""

    def get_address_line_5(self):
        return self.address_line_5 or ""

    def get_address_line_6(self):
        return self.address_line_6 or ""

    def get_address_line_7(self):
        return self.address_line_7 or ""

    def get_address_line_8(self):
        return self.address_line_8 or ""

    def get_sub_premises(self):
        return self.sub_premises or ""

    def get_double_dependent_locality(self):
        return self.double_dependent_locality or ""

    def get_dependent_locality(self):
        return self.dependent_locality or ""

    def get_locality(self):
        return self.locality or ""

    def get_sub_administrative_area(self):
        return self.sub_administrative_area or ""

    def get_administrative_area(self):
        return self.administrative_area or ""

    def get_postal_code(self):
        return self.postal_code or ""

    def get_postal_code_type(self):
        return self.postal_code_type or ""

    def get_address_type(self):
        return self.address_type or ""

    def get_address_key(self):
        return self.address_key or ""

    def get_sub_national_area(self):
        return self.sub_national_area or ""

    def get_country_name(self):
        return self.country_name or ""

    def get_country_iso3166_1_alpha2(self):
        return self.country_iso3166_1_alpha2 or ""

    def get_country_iso3166_1_alpha3(self):
        return self.country_iso3166_1_alpha3 or ""

    def get_country_iso3166_1_numeric(self):
        return self.country_iso3166_1_numeric or ""

    def get_country_subdivision_code(self):
        return self.country_subdivision_code or ""

    def get_thoroughfare(self):
        return self.thoroughfare or ""

    def get_thoroughfare_pre_direction(self):
        return self.thoroughfare_pre_direction or ""

    def get_thoroughfare_leading_type(self):
        return self.thoroughfare_leading_type or ""

    def get_thoroughfare_name(self):
        return self.thoroughfare_name or ""

    def get_thoroughfare_trailing_type(self):
        return self.thoroughfare_trailing_type or ""

    def get_thoroughfare_post_direction(self):
        return self.thoroughfare_post_direction or ""

    def get_dependent_thoroughfare(self):
        return self.dependent_thoroughfare or ""

    def get_dependent_thoroughfare_pre_direction(self):
        return self.dependent_thoroughfare_pre_direction or ""

    def get_dependent_thoroughfare_leading_type(self):
        return self.dependent_thoroughfare_leading_type or ""

    def get_dependent_thoroughfare_name(self):
        return self.dependent_thoroughfare_name or ""

    def get_dependent_thoroughfare_trailing_type(self):
        return self.dependent_thoroughfare_trailing_type or ""

    def get_dependent_thoroughfare_post_direction(self):
        return self.dependent_thoroughfare_post_direction or ""

    def get_building(self):
        return self.building or ""

    def get_premises_type(self):
        return self.premises_type or ""

    def get_premises_number(self):
        return self.premises_number or ""

    def get_sub_premises_type(self):
        return self.sub_premises_type or ""

    def get_sub_premises_number(self):
        return self.sub_premises_number or ""

    def get_post_box(self):
        return self.post_box or ""

    def get_latitude(self):
        return self.latitude or ""

    def get_longitude(self):
        return self.longitude or ""

    def get_delivery_indicator(self):
        return self.delivery_indicator or ""

    def get_melissa_address_key(self):
        return self.melissa_address_key or ""

    def get_melissa_address_key_base(self):
        return self.melissa_address_key_base or ""

    def get_post_office_location(self):
        return self.post_office_location or ""

    def get_sub_premise_level(self):
        return self.sub_premise_level or ""

    def get_sub_premise_level_type(self):
        return self.sub_premise_level_type or ""

    def get_sub_premise_level_number(self):
        return self.sub_premise_level_number or ""

    def get_sub_building(self):
        return self.sub_building or ""

    def get_sub_building_type(self):
        return self.sub_building_type or ""

    def get_sub_building_number(self):
        return self.sub_building_number or ""

    def get_utc(self):
        return self.utc or ""

    def get_dst(self):
        return self.dst or ""

    def get_delivery_point_suffix(self):
        return self.delivery_point_suffix or ""

    def get_census_key(self):
        return self.census_key or ""
    

class GlobalAddressVerificationExtras(ResponseBase):
    def __init__(self, daylight_savings_timezone="", daylight_savings_utc="", local_date_time="", 
             standard_timezone="", uprn="", carrier_route="", cbsa_code="", cbsa_division_code="", 
             cbsa_division_level="", cbsa_division_title="", cbsa_level="", cbsa_title="", 
             census_block="", census_tract="", congressional_district="", county_fips="", 
             county_name="", county_subdivision_code="", county_subdivision_name="", 
             delivery_point_check_digit="", delivery_point_code="", elementary_school_district_code="", 
             elementary_school_district_name="", place_code="", place_name="", 
             secondary_school_district_code="", secondary_school_district_name="", 
             state_district_lower="", state_district_upper="", unified_school_district_code="", 
             unified_school_district_name=""):
        self.daylight_savings_timezone = daylight_savings_timezone
        self.daylight_savings_utc = daylight_savings_utc
        self.local_date_time = local_date_time
        self.standard_timezone = standard_timezone
        self.uprn = uprn
        self.carrier_route = carrier_route
        self.cbsa_code = cbsa_code
        self.cbsa_division_code = cbsa_division_code
        self.cbsa_division_level = cbsa_division_level
        self.cbsa_division_title = cbsa_division_title
        self.cbsa_level = cbsa_level
        self.cbsa_title = cbsa_title
        self.census_block = census_block
        self.census_tract = census_tract
        self.congressional_district = congressional_district
        self.county_fips = county_fips
        self.county_name = county_name
        self.county_subdivision_code = county_subdivision_code
        self.county_subdivision_name = county_subdivision_name
        self.delivery_point_check_digit = delivery_point_check_digit
        self.delivery_point_code = delivery_point_code
        self.elementary_school_district_code = elementary_school_district_code
        self.elementary_school_district_name = elementary_school_district_name
        self.place_code = place_code
        self.place_name = place_name
        self.secondary_school_district_code = secondary_school_district_code
        self.secondary_school_district_name = secondary_school_district_name
        self.state_district_lower = state_district_lower
        self.state_district_upper = state_district_upper
        self.unified_school_district_code = unified_school_district_code
        self.unified_school_district_name = unified_school_district_name


    @classmethod
    def from_dict(cls, data: dict):
        cls.data = data
        return cls(
            daylight_savings_timezone=data.get("DaylightSavingsTimezone", ""),
            daylight_savings_utc=data.get("DaylightSavingsUTC", ""),
            local_date_time=data.get("LocalDateTime", ""),
            standard_timezone=data.get("StandardTimezone", ""),
            uprn=data.get("UPRN", ""),
            carrier_route=data.get("CarrierRoute", ""),
            cbsa_code=data.get("CBSACode", ""),
            cbsa_division_code=data.get("CBSADivisionCode", ""),
            cbsa_division_level=data.get("CBSADivisionLevel", ""),
            cbsa_division_title=data.get("CBSADivisionTitle", ""),
            cbsa_level=data.get("CBSALevel", ""),
            cbsa_title=data.get("CBSATitle", ""),
            census_block=data.get("CensusBlock", ""),
            census_tract=data.get("CensusTract", ""),
            congressional_district=data.get("CongressionalDistrict", ""),
            county_fips=data.get("CountyFIPS", ""),
            county_name=data.get("CountyName", ""),
            county_subdivision_code=data.get("CountySubdivisionCode", ""),
            county_subdivision_name=data.get("CountySubdivisionName", ""),
            delivery_point_check_digit=data.get("DeliveryPointCheckDigit", ""),
            delivery_point_code=data.get("DeliveryPointCode", ""),
            elementary_school_district_code=data.get("ElementarySchoolDistrictCode", ""),
            elementary_school_district_name=data.get("ElementarySchoolDistrictName", ""),
            place_code=data.get("PlaceCode", ""),
            place_name=data.get("PlaceName", ""),
            secondary_school_district_code=data.get("SecondarySchoolDistrictCode", ""),
            secondary_school_district_name=data.get("SecondarySchoolDistrictName", ""),
            state_district_lower=data.get("StateDistrictLower", ""),
            state_district_upper=data.get("StateDistrictUpper", ""),
            unified_school_district_code=data.get("UnifiedSchoolDistrictCode", ""),
            unified_school_district_name=data.get("UnifiedSchoolDistrictName", "")
        )
    
    # Setters
    def set_daylight_savings_timezone(self, daylight_savings_timezone):
        self.daylight_savings_timezone = daylight_savings_timezone

    def set_daylight_savings_utc(self, daylight_savings_utc):
        self.daylight_savings_utc = daylight_savings_utc

    def set_local_date_time(self, local_date_time):
        self.local_date_time = local_date_time

    def set_standard_timezone(self, standard_timezone):
        self.standard_timezone = standard_timezone

    def set_uprn(self, uprn):
        self.uprn = uprn

    def set_carrier_route(self, carrier_route):
        self.carrier_route = carrier_route

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

    def set_census_block(self, census_block):
        self.census_block = census_block

    def set_census_tract(self, census_tract):
        self.census_tract = census_tract

    def set_congressional_district(self, congressional_district):
        self.congressional_district = congressional_district

    def set_county_fips(self, county_fips):
        self.county_fips = county_fips

    def set_county_name(self, county_name):
        self.county_name = county_name

    def set_county_subdivision_code(self, county_subdivision_code):
        self.county_subdivision_code = county_subdivision_code

    def set_county_subdivision_name(self, county_subdivision_name):
        self.county_subdivision_name = county_subdivision_name

    def set_delivery_point_check_digit(self, delivery_point_check_digit):
        self.delivery_point_check_digit = delivery_point_check_digit

    def set_delivery_point_code(self, delivery_point_code):
        self.delivery_point_code = delivery_point_code

    def set_elementary_school_district_code(self, elementary_school_district_code):
        self.elementary_school_district_code = elementary_school_district_code

    def set_elementary_school_district_name(self, elementary_school_district_name):
        self.elementary_school_district_name = elementary_school_district_name

    def set_place_code(self, place_code):
        self.place_code = place_code

    def set_place_name(self, place_name):
        self.place_name = place_name

    def set_secondary_school_district_code(self, secondary_school_district_code):
        self.secondary_school_district_code = secondary_school_district_code

    def set_secondary_school_district_name(self, secondary_school_district_name):
        self.secondary_school_district_name = secondary_school_district_name

    def set_state_district_lower(self, state_district_lower):
        self.state_district_lower = state_district_lower

    def set_state_district_upper(self, state_district_upper):
        self.state_district_upper = state_district_upper

    def set_unified_school_district_code(self, unified_school_district_code):
        self.unified_school_district_code = unified_school_district_code

    def set_unified_school_district_name(self, unified_school_district_name):
        self.unified_school_district_name = unified_school_district_name


    # Getters
    def get_daylight_savings_timezone(self):
        return self.daylight_savings_timezone or ""

    def get_daylight_savings_utc(self):
        return self.daylight_savings_utc or ""

    def get_local_date_time(self):
        return self.local_date_time or ""

    def get_standard_timezone(self):
        return self.standard_timezone or ""

    def get_uprn(self):
        return self.uprn or ""

    def get_carrier_route(self):
        return self.carrier_route or ""

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

    def get_census_block(self):
        return self.census_block or ""

    def get_census_tract(self):
        return self.census_tract or ""

    def get_congressional_district(self):
        return self.congressional_district or ""

    def get_county_fips(self):
        return self.county_fips or ""

    def get_county_name(self):
        return self.county_name or ""

    def get_county_subdivision_code(self):
        return self.county_subdivision_code or ""

    def get_county_subdivision_name(self):
        return self.county_subdivision_name or ""

    def get_delivery_point_check_digit(self):
        return self.delivery_point_check_digit or ""

    def get_delivery_point_code(self):
        return self.delivery_point_code or ""

    def get_elementary_school_district_code(self):
        return self.elementary_school_district_code or ""

    def get_elementary_school_district_name(self):
        return self.elementary_school_district_name or ""

    def get_place_code(self):
        return self.place_code or ""

    def get_place_name(self):
        return self.place_name or ""

    def get_secondary_school_district_code(self):
        return self.secondary_school_district_code or ""

    def get_secondary_school_district_name(self):
        return self.secondary_school_district_name or ""

    def get_state_district_lower(self):
        return self.state_district_lower or ""

    def get_state_district_upper(self):
        return self.state_district_upper or ""

    def get_unified_school_district_code(self):
        return self.unified_school_district_code or ""

    def get_unified_school_district_name(self):
        return self.unified_school_district_name or ""






