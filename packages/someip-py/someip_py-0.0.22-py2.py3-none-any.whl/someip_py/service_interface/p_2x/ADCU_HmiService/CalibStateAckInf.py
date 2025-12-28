from someip_py.codec import *


class CalibStateAckKls(SomeIpPayload):

    IMUCalibGuide: Uint8

    IMUCalibResult: Uint8

    IMUCalibFailReason: Uint32

    IMUCalibResultRoll: Int32

    IMUCalibResultPitch: Int32

    IMUCalibResultYaw: Int32

    def __init__(self):

        self.IMUCalibGuide = Uint8()

        self.IMUCalibResult = Uint8()

        self.IMUCalibFailReason = Uint32()

        self.IMUCalibResultRoll = Int32()

        self.IMUCalibResultPitch = Int32()

        self.IMUCalibResultYaw = Int32()


class CalibStateAck(SomeIpPayload):

    CalibStateAck: CalibStateAckKls

    def __init__(self):

        self.CalibStateAck = CalibStateAckKls()
