from someip_py.codec import *


class IdtADUOCollectAndUploadCommandsKls(SomeIpPayload):

    _include_struct_len = True

    CommandTypeSeN: Uint8

    VoiceCommandTimeStampSeN: Uint64

    def __init__(self):

        self.CommandTypeSeN = Uint8()

        self.VoiceCommandTimeStampSeN = Uint64()


class IdtADUOCollectAndUploadCommands(SomeIpPayload):

    IdtADUOCollectAndUploadCommands: IdtADUOCollectAndUploadCommandsKls

    def __init__(self):

        self.IdtADUOCollectAndUploadCommands = IdtADUOCollectAndUploadCommandsKls()


class IdtADUORet(SomeIpPayload):

    IdtADUORet: Uint8

    def __init__(self):

        self.IdtADUORet = Uint8()
