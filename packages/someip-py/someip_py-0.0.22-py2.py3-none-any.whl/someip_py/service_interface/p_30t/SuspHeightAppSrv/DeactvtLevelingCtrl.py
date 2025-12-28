from someip_py.codec import *


class IdtTrueFalseCtrl(SomeIpPayload):

    IdtTrueFalseCtrl: Bool

    def __init__(self):

        self.IdtTrueFalseCtrl = Bool()
