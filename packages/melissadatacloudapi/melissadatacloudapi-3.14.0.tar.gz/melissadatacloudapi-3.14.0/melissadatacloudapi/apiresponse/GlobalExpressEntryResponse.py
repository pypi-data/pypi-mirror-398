from .ResponseBase import ResponseBase

class GlobalExpressEntryResponse(ResponseBase):

    def __init__(self, version="", result_code="", error_string="", results=None):
        self.version = version
        self.result_code = result_code
        self.error_string = error_string
        self.results = results if results is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        cls.data=data
        results = [GlobalExpressEntryRecord.from_dict(result) for result in data.get("Results", [])]
        return cls(
            version=data.get("Version", ""),
            result_code=data.get("ResultCode", ""),
            error_string=data.get("ErrorString", ""),
            results=results
        )

    # Setters
    def set_version(self, version):
        self.version = version

    def set_result_code(self, result_code):
        self.result_code = result_code

    def set_error_string(self, error_string):
        self.error_string = error_string

    # Getters
    def get_version(self):
        return self.version if self.version else ""

    def get_result_code(self):
        return self.result_code if self.result_code else ""

    def get_error_string(self):
        return self.error_string if self.error_string else ""
    
class GlobalExpressEntryRecord(ResponseBase):
    def __init__(self, address=None, country="", english="", spanish="", french="", german="", simplified_chinese="", char2_iso="", char3_iso="", iso_numeric=""):
        # For GlobalExpressAddress endpoint
        
        self.address = address  
        
        # For GlobalExpressCountry endpoint
        self.country = country
        self.english = english
        self.spanish = spanish
        self.french = french
        self.german = german
        self.simplified_chinese = simplified_chinese
        self.char2_iso = char2_iso
        self.char3_iso = char3_iso
        self.iso_numeric = iso_numeric

    @classmethod
    def from_dict(cls, data):
        cls.data=data
        return cls(
            address = GlobalExpressEntryAddress.from_dict(data.get("Address")) if data.get("Address") is not None else None,
            country=data.get("Country", ""),
            english=data.get("English", ""),
            spanish=data.get("Spanish", ""),
            french=data.get("French", ""),
            german=data.get("German", ""),
            simplified_chinese=data.get("SimplifiedChinese", ""),
            char2_iso=data.get("Char2ISO", ""),
            char3_iso=data.get("Char3ISO", ""),
            iso_numeric=data.get("ISONumeric", "")
        )
    
    # Setters
    def set_country(self, country):
        self.country = country

    def set_english(self, english):
        self.english = english

    def set_spanish(self, spanish):
        self.spanish = spanish

    def set_french(self, french):
        self.french = french

    def set_german(self, german):
        self.german = german

    def set_simplified_chinese(self, simplified_chinese):
        self.simplified_chinese = simplified_chinese

    def set_char2_iso(self, char2_iso):
        self.char2_iso = char2_iso

    def set_char3_iso(self, char3_iso):
        self.char3_iso = char3_iso

    def set_iso_numeric(self, iso_numeric):
        self.iso_numeric = iso_numeric

    # Getters
    def get_country(self):
        return self.country or ""

    def get_english(self):
        return self.english or ""

    def get_spanish(self):
        return self.spanish or ""

    def get_french(self):
        return self.french or ""

    def get_german(self):
        return self.german or ""

    def get_simplified_chinese(self):
        return self.simplified_chinese or ""

    def get_char2_iso(self):
        return self.char2_iso or ""

    def get_char3_iso(self):
        return self.char3_iso or ""

    def get_iso_numeric(self):
        return self.iso_numeric or ""

