import json
import os
from .CloudApiBase import CloudApiBase
from ..PostReqestBase import GlobalIPPostRequest


class GlobalIP(CloudApiBase):

    def __init__(self, license=None):
        super().__init__("https://globalip.melissadata.net", "/v4/web/iplocation/doiplocation")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"
        self.records = []
        self.post_body = None

        self.parameter_mappings = {
            "ip": "ip",
            "transmission_reference": "t",
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
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, value):
        self._set_parameter("ip", value)

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

    # Setters

    def set_ip(self, value):
        self._set_parameter("ip", value)

    def set_transmission_reference(self, value):
        self._set_parameter("transmission_reference", value)

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

    def get_ip(self):
        return self.parameters.get(self.parameter_mappings["ip"], "")

    def get_transmission_reference(self):
        return self.parameters.get(self.parameter_mappings["transmission_reference"], "")

    def get_cols(self):
        return self.parameters.get(self.parameter_mappings["cols"], "")
    
    def get_post_body(self):
        return self.post_body or ""
    
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
            post_request = GlobalIPPostRequest(
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
