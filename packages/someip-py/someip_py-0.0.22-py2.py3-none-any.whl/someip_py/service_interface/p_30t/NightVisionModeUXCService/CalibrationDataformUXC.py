from someip_py.codec import *


class IdtCalibrationDataformUXCKls(SomeIpPayload):

    _include_struct_len = True

    SN: SomeIpDynamicSizeString

    sensor_ID: Uint32

    focal_x: Float64

    focal_y: Float64

    center_x: Float64

    center_y: Float64

    K1: Float64

    K2: Float64

    K3: Float64

    P1: Float64

    P2: Float64

    CRCState: Uint8

    def __init__(self):

        self.SN = SomeIpDynamicSizeString()

        self.sensor_ID = Uint32()

        self.focal_x = Float64()

        self.focal_y = Float64()

        self.center_x = Float64()

        self.center_y = Float64()

        self.K1 = Float64()

        self.K2 = Float64()

        self.K3 = Float64()

        self.P1 = Float64()

        self.P2 = Float64()

        self.CRCState = Uint8()


class IdtCalibrationDataformUXC(SomeIpPayload):

    IdtCalibrationDataformUXC: IdtCalibrationDataformUXCKls

    def __init__(self):

        self.IdtCalibrationDataformUXC = IdtCalibrationDataformUXCKls()
