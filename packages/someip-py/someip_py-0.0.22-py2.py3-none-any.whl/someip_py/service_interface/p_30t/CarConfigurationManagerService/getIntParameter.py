from someip_py.codec import *


class IdtCfgIntValue(SomeIpPayload):

    IdtCfgIntValue: Int32

    def __init__(self):

        self.IdtCfgIntValue = Int32()


class IdtCarCfgParameterValue(SomeIpPayload):

    IdtCarCfgParameterValue: Int32

    def __init__(self):

        self.IdtCarCfgParameterValue = Int32()
