import json
import os
from .CloudApiBase import CloudApiBase

class GlobalExpressEntry(CloudApiBase):

    def __init__(self, license):
        super().__init__("https://expressentry.melissadata.net", "/web/GlobalExpressAddress")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"

        self.parameter_mappings = {
            "address_line_1": "line1",
            "city": "city",
            "state": "state",
            "postal": "postalcode",
            "free_form": "ff",
            "thoroughfare": "thoroughfare",
            "locality": "locality",
            "administrative_area": "administrativearea",
            "country": "country",
            "max_records": "maxrecords",
            "opt": "opt",
            "cols": "cols",
            "native_char_set": "nativecharset"
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
    def free_form(self):
        return self._free_form

    @free_form.setter
    def free_form(self, value):
        self._set_parameter("free_form", value)

    @property
    def thoroughfare(self):
        return self._thoroughfare

    @thoroughfare.setter
    def thoroughfare(self, value):
        self._set_parameter("thoroughfare", value)

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
    def country(self):
        return self._country

    @country.setter
    def country(self, value):
        self._set_parameter("country", value)

    @property
    def max_records(self):
        return self._max_records

    @max_records.setter
    def max_records(self, value):
        self._set_parameter("max_records", value)

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
    def native_char_set(self):
        return self._native_char_set

    @native_char_set.setter
    def native_char_set(self, value):
        self._set_parameter("native_char_set", value)

    # Setters

    def set_address_line_1(self, address_line_1):
        if self.endpoint.lower() == "web/globalexpressaddress":
            self._set_parameter("address_line_1", self.parameters.get("line1", "")) 
        else:
            self._set_parameter("address_line_1", address_line_1)

    def set_city(self, city):
        self._set_parameter("city", city)

    def set_state(self, state):
        self._set_parameter("state", state)

    def set_postal(self, postal):
        self._set_parameter("postal", postal)

    def set_free_form(self, free_form):
        self._set_parameter("free_form", free_form)

    def set_thoroughfare(self, thoroughfare):
        self._set_parameter("thoroughfare", thoroughfare)

    def set_locality(self, locality):
        self._set_parameter("locality", locality)

    def set_administrative_area(self, administrative_area):
        self._set_parameter("administrative_area", administrative_area)

    def set_country(self, country):
        self._set_parameter("country", country)

    def set_max_records(self, max_records):
        self._set_parameter("max_records", max_records)

    def set_opt(self, opt):
        self._set_parameter("opt", opt)

    def set_cols(self, cols):
        self._set_parameter("cols", cols)

    def set_native_char_set(self, native_char_set):
        self._set_parameter("native_char_set", native_char_set)

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

    def get_city(self):
        return self.parameters.get(self.parameter_mappings["city"], "")

    def get_state(self):
        return self.parameters.get(self.parameter_mappings["state"], "")

    def get_postal(self):
        return self.parameters.get(self.parameter_mappings["postal"], "")

    def get_free_form(self):
        return self.parameters.get(self.parameter_mappings["free_form"], "")

    def get_thoroughfare(self):
        return self.parameters.get(self.parameter_mappings["thoroughfare"], "")

    def get_locality(self):
        return self.parameters.get(self.parameter_mappings["locality"], "")

    def get_administrative_area(self):
        return self.parameters.get(self.parameter_mappings["administrative_area"], "")

    def get_country(self):
        return self.parameters.get(self.parameter_mappings["country"], "")

    def get_max_records(self):
        return self.parameters.get(self.parameter_mappings["max_records"], "")

    def get_opt(self):
        return self.parameters.get(self.parameter_mappings["opt"], "")

    def get_cols(self):
        return self.parameters.get(self.parameter_mappings["cols"], "")

    def get_native_char_set(self):
        return self.parameters.get(self.parameter_mappings["native_char_set"], "")
    
    def get_global_express_address(self, type):
        """
        Synchronous function sends the CloudAPI request using the /web/GlobalExpressAddress endpoint
        """
        self.set_endpoint("/web/GlobalExpressAddress")
        return self.get(type)

    def get_global_express_locality_administrative_area(self, type):
        """
        Synchronous function sends the CloudAPI request using the /web/GlobalExpressLocalityAdministrativeArea endpoint
        """
        self.set_endpoint("/web/GlobalExpressLocalityAdministrativeArea")
        return self.get(type)

    
    def get_global_express_country(self, type):
        """
        Synchronous function sends the CloudAPI request using the /web/GlobalExpressCountry endpoint
        """
        self.set_endpoint("/web/GlobalExpressCountry")
        return self.get(type)

    
    def get_global_express_free_form(self, type):
        """
        Synchronous function sends the CloudAPI request using the /web/GlobalExpressFreeForm endpoint
        """
        self.set_endpoint("/web/GlobalExpressFreeForm")
        return self.get(type)

    
    def get_global_express_postal_code(self, type):
        """
        Synchronous function sends the CloudAPI request using the /web/GlobalExpressPostalCode endpoint
        """
        self.set_endpoint("/web/GlobalExpressPostalCode")
        return self.get(type)

    
    def get_global_express_thoroughfare(self, type):
        """
        Synchronous function sends the CloudAPI request using the /web/GlobalExpressThoroughfare endpoint
        """
        self.set_endpoint("/web/GlobalExpressThoroughfare")
        return self.get(type)

    def get_api_version(self):
        """
        Makes a synchronous getversion request and parses the response for the API version.

        Returns:
            The Cloud API version.
        """
        json_response = self.send_version_request()
        response_objectect = json.loads(json_response)
        version = response_objectect.get("BuildNumber", "")
        return version
    
    



