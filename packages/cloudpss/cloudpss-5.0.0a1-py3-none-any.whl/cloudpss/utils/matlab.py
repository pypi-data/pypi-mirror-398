import numpy as np

def loadPyData(data): 

    """
        matlab处理python数据中的list数据.

        :data: 数据

        :return: 用户信息 

        >>> matlab.loadPyData(data)
        {
            ...
        }
    """

    if isinstance(data, dict): 
        tmp={}
        for key,val in data.items():
            tmp[key]=loadPyData(val)
        return tmp
    if isinstance(data, list): 
        try:
            x=np.array(data)
            if x.dtype.type==np.str_:
                return [loadPyData(val) for val in  data]
            if x.dtype.type==np.object_:
                return [loadPyData(val) for val in  data]
            return memoryview(x)
        except Exception as e:
            return [loadPyData(val) for val in  data]
    else:
        return data