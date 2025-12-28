from someip_py.codec import *


class IdtTailgateStopReason(SomeIpPayload):

    _include_struct_len = True

    TailgateID: Uint8

    MoveToExpectedPosition: Uint8

    AntiPinchhappend: Uint8

    AvoidObstaclehappened: Uint8

    PDOFailure: Uint8

    USSfault: Uint8

    PDOSensorFault: Uint8

    PowerStatusAbnormal: Uint8

    DriveTimeout: Uint8

    LatchFailure: Uint8

    AntiPlay: Uint8

    StallHappened: Uint8

    SafeWindowsIsInactive: Uint8

    EnvironmentTempOverLimit: Uint8

    SlopeOverLimit: Uint8

    CommandConflict: Uint8

    VehMtnSt: Uint8

    ThermalProtection: Uint8

    SmallAngle: Uint8

    ChildLockActive: Uint8

    PositionUnkown: Uint8

    OtherDoorSmallAngle: Uint8

    ChargeLidOpen: Uint8

    def __init__(self):

        self.TailgateID = Uint8()

        self.MoveToExpectedPosition = Uint8()

        self.AntiPinchhappend = Uint8()

        self.AvoidObstaclehappened = Uint8()

        self.PDOFailure = Uint8()

        self.USSfault = Uint8()

        self.PDOSensorFault = Uint8()

        self.PowerStatusAbnormal = Uint8()

        self.DriveTimeout = Uint8()

        self.LatchFailure = Uint8()

        self.AntiPlay = Uint8()

        self.StallHappened = Uint8()

        self.SafeWindowsIsInactive = Uint8()

        self.EnvironmentTempOverLimit = Uint8()

        self.SlopeOverLimit = Uint8()

        self.CommandConflict = Uint8()

        self.VehMtnSt = Uint8()

        self.ThermalProtection = Uint8()

        self.SmallAngle = Uint8()

        self.ChildLockActive = Uint8()

        self.PositionUnkown = Uint8()

        self.OtherDoorSmallAngle = Uint8()

        self.ChargeLidOpen = Uint8()


class IdtTailgatesStopReason(SomeIpPayload):

    IdtTailgatesStopReason: SomeIpDynamicSizeArray[IdtTailgateStopReason]

    def __init__(self):

        self.IdtTailgatesStopReason = SomeIpDynamicSizeArray(IdtTailgateStopReason)
