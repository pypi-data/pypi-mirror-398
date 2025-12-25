import json
import os
from .CloudApiBase import CloudApiBase
from ..PostReqestBase import PropertyPostRequest


class Property(CloudApiBase):

    def __init__(self, license=None):
        super().__init__("https://property.melissadata.net", "/v4/WEB/LookupProperty")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"
        self.records = []
        self.post_body = None

        self.parameter_mappings = {
            "address_key": "addresskey",
            "address_line_1": "a1",
            "address_line_2": "a2",
            "apn": "apn",
            "city": "city",
            "country": "ctry",
            "fips": "fips",
            "free_form": "ff",
            "mak": "mak",
            "state": "state",
            "postal": "postal",
            "transmission_reference": "t",
            "cols": "cols",
            "opt": "opt",
            "owner_mak": "mak",
            "total_records": "totalRecords",
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
    def address_key(self):
        return self._address_key

    @address_key.setter
    def address_key(self, value):
        self._set_parameter("address_key", value)

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
    def apn(self):
        return self._apn

    @apn.setter
    def apn(self, value):
        self._set_parameter("apn", value)

    @property
    def city(self):
        return self._city

    @city.setter
    def city(self, value):
        self._set_parameter("city", value)

    @property
    def country(self):
        return self._country

    @country.setter
    def country(self, value):
        self._set_parameter("country", value)

    @property
    def fips(self):
        return self._fips

    @fips.setter
    def fips(self, value):
        self._set_parameter("fips", value)

    @property
    def free_form(self):
        return self._free_form

    @free_form.setter
    def free_form(self, value):
        self._set_parameter("free_form", value)

    @property
    def mak(self):
        return self._mak

    @mak.setter
    def mak(self, value):
        self._set_parameter("mak", value)

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
    def transmission_reference(self):
        return self._transmission_reference

    @transmission_reference.setter
    def transmission_reference(self, value):
        self._set_parameter("transmission_reference", value)

    @property
    def cols(self):
        return self._cols

    @cols.setter
    def cols(self, value):
        self._set_parameter("cols", value)

    @property
    def opt(self):
        return self._opt

    @opt.setter
    def opt(self, value):
        self._set_parameter("opt", value)

    @property
    def owner_mak(self):
        return self._owner_mak

    @owner_mak.setter
    def owner_mak(self, value):
        self._set_parameter("owner_mak", value)

    @property
    def total_records(self):
        return self._total_records

    @total_records.setter
    def total_records(self, value):
        self._set_parameter("total_records", value)


    # Setters

    def set_address_key(self, address_key):
        self._set_parameter("address_key", address_key)

    def set_address_line_1(self, address_line_1):
        self._set_parameter("address_line_1", address_line_1)

    def set_address_line_2(self, address_line_2):
        self._set_parameter("address_line_2", address_line_2)

    def set_apn(self, apn):
        self._set_parameter("apn", apn)

    def set_city(self, city):
        self._set_parameter("city", city)

    def set_country(self, country):
        self._set_parameter("country", country)

    def set_fips(self, fips):
        self._set_parameter("fips", fips)

    def set_free_form(self, free_form):
        self._set_parameter("free_form", free_form)

    def set_mak(self, mak):
        self._set_parameter("mak", mak)

    def set_state(self, state):
        self._set_parameter("state", state)

    def set_postal(self, postal):
        self._set_parameter("postal", postal)

    def set_transmission_reference(self, transmission_reference):
        self._set_parameter("transmission_reference", transmission_reference)

    def set_cols(self, cols):
        self._set_parameter("cols", cols)

    def set_opt(self, opt):
        self._set_parameter("opt", opt)

    def set_owner_mak(self, owner_mak):
        self._set_parameter("owner_mak", owner_mak)

    def set_total_records(self, total_records):
        self._set_parameter("total_records", total_records)

    def set_post_body(self, post_body):
        self._set_parameter("post_body", post_body)

    def set_post_body(self, post_body):
        self.post_body = post_body
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

    def get_address_key(self):
        return self.parameters.get(self.parameter_mappings["address_key"], "")

    def get_address_line_1(self):
        return self.parameters.get(self.parameter_mappings["address_line_1"], "")

    def get_address_line_2(self):
        return self.parameters.get(self.parameter_mappings["address_line_2"], "")

    def get_apn(self):
        return self.parameters.get(self.parameter_mappings["apn"], "")

    def get_city(self):
        return self.parameters.get(self.parameter_mappings["city"], "")

    def get_country(self):
        return self.parameters.get(self.parameter_mappings["country"], "")

    def get_fips(self):
        return self.parameters.get(self.parameter_mappings["fips"], "")

    def get_free_form(self):
        return self.parameters.get(self.parameter_mappings["free_form"], "")

    def get_mak(self):
        return self.parameters.get(self.parameter_mappings["mak"], "")

    def get_state(self):
        return self.parameters.get(self.parameter_mappings["state"], "")

    def get_postal(self):
        return self.parameters.get(self.parameter_mappings["postal"], "")

    def get_transmission_reference(self):
        return self.parameters.get(self.parameter_mappings["transmission_reference"], "")

    def get_cols(self):
        return self.parameters.get(self.parameter_mappings["cols"], "")

    def get_opt(self):
        return self.parameters.get(self.parameter_mappings["opt"], "")

    def get_owner_mak(self):
        return self.parameters.get(self.parameter_mappings["owner_mak"], "")

    def get_total_records(self):
        return self.parameters.get(self.parameter_mappings["total_records"], "")

    def get_post_batch_body(self):
        return self.post_body


# Class Methods

    def add_record(self, request):
        self.records.append(request)

    def clear_records(self):
        self.records.clear()

    def get_lookup_property(self, response_type):
        """
        This synchronous function sends the CloudAPI request using the /v4/WEB/LookupProperty endpoint
        """
        self.set_endpoint("/v4/WEB/LookupProperty")
        return self.get(response_type)


    def post_lookup_property(self, response_type):
        """
        This synchronous function sends a POST request to the Cloud API using the /v4/WEB/LookupProperty endpoint
        """
        self.set_endpoint("/v4/WEB/LookupProperty")

        if self.records:
            post_request = PropertyPostRequest(
                columns=self.get_cols(),
                customer_id=self.get_license(),
                transmission_reference=self.get_transmission_reference(),
                options=self.get_opt(),
                total_records=self.get_total_records(),
                records=self.records,
            )
            response = self.send_post_request(post_request)
        else:
            response = self.send_post_request(self.post_body)

        return self.handle_response(response, response_type)

    
    def get_lookup_deeds(self, response_type):
        """
        This synchronous function sends the CloudAPI request using the /v4/WEB/LookupDeeds endpoint
        """
        self.set_endpoint("/v4/WEB/LookupDeeds")
        return self.get(response_type)

    def post_lookup_deeds(self, response_type):
        """
        This synchronous function sends a POST request to the Cloud API using the /v4/WEB/LookupDeeds endpoint
        """
        self.set_endpoint("/v4/WEB/LookupDeeds")
        response = self.send_post_request(self.post_body)
        return self.handle_response(response, response_type)
    
    def get_lookup_homes_by_owner(self, response_type):
        """
        This synchronous function sends the CloudAPI request using the /v4/WEB/LookupHomesByOwner endpoint
        """
        self.set_endpoint("/v4/WEB/LookupHomesByOwner")
        return self.get(response_type)

    def post_lookup_homes_by_owner(self, response_type):
        """
        This synchronous function sends a POST request to the Cloud API using the /v4/WEB/LookupHomesByOwner endpoint
        """
        self.set_endpoint("/v4/WEB/LookupHomesByOwner")
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