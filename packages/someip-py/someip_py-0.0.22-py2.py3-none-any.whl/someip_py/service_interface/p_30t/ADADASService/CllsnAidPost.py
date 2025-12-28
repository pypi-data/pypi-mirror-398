from someip_py.codec import *


class IdtCllsnAidPost(SomeIpPayload):

    IdtCllsnAidPost: Uint8

    def __init__(self):

        self.IdtCllsnAidPost = Uint8()
