

class GEAIException(Exception):
    """Base class for all PyGEAI exceptions."""
    pass


class UnknownArgumentError(GEAIException):
    """Argument provided is not valid"""
    pass


class MissingRequirementException(GEAIException):
    """Requirement not available"""
    pass


class WrongArgumentError(GEAIException):
    """Wrongly formatted arguments"""
    pass


class ServerResponseError(GEAIException):
    """There was an error in the request to the server"""
    pass


class APIError(GEAIException):
    """There was an error in the request to the server"""
    pass


class InvalidPathException(GEAIException):
    """There was an error trying to find the file in the specified path"""
    pass


class InvalidJSONException(GEAIException):
    """There was an error trying to load data from the JSON file"""
    pass


class InvalidAPIResponseException(GEAIException):
    """There was an error handling response from the server"""
    pass


class InvalidResponseException(GEAIException):
    """There was an error getting a response from the server"""
    pass


class InvalidAgentException(GEAIException):
    """There was an error getting a response from the server"""
    pass


class APIResponseError(GEAIException):
    pass

