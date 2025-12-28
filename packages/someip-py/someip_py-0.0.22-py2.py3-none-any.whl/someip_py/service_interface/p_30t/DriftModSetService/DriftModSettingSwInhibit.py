from someip_py.codec import *


class IdtDriftModSwInhibit(SomeIpPayload):

    IdtDriftModSwInhibit: Uint8

    def __init__(self):

        self.IdtDriftModSwInhibit = Uint8()
