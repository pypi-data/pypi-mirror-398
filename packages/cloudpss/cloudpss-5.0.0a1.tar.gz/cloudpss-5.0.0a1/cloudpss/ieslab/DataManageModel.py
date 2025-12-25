from ..utils import request, fileLoad, graphql_request
import json
import time, datetime
import copy


class DataManageModel(object):
    _kindUrlMap = {}
    _kindNameMap = {}
    _weatherUrl = ''
    _baseUri = ''
    _itemDataMap={}
    _kindItemDataMap={}
    _kindIdMap={}
    def __init__(self, simulationId):
        self.simulationId = simulationId
        self._getAllData()
    
    def _fetchItemData(self, url, kind):
        '''
            私有方法，获取kind类型对应所有数据项的列表

            :params: url string类型，request请求对应的url链接
            
            :params: kind string类型，数据的种类标识，比如PhotovoltaicSys, WindPowerGenerator, GasTurbine等等
            
            :return: list类型，返回该种类下所有数据项的的列表
        '''
        r = request('GET',
            url,
            params={
                "simu_id": self.simulationId,
                "kind": kind
        })
        url_tail  = url.split('/')[-2]
        if(url_tail in ['typhoon', 'rainfall', 'earthquake', 'extremeCold'] and r.status_code == 404):
            return []
        else :
            data = json.loads(r.text)
            return data['results']

    def _deleteItemData(self, url):
        '''
            私有方法，删除url链接对应的数据
            
            :params: url string类型，request请求对应的url链接
            
            :return: 无
        '''
        r = request('DELETE',
                    url)
        return r.text
    def _saveItemData(self, url, data):
        '''
            私有方法，保存url链接对应的data数据
            
            :params: url string类型，request请求对应的url链接

            :params: data dict类型，表示添加的数据内容，其数据结构应满足对应数据项的结构要求
            
            :return: dict类型，表示成功添加的数据内容
        '''
        r = request('POST', url, data=json.dumps(data))
        dataList = json.loads(r.text)
        return dataList

    def _updateItemData(self, url, data):
        '''
            私有方法，更新url链接对应的data数据
            
            :params: url string类型，request请求对应的url链接

            :params: data dict类型，表示添加的数据内容，其数据结构应满足对应数据项的结构要求
            
            :return: dict类型，表示成功更新的数据内容
        '''
        r = request('PATCH', url, data=json.dumps(data))
        dataList = json.loads(r.text)
        return dataList
    
    def _getAllData(self):
        '''
            私有方法，获取数据管理模块全部数据，函数初始化时调用
            
            :return: 无
        '''
        list = ['thermalLoads', 'heatingLoad', 'coolingLoad', 'electricLoads', 'fuels', 'typhoon', 'rainfall', 'earthquake', 'extremeCold', 'HydrogenLoad', 'ammoniaLoad', 'MethaneLoad']
        for kind,value in self._kindUrlMap.items():
            try:
                if kind in list:
                    dataList = self._fetchItemData(self._kindUrlMap[kind], None)
                else:
                    dataList = self._fetchItemData(self._kindUrlMap[kind], kind)
            except Exception as e:
                pass
            self._kindItemDataMap[kind]=dataList
            for val in dataList:
                self._itemDataMap[str(val['timeid'])]=val
                self._itemDataMap[str(val['id'])]=val
                self._kindIdMap[str(val['timeid'])]=kind
                self._kindIdMap[str(val['id'])]=kind

    def GetDataItem(self, ID: str):
        '''
            获取ID对应的数据信息
            
            :params: ID string类型，代表数据项的标识符，可以在所有类型的数据项中实现唯一标识
            
            :return: dict类型，为源数据的引用，返回该数据项的信息
        '''

        data = self._itemDataMap.get(str(ID),None)
        
        assert (data is not None), "找不到数据"

        return copy.deepcopy(data)

    def GetItemList(self, dataType):
        '''
            获取dataType类型对应所有数据项的列表
    
            :params: dataType enum类型，数据的种类标识，包含："光伏": "PhotovoltaicSys","风机": "WindPowerGenerator","燃气轮机": "GasTurbine","热泵": "HeatPump","燃气锅炉": "GasBoiler","热管式太阳能集热器": "HPSolarCollector","电压缩制冷机": "CompRefrg","吸收式制冷机": "AbsorptionChiller","蓄电池": "Battery","储水罐": "WaterTank","变压器": "Transformer","传输线": "TransferLine","模块化多电平变流器": "MMC","离心泵": "CentrifugalPump","管道": "Pipe","采暖制冷负荷": "thermalLoads","电负荷": "electricLoads","燃料": "fuels","热": "HVACHeating","冷": "HVACCooling","常数电价": "常数电价","分时电价": "分时电价","阶梯电价": "阶梯电价","分时阶梯电价": "分时阶梯电价"
    
            :return: list类型，返回该种类下所有数据项的列表
        '''
        assert (dataType in self._kindNameMap
                or dataType in self._kindUrlMap), "数据类型不存在"
        kind = self._kindNameMap.get(dataType, dataType)
        return copy.deepcopy(self._kindItemDataMap[kind])

    def AddDataItem(self, dataType, data):
        '''
            向dataType类型的数据库中添加内容为data的数据项
    
            :params: dataType enum类型，数据的种类标识，包含："光伏"、"风机"、"燃气轮机"、"热泵"、"燃气锅炉"、"热管式太阳能集热器"、"电压缩制冷机"、"吸收式制冷机"、"蓄电池"、"储水罐"、"变压器"、"传输线"、"模块化多电平变流器"、"离心泵"、"管道"、"采暖制冷负荷"、"电负荷"、"燃料"、"热"、"冷"、"常数电价"、"分时电价"、"阶梯电价"、"分时阶梯电价"
    
            :params: data dict类型，表示添加的数据内容，其数据结构应满足对应数据项的结构要求
    
            :return: string类型，返回新添加数据项的ID，如果数据结构不满足要求，应当抛出异常
        '''
        assert (dataType in self._kindNameMap
            or dataType in self._kindUrlMap), "数据类型不存在"
        kind = self._kindNameMap.get(dataType, dataType)
        r = copy.deepcopy(data)
        if r.get('id') is not None:
            r.pop('id')
        if r.get('timeid') is not None:
            r.pop('timeid')

        try:
            self._saveItemData(self._kindUrlMap[kind], [r])

            if kind in ['thermalLoads', 'heatingLoad', 'coolingLoad', 'electricLoads', 'fuels', 'ammoniaLoad']:
                dataList = self._fetchItemData(self._kindUrlMap[kind], None)
            else:
                dataList = self._fetchItemData(self._kindUrlMap[kind], kind)

            self._kindItemDataMap[kind] = dataList

            if not dataList:
                raise Exception("新增失败：未获取到任何该类型的数据")
            
            new_item = dataList[-1]

            id_ = new_item.get('id')
            timeid = new_item.get('timeid')

            if id_ is not None:
                self._itemDataMap[str(id_)] = new_item
                self._kindIdMap[str(id_)] = kind

            if timeid is not None:
                self._itemDataMap[str(timeid)] = new_item
                self._kindIdMap[str(timeid)] = kind

            return id_

        except Exception as e:
            raise Exception(str(e))

    def UpdateDataItem(self, ID: str, data):
        '''
            更新数据库ID对应数据项"光伏"、"风机"、"燃气轮机"、"热泵"、"燃气锅炉"、"热管式太阳能集热器"、"电压缩制冷机"、"吸收式制冷机"、"蓄电池"、"储水罐"、"变压器"、"传输线"、"模块化多电平变流器"、"离心泵"、"管道"、"采暖制冷负荷"、"电负荷"、"燃料"、"热"、"冷"、"常数电价"、"分时电价"、"阶梯电价"、"分时阶梯电价"数据
            
            :params: id string类型，代表数据项的标识符，可以在所有类型的数据项中实现唯一标识
            :params: data dict类型，表示添加的数据内容，其数据结构应满足对应数据项的结构要求
            
            :return: bool 类型，返回True 更新成功
        '''
        try:
            kind = self._kindIdMap.get(str(ID))
            if not kind:
                kind = self._kindNameMap.get(data.get('kind'), data.get('kind'))

            if not kind:
                raise Exception('未找到该ID对应的类型，或传入的数据缺乏kind类型')

            url = self._kindUrlMap[kind] + '/' + str(ID) + '/'
            updated = self._updateItemData(url, data)

            items = self._kindItemDataMap.get(kind, [])
            for idx, item in enumerate(items):
                if str(item.get('id')) == str(ID):
                    items[idx] = updated
                    break

            id_ = updated.get('id', ID)
            timeid = updated.get('timeid')

            if id_ is not None:
                self._itemDataMap[str(id_)] = updated
                self._kindIdMap[str(id_)] = kind

            if timeid is not None:
                self._itemDataMap[str(timeid)] = updated
                self._kindIdMap[str(timeid)] = kind

            return True

        except Exception as e:
            raise Exception(str(e))

    def DeleteDataItem(self, ID: str):
        '''
            向数据库中删除ID对应数据项"光伏"、"风机"、"燃气轮机"、"热泵"、"燃气锅炉"、"热管式太阳能集热器"、"电压缩制冷机"、"吸收式制冷机"、"蓄电池"、"储水罐"、"变压器"、"传输线"、"模块化多电平变流器"、"离心泵"、"管道"、"采暖制冷负荷"、"电负荷"、"燃料"、"热"、"冷"、"常数电价"、"分时电价"、"阶梯电价"、"分时阶梯电价"数据
    
            :params: ID string类型，代表数据项的标识符，可以在所有类型的数据项中实现唯一标识
            
            :return: bool 类型，删除是否成功，如果ID错误，抛出异常
        '''
        data = self._itemDataMap.get(str(ID),None)
        kind = self._kindIdMap.get(str(ID))
        if data is None or kind is None:
            raise Exception('id错误，未找到该id资源')
        else:
            url=self._kindUrlMap[kind]
            self._deleteItemData(url+str(data['id'])+'/')
            id_ = data.get('id')
            timeid = data.get('timeid')
            if id_ is not None:
                self._itemDataMap.pop(str(id_), None)
                self._kindIdMap.pop(str(id_), None)
            if timeid is not None:
                self._itemDataMap.pop(str(timeid), None)
                self._kindIdMap.pop(str(timeid), None)

            dataList = self._kindItemDataMap.get(kind, [])
            for i, item in enumerate(dataList):
                if item.get('id') == id_:
                    del dataList[i]
                    break
            return True

    def SetProjectPosition(self, longitude, latitude):
        '''
            将项目的经纬度位置坐标设置为(longitude, latitude)
            
            :params: longitude float类型，表示经度，范围为气象数据源的经度范围
            :params: latitude float类型，表示纬度，范围为气象数据源的纬度范围
        '''
        lon = float(longitude)
        lat = float(latitude)
        if (lon > 180 or lon < -180
                or lat > 90 or lat < -90):
            raise Exception('经纬度坐标不存在')
        else:
            r = request('GET',
                    self._baseUri + 'rest/weather_param/',
                    params={"simu": self.simulationId})
            param = json.loads(r.text)
            print(param)
            results = param.get("results", [])
            print(results)
            payLoad = {
                "lat": lat,
                "lng": lon,
                "simu": self.simulationId,
                "simu_id": self.simulationId,
            }
  
            if (len(results) == 0):
                request('POST',
                        self._baseUri + 'rest/weather_param/',
                        data=json.dumps(payLoad))
            else:
                id = param['results'][0]['id']
                request('PUT',
                        self._baseUri + 'rest/weather_param/' + str(id) +
                        '/',
                        data=json.dumps(payLoad))
            request('GET',
                    self._baseUri + 'load_weather/',
                    params={
                        "lat": latitude,
                        "lng": longitude,
                        "simu": self.simulationId,
                        "simu_id": self.simulationId,
                    })

    def GetAtmosData(self, startDate, endDate):
        '''
            获取在startDate到endDate之间的气象数据
            
            :params: startDate dateTime类型，表示开始时间
            :params: endDate dateTime类型，表示结束时间
            
            :return: list<dict>类型，为源数据的引用，返回当前项目位置对应时间范围内的气象数据序列，每个元素用字典进行表示，字典的key即区分不同的气象数据项（如风速、太阳辐照等）以及标识当前时间点
        '''
        sDate = datetime.date(*map(int, startDate.split('-')))
        eDate = datetime.date(*map(int, endDate.split('-')))
        res = (eDate - sDate).days * 86400 + (eDate - sDate).seconds
        if res < 0:
            raise Exception('超出有效时间范围')
        else:
            r = request('GET',
                        self._weatherUrl,
                        params={
                            "time_after": startDate,
                            "time_before": endDate,
                            "sid": self.simulationId,
                        })
            weatherData = json.loads(r.text)
            return weatherData['results']
        
    def UpdateAtmosData(self, data):
        '''
            更新气象数据
            :data:  list类型，表示数据内容，其数据结构应满足对应数据项的满足如下结构要求：
                        "lat": string类型 坐标纬度
                        "lng": string类型 坐标经度
                        "time": string类型 表示时间 需满足格式YYYY-MM-DD hh:mm:ss 如"2016-01-01 00:00:00"
                        "t10m": string类型 表示环境温度（℃）
                        "lwgab_swgdn": string类型 表示太阳辐射强度（W/m2）
                        "u10m": string类型 距地面10m处东向风速（m/s）
                        "u50m": string类型 距地面50m处东向风速（m/s）
                        "v10m": string类型 距地面10m处北向风速（m/s）
                        "v50m": string类型 距地面50m处北向风速（m/s）
                        "adj_sfc_sw_direct_all_1h": string类型 短波直射强度（W/m²）
                        "adj_sfc_sw_diff_all_1h": string类型 短波散射强度（W/m²）
                        "solar_zen_angle_1h": string类型 太阳天顶角°
            :return: bool 类型，返回True 更新成功
        '''
        r = request('POST',
                    self._weatherUrl,
                    data=json.dumps({"sid":self.simulationId, "data":data}))
        return r.ok


