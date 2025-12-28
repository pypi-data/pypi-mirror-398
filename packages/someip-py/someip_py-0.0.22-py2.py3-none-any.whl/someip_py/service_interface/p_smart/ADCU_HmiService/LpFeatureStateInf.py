from someip_py.codec import *


class LpFeatureStateKls(SomeIpPayload):

    LpRecoverSeN: Uint8

    LpStartPathSeN: Uint8

    LpStartSeN: Uint8

    LpCompleteLearnSeN: Uint8

    LpAutoParkSeN: Uint8

    LpMappingProgressSeN: Int8

    APAnobtnDisplaySeN: Uint8

    LpLevelRoadSeN: Uint8

    LpAwayEexitSeN: Uint8

    LpReachStartSeN: Uint8

    ParkStartButtonDisplay: Uint8

    SelfSelectBottonDisplay: Uint8

    LpICONDisplaySeN: Uint8

    LpRampTypeSeN: Uint8

    def __init__(self):

        self.LpRecoverSeN = Uint8()

        self.LpStartPathSeN = Uint8()

        self.LpStartSeN = Uint8()

        self.LpCompleteLearnSeN = Uint8()

        self.LpAutoParkSeN = Uint8()

        self.LpMappingProgressSeN = Int8()

        self.APAnobtnDisplaySeN = Uint8()

        self.LpLevelRoadSeN = Uint8()

        self.LpAwayEexitSeN = Uint8()

        self.LpReachStartSeN = Uint8()

        self.ParkStartButtonDisplay = Uint8()

        self.SelfSelectBottonDisplay = Uint8()

        self.LpICONDisplaySeN = Uint8()

        self.LpRampTypeSeN = Uint8()


class LpFeatureState(SomeIpPayload):

    LpFeatureState: LpFeatureStateKls

    def __init__(self):

        self.LpFeatureState = LpFeatureStateKls()
