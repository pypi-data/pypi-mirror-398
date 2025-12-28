from someip_py.codec import *


class IdtParameterIDs100(SomeIpPayload):

    IdtParameterIDs100: SomeIpDynamicSizeArray[Int16]

    def __init__(self):

        self.IdtParameterIDs100 = SomeIpDynamicSizeArray(Int16)


class IdtCarCfgValueHIPA(SomeIpPayload):

    _include_struct_len = True

    ParameterId: Int16

    ParameterValue: Int16

    def __init__(self):

        self.ParameterId = Int16()

        self.ParameterValue = Int16()


class IdtCarCfgValues100(SomeIpPayload):

    IdtCarCfgValues100: SomeIpDynamicSizeArray[IdtCarCfgValueHIPA]

    def __init__(self):

        self.IdtCarCfgValues100 = SomeIpDynamicSizeArray(IdtCarCfgValueHIPA)
