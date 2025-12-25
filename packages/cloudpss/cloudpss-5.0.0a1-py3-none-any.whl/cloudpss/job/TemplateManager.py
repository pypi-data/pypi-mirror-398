import logging
from cloudpss.job.TemplateCompiler import template
class TemplateManager():
    
    def __init__(self) -> None:
        self.templateMap = {}

    def isCreate(self, value):
        return type(value) == list and len(value) > 3 and type(value[0]) == int and value[1] == 1
    
    def create(self,  value):
        if not self.isCreate(value):
            print("is create")
            return
        id =value[0]
    
        templates=value[3:]
        if self.templateMap.get(id,None) is not None:
            logging.debug(f"template {id} is already exist")
        
        self.templateMap[id] = {'template':template(templates),'value':value}
        
        
    
    def isInvoke(self, value):
        return type(value) == list and len(value) == 3 and type(value[0]) == int and value[1] == 1
    
    def invoke(self, value):
        if not self.isInvoke(value):
            return []
        id,_version,args = value
        
        t = self.templateMap.get(id,None)
        if t is None:
            return []
        return t['template'](args)
    