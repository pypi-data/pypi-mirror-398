from someip_py.codec import *


class CalibTriggerKls(SomeIpPayload):

    CalibSensorTriggerSeN: Uint32

    CalibSensorItemsSeN: Uint64

    def __init__(self):

        self.CalibSensorTriggerSeN = Uint32()

        self.CalibSensorItemsSeN = Uint64()


class CalibTrigger(SomeIpPayload):

    CalibTrigger: CalibTriggerKls

    def __init__(self):

        self.CalibTrigger = CalibTriggerKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
