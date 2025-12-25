from typing import List
from .ResponseBase import ResponseBase

class BusinessCoderResponse(ResponseBase):
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
        records = [BusinessCoderRecord.from_dict(record) for record in data.get("Records", [])]
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
    

class BusinessCoderContacts(ResponseBase):
    def __init__(self, 
                 name_first = "", 
                 name_last = "", 
                 gender = "", 
                 title = "", 
                 contact_phone = "", 
                 email = ""):
        self.name_first = name_first
        self.name_last = name_last
        self.gender = gender
        self.title = title
        self.contact_phone = contact_phone
        self.email = email

    @classmethod
    def from_dict(cls, data: dict):
        cls.data = data
        return cls(
            name_first=data.get('NameFirst', ""),
            name_last=data.get('NameLast', ""),
            gender=data.get('Gender', ""),
            title=data.get('Title', ""),
            contact_phone=data.get('ContactPhone', ""),
            email=data.get('Email', "")
        )

    # Setters
    def set_name_first(self, name_first):
        self.name_first = name_first

    def set_name_last(self, name_last):
        self.name_last = name_last

    def set_gender(self, gender):
        self.gender = gender

    def set_title(self, title):
        self.title = title

    def set_contact_phone(self, contact_phone):
        self.contact_phone = contact_phone

    def set_email(self, email):
        self.email = email

    # Getters
    def get_name_first(self):
        return self.name_first or ""

    def get_name_last(self):
        return self.name_last or ""

    def get_gender(self):
        return self.gender or ""

    def get_title(self):
        return self.title or ""

    def get_contact_phone(self):
        return self.contact_phone or ""

    def get_email(self):
        return self.email or ""

    


