from someip_py.codec import *


class IdtHeiLvlExcutSource(SomeIpPayload):

    IdtHeiLvlExcutSource: Uint8

    def __init__(self):

        self.IdtHeiLvlExcutSource = Uint8()
