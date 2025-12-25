class BusinessCoderRecordRequest:
    def __init__(self, a1=None, a2=None, city=None, comp=None, ctry=None, freeform=None, mak=None, mek=None, phone=None, 
                 postal=None, rec=None, state=None, stock=None, suite=None, web=None):
        self.a1 = a1
        self.a2 = a2
        self.city = city
        self.comp = comp
        self.ctry = ctry
        self.freeform = freeform
        self.mak = mak
        self.mek = mek
        self.phone = phone
        self.postal = postal
        self.rec = rec
        self.state = state
        self.stock = stock
        self.suite = suite
        self.web = web

    def to_dict(self):
        return {
            "A1": self.a1,
            "A2": self.a2,
            "City": self.city,
            "Comp": self.comp,
            "Ctry": self.ctry,
            "Freeform": self.freeform,
            "Mak": self.mak,
            "Mek": self.mek,
            "Phone": self.phone,
            "Postal": self.postal,
            "Rec": self.rec,
            "State": self.state,
            "Stock": self.stock,
            "Suite": self.suite,
            "Web": self.web
        }

class GlobalAddressVerificationRecordRequest:
    def __init__(self, record_id=None, organization=None, address_line_1=None, address_line_2=None, 
                 address_line_3=None, address_line_4=None, address_line_5=None, address_line_6=None, 
                 address_line_7=None, address_line_8=None, double_dependent_locality=None, 
                 dependent_locality=None, locality=None, sub_administrative_area=None, 
                 administrative_area=None, postal_code=None, sub_national_area=None, country=None):
        
        self.record_id = record_id
        self.organization = organization
        self.address_line_1 = address_line_1
        self.address_line_2 = address_line_2
        self.address_line_3 = address_line_3
        self.address_line_4 = address_line_4
        self.address_line_5 = address_line_5
        self.address_line_6 = address_line_6
        self.address_line_7 = address_line_7
        self.address_line_8 = address_line_8
        self.double_dependent_locality = double_dependent_locality
        self.dependent_locality = dependent_locality
        self.locality = locality
        self.sub_administrative_area = sub_administrative_area
        self.administrative_area = administrative_area
        self.postal_code = postal_code
        self.sub_national_area = sub_national_area
        self.country = country

    def to_dict(self):
        return {
            "RecordID": self.record_id,
            "Organization": self.organization,
            "AddressLine1": self.address_line_1,
            "AddressLine2": self.address_line_2,
            "AddressLine3": self.address_line_3,
            "AddressLine4": self.address_line_4,
            "AddressLine5": self.address_line_5,
            "AddressLine6": self.address_line_6,
            "AddressLine7": self.address_line_7,
            "AddressLine8": self.address_line_8,
            "DoubleDependentLocality": self.double_dependent_locality,
            "DependentLocality": self.dependent_locality,
            "Locality": self.locality,
            "SubAdministrativeArea": self.sub_administrative_area,
            "AdministrativeArea": self.administrative_area,
            "PostalCode": self.postal_code,
            "SubNationalArea": self.sub_national_area,
            "Country": self.country,
        }

    
class GlobalEmailRecordRequest:
    def __init__(self, record_id=None, email=None):
        self.record_id = record_id
        self.email = email

    def to_dict(self):
        return {
            "RecordID": self.record_id,
            "Email": self.email
        }
    
class GlobalIPRecordRequest:
    def __init__(self, record_id=None, ip_address=None):
        self.record_id = record_id
        self.ip_address = ip_address

    def to_dict(self):
        return {
            "RecordID": self.record_id,
            "IPAddress": self.ip_address
        }

class GlobalNameRecordRequest:
    def __init__(self, record_id=None, full_name=None, company=None):
        self.record_id = record_id
        self.full_name = full_name
        self.company = company

    def to_dict(self):
        return {
            "RecordID": self.record_id,
            "FullName": self.full_name,
            "Company": self.company
        }
    
class GlobalPhoneRecordRequest:
    def __init__(self, record_id=None, phone_number=None, country=None, country_of_origin=None):
        self.record_id = record_id
        self.phone_number = phone_number
        self.country = country
        self.country_of_origin = country_of_origin

    def to_dict(self):
        return {
            "RecordID": self.record_id,
            "PhoneNumber": self.phone_number,
            "Country": self.country,
            "CountryOfOrigin": self.country_of_origin
        }
    

