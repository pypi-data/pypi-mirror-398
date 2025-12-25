import json
import os
from .CloudApiBase import CloudApiBase


class PeopleBusinessSearch(CloudApiBase):

    def __init__(self, license=None):
        super().__init__("https://search.melissadata.net", "/v5/web/contactsearch/docontactSearch")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"
        self.post_body = None

        self.parameter_mappings = {
            "address_line_1": "a1",
            "administrative_area": "adminarea",
            "country": "ctry",
            "locality": "loc",
            "phone": "phone",
            "postal": "postal",
            "post_direction": "postdir",
            "pre_direction": "predir",
            "premises_number": "premnum",
            "sub_premises_number": "subpremnum",
            "thoroughfare_name": "tname",
            "trailing_type": "trailingtype",
            "any_name": "anyname",
            "company": "comp",
            "first_name": "first",
            "full_name": "full",
            "last_name": "last",
            "sub_user": "subuser",
            "transmission_reference": "t",
            "match_level": "matchlevel",
            "max_records": "maxrecords",
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
    def address_line_1(self):
        return self._address_line_1

    @address_line_1.setter
    def address_line_1(self, value):
        self._set_parameter("address_line_1", value)

    @property
    def administrative_area(self):
        return self._administrative_area

    @administrative_area.setter
    def administrative_area(self, value):
        self._set_parameter("administrative_area", value)

    @property
    def country(self):
        return self._country

    @country.setter
    def country(self, value):
        self._set_parameter("country", value)

    @property
    def locality(self):
        return self._locality

    @locality.setter
    def locality(self, value):
        self._set_parameter("locality", value)

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
    def post_direction(self):
        return self._post_direction

    @post_direction.setter
    def post_direction(self, value):
        self._set_parameter("post_direction", value)

    @property
    def pre_direction(self):
        return self._pre_direction

    @pre_direction.setter
    def pre_direction(self, value):
        self._set_parameter("pre_direction", value)

    @property
    def premises_number(self):
        return self._premises_number

    @premises_number.setter
    def premises_number(self, value):
        self._set_parameter("premises_number", value)

    @property
    def sub_premises_number(self):
        return self._sub_premises_number

    @sub_premises_number.setter
    def sub_premises_number(self, value):
        self._set_parameter("sub_premises_number", value)

    @property
    def thoroughfare_name(self):
        return self._thoroughfare_name

    @thoroughfare_name.setter
    def thoroughfare_name(self, value):
        self._set_parameter("thoroughfare_name", value)

    @property
    def trailing_type(self):
        return self._trailing_type

    @trailing_type.setter
    def trailing_type(self, value):
        self._set_parameter("trailing_type", value)

    @property
    def any_name(self):
        return self._any_name

    @any_name.setter
    def any_name(self, value):
        self._set_parameter("any_name", value)

    @property
    def company(self):
        return self._company

    @company.setter
    def company(self, value):
        self._set_parameter("company", value)

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, value):
        self._set_parameter("first_name", value)

    @property
    def full_name(self):
        return self._full_name

    @full_name.setter
    def full_name(self, value):
        self._set_parameter("full_name", value)

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        self._set_parameter("last_name", value)

    @property
    def sub_user(self):
        return self._sub_user

    @sub_user.setter
    def sub_user(self, value):
        self._set_parameter("sub_user", value)

    @property
    def transmission_reference(self):
        return self._transmission_reference

    @transmission_reference.setter
    def transmission_reference(self, value):
        self._set_parameter("transmission_reference", value)

    @property
    def match_level(self):
        return self._match_level

    @match_level.setter
    def match_level(self, value):
        self._set_parameter("match_level", value)

    @property
    def max_records(self):
        return self._max_records

    @max_records.setter
    def max_records(self, value):
        self._set_parameter("max_records", value)

    # Setters

    def set_address_line_1(self, value):
        self._set_parameter("address_line_1", value)

    def set_administrative_area(self, value):
        self._set_parameter("administrative_area", value)

    def set_country(self, value):
        self._set_parameter("country", value)

    def set_locality(self, value):
        self._set_parameter("locality", value)

    def set_phone(self, value):
        self._set_parameter("phone", value)

    def set_postal(self, value):
        self._set_parameter("postal", value)

    def set_post_direction(self, value):
        self._set_parameter("post_direction", value)

    def set_pre_direction(self, value):
        self._set_parameter("pre_direction", value)

    def set_premises_number(self, value):
        self._set_parameter("premises_number", value)

    def set_sub_premises_number(self, value):
        self._set_parameter("sub_premises_number", value)

    def set_thoroughfare_name(self, value):
        self._set_parameter("thoroughfare_name", value)

    def set_trailing_type(self, value):
        self._set_parameter("trailing_type", value)

    def set_any_name(self, value):
        self._set_parameter("any_name", value)

    def set_company(self, value):
        self._set_parameter("company", value)

    def set_first_name(self, value):
        self._set_parameter("first_name", value)

    def set_full_name(self, value):
        self._set_parameter("full_name", value)

    def set_last_name(self, value):
        self._set_parameter("last_name", value)

    def set_sub_user(self, value):
        self._set_parameter("sub_user", value)

    def set_transmission_reference(self, value):
        self._set_parameter("transmission_reference", value)

    def set_match_level(self, value):
        self._set_parameter("match_level", value)

    def set_max_records(self, value):
        self._set_parameter("max_records", value)

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

    def get_address_line_1(self):
        return self.parameters.get(self.parameter_mappings["address_line_1"], "")

    def get_administrative_area(self):
        return self.parameters.get(self.parameter_mappings["administrative_area"], "")

    def get_country(self):
        return self.parameters.get(self.parameter_mappings["country"], "")

    def get_locality(self):
        return self.parameters.get(self.parameter_mappings["locality"], "")

    def get_phone(self):
        return self.parameters.get(self.parameter_mappings["phone"], "")

    def get_postal(self):
        return self.parameters.get(self.parameter_mappings["postal"], "")

    def get_post_direction(self):
        return self.parameters.get(self.parameter_mappings["post_direction"], "")

    def get_pre_direction(self):
        return self.parameters.get(self.parameter_mappings["pre_direction"], "")

    def get_premises_number(self):
        return self.parameters.get(self.parameter_mappings["premises_number"], "")

    def get_sub_premises_number(self):
        return self.parameters.get(self.parameter_mappings["sub_premises_number"], "")

    def get_thoroughfare_name(self):
        return self.parameters.get(self.parameter_mappings["thoroughfare_name"], "")

    def get_trailing_type(self):
        return self.parameters.get(self.parameter_mappings["trailing_type"], "")

    def get_any_name(self):
        return self.parameters.get(self.parameter_mappings["any_name"], "")

    def get_company(self):
        return self.parameters.get(self.parameter_mappings["company"], "")

    def get_first_name(self):
        return self.parameters.get(self.parameter_mappings["first_name"], "")

    def get_full_name(self):
        return self.parameters.get(self.parameter_mappings["full_name"], "")

    def get_last_name(self):
        return self.parameters.get(self.parameter_mappings["last_name"], "")

    def get_sub_user(self):
        return self.parameters.get(self.parameter_mappings["sub_user"], "")

    def get_transmission_reference(self):
        return self.parameters.get(self.parameter_mappings["transmission_reference"], "")

    def get_match_level(self):
        return self.parameters.get(self.parameter_mappings["match_level"], "")

    def get_max_records(self):
        return self.parameters.get(self.parameter_mappings["max_records"], "")

    def get_post_body(self):
        return self.post_body
    
    # Class Methods
    def post(self, response_type):
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





    