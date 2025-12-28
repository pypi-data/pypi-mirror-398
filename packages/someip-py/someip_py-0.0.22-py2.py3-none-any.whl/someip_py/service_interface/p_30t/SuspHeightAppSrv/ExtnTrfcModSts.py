from someip_py.codec import *


class IdtExtnTrfcModData(SomeIpPayload):

    IdtExtnTrfcModData: Uint8

    def __init__(self):

        self.IdtExtnTrfcModData = Uint8()
