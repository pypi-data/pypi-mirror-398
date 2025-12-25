import json
import os
from .CloudApiBase import CloudApiBase
from ..PostReqestBase import GlobalAddressVerificationPostRequest

class GlobalAddressVerification(CloudApiBase):
    def __init__(self, license=None):
        
        super().__init__("https://address.melissadata.net", "/v3/WEB/GlobalAddress/doGlobalAddress")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"
        self.records = []
        self.post_body = None

        self.parameter_mappings = {
            "organization": "org",
            "last_name": "last",
            "address_line_1": "a1",
            "address_line_2": "a2",
            "address_line_3": "a3",
            "address_line_4": "a4",
            "address_line_5": "a5",
            "address_line_6": "a6",
            "address_line_7": "a7",
            "address_line_8": "a8",
            "double_dependent_locality": "ddeploc",
            "dependent_locality": "deploc",
            "locality": "loc",
            "administrative_area": "admarea",
            "postal": "postal",
            "sub_national_area": "subnatarea",
            "country": "ctry",
            "transmission_reference": "t",
            "opt": "opt"
        }

        # Initialize private backing fields
        for attr in self.parameter_mappings.keys():
            setattr(self, f"_{attr}", None)

    def _set_parameter(self, attr_name, value):
        """
        Helper method to set a private attribute and update the parameters dictionary.
        """
        
        setattr(self, f"_{attr_name}", value)
        self.parameters[self.parameter_mappings[attr_name]] = value

    # Properties
    
    @property
    def organization(self):
        return self._organization

    @organization.setter
    def organization(self, value):
        self._set_parameter("organization", value)

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        self._set_parameter("last_name", value)

    @property
    def address_line_1(self):
        return self._address_line_1

    @address_line_1.setter
    def address_line_1(self, value):
        self._set_parameter("address_line_1", value)

    @property
    def address_line_2(self):
        return self._address_line_2

    @address_line_2.setter
    def address_line_2(self, value):
        self._set_parameter("address_line_2", value)

    @property
    def address_line_3(self):
        return self._address_line_3

    @address_line_3.setter
    def address_line_3(self, value):
        self._set_parameter("address_line_3", value)

    @property
    def address_line_4(self):
        return self._address_line_4

    @address_line_4.setter
    def address_line_4(self, value):
        self._set_parameter("address_line_4", value)

    @property
    def address_line_5(self):
        return self._address_line_5

    @address_line_5.setter
    def address_line_5(self, value):
        self._set_parameter("address_line_5", value)

    @property
    def address_line_6(self):
        return self._address_line_6

    @address_line_6.setter
    def address_line_6(self, value):
        self._set_parameter("address_line_6", value)

    @property
    def address_line_7(self):
        return self._address_line_7

    @address_line_7.setter
    def address_line_7(self, value):
        self._set_parameter("address_line_7", value)

    @property
    def address_line_8(self):
        return self._address_line_8

    @address_line_8.setter
    def address_line_8(self, value):
        self._set_parameter("address_line_8", value)

    @property
    def double_dependent_locality(self):
        return self._double_dependent_locality

    @double_dependent_locality.setter
    def double_dependent_locality(self, value):
        self._set_parameter("double_dependent_locality", value)

    @property
    def dependent_locality(self):
        return self._dependent_locality

    @dependent_locality.setter
    def dependent_locality(self, value):
        self._set_parameter("dependent_locality", value)

    @property
    def locality(self):
        return self._locality

    @locality.setter
    def locality(self, value):
        self._set_parameter("locality", value)

    @property
    def administrative_area(self):
        return self._administrative_area

    @administrative_area.setter
    def administrative_area(self, value):
        self._set_parameter("administrative_area", value)

    @property
    def postal(self):
        return self._postal

    @postal.setter
    def postal(self, value):
        self._set_parameter("postal", value)

    @property
    def sub_national_area(self):
        return self._sub_national_area

    @sub_national_area.setter
    def sub_national_area(self, value):
        self._set_parameter("sub_national_area", value)

    @property
    def country(self):
        return self._country

    @country.setter
    def country(self, value):
        self._set_parameter("country", value)

    @property
    def transmission_reference(self):
        return self._transmission_reference

    @transmission_reference.setter
    def transmission_reference(self, value):
        self._set_parameter("transmission_reference", value)

    @property
    def opt(self):
        return self._opt

    @opt.setter
    def opt(self, value):
        self._set_parameter("opt", value)

    # Setters

    def set_organization(self, organization):
        self._set_parameter("organization", organization)

    def set_last_name(self, last_name):
        self._set_parameter("last_name", last_name)

    def set_address_line_1(self, address_line_1):
        self._set_parameter("address_line_1", address_line_1)

    def set_address_line_2(self, address_line_2):
        self._set_parameter("address_line_2", address_line_2)

    def set_address_line_3(self, address_line_3):
        self._set_parameter("address_line_3", address_line_3)

    def set_address_line_4(self, address_line_4):
        self._set_parameter("address_line_4", address_line_4)

    def set_address_line_5(self, address_line_5):
        self._set_parameter("address_line_5", address_line_5)

    def set_address_line_6(self, address_line_6):
        self._set_parameter("address_line_6", address_line_6)

    def set_address_line_7(self, address_line_7):
        self._set_parameter("address_line_7", address_line_7)

    def set_address_line_8(self, address_line_8):
        self._set_parameter("address_line_8", address_line_8)

    def set_double_dependent_locality(self, double_dependent_locality):
        self._set_parameter("double_dependent_locality", double_dependent_locality)

    def set_dependent_locality(self, dependent_locality):
        self._set_parameter("dependent_locality", dependent_locality)

    def set_locality(self, locality):
        self._set_parameter("locality", locality)

    def set_administrative_area(self, administrative_area):
        self._set_parameter("administrative_area", administrative_area)

    def set_postal(self, postal):
        self._set_parameter("postal", postal)

    def set_sub_national_area(self, sub_national_area):
        self._set_parameter("sub_national_area", sub_national_area)

    def set_country(self, country):
        self._set_parameter("country", country)

    def set_transmission_reference(self, transmission_reference):
        self._set_parameter("transmission_reference", transmission_reference)

    def set_opt(self, opt):
        self._set_parameter("opt", opt)

    def set_post_body(self, post_body):
        self.post_body = post_body

    def set_value(self, parameter, value):
        parameter = parameter.strip() if parameter else None
        
        if parameter in self.parameter_mappings:
            parameter_key = self.parameter_mappings[parameter]
            
            property_name = next((key for key, val in self.parameter_mappings.items() 
                                  if val.lower() == parameter_key.lower()), None)
            
            if property_name:
                if hasattr(self, property_name):
                    setattr(self, property_name, value)
        else:
            # If not in derived class, go to base class implementation
            super().set_value(parameter, value)

    # Getters

    def get_organization(self):
        return self.parameters.get(self.parameter_mappings["organization"], "")

    def get_last_name(self):
        return self.parameters.get(self.parameter_mappings["last_name"], "")

    def get_address_line_1(self):
        return self.parameters.get(self.parameter_mappings["address_line_1"], "")

    def get_address_line_2(self):
        return self.parameters.get(self.parameter_mappings["address_line_2"], "")

    def get_address_line_3(self):
        return self.parameters.get(self.parameter_mappings["address_line_3"], "")

    def get_address_line_4(self):
        return self.parameters.get(self.parameter_mappings["address_line_4"], "")

    def get_address_line_5(self):
        return self.parameters.get(self.parameter_mappings["address_line_5"], "")

    def get_address_line_6(self):
        return self.parameters.get(self.parameter_mappings["address_line_6"], "")

    def get_address_line_7(self):
        return self.parameters.get(self.parameter_mappings["address_line_7"], "")

    def get_address_line_8(self):
        return self.parameters.get(self.parameter_mappings["address_line_8"], "")

    def get_double_dependent_locality(self):
        return self.parameters.get(self.parameter_mappings["double_dependent_locality"], "")

    def get_dependent_locality(self):
        return self.parameters.get(self.parameter_mappings["dependent_locality"], "")

    def get_locality(self):
        return self.parameters.get(self.parameter_mappings["locality"], "")

    def get_administrative_area(self):
        return self.parameters.get(self.parameter_mappings["administrative_area"], "")

    def get_postal(self):
        return self.parameters.get(self.parameter_mappings["postal"], "")

    def get_sub_national_area(self):
        return self.parameters.get(self.parameter_mappings["sub_national_area"], "")

    def get_country(self):
        return self.parameters.get(self.parameter_mappings["country"], "")

    def get_transmission_reference(self):
        return self.parameters.get(self.parameter_mappings["transmission_reference"], "")

    def get_opt(self):
        return self.parameters.get(self.parameter_mappings["opt"], "")

    def get_post_body(self):
        return self.post_body

    # Class Methods

    def add_record(self, record):
        self.records.append(record)

    def clear_records(self):
        self.records.clear()

    def post(self, response_type):
        """
        This synchronous function makes the batch request using the post body.

        Returns:
            A string or deserialized json response object.
        """
        if self.records and len(self.records) > 0:
            post_request = GlobalAddressVerificationPostRequest(
                transmission_reference=self.get_transmission_reference(),
                options=self.get_opt(),
                records=self.records,
                customer_id=self.get_license()
            )
            response = self.send_post_request(post_request)
        else:
            response = self.send_post_request(self.post_body)

        return self.handle_response(response, response_type)


    def get_api_version(self):
        """
        Makes a synchronous getversion request and parses the response for the API version.

        Returns:
            The Cloud API version.
        """
        json_response = self.send_version_request()

        response_objectect = json.loads(json_response)

        global_address_verification_version = response_objectect.get("Version", "")

        return global_address_verification_version

