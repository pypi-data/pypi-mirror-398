"""Kameleoon exceptions"""


class KameleoonError(Exception):
    """Base Kameleoon error"""

    def __init__(self, message=None) -> None:
        self.message = f"Kameleoon error: {message}"
        super().__init__(self.message)


class ConfigException(KameleoonError):
    """Config Exception"""


class ConfigFileNotFound(ConfigException):
    """Config File Not Found"""


class ConfigCredentialsInvalid(ConfigException):
    """Config Credentials are Invalid"""


class SiteCodeIsEmpty(KameleoonError):
    """Site Code is Empty"""


class NotFoundError(KameleoonError):
    """Base not found error"""

    def __init__(self, message=None) -> None:
        self.message = str(message) + " not found."
        super().__init__(self.message)


class FeatureError(KameleoonError):
    """Base feature flag error"""

    def __init__(self, message=None) -> None:
        super().__init__(f"Feature error: {message}")


class FeatureVariationNotFound(NotFoundError):
    """Variation configuration not found"""

    def __init__(self, message=None) -> None:
        self.message = "Variation " + str(message)
        super().__init__(self.message)


class FeatureEnvironmentDisabled(FeatureError):
    """Exception indicating that feature flag is disabled for the visitor's current environment."""


class FeatureNotFound(NotFoundError):
    """Exception indicating that the requested feature ID
    has not been found in the internal configuration of the SDK.
    This is usually normal and means that the feature flag
    has not yet been activated on Kameleoon's side."""

    def __init__(self, message=None) -> None:
        self.message = "Feature flag Id: " + str(message)
        super().__init__(self.message)


class FeatureExperimentNotFound(NotFoundError):
    """Exception indicating that the requested experiment has not been found.
    Check that the experiment's ID matches the provided one."""

    def __init__(self, message=None) -> None:
        self.message = "Experiment " + str(message)
        super().__init__(self.message)


class FeatureVariableNotFound(NotFoundError):
    """Exception indicating that the requested variable has not been found.
    Check that the variable's ID (or key) matches the one in your code."""

    def __init__(self, message=None) -> None:
        self.message = "Feature variable " + str(message)
        super().__init__(self.message)


class VisitorCodeInvalid(KameleoonError):
    """Exception indicating that visitorCode is empty or too long."""

    def __init__(self, message=None) -> None:
        self.message = "Visitor code not valid: " + str(message)
        super().__init__(self.message)
