from someip_py.codec import *


class IdtSimTrfcData(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimTxbytecount: Uint64

    SimRxbytecount: Uint64

    def __init__(self):

        self.SimNo = Uint8()

        self.SimTxbytecount = Uint64()

        self.SimRxbytecount = Uint64()


class IdtTrafficDataStructKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    TrafficData1: SomeIpDynamicSizeArray[IdtSimTrfcData]

    TrafficData2: SomeIpDynamicSizeArray[IdtSimTrfcData]

    TrafficData3: SomeIpDynamicSizeArray[IdtSimTrfcData]

    def __init__(self):

        self.TrafficData1 = SomeIpDynamicSizeArray(IdtSimTrfcData)

        self.TrafficData2 = SomeIpDynamicSizeArray(IdtSimTrfcData)

        self.TrafficData3 = SomeIpDynamicSizeArray(IdtSimTrfcData)


class IdtTrafficDataStruct(SomeIpPayload):

    IdtTrafficDataStruct: IdtTrafficDataStructKls

    def __init__(self):

        self.IdtTrafficDataStruct = IdtTrafficDataStructKls()
