from .ResponseBase import ResponseBase

class PersonatorIdentityResponse(ResponseBase):
    def __init__(
            self, version="", transmission_reference="", transaction_id="", results="", peronator_identity_name=None, 
            peronator_identity_address = None, peronator_identity_email = None, peronator_identity_phone = None, peronator_identity_identity = None
    ):
        self.version = version
        self.transmission_reference = transmission_reference
        self.transaction_id = transaction_id
        self.results = results
        self.peronator_identity_name = peronator_identity_name 
        self.peronator_identity_address = peronator_identity_address 
        self.peronator_identity_email = peronator_identity_email 
        self.peronator_identity_phone = peronator_identity_phone 
        self.peronator_identity_identity = peronator_identity_identity 

    @classmethod
    def populate_from_dict(cls, data: dict):
        cls.data = data
        return cls(
            version=data.get("Version", ""),
            transmission_reference=data.get("TransmissionReference", ""),
            transaction_id=data.get("TransactionID", ""),
            results = data.get("Results", ""),
            peronator_identity_name = PersonatorIdentityName.from_dict(data.get("Name", None)),
            peronator_identity_address = PersonatorIdentityAddress.from_dict(data.get("Address", None)),
            peronator_identity_email = PersonatorIdentityEmail.from_dict(data.get("Email", None)),
            peronator_identity_phone = PersonatorIdentityPhone.from_dict(data.get("Phone", None)),
            peronator_identity_identity = PersonatorIdentityIdentity.from_dict(data.get("Identity", None))
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
    

class PersonatorIdentityName:
    def __init__(
        self, results="", company="", name_prefix="", name_first="", name_middle="", name_last="", name_suffix="", 
        gender="", name_prefix2="", name_first2="", name_middle2="", name_last2="", name_suffix2="", gender2="",
    ):
        self.results = results
        self.company = company
        self.name_prefix = name_prefix
        self.name_first = name_first
        self.name_middle = name_middle
        self.name_last = name_last
        self.name_suffix = name_suffix
        self.gender = gender
        self.name_prefix2 = name_prefix2
        self.name_first2 = name_first2
        self.name_middle2 = name_middle2
        self.name_last2 = name_last2
        self.name_suffix2 = name_suffix2
        self.gender2 = gender2

    @classmethod
    def from_dict(cls, data: dict):
        cls.data = data
        print(data)
        return cls(
            results=data.get("Results", ""),
            company=data.get("Company", ""),
            name_prefix=data.get("NamePrefix", ""),
            name_first=data.get("NameFirst", ""),
            name_middle=data.get("NameMiddle", ""),
            name_last=data.get("NameLast", ""),
            name_suffix=data.get("NameSuffix", ""),
            gender=data.get("Gender", ""),
            name_prefix2=data.get("NamePrefix2", ""),
            name_first2=data.get("NameFirst2", ""),
            name_middle2=data.get("NameMiddle2", ""),
            name_last2=data.get("NameLast2", ""),
            name_suffix2=data.get("NameSuffix2", ""),
            gender2=data.get("Gender2", ""),
        )
    
    # Setters
    def set_results(self, results):
        self.results = results

    def set_company(self, company):
        self.company = company

    def set_name_prefix(self, name_prefix):
        self.name_prefix = name_prefix

    def set_name_first(self, name_first):
        self.name_first = name_first

    def set_name_middle(self, name_middle):
        self.name_middle = name_middle

    def set_name_last(self, name_last):
        self.name_last = name_last

    def set_name_suffix(self, name_suffix):
        self.name_suffix = name_suffix

    def set_gender(self, gender):
        self.gender = gender

    def set_name_prefix2(self, name_prefix2):
        self.name_prefix2 = name_prefix2

    def set_name_first2(self, name_first2):
        self.name_first2 = name_first2

    def set_name_middle2(self, name_middle2):
        self.name_middle2 = name_middle2

    def set_name_last2(self, name_last2):
        self.name_last2 = name_last2

    def set_name_suffix2(self, name_suffix2):
        self.name_suffix2 = name_suffix2

    def set_gender2(self, gender2):
        self.gender2 = gender2

    # Getters
    def get_results(self):
        return self.results or ""

    def get_company(self):
        return self.company or ""

    def get_name_prefix(self):
        return self.name_prefix or ""

    def get_name_first(self):
        return self.name_first or ""

    def get_name_middle(self):
        return self.name_middle or ""

    def get_name_last(self):
        return self.name_last or ""

    def get_name_suffix(self):
        return self.name_suffix or ""

    def get_gender(self):
        return self.gender or ""

    def get_name_prefix2(self):
        return self.name_prefix2 or ""

    def get_name_first2(self):
        return self.name_first2 or ""

    def get_name_middle2(self):
        return self.name_middle2 or ""

    def get_name_last2(self):
        return self.name_last2 or ""

    def get_name_suffix2(self):
        return self.name_suffix2 or ""

    def get_gender2(self):
        return self.gender2 or ""


class PersonatorIdentityAddress:
    def __init__(
        self, results="", formatted_address="", organization="", address_line_1="", address_line_2="", address_line_3="", address_line_4="", 
        address_line_5="", address_line_6="", address_line_7="", address_line_8="", sub_premises="", double_dependent_locality="", 
        dependent_locality="", locality="", sub_administrative_area="", administrative_area="", postal_code="", address_type="", address_key="", 
        sub_national_area="", country_name="", country_code="", country_iso3="", country_number="", country_subdivision_code="",
        thoroughfare="", thoroughfare_pre_direction="", thoroughfare_leading_type="", thoroughfare_name="", thoroughfare_trailing_type="", 
        thoroughfare_post_direction="", dependent_thoroughfare="", dependent_thoroughfare_pre_direction="", dependent_thoroughfare_leading_type="",
        dependent_thoroughfare_name="", dependent_thoroughfare_trailing_type="", dependent_thoroughfare_post_direction="", building="", 
        premises_type="", premises_number="", sub_premises_type="", sub_premises_number="", post_box="", latitude="", longitude="",
    ):
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
        self.address_type = address_type
        self.address_key = address_key
        self.sub_national_area = sub_national_area
        self.country_name = country_name
        self.country_code = country_code
        self.country_iso3 = country_iso3
        self.country_number = country_number
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

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            results=data.get("Results", ""),
            formatted_address=data.get("FormattedAddress", ""),
            organization=data.get("Organization", ""),
            address_line_1=data.get("AddressLine1", ""),
            address_line_2=data.get("AddressLine2", ""),
            address_line_3=data.get("AddressLine3", ""),
            address_line_4=data.get("AddressLine4", ""),
            address_line_5=data.get("AddressLine5", ""),
            address_line_6=data.get("AddressLine6", ""),
            address_line_7=data.get("AddressLine7", ""),
            address_line_8=data.get("AddressLine8", ""),
            sub_premises=data.get("SubPremises", ""),
            double_dependent_locality=data.get("DoubleDependentLocality", ""),
            dependent_locality=data.get("DependentLocality", ""),
            locality=data.get("Locality", ""),
            sub_administrative_area=data.get("SubAdministrativeArea", ""),
            administrative_area=data.get("AdministrativeArea", ""),
            postal_code=data.get("PostalCode", ""),
            address_type=data.get("AddressType", ""),
            address_key=data.get("AddressKey", ""),
            sub_national_area=data.get("SubNationalArea", ""),
            country_name=data.get("CountryName", ""),
            country_code=data.get("CountryCode", ""),
            country_iso3=data.get("CountryISO3", ""),
            country_number=data.get("CountryNumber", ""),
            country_subdivision_code=data.get("CountrySubdivisionCode", ""),
            thoroughfare=data.get("Thoroughfare", ""),
            thoroughfare_pre_direction=data.get("ThoroughfarePreDirection", ""),
            thoroughfare_leading_type=data.get("ThoroughfareLeadingType", ""),
            thoroughfare_name=data.get("ThoroughfareName", ""),
            thoroughfare_trailing_type=data.get("ThoroughfareTrailingType", ""),
            thoroughfare_post_direction=data.get("ThoroughfarePostDirection", ""),
            dependent_thoroughfare=data.get("DependentThoroughfare", ""),
            dependent_thoroughfare_pre_direction=data.get("DependentThoroughfarePreDirection", ""),
            dependent_thoroughfare_leading_type=data.get("DependentThoroughfareLeadingType", ""),
            dependent_thoroughfare_name=data.get("DependentThoroughfareName", ""),
            dependent_thoroughfare_trailing_type=data.get("DependentThoroughfareTrailingType", ""),
            dependent_thoroughfare_post_direction=data.get("DependentThoroughfarePostDirection", ""),
            building=data.get("Building", ""),
            premises_type=data.get("PremisesType", ""),
            premises_number=data.get("PremisesNumber", ""),
            sub_premises_type=data.get("SubPremisesType", ""),
            sub_premises_number=data.get("SubPremisesNumber", ""),
            post_box=data.get("PostBox", ""),
            latitude=data.get("Latitude", ""),
            longitude=data.get("Longitude", ""),
        )
    
    # Setters
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

    def set_address_type(self, address_type):
        self.address_type = address_type

    def set_address_key(self, address_key):
        self.address_key = address_key

    def set_sub_national_area(self, sub_national_area):
        self.sub_national_area = sub_national_area

    def set_country_name(self, country_name):
        self.country_name = country_name

    def set_country_code(self, country_code):
        self.country_code = country_code

    def set_country_iso3(self, country_iso3):
        self.country_iso3 = country_iso3

    def set_country_number(self, country_number):
        self.country_number = country_number

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

    # Getters
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

    def get_address_type(self):
        return self.address_type or ""

    def get_address_key(self):
        return self.address_key or ""

    def get_sub_national_area(self):
        return self.sub_national_area or ""

    def get_country_name(self):
        return self.country_name or ""

    def get_country_code(self):
        return self.country_code or ""

    def get_country_iso3(self):
        return self.country_iso3 or ""

    def get_country_number(self):
        return self.country_number or ""

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
    
