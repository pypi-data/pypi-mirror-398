from someip_py.codec import *


class AVPPopupType(SomeIpPayload):

    AVPPopupType: Uint8

    def __init__(self):

        self.AVPPopupType = Uint8()
