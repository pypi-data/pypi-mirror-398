from someip_py.codec import *


class IdtMobDevRPAReq1Kls(SomeIpPayload):

    _include_struct_len = True

    MobDevRPAReq1MobDevSts: Uint8

    MobDevRPAReq1RPAOutModeSubT: Uint8

    MobDevRPAReq1RPAReq: Uint8

    MobDevRPAReq1RSPACtrl: Uint8

    def __init__(self):

        self.MobDevRPAReq1MobDevSts = Uint8()

        self.MobDevRPAReq1RPAOutModeSubT = Uint8()

        self.MobDevRPAReq1RPAReq = Uint8()

        self.MobDevRPAReq1RSPACtrl = Uint8()


class IdtMobDevRPAReq1(SomeIpPayload):

    IdtMobDevRPAReq1: IdtMobDevRPAReq1Kls

    def __init__(self):

        self.IdtMobDevRPAReq1 = IdtMobDevRPAReq1Kls()


class IdtRPARet(SomeIpPayload):

    IdtRPARet: Uint8

    def __init__(self):

        self.IdtRPARet = Uint8()