class PersonatorIdentityEmail(ResponseBase):
    def __init__(
        self, deliverability_confidence_score="", results="", email_address="", mailbox_name="", domain_name="", 
        top_level_domain="", top_level_domain_name="", date_checked="", email_age_estimated="", domain_age_estimated="", 
        domain_expiration_date="", domain_created_date="", domain_updated_date="", domain_email="", domain_organization="", 
        domain_address1="", domain_locality="", domain_administrative_area="", domain_postal_code="", domain_country="", 
        domain_availability="", domain_country_code="", domain_private_proxy="", privacy_flag="", mx_server="", breach_count=""
    ):
        self.deliverability_confidence_score = deliverability_confidence_score
        self.results = results
        self.email_address = email_address
        self.mailbox_name = mailbox_name
        self.domain_name = domain_name
        self.top_level_domain = top_level_domain
        self.top_level_domain_name = top_level_domain_name
        self.date_checked = date_checked
        self.email_age_estimated = email_age_estimated
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
        self.domain_availability = domain_availability
        self.domain_country_code = domain_country_code
        self.domain_private_proxy = domain_private_proxy
        self.privacy_flag = privacy_flag
        self.mx_server = mx_server
        self.breach_count = breach_count

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            deliverability_confidence_score=data.get("DeliverabilityConfidenceScore", ""),
            results=data.get("Results", ""),
            email_address=data.get("EmailAddress", ""),
            mailbox_name=data.get("MailboxName", ""),
            domain_name=data.get("DomainName", ""),
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
            domain_availability=data.get("DomainAvailability", ""),
            domain_country_code=data.get("DomainCountryCode", ""),
            domain_private_proxy=data.get("DomainPrivateProxy", ""),
            privacy_flag=data.get("PrivacyFlag", ""),
            mx_server=data.get("MXServer", ""),
            breach_count=data.get("BreachCount", "")
        )
    
    # Setters
    def set_deliverability_confidence_score(self, deliverability_confidence_score):
        self.deliverability_confidence_score = deliverability_confidence_score

    def set_results(self, results):
        self.results = results

    def set_email_address(self, email_address):
        self.email_address = email_address

    def set_mailbox_name(self, mailbox_name):
        self.mailbox_name = mailbox_name

    def set_domain_name(self, domain_name):
        self.domain_name = domain_name

    def set_top_level_domain(self, top_level_domain):
        self.top_level_domain = top_level_domain

    def set_top_level_domain_name(self, top_level_domain_name):
        self.top_level_domain_name = top_level_domain_name

    def set_date_checked(self, date_checked):
        self.date_checked = date_checked

    def set_email_age_estimated(self, email_age_estimated):
        self.email_age_estimated = email_age_estimated

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

    def set_domain_availability(self, domain_availability):
        self.domain_availability = domain_availability

    def set_domain_country_code(self, domain_country_code):
        self.domain_country_code = domain_country_code

    def set_domain_private_proxy(self, domain_private_proxy):
        self.domain_private_proxy = domain_private_proxy

    def set_privacy_flag(self, privacy_flag):
        self.privacy_flag = privacy_flag

    def set_mx_server(self, mx_server):
        self.mx_server = mx_server

    def set_breach_count(self, breach_count):
        self.breach_count = breach_count

    # Getters
    def get_deliverability_confidence_score(self):
        return self.deliverability_confidence_score or ""

    def get_results(self):
        return self.results or ""

    def get_email_address(self):
        return self.email_address or ""

    def get_mailbox_name(self):
        return self.mailbox_name or ""

    def get_domain_name(self):
        return self.domain_name or ""

    def get_top_level_domain(self):
        return self.top_level_domain or ""

    def get_top_level_domain_name(self):
        return self.top_level_domain_name or ""

    def get_date_checked(self):
        return self.date_checked or ""

    def get_email_age_estimated(self):
        return self.email_age_estimated or ""

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

    def get_domain_availability(self):
        return self.domain_availability or ""

    def get_domain_country_code(self):
        return self.domain_country_code or ""

    def get_domain_private_proxy(self):
        return self.domain_private_proxy or ""

    def get_privacy_flag(self):
        return self.privacy_flag or ""

    def get_mx_server(self):
        return self.mx_server or ""

    def get_breach_count(self):
        return self.breach_count or ""

