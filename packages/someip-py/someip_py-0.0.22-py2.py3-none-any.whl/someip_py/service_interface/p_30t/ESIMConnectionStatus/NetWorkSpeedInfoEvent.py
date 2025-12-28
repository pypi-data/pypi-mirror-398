from someip_py.codec import *


class IdtSimNetSpeed(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimTxbytecount: Uint64

    SimRxbytecount: Uint64

    def __init__(self):

        self.SimNo = Uint8()

        self.SimTxbytecount = Uint64()

        self.SimRxbytecount = Uint64()


class IdtNetWorkSpeedInfoKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    NetSpeedForAPN1: SomeIpDynamicSizeArray[IdtSimNetSpeed]

    NetSpeedForAPN2: SomeIpDynamicSizeArray[IdtSimNetSpeed]

    NetSpeedForAPN3: SomeIpDynamicSizeArray[IdtSimNetSpeed]

    def __init__(self):

        self.NetSpeedForAPN1 = SomeIpDynamicSizeArray(IdtSimNetSpeed)

        self.NetSpeedForAPN2 = SomeIpDynamicSizeArray(IdtSimNetSpeed)

        self.NetSpeedForAPN3 = SomeIpDynamicSizeArray(IdtSimNetSpeed)


class IdtNetWorkSpeedInfo(SomeIpPayload):

    IdtNetWorkSpeedInfo: IdtNetWorkSpeedInfoKls

    def __init__(self):

        self.IdtNetWorkSpeedInfo = IdtNetWorkSpeedInfoKls()
