from someip_py.codec import *


class IdtVoiceCommandsKls(SomeIpPayload):

    CommandTypeSeN: Uint8

    VoiceCommandTimeStampSeN: Uint64

    def __init__(self):

        self.CommandTypeSeN = Uint8()

        self.VoiceCommandTimeStampSeN = Uint64()


class IdtVoiceCommands(SomeIpPayload):

    IdtVoiceCommands: IdtVoiceCommandsKls

    def __init__(self):

        self.IdtVoiceCommands = IdtVoiceCommandsKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
