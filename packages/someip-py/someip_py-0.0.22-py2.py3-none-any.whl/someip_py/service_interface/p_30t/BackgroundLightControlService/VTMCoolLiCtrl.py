from someip_py.codec import *


class IdtIndicatorLightKls(SomeIpPayload):

    _include_struct_len = True

    Function: Uint8

    PWM: Uint8

    def __init__(self):

        self.Function = Uint8()

        self.PWM = Uint8()


class IdtIndicatorLight(SomeIpPayload):

    IdtIndicatorLight: IdtIndicatorLightKls

    def __init__(self):

        self.IdtIndicatorLight = IdtIndicatorLightKls()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