class PersonatorIdentityPhone(ResponseBase):
    def __init__(
        self, results="", phone_number="", administrative_area="", country_abbreviation="", country_name="", carrier="", 
        caller_id="", international_phone_number="", language="", latitude="", locality="", longitude="", phone_international_prefix="", 
        phone_country_dialing_code="", phone_nation_prefix="", phone_national_destination_code="", phone_subscriber_number="", utc="", 
        postal_code="", suggestions="", dst="", time_zone_code="", time_zone_name=""
    ):
        self.results = results
        self.phone_number = phone_number
        self.administrative_area = administrative_area
        self.country_abbreviation = country_abbreviation
        self.country_name = country_name
        self.carrier = carrier
        self.caller_id = caller_id
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
        self.dst = dst
        self.time_zone_code = time_zone_code
        self.time_zone_name = time_zone_name

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            results=data.get("Results", ""),
            phone_number=data.get("PhoneNumber", ""),
            administrative_area=data.get("AdministrativeArea", ""),
            country_abbreviation=data.get("CountryAbbreviation", ""),
            country_name=data.get("CountryName", ""),
            carrier=data.get("Carrier", ""),
            caller_id=data.get("CallerID", ""),
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
            dst=data.get("DST", ""),
            time_zone_code=data.get("TimeZoneCode", ""),
            time_zone_name=data.get("TimeZoneName", "")
        )
    
    # Setters
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

    def set_dst(self, dst):
        self.dst = dst

    def set_time_zone_code(self, time_zone_code):
        self.time_zone_code = time_zone_code

    def set_time_zone_name(self, time_zone_name):
        self.time_zone_name = time_zone_name

    # Getters
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

    def get_dst(self):
        return self.dst or ""

    def get_time_zone_code(self):
        return self.time_zone_code or ""

    def get_time_zone_name(self):
        return self.time_zone_name or ""