class GlobalExpressEntryAddress(ResponseBase):
    def __init__(self, address="", address1="", address2="", address3="", address4="", address5="", address6="",
                 address7="", address8="", address9="", address10="", address11="", address12="", delivery_address="",
                 delivery_address1="", delivery_address2="", delivery_address3="", delivery_address4="", delivery_address5="",
                 delivery_address6="", delivery_address7="", delivery_address8="", delivery_address9="", delivery_address10="",
                 delivery_address11="", delivery_address12="", country_name="", iso3166_2="", iso3166_3="", iso3166_n="",
                 super_administrative_area="", administrative_area="", sub_administrative_area="", locality="",
                 city_accepted="", city_not_accepted="", dependent_locality="", double_dependent_locality="", thoroughfare="",
                 dependent_thoroughfare="", building="", premise="", sub_building="", postal_code="", postal_code_primary="",
                 postal_code_secondary="", organization="", post_box="", unmatched="", general_delivery="", delivery_installation="",
                 route="", additional_content="", country_subdivision_code="", mak="", base_mak="", latitude="", longitude="",
                 distance_from_point=""):
        
        self.address = address
        self.address1 = address1
        self.address2 = address2
        self.address3 = address3
        self.address4 = address4
        self.address5 = address5
        self.address6 = address6
        self.address7 = address7
        self.address8 = address8
        self.address9 = address9
        self.address10 = address10
        self.address11 = address11
        self.address12 = address12
        self.delivery_address = delivery_address
        self.delivery_address1 = delivery_address1
        self.delivery_address2 = delivery_address2
        self.delivery_address3 = delivery_address3
        self.delivery_address4 = delivery_address4
        self.delivery_address5 = delivery_address5
        self.delivery_address6 = delivery_address6
        self.delivery_address7 = delivery_address7
        self.delivery_address8 = delivery_address8
        self.delivery_address9 = delivery_address9
        self.delivery_address10 = delivery_address10
        self.delivery_address11 = delivery_address11
        self.delivery_address12 = delivery_address12
        self.country_name = country_name
        self.iso3166_2 = iso3166_2
        self.iso3166_3 = iso3166_3
        self.iso3166_n = iso3166_n
        self.super_administrative_area = super_administrative_area
        self.administrative_area = administrative_area
        self.sub_administrative_area = sub_administrative_area
        self.locality = locality
        self.city_accepted = city_accepted
        self.city_not_accepted = city_not_accepted
        self.dependent_locality = dependent_locality
        self.double_dependent_locality = double_dependent_locality
        self.thoroughfare = thoroughfare
        self.dependent_thoroughfare = dependent_thoroughfare
        self.building = building
        self.premise = premise
        self.sub_building = sub_building
        self.postal_code = postal_code
        self.postal_code_primary = postal_code_primary
        self.postal_code_secondary = postal_code_secondary
        self.organization = organization
        self.post_box = post_box
        self.unmatched = unmatched
        self.general_delivery = general_delivery
        self.delivery_installation = delivery_installation
        self.route = route
        self.additional_content = additional_content
        self.country_subdivision_code = country_subdivision_code
        self.mak = mak
        self.base_mak = base_mak
        self.latitude = latitude
        self.longitude = longitude
        self.distance_from_point = distance_from_point

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            address=data.get("Address", ""),
            address1=data.get("Address1", ""),
            address2=data.get("Address2", ""),
            address3=data.get("Address3", ""),
            address4=data.get("Address4", ""),
            address5=data.get("Address5", ""),
            address6=data.get("Address6", ""),
            address7=data.get("Address7", ""),
            address8=data.get("Address8", ""),
            address9=data.get("Address9", ""),
            address10=data.get("Address10", ""),
            address11=data.get("Address11", ""),
            address12=data.get("Address12", ""),
            delivery_address=data.get("DeliveryAddress", ""),
            delivery_address1=data.get("DeliveryAddress1", ""),
            delivery_address2=data.get("DeliveryAddress2", ""),
            delivery_address3=data.get("DeliveryAddress3", ""),
            delivery_address4=data.get("DeliveryAddress4", ""),
            delivery_address5=data.get("DeliveryAddress5", ""),
            delivery_address6=data.get("DeliveryAddress6", ""),
            delivery_address7=data.get("DeliveryAddress7", ""),
            delivery_address8=data.get("DeliveryAddress8", ""),
            delivery_address9=data.get("DeliveryAddress9", ""),
            delivery_address10=data.get("DeliveryAddress10", ""),
            delivery_address11=data.get("DeliveryAddress11", ""),
            delivery_address12=data.get("DeliveryAddress12", ""),
            country_name=data.get("CountryName", ""),
            iso3166_2=data.get("ISO3166_2", ""),
            iso3166_3=data.get("ISO3166_3", ""),
            iso3166_n=data.get("ISO3166_N", ""),
            super_administrative_area=data.get("SuperAdministrativeArea", ""),
            administrative_area=data.get("AdministrativeArea", ""),
            sub_administrative_area=data.get("SubAdministrativeArea", ""),
            locality=data.get("Locality", ""),
            city_accepted=data.get("CityAccepted", ""),
            city_not_accepted=data.get("CityNotAccepted", ""),
            dependent_locality=data.get("DependentLocality", ""),
            double_dependent_locality=data.get("DoubleDependentLocality", ""),
            thoroughfare=data.get("Thoroughfare", ""),
            dependent_thoroughfare=data.get("DependentThoroughfare", ""),
            building=data.get("Building", ""),
            premise=data.get("Premise", ""),
            sub_building=data.get("SubBuilding", ""),
            postal_code=data.get("PostalCode", ""),
            postal_code_primary=data.get("PostalCodePrimary", ""),
            postal_code_secondary=data.get("PostalCodeSecondary", ""),
            organization=data.get("Organization", ""),
            post_box=data.get("PostBox", ""),
            unmatched=data.get("Unmatched", ""),
            general_delivery=data.get("GeneralDelivery", ""),
            delivery_installation=data.get("DeliveryInstallation", ""),
            route=data.get("Route", ""),
            additional_content=data.get("AdditionalContent", ""),
            country_subdivision_code=data.get("CountrySubdivisionCode", ""),
            mak=data.get("MAK", ""),
            base_mak=data.get("BaseMAK", ""),
            latitude=data.get("Latitude", ""),
            longitude=data.get("Longitude", ""),
            distance_from_point=data.get("DistanceFromPoint", "")
        )
    
    # Setters
    def set_address(self, address):
        self.address = address

    def set_address1(self, address1):
        self.address1 = address1

    def set_address2(self, address2):
        self.address2 = address2

    def set_address3(self, address3):
        self.address3 = address3

    def set_address4(self, address4):
        self.address4 = address4

    def set_address5(self, address5):
        self.address5 = address5

    def set_address6(self, address6):
        self.address6 = address6

    def set_address7(self, address7):
        self.address7 = address7

    def set_address8(self, address8):
        self.address8 = address8

    def set_address9(self, address9):
        self.address9 = address9

    def set_address10(self, address10):
        self.address10 = address10

    def set_address11(self, address11):
        self.address11 = address11

    def set_address12(self, address12):
        self.address12 = address12

    def set_delivery_address(self, delivery_address):
        self.delivery_address = delivery_address

    def set_delivery_address1(self, delivery_address1):
        self.delivery_address1 = delivery_address1

    def set_delivery_address2(self, delivery_address2):
        self.delivery_address2 = delivery_address2

    def set_delivery_address3(self, delivery_address3):
        self.delivery_address3 = delivery_address3

    def set_delivery_address4(self, delivery_address4):
        self.delivery_address4 = delivery_address4

    def set_delivery_address5(self, delivery_address5):
        self.delivery_address5 = delivery_address5

    def set_delivery_address6(self, delivery_address6):
        self.delivery_address6 = delivery_address6

    def set_delivery_address7(self, delivery_address7):
        self.delivery_address7 = delivery_address7

    def set_delivery_address8(self, delivery_address8):
        self.delivery_address8 = delivery_address8

    def set_delivery_address9(self, delivery_address9):
        self.delivery_address9 = delivery_address9

    def set_delivery_address10(self, delivery_address10):
        self.delivery_address10 = delivery_address10

    def set_delivery_address11(self, delivery_address11):
        self.delivery_address11 = delivery_address11

    def set_delivery_address12(self, delivery_address12):
        self.delivery_address12 = delivery_address12

    def set_country_name(self, country_name):
        self.country_name = country_name

    def set_iso3166_2(self, iso3166_2):
        self.iso3166_2 = iso3166_2

    def set_iso3166_3(self, iso3166_3):
        self.iso3166_3 = iso3166_3

    def set_iso3166_n(self, iso3166_n):
        self.iso3166_n = iso3166_n

    def set_super_administrative_area(self, super_administrative_area):
        self.super_administrative_area = super_administrative_area

    def set_administrative_area(self, administrative_area):
        self.administrative_area = administrative_area

    def set_sub_administrative_area(self, sub_administrative_area):
        self.sub_administrative_area = sub_administrative_area

    def set_locality(self, locality):
        self.locality = locality

    def set_city_accepted(self, city_accepted):
        self.city_accepted = city_accepted

    def set_city_not_accepted(self, city_not_accepted):
        self.city_not_accepted = city_not_accepted

    def set_dependent_locality(self, dependent_locality):
        self.dependent_locality = dependent_locality

    def set_double_dependent_locality(self, double_dependent_locality):
        self.double_dependent_locality = double_dependent_locality

    def set_thoroughfare(self, thoroughfare):
        self.thoroughfare = thoroughfare

    def set_dependent_thoroughfare(self, dependent_thoroughfare):
        self.dependent_thoroughfare = dependent_thoroughfare

    def set_building(self, building):
        self.building = building

    def set_premise(self, premise):
        self.premise = premise

    def set_sub_building(self, sub_building):
        self.sub_building = sub_building

    def set_postal_code(self, postal_code):
        self.postal_code = postal_code

    def set_postal_code_primary(self, postal_code_primary):
        self.postal_code_primary = postal_code_primary

    def set_postal_code_secondary(self, postal_code_secondary):
        self.postal_code_secondary = postal_code_secondary

    def set_organization(self, organization):
        self.organization = organization

    def set_post_box(self, post_box):
        self.post_box = post_box

    def set_unmatched(self, unmatched):
        self.unmatched = unmatched

    def set_general_delivery(self, general_delivery):
        self.general_delivery = general_delivery

    def set_delivery_installation(self, delivery_installation):
        self.delivery_installation = delivery_installation

    def set_route(self, route):
        self.route = route

    def set_additional_content(self, additional_content):
        self.additional_content = additional_content

    def set_country_subdivision_code(self, country_subdivision_code):
        self.country_subdivision_code = country_subdivision_code

    def set_mak(self, mak):
        self.mak = mak

    def set_base_mak(self, base_mak):
        self.base_mak = base_mak

    def set_latitude(self, latitude):
        self.latitude = latitude

    def set_longitude(self, longitude):
        self.longitude = longitude

    def set_distance_from_point(self, distance_from_point):
        self.distance_from_point = distance_from_point

    # Getters
    def get_address(self):
        return self.address or ""

    def get_address1(self):
        return self.address1 or ""

    def get_address2(self):
        return self.address2 or ""

    def get_address3(self):
        return self.address3 or ""

    def get_address4(self):
        return self.address4 or ""

    def get_address5(self):
        return self.address5 or ""

    def get_address6(self):
        return self.address6 or ""

    def get_address7(self):
        return self.address7 or ""

    def get_address8(self):
        return self.address8 or ""

    def get_address9(self):
        return self.address9 or ""

    def get_address10(self):
        return self.address10 or ""

    def get_address11(self):
        return self.address11 or ""

    def get_address12(self):
        return self.address12 or ""

    def get_delivery_address(self):
        return self.delivery_address or ""

    def get_delivery_address1(self):
        return self.delivery_address1 or ""

    def get_delivery_address2(self):
        return self.delivery_address2 or ""

    def get_delivery_address3(self):
        return self.delivery_address3 or ""

    def get_delivery_address4(self):
        return self.delivery_address4 or ""

    def get_delivery_address5(self):
        return self.delivery_address5 or ""

    def get_delivery_address6(self):
        return self.delivery_address6 or ""

    def get_delivery_address7(self):
        return self.delivery_address7 or ""

    def get_delivery_address8(self):
        return self.delivery_address8 or ""

    def get_delivery_address9(self):
        return self.delivery_address9 or ""

    def get_delivery_address10(self):
        return self.delivery_address10 or ""

    def get_delivery_address11(self):
        return self.delivery_address11 or ""

    def get_delivery_address12(self):
        return self.delivery_address12 or ""

    def get_country_name(self):
        return self.country_name or ""

    def get_iso3166_2(self):
        return self.iso3166_2 or ""

    def get_iso3166_3(self):
        return self.iso3166_3 or ""

    def get_iso3166_n(self):
        return self.iso3166_n or ""

    def get_super_administrative_area(self):
        return self.super_administrative_area or ""

    def get_administrative_area(self):
        return self.administrative_area or ""

    def get_sub_administrative_area(self):
        return self.sub_administrative_area or ""

    def get_locality(self):
        return self.locality or ""

    def get_city_accepted(self):
        return self.city_accepted or ""

    def get_city_not_accepted(self):
        return self.city_not_accepted or ""

    def get_dependent_locality(self):
        return self.dependent_locality or ""

    def get_double_dependent_locality(self):
        return self.double_dependent_locality or ""

    def get_thoroughfare(self):
        return self.thoroughfare or ""

    def get_dependent_thoroughfare(self):
        return self.dependent_thoroughfare or ""

    def get_building(self):
        return self.building or ""

    def get_premise(self):
        return self.premise or ""

    def get_sub_building(self):
        return self.sub_building or ""

    def get_postal_code(self):
        return self.postal_code or ""

    def get_postal_code_primary(self):
        return self.postal_code_primary or ""

    def get_postal_code_secondary(self):
        return self.postal_code_secondary or ""

    def get_organization(self):
        return self.organization or ""

    def get_post_box(self):
        return self.post_box or ""

    def get_unmatched(self):
        return self.unmatched or ""

    def get_general_delivery(self):
        return self.general_delivery or ""

    def get_delivery_installation(self):
        return self.delivery_installation or ""

    def get_route(self):
        return self.route or ""

    def get_additional_content(self):
        return self.additional_content or ""

    def get_country_subdivision_code(self):
        return self.country_subdivision_code or ""

    def get_mak(self):
        return self.mak or ""

    def get_base_mak(self):
        return self.base_mak or ""

    def get_latitude(self):
        return self.latitude or ""

    def get_longitude(self):
        return self.longitude or ""

    def get_distance_from_point(self):
        return self.distance_from_point or ""



    
