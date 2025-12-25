import requests
import json
from urllib.parse import urlencode, quote
from abc import ABC

class CloudApiBase(ABC):
    """
    CloudApiBase sets the foundation of every CloudApi class.
    This class contains variables and methods that all CloudApi classes share.
    This class contains all the methods that are responsible for sending out API requests.
    """

    def __init__(self, base_url=None, endpoint=None):
        self.base_url = base_url
        self.license = None
        self.endpoint = endpoint
        self.parameters = {}
        self.parameter_mappings = {}


    # Setters
    def set_base_url(self, base_url):
        self.base_url = base_url

    def set_license(self, license):
        self.license = license

    def set_endpoint(self, endpoint):
        self.endpoint = endpoint

    def set_format(self, format):
        self.parameters["format"] = format

    # Getters
    def get_base_url(self):
        return self.base_url or ""

    def get_license(self):
        return self.license or ""

    def get_endpoint(self):
        return self.endpoint or ""

    def get_format(self):
        return self.parameters.get("format", "")

    def get_value(self, parameter):
        if parameter.lower() == "baseurl":
            return self.base_url
        elif parameter.lower() == "license":
            return self.base_url
        elif parameter.lower() == "endpoint":
            return self.base_url
        elif parameter.lower() == "format":
            return self.base_url
        
        return self.parameters.get(self.parameter_mappings[parameter], "")

    # Class Methods
    def clear(self):
        """
        This function clears all the variables set for the CloudAPI but remembers the license, baseUrl, and endpoint.
        """
        self.parameters.clear()
        self.parameters["format"] = "json"

    def get_contents(self, base_url, request_query):
        """
        This synchronous function makes the API request using the baseURL and assembled endpoint with parameters (requestQuery).
        """
        response = requests.get(f"{base_url}{request_query}")
        response.raise_for_status()
        text = response.text
        obj = json.loads(text)
        pretty_response = json.dumps(obj, indent=4)
        return pretty_response

    def process_request(self, parameters):
        """
        This synchronous function assembles the endpoint with the parameters and calls GetContents() to make the API request.
        """
        rest_request = "&id=" + quote(self.license)
        rest_request += "&" + urlencode(parameters)
        rest_request = self.endpoint + "?" + rest_request
        response = self.get_contents(self.base_url, rest_request)
        return response

    def send_post_request(self, post_request):
        """
        This synchronous function sends a batch request to the API.
        """
        try:
            headers = {'Content-Type': 'application/json'}
            json_batch = json.dumps(post_request.to_dict())  # Convert to dict first
            response = requests.post(f"{self.base_url}{self.endpoint}", headers=headers, data=json_batch)
            response.raise_for_status()
            response_content = response.text
            
            obj = json.loads(response_content)
            pretty_response = json.dumps(obj, indent=4)

            return pretty_response
        except Exception as ex:
            return str(ex)


    def get(self, response_type=None):
        """
        This function calls ProcessRequest() to send the CloudAPI request and get the response.
        This function coordinates a string or deserialized response object return.
        """
        response = self.process_request(self.parameters)
        return self.handle_response(response, response_type)


    def send_version_request(self):
        """
        This synchronous function makes a request to the getversion endpoint.
        """
        try:
            trimmed_endpoint = self.endpoint.rstrip('/')
            segments = trimmed_endpoint.split('/')
            segments[-1] = "getversion"
            version_endpoint = "/".join(segments)
            response = requests.get(f"{self.base_url}{version_endpoint}")
            response.raise_for_status()
            response_body = response.text
            return response_body
        except Exception as ex:
            return str(ex)


    def handle_response(self, response, response_type):
        """
        This function determines whether to deserialize the json response or not.
        """
        if response_type == str or response_type == None:
            return response
        data = json.loads(response)
        response_objectect = response_type.populate_from_dict(data)

        return response_objectect
