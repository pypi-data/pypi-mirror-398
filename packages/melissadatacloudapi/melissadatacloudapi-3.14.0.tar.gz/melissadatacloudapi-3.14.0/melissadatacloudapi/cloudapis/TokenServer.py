import json
import os
from .CloudApiBase import CloudApiBase
from urllib.parse import urlencode, quote


class TokenServer(CloudApiBase):

    def __init__(self, license=None):
        super().__init__("https://tokenservice.melissadata.net", "/V3/JSON/Service.svc/RequestToken")
        # super().__init__("http://kstagem1:31050/token", "/V3/JSON/Service.svc/RequestToken")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"

        self.parameter_mappings = {
            "ip": "IP",
            "packages": "P",
            "time_span": "TS"
        }

        # Initialize private backing fields
        for attr in self.parameter_mappings.keys():
            setattr(self, f"_{attr}", None)

    def _set_parameter(self, attr_name, value):
        """Helper method to set a private attribute and update the parameters dictionary."""
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
    def packages(self):
        return self._packages

    @packages.setter
    def packages(self, value):
        self._set_parameter("packages", value)

    @property
    def time_span(self):
        return self._time_span

    @time_span.setter
    def time_span(self, value):
        self._set_parameter("time_span", value)


    # Setters

    def set_ip(self, ip: str):
        self._set_parameter("ip", ip)

    def set_packages(self, packages: str):
        self._set_parameter("packages", packages)

    def set_time_span(self, time_span: str):
        self._set_parameter("time_span", time_span)

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

    def get_packages(self):
        return self.parameters.get(self.parameter_mappings["packages"], "")

    def get_time_span(self):
        return self.parameters.get(self.parameter_mappings["time_span"], "")

    # Class Methods

    def get_api_version(self):
        """
        Makes a synchronous getversion request and parses the response for the API version.

        Returns:
        - str: Cloud API version.
        """
        json_response = self.send_version_request()
        response_objectect = json.loads(json_response)
        version = response_objectect["Version"]
        return version

    async def get_api_version_async(self):
        """
        Makes an asynchronous getversion request and parses the response for the API version.

        Returns:
        - str: Cloud API version.
        """
        json_response = await self.send_version_request_async()
        response_objectect = json.loads(json_response)
        version = response_objectect["Version"]
        return version
    
    # Override Methods

    def process_request(self, parameters):
        """
        This synchronous function assembles the endpoint with the parameters and calls GetContents() to make the API request.
        This overrides the parent method because it uses "L" instead if "id" for the license string parameter
        """
        rest_request = "&L=" + quote(self.license)
        rest_request += "&" + urlencode(parameters)
        rest_request = self.endpoint + "?" + rest_request
        response = self.get_contents(self.base_url, rest_request)
        return response

    async def process_request_async(self, parameters):
        """
        This asynchronous function assembles the endpoint with the parameters and calls GetContentsAsync() to make the API request.
        This overrides the parent method because it uses "L" instead if "id" for the license string parameter
        """
        rest_request = "&L=" + quote(self.license)
        rest_request += "&" + urlencode(parameters)
        rest_request = self.endpoint + "?" + rest_request
        response = await self.get_contents_async(self.base_url, rest_request)
        return response

