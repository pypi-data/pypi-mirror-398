from someip_py.codec import *


class IdtPrkgUsgDrvModTranReq(SomeIpPayload):

    IdtPrkgUsgDrvModTranReq: Uint8

    def __init__(self):

        self.IdtPrkgUsgDrvModTranReq = Uint8()
