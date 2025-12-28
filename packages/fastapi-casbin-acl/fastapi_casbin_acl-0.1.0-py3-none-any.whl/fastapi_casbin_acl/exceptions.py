class ACLException(Exception):
    """Base exception for fastapi-casbin-acl"""
    pass

class ACLNotInitialized(ACLException):
    """Raised when the ACL system has not been initialized (Enforcer not set)"""
    pass

class ConfigError(ACLException):
    """Raised when there is a configuration error"""
    pass

class Unauthorized(ACLException):
    """Raised when the user is not authenticated (subject is None/missing) but permission is required"""
    pass

class Forbidden(ACLException):
    """Raised when the user is authenticated but lacks permission"""
    pass

