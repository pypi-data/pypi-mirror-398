class SimoSdkError(Exception):
    """Base exception for simo-sdk."""


class RestError(SimoSdkError):
    pass


class MqttError(SimoSdkError):
    pass


class BootstrapError(SimoSdkError):
    pass

