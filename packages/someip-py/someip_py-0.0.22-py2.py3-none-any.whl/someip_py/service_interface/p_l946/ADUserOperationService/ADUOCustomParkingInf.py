from someip_py.codec import *


class IdtADUOVehiclePoint(SomeIpPayload):

    _include_struct_len = True

    PositionXSeN: Int32

    PositionYSeN: Int32

    def __init__(self):

        self.PositionXSeN = Int32()

        self.PositionYSeN = Int32()


class IdtADUOCustomParkingKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    ParkingTypeSeN: Uint8

    CustomParkFlag: Uint8

    ApaCustomParkVehDirStsSeN: Uint8

    APAImagePointSeN: SomeIpDynamicSizeArray[IdtADUOVehiclePoint]

    def __init__(self):

        self.ParkingTypeSeN = Uint8()

        self.CustomParkFlag = Uint8()

        self.ApaCustomParkVehDirStsSeN = Uint8()

        self.APAImagePointSeN = SomeIpDynamicSizeArray(IdtADUOVehiclePoint)


class IdtADUOCustomParking(SomeIpPayload):

    IdtADUOCustomParking: IdtADUOCustomParkingKls

    def __init__(self):

        self.IdtADUOCustomParking = IdtADUOCustomParkingKls()


class IdtADUORet(SomeIpPayload):

    IdtADUORet: Uint8

    def __init__(self):

        self.IdtADUORet = Uint8()
