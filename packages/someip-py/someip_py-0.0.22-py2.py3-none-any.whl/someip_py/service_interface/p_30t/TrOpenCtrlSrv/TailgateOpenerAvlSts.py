from someip_py.codec import *


class IdtTailgateOpenerAvlSts(SomeIpPayload):

    _include_struct_len = True

    TailgateID: Uint8

    TailgateOpenerAvlSts: Uint8

    def __init__(self):

        self.TailgateID = Uint8()

        self.TailgateOpenerAvlSts = Uint8()


class IdtTailgatesOpenerAvlSts(SomeIpPayload):

    IdtTailgatesOpenerAvlSts: SomeIpDynamicSizeArray[IdtTailgateOpenerAvlSts]

    def __init__(self):

        self.IdtTailgatesOpenerAvlSts = SomeIpDynamicSizeArray(IdtTailgateOpenerAvlSts)