class IESSimulationDataManageModel(DataManageModel):
    _baseUri = 'api/ieslab-simulation/'
    _weatherUrl = 'api/ieslab-simulation/rest/weather_data/'
    _dataManageUrl = 'api/ieslab-simulation/editor/data_manage/'
    _kindNameMap = {
        "光伏": "PhotovoltaicSys",
        "风机": "WindPowerGenerator",
        "燃气轮机": "GasTurbine",
        "热泵": "HeatPump",
        "燃气锅炉": "GasBoiler",
        "热管式太阳能集热器": "HPSolarCollector",
        "电压缩制冷机": "CompRefrg",
        "吸收式制冷机": "AbsorptionChiller",
        "蓄电池": "Battery",
        "储水罐": "WaterTank",
        "变压器": "Transformer",
        "传输线": "TransferLine",
        "模块化多电平变流器": "MMC",
        "离心泵": "CentrifugalPump",
        "管道": "Pipe",
        "采暖制冷负荷": "thermalLoads",
        "电负荷": "electricLoads",
        "燃料": "fuels",
        "热": "HVACHeating",
        "冷": "HVACCooling",
        "常数电价": "常数电价",
        "分时电价": "分时电价",
        "阶梯电价": "阶梯电价",
        "分时阶梯电价": "分时阶梯电价",
        "台风灾害": "typhoon",
        "降雨灾害": "rainfall",
        "地震灾害": "earthquake",
        "极寒灾害": "extremeCold",
    }
    _kindUrlMap = {
        "PhotovoltaicSys": "api/ieslab-simulation/rest/dpcs/",
        "WindPowerGenerator": "api/ieslab-simulation/rest/dpcs/",
        "GasTurbine": "api/ieslab-simulation/rest/dpcs/",
        "HeatPump": "api/ieslab-simulation/rest/dhscs/",
        "GasBoiler": "api/ieslab-simulation/rest/dhscs/",
        "HPSolarCollector": "api/ieslab-simulation/rest/dhscs/",
        "CompRefrg": "api/ieslab-simulation/rest/dhscs/",
        "AbsorptionChiller": "api/ieslab-simulation/rest/dhscs/",
        "Battery": "api/ieslab-simulation/rest/escs/",
        "WaterTank": "api/ieslab-simulation/rest/escs/",
        "Transformer": "api/ieslab-simulation/rest/dstcs/",
        "TransferLine": "api/ieslab-simulation/rest/dstcs/",
        "MMC": "api/ieslab-simulation/rest/dstcs/",
        "CentrifugalPump": "api/ieslab-simulation/rest/hstcs/",
        "Pipe": "api/ieslab-simulation/rest/hstcs/",
        "thermalLoads": "api/ieslab-simulation/rest/thermalLoads/",
        "electricLoads": "api/ieslab-simulation/rest/electricLoads/",
        "fuels": "api/ieslab-simulation/rest/fuels/",
        "HVACHeating": "api/ieslab-simulation/rest/hots/",
        "HVACCooling": "api/ieslab-simulation/rest/colds/",
        "常数电价": "api/ieslab-simulation/rest/elects/",
        "分时电价": "api/ieslab-simulation/rest/elects/",
        "阶梯电价": "api/ieslab-simulation/rest/elects/",
        "分时阶梯电价": "api/ieslab-simulation/rest/elects/",
        "typhoon":  "api/ieslab-simulation/rest/typhoon/",
        "rainfall": "api/ieslab-simulation/rest/rainfall/",
        "earthquake": "api/ieslab-simulation/rest/earthquake/",
        "extremeCold": "api/ieslab-simulation/rest/extremeCold/",
    }
    pass


