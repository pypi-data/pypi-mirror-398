from someip_py.codec import *


class IdtHznProfShoKls(SomeIpPayload):

    _include_struct_len = True

    Accuracy: Uint8

    ControlPoint: Bool

    CyclicCounter: Uint8

    Distance: Uint16

    MessageType: Uint8

    Offset: Uint16

    PathIndex: Uint8

    ProfileType: Uint8

    Retransmission: Bool

    Update: Bool

    Value: Uint32

    Value1: Uint32

    def __init__(self):

        self.Accuracy = Uint8()

        self.ControlPoint = Bool()

        self.CyclicCounter = Uint8()

        self.Distance = Uint16()

        self.MessageType = Uint8()

        self.Offset = Uint16()

        self.PathIndex = Uint8()

        self.ProfileType = Uint8()

        self.Retransmission = Bool()

        self.Update = Bool()

        self.Value = Uint32()

        self.Value1 = Uint32()


class IdtHznProfSho(SomeIpPayload):

    IdtHznProfSho: IdtHznProfShoKls

    def __init__(self):

        self.IdtHznProfSho = IdtHznProfShoKls()
