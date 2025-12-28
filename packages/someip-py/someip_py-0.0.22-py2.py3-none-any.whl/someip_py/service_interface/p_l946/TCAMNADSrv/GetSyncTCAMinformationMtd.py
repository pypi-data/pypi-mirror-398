from someip_py.codec import *


class SyncTCAMinformationKls(SomeIpPayload):

    _include_struct_len = True

    DU: SomeIpDynamicSizeString

    HWSDHWKN: SomeIpDynamicSizeString

    SXBL: SomeIpDynamicSizeString

    SXDISXBL: SomeIpDynamicSizeString

    SWDISWBL: SomeIpDynamicSizeString

    SWLMSWLx: SomeIpDynamicSizeString

    SXDISWLM: SomeIpDynamicSizeString

    IMSI: SomeIpDynamicSizeString

    ICCID: SomeIpDynamicSizeString

    MSISDN: SomeIpDynamicSizeString

    IMEI: SomeIpDynamicSizeString

    TCAMID: SomeIpDynamicSizeString

    RetVal: Uint8

    def __init__(self):

        self.DU = SomeIpDynamicSizeString()

        self.HWSDHWKN = SomeIpDynamicSizeString()

        self.SXBL = SomeIpDynamicSizeString()

        self.SXDISXBL = SomeIpDynamicSizeString()

        self.SWDISWBL = SomeIpDynamicSizeString()

        self.SWLMSWLx = SomeIpDynamicSizeString()

        self.SXDISWLM = SomeIpDynamicSizeString()

        self.IMSI = SomeIpDynamicSizeString()

        self.ICCID = SomeIpDynamicSizeString()

        self.MSISDN = SomeIpDynamicSizeString()

        self.IMEI = SomeIpDynamicSizeString()

        self.TCAMID = SomeIpDynamicSizeString()

        self.RetVal = Uint8()


class SyncTCAMinformation(SomeIpPayload):

    SyncTCAMinformation: SyncTCAMinformationKls

    def __init__(self):

        self.SyncTCAMinformation = SyncTCAMinformationKls()