class IESPlanDataManageModel(DataManageModel):
    _baseUri = 'api/ieslab-plan/'
    _weatherUrl = 'api/ieslab-plan/rest/weather_data/'
    _dataManageUrl = 'api/ieslab-plan/editor/data_manage/'
    _kindNameMap = {
        "光伏": "PhotovoltaicSys",
        "风机": "WindPowerGenerator",
        "燃气轮机": "GasTurbine",
        "热泵": "HeatPump",
        "燃气锅炉": "GasBoiler",
        "热管式太阳能集热器": "HPSolarCollector",
        "电压缩制冷机": "CompRefrg",
        "吸收式制冷机": "AbsorptionChiller",
        "蓄电池": "Battery",
        "储水罐": "WaterTank",
        "蓄冰空调": "IceStorageAC",
        "变压器": "Transformer",
        "传输线": "TransferLine",
        "模块化多电平变流器": "MMC",
        "离心泵": "CentrifugalPump",
        "管道": "Pipe",
        "采暖制冷负荷": "thermalLoads",
        "电负荷": "electricLoads",
        "燃料": "fuels",
        "热": "HVACHeating",
        "冷": "HVACCooling",
        "常数电价": "常数电价",
        "分时电价": "分时电价",
        "阶梯电价": "阶梯电价",
        "分时阶梯电价": "分时阶梯电价",
        "台风灾害": "typhoon",
        "降雨灾害": "rainfall",
        "地震灾害": "earthquake",
        "极寒灾害": "extremeCold",
        "换热器": "HeatExchanger",
    }
    _kindUrlMap = {
        "PhotovoltaicSys": "api/ieslab-plan/rest/dpcs/",
        "WindPowerGenerator": "api/ieslab-plan/rest/dpcs/",
        "GasTurbine": "api/ieslab-plan/rest/dpcs/",
        "HeatPump": "api/ieslab-plan/rest/dhscs/",
        "GasBoiler": "api/ieslab-plan/rest/dhscs/",
        "HPSolarCollector": "api/ieslab-plan/rest/dhscs/",
        "CompRefrg": "api/ieslab-plan/rest/dhscs/",
        "AbsorptionChiller": "api/ieslab-plan/rest/dhscs/",
        "Battery": "api/ieslab-plan/rest/escs/",
        "WaterTank": "api/ieslab-plan/rest/escs/",
        "IceStorageAC": "api/ieslab-plan/rest/escs/",
        "Transformer": "api/ieslab-plan/rest/dstcs/",
        "TransferLine": "api/ieslab-plan/rest/dstcs/",
        "MMC": "api/ieslab-plan/rest/dstcs/",
        "CentrifugalPump": "api/ieslab-plan/rest/hstcs/",
        "Pipe": "api/ieslab-plan/rest/hstcs/",
        "thermalLoads": "api/ieslab-plan/rest/thermalLoads/",
        "electricLoads": "api/ieslab-plan/rest/electricLoads/",
        "fuels": "api/ieslab-plan/rest/fuels/",
        "HVACHeating": "api/ieslab-plan/rest/hots/",
        "HVACCooling": "api/ieslab-plan/rest/colds/",
        "常数电价": "api/ieslab-plan/rest/elects/",
        "分时电价": "api/ieslab-plan/rest/elects/",
        "阶梯电价": "api/ieslab-plan/rest/elects/",
        "分时阶梯电价": "api/ieslab-plan/rest/elects/",
        "typhoon":  "api/ieslab-plan/rest/typhoon/",
        "rainfall": "api/ieslab-plan/rest/rainfall/",
        "earthquake": "api/ieslab-plan/rest/earthquake/",
        "extremeCold": "api/ieslab-plan/rest/extremeCold/",
        "HeatExchanger": "api/ieslab-plan/rest/hstcs/",
    }
    pass

