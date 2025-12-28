from someip_py.codec import *


class Pos2D(SomeIpPayload):

    LongitudePos2DSeN: Float64

    LatitudePos2DSeN: Float64

    def __init__(self):

        self.LongitudePos2DSeN = Float64()

        self.LatitudePos2DSeN = Float64()


class AutoNaviSearchParamKls(SomeIpPayload):

    TaskId: Uint64

    SearchModel: Uint8

    SearchMode: Uint8

    SearchNearestPoiLoc: Pos2D

    SearchNaviInfoPoiId: SomeIpDynamicSizeString

    SearchNaviInfoRelType: SomeIpDynamicSizeString

    SearchKeywordQueryType: SomeIpDynamicSizeString

    SearchKeywordPoiLoc: Pos2D

    SearchKeywordKeywords: SomeIpDynamicSizeString

    SearchKeywordGeoObj: SomeIpDynamicSizeString

    SearchKeywordRange: SomeIpDynamicSizeString

    def __init__(self):

        self.TaskId = Uint64()

        self.SearchModel = Uint8()

        self.SearchMode = Uint8()

        self.SearchNearestPoiLoc = Pos2D()

        self.SearchNaviInfoPoiId = SomeIpDynamicSizeString()

        self.SearchNaviInfoRelType = SomeIpDynamicSizeString()

        self.SearchKeywordQueryType = SomeIpDynamicSizeString()

        self.SearchKeywordPoiLoc = Pos2D()

        self.SearchKeywordKeywords = SomeIpDynamicSizeString()

        self.SearchKeywordGeoObj = SomeIpDynamicSizeString()

        self.SearchKeywordRange = SomeIpDynamicSizeString()


class AutoNaviSearchParam(SomeIpPayload):

    AutoNaviSearchParam: AutoNaviSearchParamKls

    def __init__(self):

        self.AutoNaviSearchParam = AutoNaviSearchParamKls()