class BusinessCoderRecord(ResponseBase):
    def __init__(self, 
             record_id="", 
             company_name="", 
             current_company_name="", 
             address_line_1="", 
             suite="", 
             city="", 
             state="", 
             postal_code="", 
             total_contacts="", 
             melissa_enterprise_key="", 
             location_type="", 
             phone="", 
             employees_estimate="", 
             sales_estimate="", 
             stock_ticker="", 
             web_address="", 
             contacts: List[BusinessCoderContacts] = None, 
             country_code="", 
             country_name="", 
             delivery_indicator="", 
             melissa_address_key="", 
             melissa_address_key_base="", 
             plus4="", 
             ein="", 
             sic_code1="", 
             sic_code2="", 
             sic_code3="", 
             naics_code1="", 
             naics_code2="", 
             naics_code3="", 
             sic_description1="", 
             sic_description2="", 
             sic_description3="", 
             naics_description1="", 
             naics_description2="", 
             naics_description3="", 
             latitude="", 
             longitude="", 
             county_name="", 
             county_fips="", 
             census_tract="", 
             census_block="", 
             place_code="", 
             place_name="", 
             results=""):
        self.record_id = record_id
        self.company_name = company_name
        self.current_company_name = current_company_name
        self.address_line_1 = address_line_1
        self.suite = suite
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.total_contacts = total_contacts
        self.melissa_enterprise_key = melissa_enterprise_key
        self.location_type = location_type
        self.phone = phone
        self.employees_estimate = employees_estimate
        self.sales_estimate = sales_estimate
        self.stock_ticker = stock_ticker
        self.web_address = web_address
        self.contacts = contacts if contacts is not None else []
        self.country_code = country_code
        self.country_name = country_name
        self.delivery_indicator = delivery_indicator
        self.melissa_address_key = melissa_address_key
        self.melissa_address_key_base = melissa_address_key_base
        self.plus4 = plus4
        self.ein = ein
        self.sic_code1 = sic_code1
        self.sic_code2 = sic_code2
        self.sic_code3 = sic_code3
        self.naics_code1 = naics_code1
        self.naics_code2 = naics_code2
        self.naics_code3 = naics_code3
        self.sic_description1 = sic_description1
        self.sic_description2 = sic_description2
        self.sic_description3 = sic_description3
        self.naics_description1 = naics_description1
        self.naics_description2 = naics_description2
        self.naics_description3 = naics_description3
        self.latitude = latitude
        self.longitude = longitude
        self.county_name = county_name
        self.county_fips = county_fips
        self.census_tract = census_tract
        self.census_block = census_block
        self.place_code = place_code
        self.place_name = place_name
        self.results = results
    
    @classmethod
    def from_dict(cls, data: dict):
        cls.data = data
        return cls(
            record_id=data.get('RecordID', ""),
            company_name=data.get('CompanyName', ""),
            current_company_name=data.get('CurrentCompanyName', ""),
            address_line_1=data.get('AddressLine1', ""),
            suite=data.get('Suite', ""),
            city=data.get('City', ""),
            state=data.get('State', ""),
            postal_code=data.get('PostalCode', ""),
            total_contacts=data.get('TotalContacts', ""),
            melissa_enterprise_key=data.get('MelissaEnterpriseKey', ""),
            location_type=data.get('LocationType', ""),
            phone=data.get('Phone', ""),
            employees_estimate=data.get('EmployeesEstimate', ""),
            sales_estimate=data.get('SalesEstimate', ""),
            stock_ticker=data.get('StockTicker', ""),
            web_address=data.get('WebAddress', ""),
            contacts=[BusinessCoderContacts.from_dict(data) for data in data.get('Contacts', [])],
            country_code=data.get('CountryCode', ""),
            country_name=data.get('CountryName', ""),
            delivery_indicator=data.get('DeliveryIndicator', ""),
            melissa_address_key=data.get('MelissaAddressKey', ""),
            melissa_address_key_base=data.get('MelissaAddressKeyBase', ""),
            plus4=data.get('Plus4', ""),
            ein=data.get('EIN', ""),
            sic_code1=data.get('SICCode1', ""),
            sic_code2=data.get('SICCode2', ""),
            sic_code3=data.get('SICCode3', ""),
            naics_code1=data.get('NAICSCode1', ""),
            naics_code2=data.get('NAICSCode2', ""),
            naics_code3=data.get('NAICSCode3', ""),
            sic_description1=data.get('SICDescription1', ""),
            sic_description2=data.get('SICDescription2', ""),
            sic_description3=data.get('SICDescription3', ""),
            naics_description1=data.get('NAICSDescription1', ""),
            naics_description2=data.get('NAICSDescription2', ""),
            naics_description3=data.get('NAICSDescription3', ""),
            latitude=data.get('Latitude', ""),
            longitude=data.get('Longitude', ""),
            county_name=data.get('CountyName', ""),
            county_fips=data.get('CountyFIPS', ""),
            census_tract=data.get('CensusTract', ""),
            census_block=data.get('CensusBlock', ""),
            place_code=data.get('PlaceCode', ""),
            place_name=data.get('PlaceName', ""),
            results=data.get('Results', "")
        )

    # Setters
    def set_record_id(self, record_id):
       self.record_id = record_id

    def set_company_name(self, company_name):
        self.company_name = company_name

    def set_current_company_name(self, current_company_name):
        self.current_company_name = current_company_name

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

    def set_total_contacts(self, total_contacts):
        self.total_contacts = total_contacts

    def set_melissa_enterprise_key(self, melissa_enterprise_key):
        self.melissa_enterprise_key = melissa_enterprise_key

    def set_location_type(self, location_type):
        self.location_type = location_type

    def set_phone(self, phone):
        self.phone = phone

    def set_employees_estimate(self, employees_estimate):
        self.employees_estimate = employees_estimate

    def set_sales_estimate(self, sales_estimate):
        self.sales_estimate = sales_estimate

    def set_stock_ticker(self, stock_ticker):
        self.stock_ticker = stock_ticker

    def set_web_address(self, web_address):
        self.web_address = web_address

    def set_country_code(self, country_code):
        self.country_code = country_code

    def set_country_name(self, country_name):
        self.country_name = country_name

    def set_delivery_indicator(self, delivery_indicator):
        self.delivery_indicator = delivery_indicator

    def set_melissa_address_key(self, melissa_address_key):
        self.melissa_address_key = melissa_address_key

    def set_melissa_address_key_base(self, melissa_address_key_base):
        self.melissa_address_key_base = melissa_address_key_base

    def set_plus4(self, plus4):
        self.plus4 = plus4

    def set_ein(self, ein):
        self.ein = ein

    def set_sic_code1(self, sic_code1):
        self.sic_code1 = sic_code1

    def set_sic_code2(self, sic_code2):
        self.sic_code2 = sic_code2

    def set_sic_code3(self, sic_code3):
        self.sic_code3 = sic_code3

    def set_naics_code1(self, naics_code1):
        self.naics_code1 = naics_code1

    def set_naics_code2(self, naics_code2):
        self.naics_code2 = naics_code2

    def set_naics_code3(self, naics_code3):
        self.naics_code3 = naics_code3

    def set_sic_description1(self, sic_description1):
        self.sic_description1 = sic_description1

    def set_sic_description2(self, sic_description2):
        self.sic_description2 = sic_description2

    def set_sic_description3(self, sic_description3):
        self.sic_description3 = sic_description3

    def set_naics_description1(self, naics_description1):
        self.naics_description1 = naics_description1

    def set_naics_description2(self, naics_description2):
        self.naics_description2 = naics_description2

    def set_naics_description3(self, naics_description3):
        self.naics_description3 = naics_description3

    def set_latitude(self, latitude):
        self.latitude = latitude

    def set_longitude(self, longitude):
        self.longitude = longitude

    def set_county_name(self, county_name):
        self.county_name = county_name

    def set_county_fips(self, county_fips):
        self.county_fips = county_fips

    def set_census_tract(self, census_tract):
        self.census_tract = census_tract

    def set_census_block(self, census_block):
        self.census_block = census_block

    def set_place_code(self, place_code):
        self.place_code = place_code

    def set_place_name(self, place_name):
        self.place_name = place_name

    def set_results(self, results):
        self.results = results

    # Getters
    def get_record_id(self):
        return self.record_id if self.record_id else ""

    def get_company_name(self):
        return self.company_name if self.company_name else ""

    def get_current_company_name(self):
        return self.current_company_name if self.current_company_name else ""

    def get_address_line_1(self):
        return self.address_line_1 if self.address_line_1 else ""

    def get_suite(self):
        return self.suite if self.suite else ""

    def get_city(self):
        return self.city if self.city else ""

    def get_state(self):
        return self.state if self.state else ""

    def get_postal_code(self):
        return self.postal_code if self.postal_code else ""

    def get_total_contacts(self):
        return self.total_contacts if self.total_contacts else ""

    def get_melissa_enterprise_key(self):
        return self.melissa_enterprise_key if self.melissa_enterprise_key else ""

    def get_location_type(self):
        return self.location_type if self.location_type else ""

    def get_phone(self):
        return self.phone if self.phone else ""

    def get_employees_estimate(self):
        return self.employees_estimate if self.employees_estimate else ""

    def get_sales_estimate(self):
        return self.sales_estimate if self.sales_estimate else ""

    def get_stock_ticker(self):
        return self.stock_ticker if self.stock_ticker else ""

    def get_web_address(self):
        return self.web_address if self.web_address else ""

    def get_country_code(self):
        return self.country_code if self.country_code else ""

    def get_country_name(self):
        return self.country_name if self.country_name else ""

    def get_delivery_indicator(self):
        return self.delivery_indicator if self.delivery_indicator else ""

    def get_melissa_address_key(self):
        return self.melissa_address_key if self.melissa_address_key else ""

    def get_melissa_address_key_base(self):
        return self.melissa_address_key_base if self.melissa_address_key_base else ""

    def get_plus4(self):
        return self.plus4 if self.plus4 else ""

    def get_ein(self):
        return self.ein if self.ein else ""

    def get_sic_code1(self):
        return self.sic_code1 if self.sic_code1 else ""

    def get_sic_code2(self):
        return self.sic_code2 if self.sic_code2 else ""

    def get_sic_code3(self):
        return self.sic_code3 if self.sic_code3 else ""

    def get_naics_code1(self):
        return self.naics_code1 if self.naics_code1 else ""

    def get_naics_code2(self):
        return self.naics_code2 if self.naics_code2 else ""

    def get_naics_code3(self):
        return self.naics_code3 if self.naics_code3 else ""

    def get_sic_description1(self):
        return self.sic_description1 if self.sic_description1 else ""

    def get_sic_description2(self):
        return self.sic_description2 if self.sic_description2 else ""

    def get_sic_description3(self):
        return self.sic_description3 if self.sic_description3 else ""

    def get_naics_description1(self):
        return self.naics_description1 if self.naics_description1 else ""

    def get_naics_description2(self):
        return self.naics_description2 if self.naics_description2 else ""

    def get_naics_description3(self):
        return self.naics_description3 if self.naics_description3 else ""

    def get_latitude(self):
        return self.latitude if self.latitude else ""

    def get_longitude(self):
        return self.longitude if self.longitude else ""

    def get_county_name(self):
        return self.county_name if self.county_name else ""

    def get_county_fips(self):
        return self.county_fips if self.county_fips else ""

    def get_census_tract(self):
        return self.census_tract if self.census_tract else ""

    def get_census_block(self):
        return self.census_block if self.census_block else ""

    def get_place_code(self):
        return self.place_code if self.place_code else ""

    def get_place_name(self):
        return self.place_name if self.place_name else ""

    def get_results(self):
        return self.results if self.results else ""
    

