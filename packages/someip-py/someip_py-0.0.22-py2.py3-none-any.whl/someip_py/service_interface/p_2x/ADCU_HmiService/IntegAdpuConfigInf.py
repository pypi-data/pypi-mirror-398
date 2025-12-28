from someip_py.codec import *


class IntegAdpuConfig(SomeIpPayload):

    IntegAdpuConfig: Uint8

    def __init__(self):

        self.IntegAdpuConfig = Uint8()
