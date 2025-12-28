from someip_py.codec import *


class IdtCarCfgValue(SomeIpPayload):

    _include_struct_len = True

    ParameterId: Int32

    ParameterValue: Int32

    def __init__(self):

        self.ParameterId = Int32()

        self.ParameterValue = Int32()


class IdtCarCfgValues(SomeIpPayload):

    IdtCarCfgValues: SomeIpDynamicSizeArray[IdtCarCfgValue]

    def __init__(self):

        self.IdtCarCfgValues = SomeIpDynamicSizeArray(IdtCarCfgValue)


class IdtCfgIntValue(SomeIpPayload):

    IdtCfgIntValue: Int32

    def __init__(self):

        self.IdtCfgIntValue = Int32()
