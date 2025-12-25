import json
import os
from .CloudApiBase import CloudApiBase
from ..RecordRequests import PersonatorIdentityRecordRequest


class PersonatorIdentity(CloudApiBase):

    def __init__(self, license=None):
        super().__init__("https://globalpersonator.melissadata.net", "/v1/doContactVerify")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"
        self.post_body = None

        self.parameter_mappings = {
            "action": "act",
            "national_id": "nat",
            "first_name": "first",
            "last_name": "last",
            "full_name": "full",
            "company": "comp",
            "phone": "phone",
            "email": "email",
            "dob": "dob",
            "account_number": "accountNumber",
            "address_line_1": "a1",
            "address_line_2": "a2",
            "address_line_3": "a3",
            "address_line_4": "a4",
            "address_line_5": "a5",
            "address_line_6": "a6",
            "address_line_7": "a7",
            "address_line_8": "a8",
            "locality": "loc",
            "administrative_area": "admarea",
            "postal": "postal",
            "country": "ctry",
            "country_origin": "ctryOrg",
            "transmission_reference": "t",
            "address_opt": "addrOpt",
            "name_opt": "nameOpt",
            "email_opt": "emailOpt",
            "phone_opt": "phoneOpt",
            "opt": "opt",
            "privacy": "privacy"
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
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        self._set_parameter("action", value)

    @property
    def national_id(self):
        return self._national_id

    @national_id.setter
    def national_id(self, value):
        self._set_parameter("national_id", value)

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, value):
        self._set_parameter("first_name", value)

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        self._set_parameter("last_name", value)

    @property
    def full_name(self):
        return self._full_name

    @full_name.setter
    def full_name(self, value):
        self._set_parameter("full_name", value)

    @property
    def company(self):
        return self._company

    @company.setter
    def company(self, value):
        self._set_parameter("company", value)

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, value):
        self._set_parameter("phone", value)

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._set_parameter("email", value)

    @property
    def dob(self):
        return self._dob

    @dob.setter
    def dob(self, value):
        self._set_parameter("dob", value)

    @property
    def account_number(self):
        return self._account_number

    @account_number.setter
    def account_number(self, value):
        self._set_parameter("account_number", value)

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
    def country(self):
        return self._country

    @country.setter
    def country(self, value):
        self._set_parameter("country", value)

    @property
    def country_origin(self):
        return self._country_origin

    @country_origin.setter
    def country_origin(self, value):
        self._set_parameter("country_origin", value)

    @property
    def transmission_reference(self):
        return self._transmission_reference

    @transmission_reference.setter
    def transmission_reference(self, value):
        self._set_parameter("transmission_reference", value)

    @property
    def address_opt(self):
        return self._address_opt

    @address_opt.setter
    def address_opt(self, value):
        self._set_parameter("address_opt", value)

    @property
    def name_opt(self):
        return self._name_opt

    @name_opt.setter
    def name_opt(self, value):
        self._set_parameter("name_opt", value)

    @property
    def email_opt(self):
        return self._email_opt

    @email_opt.setter
    def email_opt(self, value):
        self._set_parameter("email_opt", value)

    @property
    def phone_opt(self):
        return self._phone_opt

    @phone_opt.setter
    def phone_opt(self, value):
        self._set_parameter("phone_opt", value)

    @property
    def opt(self):
        return self._opt

    @opt.setter
    def opt(self, value):
        self._set_parameter("opt", value)

    @property
    def privacy(self):
        return self._privacy

    @privacy.setter
    def privacy(self, value):
        self._set_parameter("privacy", value)

    # Setters

    def set_action(self, action):
        self._set_parameter("action", action)

    def set_national_id(self, national_id):
        self._set_parameter("national_id", national_id)

    def set_first_name(self, first_name):
        self._set_parameter("first_name", first_name)

    def set_last_name(self, last_name):
        self._set_parameter("last_name", last_name)

    def set_full_name(self, full_name):
        self._set_parameter("full_name", full_name)

    def set_company(self, company):
        self._set_parameter("company", company)

    def set_phone(self, phone):
        self._set_parameter("phone", phone)

    def set_email(self, email):
        self._set_parameter("email", email)

    def set_dob(self, dob):
        self._set_parameter("dob", dob)

    def set_account_number(self, account_number):
        self._set_parameter("account_number", account_number)

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

    def set_locality(self, locality):
        self._set_parameter("locality", locality)

    def set_administrative_area(self, administrative_area):
        self._set_parameter("administrative_area", administrative_area)

    def set_postal(self, postal):
        self._set_parameter("postal", postal)

    def set_country(self, country):
        self._set_parameter("country", country)

    def set_country_origin(self, country_origin):
        self._set_parameter("country_origin", country_origin)

    def set_transmission_reference(self, transmission_reference):
        self._set_parameter("transmission_reference", transmission_reference)

    def set_address_opt(self, address_opt):
        self._set_parameter("address_opt", address_opt)

    def set_name_opt(self, name_opt):
        self._set_parameter("name_opt", name_opt)

    def set_email_opt(self, email_opt):
        self._set_parameter("email_opt", email_opt)

    def set_phone_opt(self, phone_opt):
        self._set_parameter("phone_opt", phone_opt)

    def set_opt(self, opt):
        self._set_parameter("opt", opt)

    def set_privacy(self, privacy):
        self._set_parameter("privacy", privacy)

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

    def get_action(self):
        return self.parameters.get(self.parameter_mappings["action"], "")

    def get_national_id(self):
        return self.parameters.get(self.parameter_mappings["national_id"], "")

    def get_first_name(self):
        return self.parameters.get(self.parameter_mappings["first_name"], "")

    def get_last_name(self):
        return self.parameters.get(self.parameter_mappings["last_name"], "")

    def get_full_name(self):
        return self.parameters.get(self.parameter_mappings["full_name"], "")

    def get_company(self):
        return self.parameters.get(self.parameter_mappings["company"], "")

    def get_phone(self):
        return self.parameters.get(self.parameter_mappings["phone"], "")

    def get_email(self):
        return self.parameters.get(self.parameter_mappings["email"], "")

    def get_dob(self):
        return self.parameters.get(self.parameter_mappings["dob"], "")

    def get_account_number(self):
        return self.parameters.get(self.parameter_mappings["account_number"], "")

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

    def get_locality(self):
        return self.parameters.get(self.parameter_mappings["locality"], "")

    def get_administrative_area(self):
        return self.parameters.get(self.parameter_mappings["administrative_area"], "")

    def get_postal(self):
        return self.parameters.get(self.parameter_mappings["postal"], "")

    def get_country(self):
        return self.parameters.get(self.parameter_mappings["country"], "")

    def get_country_origin(self):
        return self.parameters.get(self.parameter_mappings["country_origin"], "")

    def get_transmission_reference(self):
        return self.parameters.get(self.parameter_mappings["transmission_reference"], "")

    def get_address_opt(self):
        return self.parameters.get(self.parameter_mappings["address_opt"], "")

    def get_name_opt(self):
        return self.parameters.get(self.parameter_mappings["name_opt"], "")

    def get_email_opt(self):
        return self.parameters.get(self.parameter_mappings["email_opt"], "")

    def get_phone_opt(self):
        return self.parameters.get(self.parameter_mappings["phone_opt"], "")

    def get_opt(self):
        return self.parameters.get(self.parameter_mappings["opt"], "")

    def get_privacy(self):
        return self.parameters.get(self.parameter_mappings["privacy"], "")

    def get_post_body(self):
        return self.post_body or ""
    
    # Class Methods
    
    def post(self, response_type=None):
        """
        This synchronous function makes the batch request using the post body.

        Returns:
            A string or deserialized json response object.
        """

        
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
        version = response_objectect["Version"]
        return version
