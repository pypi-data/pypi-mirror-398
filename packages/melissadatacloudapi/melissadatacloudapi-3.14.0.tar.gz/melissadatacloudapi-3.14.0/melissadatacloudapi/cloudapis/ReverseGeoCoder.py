import json
import os
from .CloudApiBase import CloudApiBase

class ReverseGeoCoder(CloudApiBase):

    def __init__(self, license=None):
        super().__init__("https://reversegeo.melissadata.net", "/v3/web/ReverseGeoCode/doLookup")
        self.license = license or os.environ.get("MD_LICENSE")
        self.parameters["format"] = "json"
        self.post_body = None

        self.parameter_mappings = {
            "latitude": "lat",
            "longitude": "long",
            "max_records": "recs",
            "max_distance": "dist",
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
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, value):
        self._set_parameter("latitude", value)

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, value):
        self._set_parameter("longitude", value)

    @property
    def max_records(self):
        return self._max_records

    @max_records.setter
    def max_records(self, value):
        self._set_parameter("max_records", value)

    @property
    def max_distance(self):
        return self._max_distance

    @max_distance.setter
    def max_distance(self, value):
        self._set_parameter("max_distance", value)

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

    def set_latitude(self, latitude: str):
        self._set_parameter("latitude", latitude)

    def set_longitude(self, longitude: str):
        self._set_parameter("longitude", longitude)

    def set_max_records(self, records: str):
        self._set_parameter("max_records", records)

    def set_max_distance(self, distance: str):
        self._set_parameter("max_distance", distance)

    def set_transmission_reference(self, transmission_reference: str):
        self._set_parameter("transmission_reference", transmission_reference)

    def set_opt(self, opt: str):
        self._set_parameter("opt", opt)

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

    def get_latitude(self):
        return self.parameters.get(self.parameter_mappings["latitude"], "")

    def get_longitude(self):
        return self.parameters.get(self.parameter_mappings["longitude"], "")

    def get_max_records(self):
        return self.parameters.get(self.parameter_mappings["max_records"], "")

    def get_max_distance(self):
        return self.parameters.get(self.parameter_mappings["max_distance"], "")

    def get_transmission_reference(self):
        return self.parameters.get(self.parameter_mappings["transmission_reference"], "")

    def get_opt(self):
        return self.parameters.get(self.parameter_mappings["opt"], "")

    def get_post_batch_body(self):
        return self.post_body
    
    # Class Methods

    def get_do_lookup(self, response_type):
        """
        This synchronous function sends the CloudAPI request using the /v3/web/ReverseGeoCode/doLookup endpoint
        """
        self.set_endpoint("/v3/web/ReverseGeoCode/doLookup")
        return self.get(response_type)

    
    def post_do_lookup(self, response_type):
        """
        This synchronous function sends a post request to the Cloud API using the /v3/web/ReverseGeoCode/doLookup endpoint
        """
        self.set_endpoint("/v3/web/ReverseGeoCode/doLookup")
        response = self.send_post_request(self.post_body)
        return self.handle_response(response, response_type)

    
    def get_do_lookup_postal_codes(self, response_type):
        """
        This synchronous function sends the CloudAPI request using the /V3/WEB/ReverseGeoCode/doLookupPostalCodes endpoint
        """
        self.set_endpoint("/V3/WEB/ReverseGeoCode/doLookupPostalCodes")
        return self.get(response_type)

    
    def post_do_lookup_postal_codes(self, response_type):
        """
        This synchronous function sends a post request to the Cloud API using the /V3/WEB/ReverseGeoCode/doLookupPostalCodes endpoint
        """
        self.set_endpoint("/V3/WEB/ReverseGeoCode/doLookupPostalCodes")
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
