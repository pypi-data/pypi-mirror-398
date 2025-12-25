class MissingMetatronException(Exception):
    """A custom exception to notify users that Metatron is not installed"""
    
    def __init__(self, message="Missing Metatron module. Install package using internal extras (i.e pickley install ntscli-client[internal])"):
        self.message = message
        super().__init__(self.message)

class UnauthorizedException(Exception):
    """A custom exception to notify users that their request is unauthorized"""

    def __init__(self, message):
        self.message = f"{message} (401 Client Error: Unauthorized)"
        super().__init__(self.message)

class ForbiddenException(Exception):
    """A custom exception to notify users that their request is forbidden"""

    def __init__(self, message):
        self.message = f"{message} (403 Client Error: Forbidden)"
        super().__init__(self.message)

class UnclaimedDeviceException(Exception):
    """A custom exception to notify users that they must claim the device they're executing NTS-CLI commands for"""

    def __init__(self, message):
        self.message = f"{message} (Device must be claimed in HWM)"
        super().__init__(self.message)

class DeviceAlreadyReservedException(Exception):
    """A custom exception to notify users that the device they're attempting to run a test plan for is already reserved"""

    def __init__(self, message):
        self.message = f"{message} (Device has already been reserved)"
        super().__init__(self.message)

class DeviceIsUnavailableException(Exception):
    """A custom exception to notify users that the device they're attempting to run a test plan for is unavailable"""

    def __init__(self, message):
        self.message = f"{message} (Device is unavailable)"
        super().__init__(self.message)