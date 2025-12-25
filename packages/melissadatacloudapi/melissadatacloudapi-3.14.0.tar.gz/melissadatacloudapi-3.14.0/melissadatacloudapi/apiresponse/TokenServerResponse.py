from .ResponseBase import ResponseBase

class TokenServerResponse(ResponseBase):
    def __init__(self, request_token_response="", result="", token=""):
        self.request_token_response = request_token_response,
        self.result = result,
        self.token = token
        

    @classmethod
    def populate_from_dict(cls, data: dict):
        cls.data = data
        return cls(
            request_token_response=data.get("RequestTokenResponse", ""),
            result=data.get("Result", ""),
            token=data.get("Token", ""),
        )
    
    # Setters
    def set_request_token_response(self, request_token_response):
        self.request_token_response = request_token_response

    def set_result(self, result):
        self.result = result

    def set_token(self, token):
        self.token = token
    
    # Getters
    def get_request_token_response(self):
        return self.request_token_response or ""

    def get_result(self):
        return self.result or ""

    def get_token(self):
        return self.token or ""
  

