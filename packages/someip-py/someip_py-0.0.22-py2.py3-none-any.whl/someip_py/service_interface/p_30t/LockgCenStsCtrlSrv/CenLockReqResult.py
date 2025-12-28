from someip_py.codec import *


class IdtReqResultKls(SomeIpPayload):

    _include_struct_len = True

    LockTrigSrc: Uint8

    Success: Uint8

    DrivingModeAndPGear: Uint8

    CarMode: Uint8

    Unlocked: Uint8

    Locked: Uint8

    NoPGear: Uint8

    DoorOpen: Uint8

    PEDisableByModeAndOccupy: Uint8

    EngineRun: Uint8

    Reserved1: Uint8

    def __init__(self):

        self.LockTrigSrc = Uint8()

        self.Success = Uint8()

        self.DrivingModeAndPGear = Uint8()

        self.CarMode = Uint8()

        self.Unlocked = Uint8()

        self.Locked = Uint8()

        self.NoPGear = Uint8()

        self.DoorOpen = Uint8()

        self.PEDisableByModeAndOccupy = Uint8()

        self.EngineRun = Uint8()

        self.Reserved1 = Uint8()


class IdtReqResult(SomeIpPayload):

    IdtReqResult: IdtReqResultKls

    def __init__(self):

        self.IdtReqResult = IdtReqResultKls()
