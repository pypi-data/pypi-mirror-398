from someip_py.codec import *


class IdtFwRuleLocalCmd(SomeIpPayload):

    IdtFwRuleLocalCmd: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtFwRuleLocalCmd = SomeIpDynamicSizeString()


class IdtFwRuleLocalResp(SomeIpPayload):

    IdtFwRuleLocalResp: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtFwRuleLocalResp = SomeIpDynamicSizeString()
