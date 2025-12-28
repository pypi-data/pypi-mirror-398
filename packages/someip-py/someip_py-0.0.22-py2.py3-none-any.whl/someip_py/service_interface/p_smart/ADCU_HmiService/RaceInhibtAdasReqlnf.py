from someip_py.codec import *


class RaceInhibtAdasReqKls(SomeIpPayload):

    RaceInhibtAdasReqSEN: Uint8

    def __init__(self):

        self.RaceInhibtAdasReqSEN = Uint8()


class RaceInhibtAdasReq(SomeIpPayload):

    RaceInhibtAdasReq: RaceInhibtAdasReqKls

    def __init__(self):

        self.RaceInhibtAdasReq = RaceInhibtAdasReqKls()
