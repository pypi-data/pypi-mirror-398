from someip_py.codec import *


class IdtSwtTouchBtn(SomeIpPayload):

    IdtSwtTouchBtn: Uint8

    def __init__(self):

        self.IdtSwtTouchBtn = Uint8()