class PersonatorIdentityIdentity(ResponseBase):
    def __init__(self, results="", confidence="", datasources=None, watchlists=None, 
                 watchlist_persons="", national_id="", date_of_birth="", account_number=None, 
                 business_information=None
    ):
        self.results = results
        self.confidence = confidence
        self.datasources = datasources if datasources is not None else []
        self.watchlists = watchlists
        self.watchlist_persons = watchlist_persons
        self.national_id = national_id
        self.date_of_birth = date_of_birth
        self.account_number = account_number
        self.business_information = business_information

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            results=data.get("Results", ""),
            confidence=data.get("Confidence", ""),
            datasources=data.get("Datasources", []),
            watchlists=IdentityWatchlists.from_dict(data["Watchlists"]) if data.get("Watchlists") else None,
            watchlist_persons=data.get("WatchlistPersons", ""),
            national_id=data.get("NationalID", ""),
            date_of_birth=data.get("DateOfBirth", ""),
            account_number=IdentityAccountNumber.from_dict(data["AccountNumber"]) if data.get("AccountNumber") else None,
            business_information=IdentityBusinessInformation.from_dict(data["BusinessInformation"]) if data.get("BusinessInformation") else None
        )

    # Setters
    def set_results(self, results):
        self.results = results

    def set_confidence(self, confidence):
        self.confidence = confidence

    def set_datasources(self, datasources):
        self.datasources = datasources

    def set_watchlists(self, watchlists):
        self.watchlists = watchlists

    def set_watchlist_persons(self, watchlist_persons):
        self.watchlist_persons = watchlist_persons

    def set_national_id(self, national_id):
        self.national_id = national_id

    def set_date_of_birth(self, date_of_birth):
        self.date_of_birth = date_of_birth

    def set_account_number(self, account_number):
        self.account_number = account_number

    def set_business_information(self, business_information):
        self.business_information = business_information
    
    # Getters
    def get_results(self):
        return self.results or ""

    def get_confidence(self):
        return self.confidence or ""

    def get_datasources(self):
        return self.datasources or []

    def get_watchlists(self):
        return self.watchlists or None

    def get_watchlist_persons(self):
        return self.watchlist_persons or ""

    def get_national_id(self):
        return self.national_id or ""

    def get_date_of_birth(self):
        return self.date_of_birth or ""

    def get_account_number(self):
        return self.account_number or None

    def get_business_information(self):
        return self.business_information or None

