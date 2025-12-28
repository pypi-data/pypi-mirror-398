from someip_py.codec import *


class APAparkInfoKls(SomeIpPayload):

    APAparkbuttonSeN: Uint8

    APAleftparkSeN: Uint8

    APArightparkSeN: Uint8

    APAparkmodSeN: Uint8

    def __init__(self):

        self.APAparkbuttonSeN = Uint8()

        self.APAleftparkSeN = Uint8()

        self.APArightparkSeN = Uint8()

        self.APAparkmodSeN = Uint8()


class APAparkInfo(SomeIpPayload):

    APAparkInfo: APAparkInfoKls

    def __init__(self):

        self.APAparkInfo = APAparkInfoKls()
