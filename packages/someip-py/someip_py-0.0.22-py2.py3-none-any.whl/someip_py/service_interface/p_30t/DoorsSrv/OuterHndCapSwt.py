from someip_py.codec import *


class IdtSingle2OuterHndCapSwt(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    SwitchSts: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.SwitchSts = Uint8()


class IdtOuter2HndCapSwt(SomeIpPayload):

    IdtOuter2HndCapSwt: SomeIpDynamicSizeArray[IdtSingle2OuterHndCapSwt]

    def __init__(self):

        self.IdtOuter2HndCapSwt = SomeIpDynamicSizeArray(IdtSingle2OuterHndCapSwt)