class IdentityWatchlists(ResponseBase):
    def __init__(self, hit="", sources=None, articles=None, report_link=""):
        self.hit = hit
        self.sources = sources if sources is not None else []
        self.articles = articles if articles is not None else []
        self.report_link = report_link

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            hit=data.get("Hit", ""),
            sources=data.get("Sources", []),
            articles=data.get("Articles", []),
            report_link=data.get("ReportLink", "")
        )

    # Setters
    def set_hit(self, hit):
        self.hit = hit

    def set_report_link(self, report_link):
        self.report_link = report_link

    # Getters
    def get_hit(self):
        return self.hit or ""

    def get_report_link(self):
        return self.report_link or ""
    

class IdentityAccountNumber(ResponseBase):
    def __init__(self, validated=""):
        self.validated = validated

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            validated=data.get("Validated", "")
        )

    # Setters
    def set_validated(self, validated):
        self.validated = validated

    # Getters
    def get_validated(self):
        return self.validated or ""

class IdentityBusinessInformation(ResponseBase):
    def __init__(self, name="", id="", status="", type="", registration_date=""):
        self.name = name
        self.id = id
        self.status = status
        self.type = type
        self.registration_date = registration_date

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            name=data.get("Name", ""),
            id=data.get("ID", ""),
            status=data.get("Status", ""),
            type=data.get("Type", ""),
            registration_date=data.get("RegistrationDate", "")
        )

    # Setters
    def set_name(self, name):
        self.name = name

    def set_id(self, id):
        self.id = id

    def set_status(self, status):
        self.status = status

    def set_type(self, type):
        self.type = type

    def set_registration_date(self, registration_date):
        self.registration_date = registration_date

    # Getters
    def get_name(self):
        return self.name or ""

    def get_id(self):
        return self.id or ""

    def get_status(self):
        return self.status or ""

    def get_type(self):
        return self.type or ""

    def get_registration_date(self):
        return self.registration_date or ""

