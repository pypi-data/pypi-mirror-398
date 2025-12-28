from someip_py.codec import *


class ESIMTrafficData(SomeIpPayload):

    _include_struct_len = True

    Txbytecount: Uint64

    Rxbytecount: Uint64

    def __init__(self):

        self.Txbytecount = Uint64()

        self.Rxbytecount = Uint64()


class ESIMstatusKls(SomeIpPayload):

    _include_struct_len = True

    Available: Uint8

    ESIMConnectionStatus: Uint8

    Hispeedfun: Uint8

    Signalstrength: Uint8

    Signallevl: Uint8

    Ipadr: SomeIpDynamicSizeString

    DataConnectionStatus: Uint8

    ESIMTrafficData: ESIMTrafficData

    Operator: Uint8

    def __init__(self):

        self.Available = Uint8()

        self.ESIMConnectionStatus = Uint8()

        self.Hispeedfun = Uint8()

        self.Signalstrength = Uint8()

        self.Signallevl = Uint8()

        self.Ipadr = SomeIpDynamicSizeString()

        self.DataConnectionStatus = Uint8()

        self.ESIMTrafficData = ESIMTrafficData()

        self.Operator = Uint8()


class ESIMstatus(SomeIpPayload):

    ESIMstatus: ESIMstatusKls

    def __init__(self):

        self.ESIMstatus = ESIMstatusKls()
