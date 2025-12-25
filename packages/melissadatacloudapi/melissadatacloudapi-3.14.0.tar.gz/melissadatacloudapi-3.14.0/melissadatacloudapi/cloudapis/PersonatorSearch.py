import json
import os
from .CloudApiBase import CloudApiBase


class PersonatorSearch(CloudApiBase):

    def __init__(self, license=None):
        super().__init__("http://personatorsearch.melissadata.net", "/WEB/doPersonatorSearch")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"

        self.parameter_mappings = {
            "transmission_reference": "t",
            "opt": "opt",
            "cols": "cols",
            "free_form": "ff",
            "full_name": "full",
            "first_name": "first",
            "last_name": "last",
            "address_line_1": "a1",
            "action": "act",
            "city": "city",
            "state": "state",
            "postal": "postal",
            "phone": "phone",
            "email": "email",
            "mak": "mak",
            "birth_day": "bday",
            "birth_month": "bmonth",
            "birth_year": "byear"
        }

        # Initialize private backing fields
        for attr in self.parameter_mappings.keys():
            setattr(self, f"_{attr}", "")

    def _set_parameter(self, attr_name, value):
        setattr(self, f"_{attr_name}", value)
        self.parameters[self.parameter_mappings[attr_name]] = value

    # Properties

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
    def address_line_1(self):
        return self._address_line_1

    @address_line_1.setter
    def address_line_1(self, value):
        self._set_parameter("address_line_1", value)

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        self._set_parameter("action", value)

    @property
    def city(self):
        return self._city

    @city.setter
    def city(self, value):
        self._set_parameter("city", value)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._set_parameter("state", value)

    @property
    def postal(self):
        return self._postal

    @postal.setter
    def postal(self, value):
        self._set_parameter("postal", value)

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
    def mak(self):
        return self._mak

    @mak.setter
    def mak(self, value):
        self._set_parameter("mak", value)

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

    # Setters

    def set_transmission_reference(self, value):
        self._set_parameter("transmission_reference", value)

    def set_opt(self, value):
        self._set_parameter("opt", value)

    def set_cols(self, value):
        self._set_parameter("cols", value)

    def set_free_form(self, value):
        self._set_parameter("free_form", value)

    def set_full_name(self, value):
        self._set_parameter("full_name", value)

    def set_first_name(self, value):
        self._set_parameter("first_name", value)

    def set_last_name(self, value):
        self._set_parameter("last_name", value)

    def set_address_line_1(self, value):
        self._set_parameter("address_line_1", value)

    def set_action(self, value):
        self._set_parameter("action", value)

    def set_city(self, value):
        self._set_parameter("city", value)

    def set_state(self, value):
        self._set_parameter("state", value)

    def set_postal(self, value):
        self._set_parameter("postal", value)

    def set_phone(self, value):
        self._set_parameter("phone", value)

    def set_email(self, value):
        self._set_parameter("email", value)

    def set_mak(self, value):
        self._set_parameter("mak", value)

    def set_birth_day(self, value):
        self._set_parameter("birth_day", value)

    def set_birth_month(self, value):
        self._set_parameter("birth_month", value)

    def set_birth_year(self, value):
        self._set_parameter("birth_year", value)

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

    def get_transmission_reference(self):
        return self.parameters.get(self.parameter_mappings["transmission_reference"], "")

    def get_opt(self):
        return self.parameters.get(self.parameter_mappings["opt"], "")

    def get_cols(self):
        return self.parameters.get(self.parameter_mappings["cols"], "")

    def get_free_form(self):
        return self.parameters.get(self.parameter_mappings["free_form"], "")

    def get_full_name(self):
        return self.parameters.get(self.parameter_mappings["full_name"], "")

    def get_first_name(self):
        return self.parameters.get(self.parameter_mappings["first_name"], "")

    def get_last_name(self):
        return self.parameters.get(self.parameter_mappings["last_name"], "")

    def get_address_line_1(self):
        return self.parameters.get(self.parameter_mappings["address_line_1"], "")

    def get_action(self):
        return self.parameters.get(self.parameter_mappings["action"], "")

    def get_city(self):
        return self.parameters.get(self.parameter_mappings["city"], "")

    def get_state(self):
        return self.parameters.get(self.parameter_mappings["state"], "")

    def get_postal(self):
        return self.parameters.get(self.parameter_mappings["postal"], "")

    def get_phone(self):
        return self.parameters.get(self.parameter_mappings["phone"], "")

    def get_email(self):
        return self.parameters.get(self.parameter_mappings["email"], "")

    def get_mak(self):
        return self.parameters.get(self.parameter_mappings["mak"], "")

    def get_birth_day(self):
        return self.parameters.get(self.parameter_mappings["birth_day"], "")

    def get_birth_month(self):
        return self.parameters.get(self.parameter_mappings["birth_month"], "")

    def get_birth_year(self):
        return self.parameters.get(self.parameter_mappings["birth_year"], "")
    
    # Class Methods
    
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