class PeopleBusinessSearchRecordRequest:
    def __init__(self, customer_id=None, match_level=None, max_records=None, transmission_reference=None,
                 address_line_1=None, administrative_area=None, country=None, locality=None, phone_number=None,
                 postal_code=None, premise_number=None, subpremises_number=None, thoroughfare_name=None,
                 thoroughfare_postdirection=None, thoroughfare_predirection=None, thoroughfare_trailing_type=None,
                 any_name=None, company_name=None, first_name=None, full_name=None, last_name=None, sub_user=None):
        self.customer_id = customer_id
        self.match_level = match_level
        self.max_records = max_records
        self.transmission_reference = transmission_reference

        # Address Parameters
        self.address_line_1 = address_line_1
        self.administrative_area = administrative_area
        self.country = country
        self.locality = locality
        self.phone_number = phone_number
        self.postal_code = postal_code
        self.premise_number = premise_number
        self.subpremises_number = subpremises_number
        self.thoroughfare_name = thoroughfare_name
        self.thoroughfare_postdirection = thoroughfare_postdirection
        self.thoroughfare_predirection = thoroughfare_predirection
        self.thoroughfare_trailing_type = thoroughfare_trailing_type

        # Name Parameters
        self.any_name = any_name
        self.company_name = company_name
        self.first_name = first_name
        self.full_name = full_name
        self.last_name = last_name
        self.sub_user = sub_user

    def to_dict(self):
        return {
            "CustomerID": self.customer_id,
            "MatchLevel": self.match_level,
            "MaxRecords": self.max_records,
            "TransmissionReference": self.transmission_reference,
            
            # Address Parameters
            "AddressLine1": self.address_line_1,
            "AdministrativeArea": self.administrative_area,
            "Country": self.country,
            "Locality": self.locality,
            "PhoneNumber": self.phone_number,
            "PostalCode": self.postal_code,
            "PremiseNumber": self.premise_number,
            "SubpremisesNumber": self.subpremises_number,
            "ThoroughfareName": self.thoroughfare_name,
            "ThoroughfarePostdirection": self.thoroughfare_postdirection,
            "ThoroughfarePredirection": self.thoroughfare_predirection,
            "ThoroughfareTrailingType": self.thoroughfare_trailing_type,
            
            # Name Parameters
            "AnyName": self.any_name,
            "CompanyName": self.company_name,
            "FirstName": self.first_name,
            "FullName": self.full_name,
            "LastName": self.last_name,
            "SubUser": self.sub_user
        }


class PersonatorConsumerRecordRequest:
    def __init__(self, record_id=None, address_line_1=None, address_line_2=None, birth_day=None, birth_month=None,
                 birth_year=None, city=None, company_name=None, country=None, email_address=None, first_name=None,
                 free_form=None, full_name=None, ip_address=None, last_line=None, last_name=None, melissa_address_key=None,
                 phone_number=None, postal_code=None, social_security=None, state=None):
        self.record_id = record_id
        self.address_line_1 = address_line_1
        self.address_line_2 = address_line_2
        self.birth_day = birth_day
        self.birth_month = birth_month
        self.birth_year = birth_year
        self.city = city
        self.company_name = company_name
        self.country = country
        self.email_address = email_address
        self.first_name = first_name
        self.free_form = free_form
        self.full_name = full_name
        self.ip_address = ip_address
        self.last_line = last_line
        self.last_name = last_name
        self.melissa_address_key = melissa_address_key
        self.phone_number = phone_number
        self.postal_code = postal_code
        self.social_security = social_security
        self.state = state

    def to_dict(self):
        return {
            "RecordID": self.record_id,
            "AddressLine1": self.address_line_1,
            "AddressLine2": self.address_line_2,
            "BirthDay": self.birth_day,
            "BirthMonth": self.birth_month,
            "BirthYear": self.birth_year,
            "City": self.city,
            "CompanyName": self.company_name,
            "Country": self.country,
            "EmailAddress": self.email_address,
            "FirstName": self.first_name,
            "FreeForm": self.free_form,
            "FullName": self.full_name,
            "IPAddress": self.ip_address,
            "LastLine": self.last_line,
            "LastName": self.last_name,
            "MelissaAddressKey": self.melissa_address_key,
            "PhoneNumber": self.phone_number,
            "PostalCode": self.postal_code,
            "SocialSecurity": self.social_security,
            "State": self.state
        }