class IESOptDataManageModel(DataManageModel):
    _baseUri = 'api/ieslab-opt/'
    _weatherUrl = 'api/ieslab-opt/rest/weather_data/'
    _kindNameMap = {
        "光伏": "PhotovoltaicSys",
        "风机": "WindPowerGenerator",
        "燃料发电机组": "GasTurbine",
        "空气源热泵": "HeatPump",
        "燃气锅炉": "GasBoiler",
        "太阳能集热器": "HPSolarCollector",
        "吸收式热泵": "AbsorptionHeatPump",
        "单工况制冷机": "SingleConChiller",
        "双工况制冷机": "DualConChiller",
        "吸收式制冷机": "AbsorptionChiller",
        "蓄电池": "Battery",
        "蓄冰槽": "IceStorageAC",
        "变压器": "Transformer",
        "传输线": "TransferLine",
        "模块化多电平变流器": "MMC",
        "离心泵": "CentrifugalPump",
        "管道": "Pipe",
        "热负荷": "heatingLoad",
        "冷负荷": "coolingLoad",
        "电负荷": "electricLoads",
        "燃料": "fuels",
        "热": "HVACHeating",
        "冷": "HVACCooling",
        "常数电价": "常数电价",
        "分时电价": "分时电价",
        "阶梯电价": "阶梯电价",
        "分时阶梯电价": "分时阶梯电价",
        "台风灾害": "typhoon",
        "降雨灾害": "rainfall",
        "地震灾害": "earthquake",
        "极寒灾害": "extremeCold",
        "PEM燃料电池": "PEMF",
        "SOFC": "SOFC",
        "碱性电解槽": "ALK",
        "PEM电解槽": "PEME",
        "SOEC": "SOEC",
        "储氢罐": "HydrogenTank",
        "储热罐": "HeatStoTank",
        "储冷罐": "CoolStoTank",
        "换热器": "HeatExchanger",
        "氢气压缩设备": "HydrogenCompression",
        "氢负荷": "HydrogenLoad",
        "氢": "HydrogenProductionFuels",
        "运氢槽车": "HydrogenTanker",
        "制氨设备": "AmmoniaProduction",
        "储氨罐": "AmmoniaStoTank",
        "制氮设备": "NitrogenProduction",
        "氨负荷": "ammoniaLoad",
        "氨": "Ammonia",
        "制甲烷设备": "MethaneProduction",
        "碳捕集设备": "CarbonCapture",
        "储碳装置": "CarbonStorage",
        "甲烷负荷": "MethaneLoad",
        "甲烷": "Methane",
    }
    _kindUrlMap = {
        "PhotovoltaicSys": "api/ieslab-opt/rest/dpcs/",
        "WindPowerGenerator": "api/ieslab-opt/rest/dpcs/",
        "GasTurbine": "api/ieslab-opt/rest/dpcs/",
        "HeatPump": "api/ieslab-opt/rest/dhscs/",
        "GasBoiler": "api/ieslab-opt/rest/dhscs/",
        "HPSolarCollector": "api/ieslab-opt/rest/dhscs/",
        "AbsorptionHeatPump": "api/ieslab-opt/rest/dhscs/",
        "SingleConChiller": "api/ieslab-opt/rest/dhscs/",
        "DualConChiller": "api/ieslab-opt/rest/dhscs/",
        "AbsorptionChiller": "api/ieslab-opt/rest/dhscs/",
        "Battery": "api/ieslab-opt/rest/escs/",
        "IceStorageAC": "api/ieslab-opt/rest/escs/",
        "Transformer": "api/ieslab-opt/rest/dstcs/",
        "TransferLine": "api/ieslab-opt/rest/dstcs/",
        "MMC": "api/ieslab-opt/rest/dstcs/",
        "CentrifugalPump": "api/ieslab-opt/rest/hstcs/",
        "Pipe": "api/ieslab-opt/rest/hstcs/",
        "heatingLoad": "api/ieslab-opt/rest/heatingLoad/",
        "coolingLoad": "api/ieslab-opt/rest/coolingLoad/",
        "electricLoads": "api/ieslab-opt/rest/electricLoads/",
        "fuels": "api/ieslab-opt/rest/fuels/",
        "HVACHeating": "api/ieslab-opt/rest/hots/",
        "HVACCooling": "api/ieslab-opt/rest/colds/",
        "常数电价": "api/ieslab-opt/rest/elects/",
        "分时电价": "api/ieslab-opt/rest/elects/",
        "阶梯电价": "api/ieslab-opt/rest/elects/",
        "分时阶梯电价": "api/ieslab-opt/rest/elects/",
        "typhoon":  "api/ieslab-opt/rest/typhoon/",
        "rainfall": "api/ieslab-opt/rest/rainfall/",
        "earthquake": "api/ieslab-opt/rest/earthquake/",
        "extremeCold": "api/ieslab-opt/rest/extremeCold/",
        "HydrogenTank": "api/ieslab-opt/rest/escs/",
        "HeatStoTank": "api/ieslab-opt/rest/escs/",
        "CoolStoTank": "api/ieslab-opt/rest/escs/",
        "HeatExchanger": "api/ieslab-opt/rest/hstcs/",
        "HydrogenCompression": "api/ieslab-opt/rest/hsec/",
        "HydrogenLoad": "api/ieslab-opt/rest/hydrogenLoad/",
        "HydrogenProductionFuels": "api/ieslab-opt/rest/hydrogen/",
        "HydrogenTanker": "api/ieslab-opt/rest/hydrogen/",
        "PEMF": "api/ieslab-opt/rest/dhscs/",
        "SOFC": "api/ieslab-opt/rest/dhscs/",
        "ALK": "api/ieslab-opt/rest/hpc/",
        "PEME": "api/ieslab-opt/rest/hpc/",
        "SOEC": "api/ieslab-opt/rest/hpc/",
        "AmmoniaProduction": "api/ieslab-opt/rest/apc/",
        "AmmoniaStoTank": "api/ieslab-opt/rest/escs/",
        "NitrogenProduction": "api/ieslab-opt/rest/asec/",
        "ammoniaLoad": "api/ieslab-opt/rest/ammoniaLoad/",
        "Ammonia": "api/ieslab-opt/rest/ammonia/",
        "MethaneProduction": "api/ieslab-opt/rest/mcp/",
        "CarbonCapture": "api/ieslab-opt/rest/ccp/",
        "CarbonStorage": "api/ieslab-opt/rest/escs/",
        "MethaneLoad": "api/ieslab-opt/rest/methaneLoad/",
        "Methane": "api/ieslab-opt/rest/methane/",
    }
    pass