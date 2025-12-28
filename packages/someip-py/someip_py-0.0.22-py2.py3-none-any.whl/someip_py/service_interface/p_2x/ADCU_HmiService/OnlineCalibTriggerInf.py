from someip_py.codec import *


class IdtOnlineCalibTriggerKls(SomeIpPayload):

    OnlineCalibTrigger: Uint8

    CalibItems: Uint32

    def __init__(self):

        self.OnlineCalibTrigger = Uint8()

        self.CalibItems = Uint32()


class IdtOnlineCalibTrigger(SomeIpPayload):

    IdtOnlineCalibTrigger: IdtOnlineCalibTriggerKls

    def __init__(self):

        self.IdtOnlineCalibTrigger = IdtOnlineCalibTriggerKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
