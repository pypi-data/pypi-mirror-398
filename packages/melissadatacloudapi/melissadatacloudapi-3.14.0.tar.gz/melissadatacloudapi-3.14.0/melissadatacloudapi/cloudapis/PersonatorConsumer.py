import json
import os
from .CloudApiBase import CloudApiBase
from ..PostReqestBase import PersonatorConsumerPostRequest


class PersonatorConsumer(CloudApiBase):

    def __init__(self, license=None):
        super().__init__("https://personator.melissadata.net", "/v3/WEB/ContactVerify/doContactVerify")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"
        self.records = []
        self.post_body = None

        self.parameter_mappings = {
            "action": "act",
            "address_line_1": "a1",
            "address_line_2": "a2",
            "birth_day": "bday",
            "birth_month": "bmo",
            "birth_year": "byr",
            "city": "city",
            "company": "comp",
            "country": "ctry",
            "email": "email",
            "first_name": "first",
            "free_form": "ff",
            "full_name": "full",
            "ip": "ip",
            "last_line": "lastline",
            "last_name": "last",
            "mak": "mak",
            "mik": "MIK",
            "phone": "phone",
            "postal": "postal",
            "ssn": "ss",
            "state": "state",
            "transmission_reference": "t",
            "opt": "opt",
            "cols": "cols"
        }

        self.parameters = {}

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
    def birth_day(self):
        return self._birth_day

    @birth_day.setter
    def birth_day(self, value):
        self._set_parameter("birth_day", value)

    @property
    def birth_month(self):
        return self._birth_month

    @birth_month.setter
    def birth_month(self, value):
        self._set_parameter("birth_month", value)

    @property
    def birth_year(self):
        return self._birth_year

    @birth_year.setter
    def birth_year(self, value):
        self._set_parameter("birth_year", value)

    @property
    def city(self):
        return self._city

    @city.setter
    def city(self, value):
        self._set_parameter("city", value)

    @property
    def company(self):
        return self._company

    @company.setter
    def company(self, value):
        self._set_parameter("company", value)

    @property
    def country(self):
        return self._country

    @country.setter
    def country(self, value):
        self._set_parameter("country", value)

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._set_parameter("email", value)

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, value):
        self._set_parameter("first_name", value)

    @property
    def free_form(self):
        return self._free_form

    @free_form.setter
    def free_form(self, value):
        self._set_parameter("free_form", value)

    @property
    def full_name(self):
        return self._full_name

    @full_name.setter
    def full_name(self, value):
        self._set_parameter("full_name", value)

    @property
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, value):
        self._set_parameter("ip", value)

    @property
    def last_line(self):
        return self._last_line

    @last_line.setter
    def last_line(self, value):
        self._set_parameter("last_line", value)

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        self._set_parameter("last_name", value)

    @property
    def mak(self):
        return self._mak

    @mak.setter
    def mak(self, value):
        self._set_parameter("mak", value)

    @property
    def mik(self):
        return self._mik

    @mik.setter
    def mik(self, value):
        self._set_parameter("mik", value)

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, value):
        self._set_parameter("phone", value)

    @property
    def postal(self):
        return self._postal

    @postal.setter
    def postal(self, value):
        self._set_parameter("postal", value)

    @property
    def ssn(self):
        return self._ssn

    @ssn.setter
    def ssn(self, value):
        self._set_parameter("ssn", value)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._set_parameter("state", value)

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

    @property
    def cols(self):
        return self._cols

    @cols.setter
    def cols(self, value):
        self._set_parameter("cols", value)

    # Setters

    def set_action(self, value):
        self._set_parameter("action", value)
    
    def set_address_line_1(self, value):
        self._set_parameter("address_line_1", value)
    
    def set_address_line_2(self, value):
        self._set_parameter("address_line_2", value)
    
    def set_birth_day(self, value):
        self._set_parameter("birth_day", value)
    
    def set_birth_month(self, value):
        self._set_parameter("birth_month", value)
    
    def set_birth_year(self, value):
        self._set_parameter("birth_year", value)
    
    def set_city(self, value):
        self._set_parameter("city", value)
    
    def set_company(self, value):
        self._set_parameter("company", value)
    
    def set_country(self, value):
        self._set_parameter("country", value)
    
    def set_email(self, value):
        self._set_parameter("email", value)
    
    def set_first_name(self, value):
        self._set_parameter("first_name", value)
    
    def set_free_form(self, value):
        self._set_parameter("free_form", value)
    
    def set_full_name(self, value):
        self._set_parameter("full_name", value)
    
    def set_ip(self, value):
        self._set_parameter("ip", value)
    
    def set_last_line(self, value):
        self._set_parameter("last_line", value)
    
    def set_last_name(self, value):
        self._set_parameter("last_name", value)
    
    def set_mak(self, value):
        self._set_parameter("mak", value)
    
    def set_mik(self, value):
        self._set_parameter("mik", value)
    
    def set_phone(self, value):
        self._set_parameter("phone", value)
    
    def set_postal(self, value):
        self._set_parameter("postal", value)
    
    def set_ssn(self, value):
        self._set_parameter("ssn", value)
    
    def set_state(self, value):
        self._set_parameter("state", value)
    
    def set_transmission_reference(self, value):
        self._set_parameter("transmission_reference", value)
    
    def set_opt(self, value):
        self._set_parameter("opt", value)
    
    def set_cols(self, value):
        self._set_parameter("cols", value)

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

    def get_address_line_1(self):
        return self.parameters.get(self.parameter_mappings["address_line_1"], "")

    def get_address_line_2(self):
        return self.parameters.get(self.parameter_mappings["address_line_2"], "")

    def get_birth_day(self):
        return self.parameters.get(self.parameter_mappings["birth_day"], "")

    def get_birth_month(self):
        return self.parameters.get(self.parameter_mappings["birth_month"], "")

    def get_birth_year(self):
        return self.parameters.get(self.parameter_mappings["birth_year"], "")

    def get_city(self):
        return self.parameters.get(self.parameter_mappings["city"], "")

    def get_company(self):
        return self.parameters.get(self.parameter_mappings["company"], "")

    def get_country(self):
        return self.parameters.get(self.parameter_mappings["country"], "")

    def get_email(self):
        return self.parameters.get(self.parameter_mappings["email"], "")

    def get_first_name(self):
        return self.parameters.get(self.parameter_mappings["first_name"], "")

    def get_free_form(self):
        return self.parameters.get(self.parameter_mappings["free_form"], "")

    def get_full_name(self):
        return self.parameters.get(self.parameter_mappings["full_name"], "")

    def get_ip(self):
        return self.parameters.get(self.parameter_mappings["ip"], "")

    def get_last_line(self):
        return self.parameters.get(self.parameter_mappings["last_line"], "")

    def get_last_name(self):
        return self.parameters.get(self.parameter_mappings["last_name"], "")

    def get_mak(self):
        return self.parameters.get(self.parameter_mappings["mak"], "")

    def get_mik(self):
        return self.parameters.get(self.parameter_mappings["mik"], "")

    def get_phone(self):
        return self.parameters.get(self.parameter_mappings["phone"], "")

    def get_postal(self):
        return self.parameters.get(self.parameter_mappings["postal"], "")

    def get_ssn(self):
        return self.parameters.get(self.parameter_mappings["ssn"], "")

    def get_state(self):
        return self.parameters.get(self.parameter_mappings["state"], "")

    def get_transmission_reference(self):
        return self.parameters.get(self.parameter_mappings["transmission_reference"], "")

    def get_opt(self):
        return self.parameters.get(self.parameter_mappings["opt"], "")

    def get_cols(self):
        return self.parameters.get(self.parameter_mappings["cols"], "")

    def get_post_body(self):
        return self.post_body

    # Class Methods
    
    def add_record(self, request):
        self.records.append(request)

    def clear_records(self):
        self.records.clear()

    def post(self, response_type):
        """
        This synchronous function makes the batch request using the post body.

        Returns:
            A string or deserialized json response object.
        """

        if self.records and len(self.records) > 0:
            post_request = PersonatorConsumerPostRequest(
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
        version = response_objectect["Version"]
        return version
