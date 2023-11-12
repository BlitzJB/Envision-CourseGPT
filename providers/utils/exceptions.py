class RequestFailedException(Exception):
    pass

class RateLimitException(RequestFailedException):
    pass

class BadGatewayException(RequestFailedException):
    pass

class MaxRetriesExceeded(Exception):
    pass