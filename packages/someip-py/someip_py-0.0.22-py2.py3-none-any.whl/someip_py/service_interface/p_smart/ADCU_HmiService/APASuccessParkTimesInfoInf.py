from someip_py.codec import *


class APASuccessParkTimesInfoKls(SomeIpPayload):

    APASuccessParkTimesSeN: Uint16

    RPASuccessParkTimesSeN: Uint16

    LPSuccessParkTimesSeN: Uint16

    def __init__(self):

        self.APASuccessParkTimesSeN = Uint16()

        self.RPASuccessParkTimesSeN = Uint16()

        self.LPSuccessParkTimesSeN = Uint16()


class APASuccessParkTimesInfo(SomeIpPayload):

    APASuccessParkTimesInfo: APASuccessParkTimesInfoKls

    def __init__(self):

        self.APASuccessParkTimesInfo = APASuccessParkTimesInfoKls()
