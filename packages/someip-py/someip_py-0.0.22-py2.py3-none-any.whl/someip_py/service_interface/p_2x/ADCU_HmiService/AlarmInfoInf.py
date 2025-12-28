from someip_py.codec import *


class AlarmInfoKls(SomeIpPayload):

    AlarmIDSeN: Uint32

    AlarmLevelSeN: Uint8

    SecondaryPrioritySeN: Uint16

    DIMTextSeN: Uint8

    CSDTextSeN: Uint8

    BreathingLampSeN: Uint8

    BreathingLampColorSeN: Uint8

    SoundEffectSeN: Uint8

    SoundEffectTypeSeN: Uint8

    VoiceSeN: Uint8

    ProgressSeN: Int8

    ParameterSeN: Int16

    def __init__(self):

        self.AlarmIDSeN = Uint32()

        self.AlarmLevelSeN = Uint8()

        self.SecondaryPrioritySeN = Uint16()

        self.DIMTextSeN = Uint8()

        self.CSDTextSeN = Uint8()

        self.BreathingLampSeN = Uint8()

        self.BreathingLampColorSeN = Uint8()

        self.SoundEffectSeN = Uint8()

        self.SoundEffectTypeSeN = Uint8()

        self.VoiceSeN = Uint8()

        self.ProgressSeN = Int8()

        self.ParameterSeN = Int16()


class AlarmInfo(SomeIpPayload):

    AlarmInfo: AlarmInfoKls

    def __init__(self):

        self.AlarmInfo = AlarmInfoKls()
