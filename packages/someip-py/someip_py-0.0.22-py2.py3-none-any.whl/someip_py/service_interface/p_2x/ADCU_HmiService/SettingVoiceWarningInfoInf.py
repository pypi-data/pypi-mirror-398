from someip_py.codec import *


class VoiceWarningOption(SomeIpPayload):

    VoiceWarningOption: Uint8

    def __init__(self):

        self.VoiceWarningOption = Uint8()
