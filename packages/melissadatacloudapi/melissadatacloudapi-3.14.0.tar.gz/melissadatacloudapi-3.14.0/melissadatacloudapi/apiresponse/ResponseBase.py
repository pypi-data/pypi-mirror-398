from abc import ABC, abstractmethod


class ResponseBase(ABC):
    """
    All response structures will inherit the Response Base and be able to access this function.
    This is a getter function that allows you to get response structure variable values by their name
    """

    def __init__(self):
        self.data = None
    
    def set_response(self, data):
        self.data = data

    def get_value(self, attribute):
        '''
        This method retrieves the value directly from the JSON response.
        Ensure that your input attibute matches the exact casing of the JSON output.
        Use this method especially when the API response may have been updated but 
        this library has not yet been updated to match.

        When you use get_value and the attribute is a list, this will always return a list of strings. 
        It will not parse the JSON into an object.
        '''

        value = self.data.get(attribute, "")

        if value == None:
            raise AttributeError(f"Attribute '{attribute}' not found")
        
        return value