class PersonatorIdentityRecordRequest():
    def __init__(
        self, transmission_reference="", customer_id="", actions="", address_options="", email_options="", phone_options="", 
        name_options="", options="", national_id="", first_name="", last_name="", full_name="", company="", phone_number="", 
        email="", date_of_birth="", account_number="", address_line_1="", address_line_2="", address_line_3="", address_line_4="", 
        address_line_5="", address_line_6="", address_line_7="", address_line_8="", locality="", administrative_area="", 
        postal_code="", country="", country_of_origin="", state=""
    ):
        self.transmission_reference = transmission_reference
        self.customer_id = customer_id
        self.actions = actions
        self.address_options = address_options
        self.email_options = email_options
        self.phone_options = phone_options
        self.name_options = name_options
        self.options = options
        self.national_id = national_id
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = full_name
        self.company = company
        self.phone_number = phone_number
        self.email = email
        self.date_of_birth = date_of_birth
        self.account_number = account_number
        self.address_line_1 = address_line_1
        self.address_line_2 = address_line_2
        self.address_line_3 = address_line_3
        self.address_line_4 = address_line_4
        self.address_line_5 = address_line_5
        self.address_line_6 = address_line_6
        self.address_line_7 = address_line_7
        self.address_line_8 = address_line_8
        self.locality = locality
        self.administrative_area = administrative_area
        self.postal_code = postal_code
        self.country = country
        self.country_of_origin = country_of_origin
        self.state = state

    def to_dict(self):
        return {
            "TransmissionReference": self.transmission_reference,
            "CustomerID": self.customer_id,
            "Actions": self.actions,
            "AddressOptions": self.address_options,
            "EmailOptions": self.email_options,
            "PhoneOptions": self.phone_options,
            "NameOptions": self.name_options,
            "Options": self.options,
            "NationalID": self.national_id,
            "FirstName": self.first_name,
            "LastName": self.last_name,
            "FullName": self.full_name,
            "Company": self.company,
            "PhoneNumber": self.phone_number,
            "Email": self.email,
            "DateOfBirth": self.date_of_birth,
            "AccountNumber": self.account_number,
            "AddressLine1": self.address_line_1,
            "AddressLine2": self.address_line_2,
            "AddressLine3": self.address_line_3,
            "AddressLine4": self.address_line_4,
            "AddressLine5": self.address_line_5,
            "AddressLine6": self.address_line_6,
            "AddressLine7": self.address_line_7,
            "AddressLine8": self.address_line_8,
            "Locality": self.locality,
            "AdministrativeArea": self.administrative_area,
            "PostalCode": self.postal_code,
            "Country": self.country,
            "CountryOfOrigin": self.country_of_origin,
            "State": self.state,
        }

class PropertyRecordRequest:
    def __init__(
        self, 
        transmission_reference="", customer_id="", columns="", options="",
        record_id="", account="", address_key="", address_line_1="", 
        address_line_2="", apn="", city="", country="", fips="", 
        free_form="", property_mak="", owner_mak="", mak="", 
        state="", postal_code="", transaction_id=""
    ):
        self.transmission_reference = transmission_reference
        self.customer_id = customer_id
        self.columns = columns
        self.options = options
        self.record_id = record_id
        self.account = account
        self.address_key = address_key
        self.address_line_1 = address_line_1
        self.address_line_2 = address_line_2
        self.apn = apn
        self.city = city
        self.country = country
        self.fips = fips
        self.free_form = free_form
        self.property_mak = property_mak
        self.owner_mak = owner_mak
        self.mak = mak
        self.state = state
        self.postal_code = postal_code
        self.transaction_id = transaction_id

    def to_dict(self):
        return {
            "TransmissionReference": self.transmission_reference,
            "CustomerId": self.customer_id,
            "Columns": self.columns,
            "Options": self.options,
            "RecordId": self.record_id,
            "Account": self.account,
            "AddressKey": self.address_key,
            "AddressLine1": self.address_line_1,
            "AddressLine2": self.address_line_2,
            "APN": self.apn,
            "City": self.city,
            "Country": self.country,
            "FIPS": self.fips,
            "FreeForm": self.free_form,
            "PropertyMAK": self.property_mak,
            "OwnerMAK": self.owner_mak,
            "MAK": self.mak,
            "State": self.state,
            "PostalCode": self.postal_code,
            "TransactionID": self.transaction_id
        }


