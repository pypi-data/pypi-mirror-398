from someip_py.codec import *


class IdtFeatureState2(SomeIpPayload):

    Key: Uint16

    Value: Int32

    def __init__(self):

        self.Key = Uint16()

        self.Value = Int32()


class FeatureState2(SomeIpPayload):

    FeatureState2: SomeIpDynamicSizeArray[IdtFeatureState2]

    def __init__(self):

        self.FeatureState2 = SomeIpDynamicSizeArray(IdtFeatureState2)
