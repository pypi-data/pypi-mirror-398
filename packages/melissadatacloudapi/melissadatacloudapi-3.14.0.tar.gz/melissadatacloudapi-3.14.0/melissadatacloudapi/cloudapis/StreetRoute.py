import json
import os
from .CloudApiBase import CloudApiBase
from ..PostReqestBase import StreetRoutePostRequest

class StreetRoute(CloudApiBase):

    def __init__(self, license=None):
        super().__init__("https://streetroute.melissadata.net", "/v1/WEB/StreetRoute/getDistance")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"
        self.records = []
        self.post_body = None

        self.parameter_mappings = {
            "units": "units",
            "start_latitude": "StartLatitude",
            "start_longitude": "StartLongitude",
            "end_latitude": "EndLatitude",
            "end_longitude": "EndLongitude",
            "transmission_reference": "t"
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
    def units(self):
        return self._units

    @units.setter
    def units(self, value):
        self._set_parameter("units", value)

    @property
    def start_latitude(self):
        return self._start_latitude

    @start_latitude.setter
    def start_latitude(self, value):
        self._set_parameter("start_latitude", value)

    @property
    def start_longitude(self):
        return self._start_longitude

    @start_longitude.setter
    def start_longitude(self, value):
        self._set_parameter("start_longitude", value)

    @property
    def end_latitude(self):
        return self._end_latitude

    @end_latitude.setter
    def end_latitude(self, value):
        self._set_parameter("end_latitude", value)

    @property
    def end_longitude(self):
        return self._end_longitude

    @end_longitude.setter
    def end_longitude(self, value):
        self._set_parameter("end_longitude", value)

    @property
    def transmission_reference(self):
        return self._transmission_reference

    @transmission_reference.setter
    def transmission_reference(self, value):
        self._set_parameter("transmission_reference", value)

    # Setters

    def set_units(self, units: str):
        self._set_parameter("units", units)

    def set_start_latitude(self, start_latitude: str):
        self._set_parameter("start_latitude", start_latitude)

    def set_start_longitude(self, start_longitude: str):
        self._set_parameter("start_longitude", start_longitude)

    def set_end_latitude(self, end_latitude: str):
        self._set_parameter("end_latitude", end_latitude)

    def set_end_longitude(self, end_longitude: str):
        self._set_parameter("end_longitude", end_longitude)

    def set_transmission_reference(self, transmission_reference: str):
        self._set_parameter("transmission_reference", transmission_reference)

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

    def get_units(self):
        return self.parameters.get(self.parameter_mappings["units"], "")

    def get_start_latitude(self):
        return self.parameters.get(self.parameter_mappings["start_latitude"], "")

    def get_start_longitude(self):
        return self.parameters.get(self.parameter_mappings["start_longitude"], "")

    def get_end_latitude(self):
        return self.parameters.get(self.parameter_mappings["end_latitude"], "")

    def get_end_longitude(self):
        return self.parameters.get(self.parameter_mappings["end_longitude"], "")

    def get_transmission_reference(self):
        return self.parameters.get(self.parameter_mappings["transmission_reference"], "")

    def get_post_body(self):
        return self.post_body
    
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
            post_request = StreetRoutePostRequest(
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