class ReverseGeoCoderRecordRequest:
    def __init__(
        self,
        customer_id="",
        latitude="",
        longitude="",
        max_distance="",
        max_records="",
        options="",
        transmission_reference="",
    ):
        self.customer_id = customer_id
        self.latitude = latitude
        self.longitude = longitude
        self.max_distance = max_distance
        self.max_records = max_records
        self.options = options
        self.transmission_reference = transmission_reference

    def to_dict(self):
        return {
            "CustomerId": self.customer_id,
            "Latitude": self.latitude,
            "Longitude": self.longitude,
            "MaxDistance": self.max_distance,
            "MaxRecords": self.max_records,
            "Options": self.options,
            "TransmissionReference": self.transmission_reference,
        }

class SmartMoverRecordRequest:
    def __init__(self, record_id="", company="", name_full="", name_first="", name_middle="",
                 name_prefix="", name_suffix="", name_last="", urbanization="", address_line_1="",
                 address_line_2="", suite="", private_mailbox="", city="", state="", postal_code="",
                 plus4="", country=""):
        self.record_id = record_id
        self.company = company
        self.name_full = name_full
        self.name_first = name_first
        self.name_middle = name_middle
        self.name_prefix = name_prefix
        self.name_suffix = name_suffix
        self.name_last = name_last
        self.urbanization = urbanization
        self.address_line_1 = address_line_1
        self.address_line_2 = address_line_2
        self.suite = suite
        self.private_mailbox = private_mailbox
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.plus4 = plus4
        self.country = country

    def to_dict(self):
        return {
            "RecordID": self.record_id,
            "Company": self.company,
            "NameFull": self.name_full,
            "NameFirst": self.name_first,
            "NameMiddle": self.name_middle,
            "NamePrefix": self.name_prefix,
            "NameSuffix": self.name_suffix,
            "NameLast": self.name_last,
            "Urbanization": self.urbanization,
            "AddressLine1": self.address_line_1,
            "AddressLine2": self.address_line_2,
            "Suite": self.suite,
            "PrivateMailbox": self.private_mailbox,
            "City": self.city,
            "State": self.state,
            "PostalCode": self.postal_code,
            "Plus4": self.plus4,
            "Country": self.country
        }
    
class SSNNameMatchRecordRequest:
    def __init__(
        self,
        record_id="",
        ssn="",
        first_name="",
        last_name="",
        full_name=""
    ):
        self.record_id = record_id
        self.ssn = ssn
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = full_name

    def to_dict(self):
        return {
            "RecordID": self.record_id,
            "SSN": self.ssn,
            "FirstName": self.first_name,
            "LastName": self.last_name,
            "FullName": self.full_name
        }
    
class StreetRouteRecordRequest:
    def __init__(self, record_id="", start_latitude="", start_longitude="", end_latitude="", end_longitude=""):
        self.record_id = record_id
        self.start_latitude = start_latitude
        self.start_longitude = start_longitude
        self.end_latitude = end_latitude
        self.end_longitude = end_longitude

    def to_dict(self):
        return {
            "RecordID": self.record_id,
            "StartLatitude": self.start_latitude,
            "StartLongitude": self.start_longitude,
            "EndLatitude": self.end_latitude,
            "EndLongitude": self.end_longitude
        }

class TokenServerRecordRequest:
    def __init__(self, record_id="", ip="", l="", p="", ts=""):
        self.record_id = record_id
        self.ip = ip
        self.l = l
        self.p = p
        self.ts = ts

    def to_dict(self):
        return {
            "RecordID": self.record_id,
            "IP": self.ip,
            "L": self.l,
            "P": self.p,
            "TS": self.ts
        }


