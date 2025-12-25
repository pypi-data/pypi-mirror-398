import json
import os
from .CloudApiBase import CloudApiBase
from ..PostReqestBase import SmartMoverPostRequest

class SmartMover(CloudApiBase):

    def __init__(self, license=None):
        super().__init__("https://smartmover.melissadata.net", "/V3/WEB/SmartMover/doSmartMover")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"
        self.records = []
        self.post_body = None

        self.parameter_mappings = {
            "job_id": "jobid",
            "paf_id": "pafid",
            "action": "act",
            "list": "list",
            "company": "comp",
            "full_name": "full",
            "first_name": "first",
            "middle_name": "middle",
            "name_prefix": "namepre",
            "name_suffix": "namesfx",
            "last_name": "last",
            "urbanization": "u",
            "address_line_1": "a1",
            "address_line_2": "a2",
            "suite": "ste",
            "private_mailbox": "pmb",
            "city": "city",
            "state": "state",
            "postal": "postal",
            "plus4": "plus4",
            "country": "ctry",
            "transmission_reference": "t",
            "opt": "opt",
            "cols": "cols"
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
    def job_id(self):
        return self._job_id

    @job_id.setter
    def job_id(self, value):
        self._set_parameter("job_id", value)

    @property
    def paf_id(self):
        return self._paf_id

    @paf_id.setter
    def paf_id(self, value):
        self._set_parameter("paf_id", value)

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        self._set_parameter("action", value)

    @property
    def list(self):
        return self._list

    @list.setter
    def list(self, value):
        self._set_parameter("list", value)

    @property
    def company(self):
        return self._company

    @company.setter
    def company(self, value):
        self._set_parameter("company", value)

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
    def middle_name(self):
        return self._middle_name

    @middle_name.setter
    def middle_name(self, value):
        self._set_parameter("middle_name", value)

    @property
    def name_prefix(self):
        return self._name_prefix

    @name_prefix.setter
    def name_prefix(self, value):
        self._set_parameter("name_prefix", value)

    @property
    def name_suffix(self):
        return self._name_suffix

    @name_suffix.setter
    def name_suffix(self, value):
        self._set_parameter("name_suffix", value)

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        self._set_parameter("last_name", value)

    @property
    def urbanization(self):
        return self._urbanization

    @urbanization.setter
    def urbanization(self, value):
        self._set_parameter("urbanization", value)

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
    def private_mailbox(self):
        return self._private_mailbox

    @private_mailbox.setter
    def private_mailbox(self, value):
        self._set_parameter("private_mailbox", value)

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
    def plus4(self):
        return self._plus4

    @plus4.setter
    def plus4(self, value):
        self._set_parameter("plus4", value)

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

    @property
    def cols(self):
        return self._cols

    @cols.setter
    def cols(self, value):
        self._set_parameter("cols", value)

    # Setters

    
    def set_job_id(self, job_id):
        self._set_parameter("job_id", job_id)

    def set_paf_id(self, paf_id):
        self._set_parameter("paf_id", paf_id)

    def set_action(self, action):
        self._set_parameter("action", action)

    def set_list(self, list_):
        self._set_parameter("list", list_)

    def set_company(self, company):
        self._set_parameter("company", company)

    def set_full_name(self, full_name):
        self._set_parameter("full_name", full_name)

    def set_first_name(self, first_name):
        self._set_parameter("first_name", first_name)

    def set_middle_name(self, middle_name):
        self._set_parameter("middle_name", middle_name)

    def set_name_prefix(self, name_prefix):
        self._set_parameter("name_prefix", name_prefix)

    def set_name_suffix(self, name_suffix):
        self._set_parameter("name_suffix", name_suffix)

    def set_last_name(self, last_name):
        self._set_parameter("last_name", last_name)

    def set_urbanization(self, urbanization):
        self._set_parameter("urbanization", urbanization)

    def set_address_line_1(self, address_line_1):
        self._set_parameter("address_line_1", address_line_1)

    def set_address_line_2(self, address_line_2):
        self._set_parameter("address_line_2", address_line_2)

    def set_suite(self, suite):
        self._set_parameter("suite", suite)

    def set_private_mailbox(self, private_mailbox):
        self._set_parameter("private_mailbox", private_mailbox)

    def set_city(self, city):
        self._set_parameter("city", city)

    def set_state(self, state):
        self._set_parameter("state", state)

    def set_postal(self, postal):
        self._set_parameter("postal", postal)

    def set_plus4(self, plus4):
        self._set_parameter("plus4", plus4)

    def set_country(self, country):
        self._set_parameter("country", country)

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

    def get_job_id(self):
        return self.parameters.get(self.parameter_mappings["job_id"], "")

    def get_paf_id(self):
        return self.parameters.get(self.parameter_mappings["paf_id"], "")

    def get_action(self):
        return self.parameters.get(self.parameter_mappings["action"], "")

    def get_list(self):
        return self.parameters.get(self.parameter_mappings["list"], "")

    def get_company(self):
        return self.parameters.get(self.parameter_mappings["company"], "")

    def get_full_name(self):
        return self.parameters.get(self.parameter_mappings["full_name"], "")

    def get_first_name(self):
        return self.parameters.get(self.parameter_mappings["first_name"], "")

    def get_middle_name(self):
        return self.parameters.get(self.parameter_mappings["middle_name"], "")

    def get_name_prefix(self):
        return self.parameters.get(self.parameter_mappings["name_prefix"], "")

    def get_name_suffix(self):
        return self.parameters.get(self.parameter_mappings["name_suffix"], "")

    def get_last_name(self):
        return self.parameters.get(self.parameter_mappings["last_name"], "")

    def get_urbanization(self):
        return self.parameters.get(self.parameter_mappings["urbanization"], "")

    def get_address_line_1(self):
        return self.parameters.get(self.parameter_mappings["address_line_1"], "")

    def get_address_line_2(self):
        return self.parameters.get(self.parameter_mappings["address_line_2"], "")

    def get_suite(self):
        return self.parameters.get(self.parameter_mappings["suite"], "")

    def get_private_mailbox(self):
        return self.parameters.get(self.parameter_mappings["private_mailbox"], "")

    def get_city(self):
        return self.parameters.get(self.parameter_mappings["city"], "")

    def get_state(self):
        return self.parameters.get(self.parameter_mappings["state"], "")

    def get_postal(self):
        return self.parameters.get(self.parameter_mappings["postal"], "")

    def get_plus4(self):
        return self.parameters.get(self.parameter_mappings["plus4"], "")

    def get_country(self):
        return self.parameters.get(self.parameter_mappings["country"], "")

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
            post_request = SmartMoverPostRequest(
                transmission_reference=self.get_transmission_reference(),
                records=self.records,
                customer_id=self.get_license(),
                job_id=self.get_job_id(),
                paf_id=self.get_paf_id(),
                actions=self.get_action(),
                options=self.get_opt(),
                columns=self.get_cols(),
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

