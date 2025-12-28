from someip_py.codec import *


class NOPTime1(SomeIpPayload):

    hour: Uint16

    minute: Uint16

    def __init__(self):

        self.hour = Uint16()

        self.minute = Uint16()


class NOPUsageStaInfoKls(SomeIpPayload):

    NOPTotalTime: NOPTime1

    NOPTotalDistance: Uint16

    NOPSuccessLaneChangetimes: Uint16

    NOPSuccessNaviLaneChangetimes: Uint16

    NOPSafePassTunneltimes: Uint16

    NOPAvoidDangertimes: Uint16

    NOPRampInOutTimes: Uint16

    NOPCutInYieldTimes: Uint16

    NOPBypassSuccessTimes: Uint16

    NOPIntersectionPassTimes: Uint16

    NOPRoundaboutPassTimes: Uint16

    NOPUTurnSuccessTimes: Uint16

    NOPDistanceRatio: Uint16

    def __init__(self):

        self.NOPTotalTime = NOPTime1()

        self.NOPTotalDistance = Uint16()

        self.NOPSuccessLaneChangetimes = Uint16()

        self.NOPSuccessNaviLaneChangetimes = Uint16()

        self.NOPSafePassTunneltimes = Uint16()

        self.NOPAvoidDangertimes = Uint16()

        self.NOPRampInOutTimes = Uint16()

        self.NOPCutInYieldTimes = Uint16()

        self.NOPBypassSuccessTimes = Uint16()

        self.NOPIntersectionPassTimes = Uint16()

        self.NOPRoundaboutPassTimes = Uint16()

        self.NOPUTurnSuccessTimes = Uint16()

        self.NOPDistanceRatio = Uint16()


class NOPUsageStaInfo(SomeIpPayload):

    NOPUsageStaInfo: NOPUsageStaInfoKls

    def __init__(self):

        self.NOPUsageStaInfo = NOPUsageStaInfoKls()
