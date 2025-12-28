from someip_py.codec import *


class IdtCfigRuleLocalCmd(SomeIpPayload):

    IdtCfigRuleLocalCmd: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtCfigRuleLocalCmd = SomeIpDynamicSizeString()


class IdtCfigRuleLocalResp(SomeIpPayload):

    IdtCfigRuleLocalResp: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtCfigRuleLocalResp = SomeIpDynamicSizeString()
