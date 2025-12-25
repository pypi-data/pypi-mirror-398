import json
import os
from .CloudApiBase import CloudApiBase
from ..PostReqestBase import BusinessCoderPostRequest

class BusinessCoder(CloudApiBase):
    def __init__(self, license=None):

        super().__init__("https://businesscoder.melissadata.net", "/WEB/BusinessCoder/doBusinessCoderUS")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"
        self.records = []
        self.post_body = None

        self.parameter_mappings = {
            "record_id": "rec",
            "company": "comp",
            "phone": "phone",
            "address_line_1": "a1",
            "address_line_2": "a2",
            "suite": "suite",
            "city": "city",
            "state": "state",
            "postal": "postal",
            "country": "ctry",
            "mak": "mak",
            "stock_ticker": "stock",
            "web_address": "web",
            "mek": "mek",
            "free_form": "freeform",
            "transmission_reference": "t",
            "opt": "opt",
            "cols": "cols",
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
    def record_id(self):
        return self._record_id

    @record_id.setter
    def record_id(self, value):
        self._set_parameter("record_id", value)

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
    def suite(self):
        return self._suite

    @suite.setter
    def suite(self, value):
        self._set_parameter("suite", value)

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
    def country(self):
        return self._country

    @country.setter
    def country(self, value):
        self._set_parameter("country", value)

    @property
    def mak(self):
        return self._mak

    @mak.setter
    def mak(self, value):
        self._set_parameter("mak", value)

    @property
    def stock_ticker(self):
        return self._stock_ticker

    @stock_ticker.setter
    def stock_ticker(self, value):
        self._set_parameter("stock_ticker", value)

    @property
    def web_address(self):
        return self._web_address

    @web_address.setter
    def web_address(self, value):
        self._set_parameter("web_address", value)

    @property
    def mek(self):
        return self._mek

    @mek.setter
    def mek(self, value):
        self._set_parameter("mek", value)

    @property
    def free_form(self):
        return self._free_form

    @free_form.setter
    def free_form(self, value):
        self._set_parameter("free_form", value)

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
    def set_record_id(self, record_id):
        self._set_parameter("record_id", record_id)

    def set_company(self, company):
        self._set_parameter("company", company)

    def set_phone(self, phone):
        self._set_parameter("phone", phone)

    def set_address_line_1(self, address_line_1):
        self._set_parameter("address_line_1", address_line_1)

    def set_address_line_2(self, address_line_2):
        self._set_parameter("address_line_2", address_line_2)

    def set_suite(self, suite):
        self._set_parameter("suite", suite)

    def set_city(self, city):
        self._set_parameter("city", city)

    def set_state(self, state):
        self._set_parameter("state", state)

    def set_postal(self, postal):
        self._set_parameter("postal", postal)

    def set_country(self, country):
        self._set_parameter("country", country)

    def set_mak(self, mak):
        self._set_parameter("mak", mak)

    def set_stock_ticker(self, ticker):
        self._set_parameter("stock_ticker", ticker)

    def set_web_address(self, url):
        self._set_parameter("web_address", url)

    def set_mek(self, mek):
        self._set_parameter("mek", mek)

    def set_free_form(self, ff):
        self._set_parameter("free_form", ff)

    def set_transmission_reference(self, transmission_reference):
        self._set_parameter("transmission_reference", transmission_reference)

    def set_opt(self, opt):
        self._set_parameter("opt", opt)

    def set_cols(self, cols):
        self._set_parameter("cols", cols)

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
    def get_record_id(self):
        return self.parameters.get(self.parameter_mappings["record_id"], "")

    def get_company(self):
        return self.parameters.get(self.parameter_mappings["company"], "")

    def get_phone(self):
        return self.parameters.get(self.parameter_mappings["phone"], "")

    def get_address_line_1(self):
        return self.parameters.get(self.parameter_mappings["address_line_1"], "")

    def get_address_line_2(self):
        return self.parameters.get(self.parameter_mappings["address_line_2"], "")

    def get_suite(self):
        return self.parameters.get(self.parameter_mappings["suite"], "")

    def get_city(self):
        return self.parameters.get(self.parameter_mappings["city"], "")

    def get_state(self):
        return self.parameters.get(self.parameter_mappings["state"], "")

    def get_postal(self):
        return self.parameters.get(self.parameter_mappings["postal"], "")

    def get_country(self):
        return self.parameters.get(self.parameter_mappings["country"], "")

    def get_mak(self):
        return self.parameters.get(self.parameter_mappings["mak"], "")

    def get_stock_ticker(self):
        return self.parameters.get(self.parameter_mappings["stock_ticker"], "")

    def get_web_address(self):
        return self.parameters.get(self.parameter_mappings["web_address"], "")

    def get_mek(self):
        return self.parameters.get(self.parameter_mappings["mek"], "")

    def get_free_form(self):
        return self.parameters.get(self.parameter_mappings["free_form"], "")

    def get_transmission_reference(self):
        return self.parameters.get(self.parameter_mappings["transmission_reference"], "")

    def get_opt(self):
        return self.parameters.get(self.parameter_mappings["opt"], "")

    def get_cols(self):
        return self.parameters.get(self.parameter_mappings["cols"], "")

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
            post_request = BusinessCoderPostRequest(
                cols=self.get_cols(),
                id=self.get_license(),
                t=self.get_transmission_reference(),
                opt=self.get_opt(),
                records=self.records
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
        business_coder_version = response_objectect["businessCoderVersion"]
        return business_coder_version

    