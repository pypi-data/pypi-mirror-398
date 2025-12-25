from .ResponseBase import ResponseBase

class GlobalIPResponse(ResponseBase):
    def __init__(self, version="", transmission_reference="", transmission_results="", records=None):
        self.version = version
        self.transmission_reference = transmission_reference
        self.transmission_results = transmission_results
        self.records = records if records is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        records = [GlobalIPRecord.from_dict(record) for record in data.get("Records", [])]
        return cls(
            version=data.get("Version", ""),
            transmission_reference=data.get("TransmissionReference", ""),
            transmission_results=data.get("TransmissionResults", ""),
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

class GlobalIPRecord(ResponseBase):
    def __init__(self, city="", connection_speed="", connection_type="", continent="", country_abbreviation="", 
                 country_name="", domain_address1="", domain_administrative_area="", domain_age_estimated="", 
                 domain_availability="", domain_country="", domain_country_code="", domain_created_date="", 
                 domain_email="", domain_expiration_date="", domain_locality="", domain_name="", domain_organization="", 
                 domain_postal_code="", domain_private_proxy="", domain_updated_date="", dst="", ip_address="", 
                 isp_name="", latitude="", longitude="", postal_code="", proxy_description="", proxy_type="", 
                 record_id="", region="", result="", time_zone_code="", time_zone_name="", utc=""):
        self.city = city
        self.connection_speed = connection_speed
        self.connection_type = connection_type
        self.continent = continent
        self.country_abbreviation = country_abbreviation
        self.country_name = country_name
        self.domain_address1 = domain_address1
        self.domain_administrative_area = domain_administrative_area
        self.domain_age_estimated = domain_age_estimated
        self.domain_availability = domain_availability
        self.domain_country = domain_country
        self.domain_country_code = domain_country_code
        self.domain_created_date = domain_created_date
        self.domain_email = domain_email
        self.domain_expiration_date = domain_expiration_date
        self.domain_locality = domain_locality
        self.domain_name = domain_name
        self.domain_organization = domain_organization
        self.domain_postal_code = domain_postal_code
        self.domain_private_proxy = domain_private_proxy
        self.domain_updated_date = domain_updated_date
        self.dst = dst
        self.ip_address = ip_address
        self.isp_name = isp_name
        self.latitude = latitude
        self.longitude = longitude
        self.postal_code = postal_code
        self.proxy_description = proxy_description
        self.proxy_type = proxy_type
        self.record_id = record_id
        self.region = region
        self.result = result
        self.time_zone_code = time_zone_code
        self.time_zone_name = time_zone_name
        self.utc = utc

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            city=data.get("City", ""),
            connection_speed=data.get("ConnectionSpeed", ""),
            connection_type=data.get("ConnectionType", ""),
            continent=data.get("Continent", ""),
            country_abbreviation=data.get("CountryAbbreviation", ""),
            country_name=data.get("CountryName", ""),
            domain_address1=data.get("DomainAddress1", ""),
            domain_administrative_area=data.get("DomainAdministrativeArea", ""),
            domain_age_estimated=data.get("DomainAgeEstimated", ""),
            domain_availability=data.get("DomainAvailability", ""),
            domain_country=data.get("DomainCountry", ""),
            domain_country_code=data.get("DomainCountryCode", ""),
            domain_created_date=data.get("DomainCreatedDate", ""),
            domain_email=data.get("DomainEmail", ""),
            domain_expiration_date=data.get("DomainExpirationDate", ""),
            domain_locality=data.get("DomainLocality", ""),
            domain_name=data.get("DomainName", ""),
            domain_organization=data.get("DomainOrganization", ""),
            domain_postal_code=data.get("DomainPostalCode", ""),
            domain_private_proxy=data.get("DomainPrivateProxy", ""),
            domain_updated_date=data.get("DomainUpdatedDate", ""),
            dst=data.get("DST", ""),
            ip_address=data.get("IPAddress", ""),
            isp_name=data.get("ISPName", ""),
            latitude=data.get("Latitude", ""),
            longitude=data.get("Longitude", ""),
            postal_code=data.get("PostalCode", ""),
            proxy_description=data.get("ProxyDescription", ""),
            proxy_type=data.get("ProxyType", ""),
            record_id=data.get("RecordID", ""),
            region=data.get("Region", ""),
            result=data.get("Result", ""),
            time_zone_code=data.get("TimeZoneCode", ""),
            time_zone_name=data.get("TimeZoneName", ""),
            utc=data.get("UTC", "")
        )

    # Setters
    def set_city(self, city):
        self.city = city

    def set_connection_speed(self, connection_speed):
        self.connection_speed = connection_speed

    def set_connection_type(self, connection_type):
        self.connection_type = connection_type

    def set_continent(self, continent):
        self.continent = continent

    def set_country_abbreviation(self, country_abbreviation):
        self.country_abbreviation = country_abbreviation

    def set_country_name(self, country_name):
        self.country_name = country_name

    def set_domain_address1(self, domain_address1):
        self.domain_address1 = domain_address1

    def set_domain_administrative_area(self, domain_administrative_area):
        self.domain_administrative_area = domain_administrative_area

    def set_domain_age_estimated(self, domain_age_estimated):
        self.domain_age_estimated = domain_age_estimated

    def set_domain_availability(self, domain_availability):
        self.domain_availability = domain_availability

    def set_domain_country(self, domain_country):
        self.domain_country = domain_country

    def set_domain_country_code(self, domain_country_code):
        self.domain_country_code = domain_country_code

    def set_domain_created_date(self, domain_created_date):
        self.domain_created_date = domain_created_date

    def set_domain_email(self, domain_email):
        self.domain_email = domain_email

    def set_domain_expiration_date(self, domain_expiration_date):
        self.domain_expiration_date = domain_expiration_date

    def set_domain_locality(self, domain_locality):
        self.domain_locality = domain_locality

    def set_domain_name(self, domain_name):
        self.domain_name = domain_name

    def set_domain_organization(self, domain_organization):
        self.domain_organization = domain_organization

    def set_domain_postal_code(self, domain_postal_code):
        self.domain_postal_code = domain_postal_code

    def set_domain_private_proxy(self, domain_private_proxy):
        self.domain_private_proxy = domain_private_proxy

    def set_domain_updated_date(self, domain_updated_date):
        self.domain_updated_date = domain_updated_date

    def set_dst(self, dst):
        self.dst = dst

    def set_ip_address(self, ip_address):
        self.ip_address = ip_address

    def set_isp_name(self, isp_name):
        self.isp_name = isp_name

    def set_latitude(self, latitude):
        self.latitude = latitude

    def set_longitude(self, longitude):
        self.longitude = longitude

    def set_postal_code(self, postal_code):
        self.postal_code = postal_code

    def set_proxy_description(self, proxy_description):
        self.proxy_description = proxy_description

    def set_proxy_type(self, proxy_type):
        self.proxy_type = proxy_type

    def set_record_id(self, record_id):
        self.record_id = record_id

    def set_region(self, region):
        self.region = region

    def set_result(self, result):
        self.result = result

    def set_time_zone_code(self, time_zone_code):
        self.time_zone_code = time_zone_code

    def set_time_zone_name(self, time_zone_name):
        self.time_zone_name = time_zone_name

    def set_utc(self, utc):
        self.utc = utc

    # Getters
    def get_city(self):
        return self.city or ""

    def get_connection_speed(self):
        return self.connection_speed or ""

    def get_connection_type(self):
        return self.connection_type or ""

    def get_continent(self):
        return self.continent or ""

    def get_country_abbreviation(self):
        return self.country_abbreviation or ""

    def get_country_name(self):
        return self.country_name or ""

    def get_domain_address1(self):
        return self.domain_address1 or ""

    def get_domain_administrative_area(self):
        return self.domain_administrative_area or ""

    def get_domain_age_estimated(self):
        return self.domain_age_estimated or ""

    def get_domain_availability(self):
        return self.domain_availability or ""

    def get_domain_country(self):
        return self.domain_country or ""

    def get_domain_country_code(self):
        return self.domain_country_code or ""

    def get_domain_created_date(self):
        return self.domain_created_date or ""

    def get_domain_email(self):
        return self.domain_email or ""

    def get_domain_expiration_date(self):
        return self.domain_expiration_date or ""

    def get_domain_locality(self):
        return self.domain_locality or ""

    def get_domain_name(self):
        return self.domain_name or ""

    def get_domain_organization(self):
        return self.domain_organization or ""

    def get_domain_postal_code(self):
        return self.domain_postal_code or ""

    def get_domain_private_proxy(self):
        return self.domain_private_proxy or ""

    def get_domain_updated_date(self):
        return self.domain_updated_date or ""

    def get_dst(self):
        return self.dst or ""

    def get_ip_address(self):
        return self.ip_address or ""

    def get_isp_name(self):
        return self.isp_name or ""

    def get_latitude(self):
        return self.latitude or ""

    def get_longitude(self):
        return self.longitude or ""

    def get_postal_code(self):
        return self.postal_code or ""

    def get_proxy_description(self):
        return self.proxy_description or ""

    def get_proxy_type(self):
        return self.proxy_type or ""

    def get_record_id(self):
        return self.record_id or ""

    def get_region(self):
        return self.region or ""

    def get_result(self):
        return self.result or ""

    def get_time_zone_code(self):
        return self.time_zone_code or ""

    def get_time_zone_name(self):
        return self.time_zone_name or ""

    def get_utc(self):
        return self.utc or ""