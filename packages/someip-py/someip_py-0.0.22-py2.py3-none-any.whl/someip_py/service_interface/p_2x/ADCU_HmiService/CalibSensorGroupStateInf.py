from someip_py.codec import *


class CalibSensorGroupStateKls(SomeIpPayload):

    AllSensorCalibState: Uint8

    SensorCalibGroup: Uint8

    OnlineCalibProgress: Uint8

    def __init__(self):

        self.AllSensorCalibState = Uint8()

        self.SensorCalibGroup = Uint8()

        self.OnlineCalibProgress = Uint8()


class CalibSensorGroupState(SomeIpPayload):

    CalibSensorGroupState: CalibSensorGroupStateKls

    def __init__(self):

        self.CalibSensorGroupState = CalibSensorGroupStateKls()
