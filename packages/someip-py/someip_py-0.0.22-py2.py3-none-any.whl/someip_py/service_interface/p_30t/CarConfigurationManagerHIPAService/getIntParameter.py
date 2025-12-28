from someip_py.codec import *


class IdtCfgIntValueHIPA(SomeIpPayload):

    IdtCfgIntValueHIPA: Int16

    def __init__(self):

        self.IdtCfgIntValueHIPA = Int16()


class IdtCarCfgParameterValueHIPA(SomeIpPayload):

    IdtCarCfgParameterValueHIPA: Int16

    def __init__(self):

        self.IdtCarCfgParameterValueHIPA = Int16()
