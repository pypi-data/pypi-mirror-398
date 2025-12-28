from someip_py.codec import *


class IdtTooManyCars(SomeIpPayload):

    IdtTooManyCars: Bool

    def __init__(self):

        self.IdtTooManyCars = Bool()
