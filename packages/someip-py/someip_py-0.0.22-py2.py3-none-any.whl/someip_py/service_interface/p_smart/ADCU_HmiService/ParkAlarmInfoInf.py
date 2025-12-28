from someip_py.codec import *


class ParkAlarmInfoKls(SomeIpPayload):

    ParkAlarmSeN: Uint32

    def __init__(self):

        self.ParkAlarmSeN = Uint32()


class ParkAlarmInfo(SomeIpPayload):

    ParkAlarmInfo: ParkAlarmInfoKls

    def __init__(self):

        self.ParkAlarmInfo = ParkAlarmInfoKls()
