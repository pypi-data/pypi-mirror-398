from .ResponseBase import ResponseBase

class GlobalEmailResponse(ResponseBase):

    def __init__(self, version="", transmission_reference="", transmission_results="", total_records="", records=None):
        self.version = version
        self.transmission_reference = transmission_reference
        self.transmission_results = transmission_results
        self.total_records = total_records
        self.records = records if records is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        cls.data = data
        records = [GlobalEmailRecord.from_dict(record) for record in data.get("Records", [])]
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

class GlobalEmailRecord(ResponseBase):
    def __init__(self, record_id="", results="", email_address="", mailbox_name="", domain_name="", 
             domain_authentication_status="", top_level_domain="", top_level_domain_name="", 
             date_checked="", email_age_estimated="", deliverability_confidence_score="", 
             domain_age_estimated="", domain_expiration_date="", domain_created_date="", 
             domain_updated_date="", domain_email="", domain_organization="", domain_address1="", 
             domain_locality="", domain_administrative_area="", domain_postal_code="", 
             domain_country="", domain_country_code="", domain_availability="", 
             domain_private_proxy="", privacy_flag="", mx_server="", domain_type_indicator="", 
             breach_count=""):
        self.record_id = record_id
        self.results = results
        self.email_address = email_address
        self.mailbox_name = mailbox_name
        self.domain_name = domain_name
        self.domain_authentication_status = domain_authentication_status
        self.top_level_domain = top_level_domain
        self.top_level_domain_name = top_level_domain_name
        self.date_checked = date_checked
        self.email_age_estimated = email_age_estimated
        self.deliverability_confidence_score = deliverability_confidence_score
        self.domain_age_estimated = domain_age_estimated
        self.domain_expiration_date = domain_expiration_date
        self.domain_created_date = domain_created_date
        self.domain_updated_date = domain_updated_date
        self.domain_email = domain_email
        self.domain_organization = domain_organization
        self.domain_address1 = domain_address1
        self.domain_locality = domain_locality
        self.domain_administrative_area = domain_administrative_area
        self.domain_postal_code = domain_postal_code
        self.domain_country = domain_country
        self.domain_country_code = domain_country_code
        self.domain_availability = domain_availability
        self.domain_private_proxy = domain_private_proxy
        self.privacy_flag = privacy_flag
        self.mx_server = mx_server
        self.domain_type_indicator = domain_type_indicator
        self.breach_count = breach_count


    @classmethod
    def from_dict(cls, data: dict):
        cls.data = data
        return cls(
            record_id=data.get("RecordID", ""),
            deliverability_confidence_score=data.get("DeliverabilityConfidenceScore", ""),
            results=data.get("Results", ""),
            email_address=data.get("EmailAddress", ""),
            mailbox_name=data.get("MailboxName", ""),
            domain_name=data.get("DomainName", ""),
            domain_authentication_status=data.get("DomainAuthenticationStatus", ""),
            top_level_domain=data.get("TopLevelDomain", ""),
            top_level_domain_name=data.get("TopLevelDomainName", ""),
            date_checked=data.get("DateChecked", ""),
            email_age_estimated=data.get("EmailAgeEstimated", ""),
            domain_age_estimated=data.get("DomainAgeEstimated", ""),
            domain_expiration_date=data.get("DomainExpirationDate", ""),
            domain_created_date=data.get("DomainCreatedDate", ""),
            domain_updated_date=data.get("DomainUpdatedDate", ""),
            domain_email=data.get("DomainEmail", ""),
            domain_organization=data.get("DomainOrganization", ""),
            domain_address1=data.get("DomainAddress1", ""),
            domain_locality=data.get("DomainLocality", ""),
            domain_administrative_area=data.get("DomainAdministrativeArea", ""),
            domain_postal_code=data.get("DomainPostalCode", ""),
            domain_country=data.get("DomainCountry", ""),
            domain_country_code=data.get("DomainCountryCode", ""),
            domain_availability=data.get("DomainAvailability", ""),
            domain_private_proxy=data.get("DomainPrivateProxy", ""),
            privacy_flag=data.get("PrivacyFlag", ""),
            mx_server=data.get("MXServer", ""),
            domain_type_indicator=data.get("DomainTypeIndicator", ""),
            breach_count=data.get("BreachCount", "")
        )
    
    # Setters
    def set_record_id(self, record_id):
        self.record_id = record_id

    def set_results(self, results):
        self.results = results

    def set_email_address(self, email_address):
        self.email_address = email_address

    def set_mailbox_name(self, mailbox_name):
        self.mailbox_name = mailbox_name

    def set_domain_name(self, domain_name):
        self.domain_name = domain_name

    def set_domain_authentication_status(self, domain_authentication_status):
        self.domain_authentication_status = domain_authentication_status

    def set_top_level_domain(self, top_level_domain):
        self.top_level_domain = top_level_domain

    def set_top_level_domain_name(self, top_level_domain_name):
        self.top_level_domain_name = top_level_domain_name

    def set_date_checked(self, date_checked):
        self.date_checked = date_checked

    def set_email_age_estimated(self, email_age_estimated):
        self.email_age_estimated = email_age_estimated

    def set_deliverability_confidence_score(self, deliverability_confidence_score):
        self.deliverability_confidence_score = deliverability_confidence_score

    def set_domain_age_estimated(self, domain_age_estimated):
        self.domain_age_estimated = domain_age_estimated

    def set_domain_expiration_date(self, domain_expiration_date):
        self.domain_expiration_date = domain_expiration_date

    def set_domain_created_date(self, domain_created_date):
        self.domain_created_date = domain_created_date

    def set_domain_updated_date(self, domain_updated_date):
        self.domain_updated_date = domain_updated_date

    def set_domain_email(self, domain_email):
        self.domain_email = domain_email

    def set_domain_organization(self, domain_organization):
        self.domain_organization = domain_organization

    def set_domain_address1(self, domain_address1):
        self.domain_address1 = domain_address1

    def set_domain_locality(self, domain_locality):
        self.domain_locality = domain_locality

    def set_domain_administrative_area(self, domain_administrative_area):
        self.domain_administrative_area = domain_administrative_area

    def set_domain_postal_code(self, domain_postal_code):
        self.domain_postal_code = domain_postal_code

    def set_domain_country(self, domain_country):
        self.domain_country = domain_country

    def set_domain_country_code(self, domain_country_code):
        self.domain_country_code = domain_country_code

    def set_domain_availability(self, domain_availability):
        self.domain_availability = domain_availability

    def set_domain_private_proxy(self, domain_private_proxy):
        self.domain_private_proxy = domain_private_proxy

    def set_privacy_flag(self, privacy_flag):
        self.privacy_flag = privacy_flag

    def set_mx_server(self, mx_server):
        self.mx_server = mx_server

    def set_domain_type_indicator(self, domain_type_indicator):
        self.domain_type_indicator = domain_type_indicator

    def set_breach_count(self, breach_count):
        self.breach_count = breach_count


    # Getters
    def get_record_id(self):
        return self.record_id or ""

    def get_results(self):
        return self.results or ""

    def get_email_address(self):
        return self.email_address or ""

    def get_mailbox_name(self):
        return self.mailbox_name or ""

    def get_domain_name(self):
        return self.domain_name or ""

    def get_domain_authentication_status(self):
        return self.domain_authentication_status or ""

    def get_top_level_domain(self):
        return self.top_level_domain or ""

    def get_top_level_domain_name(self):
        return self.top_level_domain_name or ""

    def get_date_checked(self):
        return self.date_checked or ""

    def get_email_age_estimated(self):
        return self.email_age_estimated or ""

    def get_deliverability_confidence_score(self):
        return self.deliverability_confidence_score or ""

    def get_domain_age_estimated(self):
        return self.domain_age_estimated or ""

    def get_domain_expiration_date(self):
        return self.domain_expiration_date or ""

    def get_domain_created_date(self):
        return self.domain_created_date or ""

    def get_domain_updated_date(self):
        return self.domain_updated_date or ""

    def get_domain_email(self):
        return self.domain_email or ""

    def get_domain_organization(self):
        return self.domain_organization or ""

    def get_domain_address1(self):
        return self.domain_address1 or ""

    def get_domain_locality(self):
        return self.domain_locality or ""

    def get_domain_administrative_area(self):
        return self.domain_administrative_area or ""

    def get_domain_postal_code(self):
        return self.domain_postal_code or ""

    def get_domain_country(self):
        return self.domain_country or ""

    def get_domain_country_code(self):
        return self.domain_country_code or ""

    def get_domain_availability(self):
        return self.domain_availability or ""

    def get_domain_private_proxy(self):
        return self.domain_private_proxy or ""

    def get_privacy_flag(self):
        return self.privacy_flag or ""

    def get_mx_server(self):
        return self.mx_server or ""

    def get_domain_type_indicator(self):
        return self.domain_type_indicator or ""

    def get_breach_count(self):
        return self.breach_count or ""

