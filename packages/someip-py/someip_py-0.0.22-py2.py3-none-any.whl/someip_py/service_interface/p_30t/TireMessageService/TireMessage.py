from someip_py.codec import *


class IdtTireMsg(SomeIpPayload):

    _include_struct_len = True

    TireMsgT: Int16

    TireMsgP: Float32

    TireMsgTWarnFlg: Uint8

    TireMsgPWarnFlg: Uint8

    TireMsgSysWarnFlg: Uint8

    TireMsgFastLoseWarnFlg: Uint8

    TireMsgBattLoSt: Uint8

    TireMsgMsgOldFlg: Uint8

    TireMsgTireFillgAssiPSts: Uint8

    def __init__(self):

        self.TireMsgT = Int16()

        self.TireMsgP = Float32()

        self.TireMsgTWarnFlg = Uint8()

        self.TireMsgPWarnFlg = Uint8()

        self.TireMsgSysWarnFlg = Uint8()

        self.TireMsgFastLoseWarnFlg = Uint8()

        self.TireMsgBattLoSt = Uint8()

        self.TireMsgMsgOldFlg = Uint8()

        self.TireMsgTireFillgAssiPSts = Uint8()


class IdtTireMsgGroup(SomeIpPayload):

    _include_struct_len = True

    TireID: Uint8

    TireMsg: IdtTireMsg

    def __init__(self):

        self.TireID = Uint8()

        self.TireMsg = IdtTireMsg()


class IdtTireMessage(SomeIpPayload):

    IdtTireMessage: SomeIpDynamicSizeArray[IdtTireMsgGroup]

    def __init__(self):

        self.IdtTireMessage = SomeIpDynamicSizeArray(IdtTireMsgGroup)
