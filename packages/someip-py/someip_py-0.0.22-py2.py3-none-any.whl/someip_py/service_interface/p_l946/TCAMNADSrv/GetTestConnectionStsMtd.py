from someip_py.codec import *


class TcamDtcInfo(SomeIpPayload):

    _include_struct_len = True

    DtcCode: SomeIpDynamicSizeString

    DtcCodeValue: SomeIpDynamicSizeString

    def __init__(self):

        self.DtcCode = SomeIpDynamicSizeString()

        self.DtcCodeValue = SomeIpDynamicSizeString()


class TcamDtcTestStatus(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    TcamDtcStatus: Uint8

    TcamDtcList: SomeIpDynamicSizeArray[TcamDtcInfo]

    def __init__(self):

        self.TcamDtcStatus = Uint8()

        self.TcamDtcList = SomeIpDynamicSizeArray(TcamDtcInfo)


class SimCardInfo(SomeIpPayload):

    _include_struct_len = True

    SimIMSI: SomeIpDynamicSizeString

    SimICCID: SomeIpDynamicSizeString

    SimMSISDN: SomeIpDynamicSizeString

    SimIMEI: SomeIpDynamicSizeString

    def __init__(self):

        self.SimIMSI = SomeIpDynamicSizeString()

        self.SimICCID = SomeIpDynamicSizeString()

        self.SimMSISDN = SomeIpDynamicSizeString()

        self.SimIMEI = SomeIpDynamicSizeString()


class SimTestStatus(SomeIpPayload):

    _include_struct_len = True

    SimStatus: Uint8

    SimCardInfo: SimCardInfo

    def __init__(self):

        self.SimStatus = Uint8()

        self.SimCardInfo = SimCardInfo()


class ConnectInfoList(SomeIpPayload):

    _include_struct_len = True

    ConnUrl: SomeIpDynamicSizeString

    Packetloss: Uint8

    Responsetime: Uint16

    ConnStatus: Uint8

    def __init__(self):

        self.ConnUrl = SomeIpDynamicSizeString()

        self.Packetloss = Uint8()

        self.Responsetime = Uint16()

        self.ConnStatus = Uint8()


class ConnectTestStatus(SomeIpPayload):

    _include_struct_len = True

    ConnectStatus: Uint8

    ConnectInfoList: ConnectInfoList

    def __init__(self):

        self.ConnectStatus = Uint8()

        self.ConnectInfoList = ConnectInfoList()


class Networkinfo(SomeIpPayload):

    _include_struct_len = True

    SimConStatus: Uint8

    SimOperatorStatus: Uint8

    LteMode: Uint8

    SimCardInfo: SimCardInfo

    Ipadr: SomeIpDynamicSizeString

    Rssnr: Uint8

    Rsrq: Int8

    Rsrp: Int16

    Rssi: Int8

    Mcc: SomeIpDynamicSizeString

    Mnc: SomeIpDynamicSizeString

    Pci: Uint16

    Earfcn: Uint16

    Lac: Uint16

    Tac: Uint32

    def __init__(self):

        self.SimConStatus = Uint8()

        self.SimOperatorStatus = Uint8()

        self.LteMode = Uint8()

        self.SimCardInfo = SimCardInfo()

        self.Ipadr = SomeIpDynamicSizeString()

        self.Rssnr = Uint8()

        self.Rsrq = Int8()

        self.Rsrp = Int16()

        self.Rssi = Int8()

        self.Mcc = SomeIpDynamicSizeString()

        self.Mnc = SomeIpDynamicSizeString()

        self.Pci = Uint16()

        self.Earfcn = Uint16()

        self.Lac = Uint16()

        self.Tac = Uint32()


class NetworkTestStatus(SomeIpPayload):

    _include_struct_len = True

    NetworkStatus: Uint8

    Networkinfo: Networkinfo

    def __init__(self):

        self.NetworkStatus = Uint8()

        self.Networkinfo = Networkinfo()


class SmsTestStatus(SomeIpPayload):

    _include_struct_len = True

    SmsStatus: Uint8

    Smsreceipt: Uint8

    def __init__(self):

        self.SmsStatus = Uint8()

        self.Smsreceipt = Uint8()


class GpsInfo(SomeIpPayload):

    _include_struct_len = True

    Longitude: Int32

    Latitude: Int32

    def __init__(self):

        self.Longitude = Int32()

        self.Latitude = Int32()


class TestConnectionStsKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    Vin: SomeIpDynamicSizeString

    TemID: SomeIpDynamicSizeString

    TcamDtcTestStatus: TcamDtcTestStatus

    SimTestStatus: SimTestStatus

    ConnectTestStatus: ConnectTestStatus

    NetworkTestStatus: NetworkTestStatus

    SmsTestStatus: SmsTestStatus

    GpsInfo: GpsInfo

    CallTestStatus: Uint8

    Gnssfault: Uint8

    Wififault: Uint8

    Modemfault: Uint8

    Mcufault: Uint8

    Cpuusagerate: Uint8

    Emmcfreespace: Uint32

    Memoryfreespace: Uint32

    RetVal: Uint8

    def __init__(self):

        self.Vin = SomeIpDynamicSizeString()

        self.TemID = SomeIpDynamicSizeString()

        self.TcamDtcTestStatus = TcamDtcTestStatus()

        self.SimTestStatus = SimTestStatus()

        self.ConnectTestStatus = ConnectTestStatus()

        self.NetworkTestStatus = NetworkTestStatus()

        self.SmsTestStatus = SmsTestStatus()

        self.GpsInfo = GpsInfo()

        self.CallTestStatus = Uint8()

        self.Gnssfault = Uint8()

        self.Wififault = Uint8()

        self.Modemfault = Uint8()

        self.Mcufault = Uint8()

        self.Cpuusagerate = Uint8()

        self.Emmcfreespace = Uint32()

        self.Memoryfreespace = Uint32()

        self.RetVal = Uint8()


class TestConnectionSts(SomeIpPayload):

    TestConnectionSts: TestConnectionStsKls

    def __init__(self):

        self.TestConnectionSts = TestConnectionStsKls()
