import json
import os
from .CloudApiBase import CloudApiBase
from ..PostReqestBase import GlobalPhonePostRequest


class GlobalPhone(CloudApiBase):

    def __init__(self, license=None):
        super().__init__("https://globalphone.melissadata.net", "/v4/WEB/GlobalPhone/doGlobalPhone")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"
        self.records = []
        self.post_body = None

        self.parameter_mappings = {
            "phone": "phone",
            "country": "ctry",
            "country_origin": "ctryOrg",
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
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, value):
        self._set_parameter("phone", value)

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
    def opt(self):
        return self._opt

    @opt.setter
    def opt(self, value):
        self._set_parameter("opt", value)

    # Setters

    def set_phone(self, value):
        self._set_parameter("phone", value)

    def set_country(self, value):
        self._set_parameter("country", value)

    def set_country_origin(self, value):
        self._set_parameter("country_origin", value)

    def set_transmission_reference(self, value):
        self._set_parameter("transmission_reference", value)

    def set_opt(self, value):
        self._set_parameter("opt", value)

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

    def get_phone(self):
        return self.parameters.get(self.parameter_mappings["phone"], "")

    def get_country(self):
        return self.parameters.get(self.parameter_mappings["country"], "")

    def get_country_origin(self):
        return self.parameters.get(self.parameter_mappings["country_origin"], "")

    def get_transmission_reference(self):
        return self.parameters.get(self.parameter_mappings["transmission_reference"], "")

    def get_opt(self):
        return self.parameters.get(self.parameter_mappings["opt"], "")

    def get_post_body(self):
        return self.post_body or ""

    # Class Methods
    def add_record(self, request):
        self.records.append(request)

    def clear_records(self):
        self.records.clear()

    def post(self, response_type=None):
        """
        This synchronous function makes the batch request using the post body.

        Returns:
            A string or deserialized json response object.
        """

        if self.records and len(self.records) > 0:
            post_request = GlobalPhonePostRequest(
                transmission_reference=self.get_transmission_reference(),
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
