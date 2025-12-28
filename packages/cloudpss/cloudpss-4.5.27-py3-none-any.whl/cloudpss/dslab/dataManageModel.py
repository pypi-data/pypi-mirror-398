from ..utils import request, fileLoad, graphql_request
import json
import time, datetime
import urllib.parse
import copy
import os 
from cloudpss.dslab.files import getCurveData

class DataManageModel(object):
    _weatherUrl = ''
    _baseUri = ''
    _kindUrlMap = {}
    _itemDataMap={}
    _kindItemDataMap={}
    _kindIdMap={}

    def __init__(self, resourceId):
        self.resourceId = resourceId
        self._fetchTypes()
    def _status(self):
        '''
            获取运行状态

            :return: boolean 类型
        '''
        pass
    def _fetchTypes(self):
        '''
            获取所有数据项的类型

            :return: list 类型，返回所有数据项的类型
        '''
        url = f"{self._baseUri}rest/types"
        r = request('GET',url)
        types = json.loads(r.text)
        self._kindUrlMap = {kind['name']: f"api/dslab/rest/{kind['name']}" for kind in types}
    def _fetchItemData(self, url):
        '''
            私有方法，获取simu对应所有数据项的列表
            :params: url string类型，request请求对应的url链接
            
            :return: list类型，返回该种类下所有数据项的的列表
        '''
        r = request('GET',
                    url,
                    params={
                        "simu": self.resourceId,
                    })
        return json.loads(r.text)
    
    def _saveItemData(self, url, data):
        '''
            私有方法，保存url链接对应的data数据
            :params: url string类型，request请求对应的url链接
            :params: data dict类型，表示添加的数据内容，其数据结构应满足对应数据项的结构要求
            
            :return: 无
        '''
        r = request('POST', url, data=json.dumps(data))
        

    def _updateItemData(self, url, data):
        '''
            私有方法，更新url链接对应的data数据
            :params: url string类型，request请求对应的url链接
            :params: data dict类型，表示添加的数据内容，其数据结构应满足对应数据项的结构要求
            
            :return: 无
        '''
        r = request('PUT', url, data=json.dumps(data))
    
    def _deleteItemData(self, url):
        '''
            私有方法，删除url链接对应的数据
            :params: url string类型，request请求对应的url链接
            
            :return: 无
        '''
        r = request('DELETE',url)

    def LocationGet(self):
        '''
            获取气象定位点数据

            :return: list<dict>类型，为源数据的引用，包含id，经度坐标，纬度坐标，定位点名称
        '''
        url = f"{self._baseUri}rest/location"
        r = request('GET',
            url,
            params={"simu": self.resourceId})
        return json.loads(r.text)

    def LocationCreate(self, name=None, longitude=None, latitude=None):
        '''
            创建气象定位点
            :param: name 定位点名称，可选
            :params: longitude float类型，可选，表示经度，范围为气象数据源的经度范围
            :params: latitude float类型，可选，表示纬度，范围为气象数据源的纬度范围
    
            :return: 无
        '''
        url = f"{self._baseUri}rest/location"
        r = request('POST',
            url,
            data=json.dumps({
                "lat": latitude  if latitude is not None else '34.734492',
                "lng": longitude if longitude is not None else '113.648906',
                "simu": self.resourceId,
                "name": name if name is not None else '定位点'
            }))
        d = json.loads(r.text)
        
    def LocationUpdate(self, id, name, longitude, latitude):
        '''
            修改气象定位点
            :param id: 定位点id
            :param: name 定位点名称，可选
            :params: longitude float类型，可选，表示经度，范围为气象数据源的经度范围
            :params: latitude float类型，可选，表示纬度，范围为气象数据源的纬度范围
    
            :return: 无
        '''
        if (float(longitude) > 180 or float(longitude) < -180
            or float(latitude) > 90 or float(latitude) < -90):
            raise Exception('经纬度坐标不存在')
        else:
            url = f"{self._baseUri}rest/location"
            r = request('PUT',
                url,
                data=json.dumps({
                    "lat": latitude,
                    "lng": longitude,
                    "simu": self.resourceId,
                    "name": name,
                    "id": id
                }))
            
    def LocationDelete(self, id):
        '''
            删除气象定位点
            :param id: 定位点id

            :return: 无
        '''
        url = f"{self._baseUri}rest/location/{str(id)}"
        r = request('DELETE',
                url)

    def LoadWeather(self):
        '''
            加载气象数据

            :return: 无
        '''
        url = f"{self._baseUri}rest/load_weather"
        r = request('GET',
            url,
            params = {
                "simu": self.resourceId,
            })
        
    def GetAtmosData(self, locationId, date):
        '''
            获取日期在date的气象数据
            :params: locationId str类型，表示定位点id
            :params: date dateTime类型，表示时间
            
            :return: list<dict>类型，为源数据的引用，返回当前项目位置对应时间范围内的气象数据序列，每个元素用字典进行表示，字典的key即区分不同的气象数据项（如风速、太阳辐照等）以及标识当前时间点
        '''
        rDate = datetime.date(*map(int, date.split('-')))
        r = request('GET',
                    self._weatherUrl, 
                    params={
                        "locationId": str(locationId),
                        "date": rDate,
                    })
        return json.loads(r.text)
    
    def AddDataItem(self, kind, data, extra=None):
        '''
            向kind类型的数据库中添加内容为data的数据项
            :params: kind str类型，数据的种类标识，包含：光伏、光伏曲线、风机、风机曲线、燃气、燃气曲线、水电、水电曲线、火电、火电曲线、生物质发电、生物质发电曲线、垃圾电厂、垃圾电厂曲线、传输线、变压器、开关、负荷分类、负荷用户、储能设备、储能运行策略、上网电价、输配电价、常数电价、阶梯电价、分时电价、分时阶梯电价
            :params: data dict类型，表示添加的数据内容，其数据结构应满足对应数据项的结构要求
            :params extra list类型，表示添加的基准出力曲线、负荷曲线、策略曲线数据
    
            :return: list<dict>类型，返回该种类下所有数据项的列表
        '''
        if extra is None or not extra:
            curveData = getCurveData(kind)
            if len(curveData) > 0:
                r = {
                    'simu': self.resourceId,
                    'name': data.get('name', ''),
                    'extra': curveData,
                    'data': data.get('data', {}),
                }
                url = f"{self._baseUri}rest/{kind}"
                self._saveItemData(url, r)
                return self._fetchItemData(url)
            else:
                r = {
                    'simu': self.resourceId,
                    'name': data.get('name', ''),
                    'data': data.get('data', {}),
                }
                url = f"{self._baseUri}rest/{kind}"
                self._saveItemData(url, r)
                return self._fetchItemData(url)
        else:
            r = {
                'simu': self.resourceId,
                'name': data.get('name', ''),
                'extra': extra,
                'data': data.get('data', {}),
            }
            url = f"{self._baseUri}rest/{kind}"
            self._saveItemData(url, r)
            return self._fetchItemData(url)

    def DeleteDataItem(self, id, kind):
        '''
            获取kind类型对应所有数据项的列表
            :params: id int类型，数据的id
            :params: kind str类型，数据的种类标识，包含：光伏、光伏曲线、风机、风机曲线、燃气、燃气曲线、水电、水电曲线、火电、火电曲线、生物质发电、生物质发电曲线、垃圾电厂、垃圾电厂曲线、传输线、变压器、开关、负荷分类、负荷用户、储能设备、储能运行策略、上网电价、输配电价、常数电价、阶梯电价、分时电价、分时阶梯电价
    
            :return: list<dict>类型，返回该种类下所有数据项的列表
        '''
        url = f"{self._baseUri}rest/id/{str(id)}"
        self._deleteItemData(url)
        return self._fetchItemData(f"{self._baseUri}rest/{kind}")


    def UpdateDataItem(self, kind, data):
        '''
            更新kind类型对应数据项
            :params: kind str类型，数据的种类标识，包含：光伏、光伏曲线、风机、风机曲线、燃气、燃气曲线、水电、水电曲线、火电、火电曲线、生物质发电、生物质发电曲线、垃圾电厂、垃圾电厂曲线、传输线、变压器、开关、负荷分类、负荷用户、储能设备、储能运行策略、上网电价、输配电价、常数电价、阶梯电价、分时电价、分时阶梯电价
            :params: data dict类型，表示添加的数据内容，其数据结构应满足对应数据项的结构要求
    
            :return: list<dict>类型，返回该种类下所有数据项的列表
        '''
        url = f"{self._baseUri}rest/{kind}"
        r = {
            'id': data.get('id', ''),
            'name': data.get('name', ''),
            'data': data.get('data', {}),
        }
        self._updateItemData(url, r)
        return self._fetchItemData(url)

        
    def GetItemList(self, kind):
        '''
            获取kind类型对应所有数据项的列表
            :params: kind str类型，数据的种类标识，包含：光伏、光伏曲线、风机、风机曲线、燃气、燃气曲线、水电、水电曲线、火电、火电曲线、生物质发电、生物质发电曲线、垃圾电厂、垃圾电厂曲线、传输线、变压器、开关、负荷分类、负荷用户、储能设备、储能运行策略、上网电价、输配电价、常数电价、阶梯电价、分时电价、分时阶梯电价
    
            :return: list<dict>类型，返回该种类下所有数据项的列表
        '''
        url = f"{self._baseUri}rest/{kind}"
        return self._fetchItemData(url)
    
    def GetItemExtra(self, kind, uuid):
        '''
            获取kind类型对应数据项的基准出力曲线、负荷曲线、策略曲线数据
            :params: kind str类型，数据的类型
            :params: uuid str类型，数据的unique id
        '''
        url = f"{self._baseUri}rest/id/{uuid}"
        data = self._fetchItemData(url)
        if data.get('extra', None) is None:
            return None
        return data.get('extra', None).get('data', None)
    
    def UpdateItemExtra(self, kind, data):
        '''
            更新kind类型对应数据项的基准出力曲线、负荷曲线、策略曲线数据
            :params: kind str类型，数据的种类标识，包含：光伏、光伏曲线、风机、风机曲线、燃气、燃气曲线、水电、水电曲线、火电、火电曲线、生物质发电、生物质发电曲线、垃圾电厂、垃圾电厂曲线、传输线、变压器、开关、负荷分类、负荷用户、储能设备、储能运行策略、上网电价、输配电价、常数电价、阶梯电价、分时电价、分时阶梯电价
            :params: data dict类型，表示添加的数据内容，其数据结构应满足对应数据项的结构要求，形如：{'data': {}, 'extra': [], 'id': ""}
    
            :return: list<dict>类型，返回该种类下所有数据项的列表
        '''
        url = f"{self._baseUri}rest/{kind}"
        r = {
            'id': data.get('id', ''),
            'data': data.get('data', {}),
            'extra': data.get('extra', []),
        }

        self._updateItemData(url, r)
        return self._fetchItemData(url)

class DSLabDataManageModel(DataManageModel):
    _baseUri = 'api/dslab/'
    _weatherUrl = 'api/dslab/rest/weather'

