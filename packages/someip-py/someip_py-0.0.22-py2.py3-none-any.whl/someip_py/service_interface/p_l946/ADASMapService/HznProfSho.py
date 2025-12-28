from someip_py.codec import *


class IdtHznProfShoKls(SomeIpPayload):

    _include_struct_len = True

    CyclicCounter: Uint8

    MessageType: Uint8

    Offset: Uint16

    PathIndex: Uint8

    ProfileType: Uint8

    Value: Uint32

    Accuracy: Uint8

    Distance: Uint16

    ControlPoint: Bool

    Retransmission: Bool

    Update: Bool

    Value1: Uint32

    def __init__(self):

        self.CyclicCounter = Uint8()

        self.MessageType = Uint8()

        self.Offset = Uint16()

        self.PathIndex = Uint8()

        self.ProfileType = Uint8()

        self.Value = Uint32()

        self.Accuracy = Uint8()

        self.Distance = Uint16()

        self.ControlPoint = Bool()

        self.Retransmission = Bool()

        self.Update = Bool()

        self.Value1 = Uint32()


class IdtHznProfSho(SomeIpPayload):

    IdtHznProfSho: IdtHznProfShoKls

    def __init__(self):

        self.IdtHznProfSho = IdtHznProfShoKls()
