import os,sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..\\'))
import cloudpss 
import socketio
import threading
import struct
import json

class RealTimeSream(socketio.ClientNamespace):
    
    config = None
    messages = []
    series=[]
    outputNumericValue={}
    inputNumericValue={}
    
    end=False
    
    def __init__(self, namespace=None, *args, **kwargs):
        super().__init__(namespace)
        
        setattr(self, 'on_data-panel', self.on_data_panel)
        setattr(self, 'on_start-job', self.on_start_job)
        setattr(self, 'on_stop-job', self.on_stop_job)
        setattr(self, 'on_close-job', self.on_close_job)
        self.numericValueCallBack = kwargs.get('numericValueCallBack',None)
        self.chartCallBack = kwargs.get('chartCallBack',None)
        
        
        
        
    def on_connect(self):
        self.emit('start-job', { 'type': 'start-job', 'context': 'real-time-data' })
        pass

    def on_disconnect(self):
        pass

    def on_data_panel(self, data):
        # self.numericValue=data
        virtual_input=self.config['virtual_input']
        virtual_output=self.config['virtual_output']
        display=self.config['display']
        
        d ={}
        for x,v in display.items():
            d[v]=x
        
        for i in range(0,virtual_input):
            self.inputNumericValue[d[i]]=data[i]
        for i in range(0,virtual_output): 
            self.outputNumericValue[d[virtual_input+i]]=data[virtual_input+i]
        if self.numericValueCallBack is not None:
            self.numericValueCallBack(self.inputNumericValue,self.outputNumericValue)
    def on_start_job(self,data):
        self.config =data
        print( 'on_start_job',self.config)
    def on_stop_job(self,data):
        print('on_stop_job',flush=True)
        self.disconnect()
        self.end=True
    def on_close_job(self,data):
        print('on_close_job',flush=True)
        self.disconnect()
        self.end=True
    def on_recording(self,data):
        print( 'on_recording',data)
    def on_load_record_data(self,data):
        print( 'on_load_record_data',data)
    def on_real_time_data(self,msg):
        display=self.config['display']
        d ={}
        for x,v in display.items():
            d[v]=x
        data =struct.unpack('d'*int(len(msg)/8),msg)
        i = 0
        runTime =0
        self.series=[]
        channelLength=int(self.config['portNumber'])+1
        virtual_input=int(self.config['virtual_input'])
        for index in range(0,len(data)):
            val = data[index]
            if(index%channelLength==0):
                i=0
                runTime = val
            elif i>virtual_input:
                serieIndex = i - virtual_input - 1
                
                if len(self.series)-1<serieIndex:
                    serie=  {
                        'name':  d[i-1],
                        'type': 'scatter',
                        'x': [],
                        'y': []
                    }  
                    self.series.append(serie)
                else:
                    serie=self.series[serieIndex]
                
                serie['x'].append(runTime)
                serie['y'].append(val)
            i+=1
        if self.chartCallBack is not None:
            self.chartCallBack(self.series)

    def close(self):
        self.end =True
        self.disconnect()
        # self.emit('close-job', { 'type': 'close-job', 'context': 'close-job' })
    def write(self,data):
        print('write',data,flush=True)
        self.emit('send-message', data)
    @staticmethod
    def connect(*args, **kwargs):
        sio = socketio.Client()
        stream = RealTimeSream('',*args, **kwargs)
        
        sio.register_namespace(stream)
        
        url = os.environ.get('CLOUDPSS_API_URL')
        
        if url is None:
            url = 'http://10.101.10.91/'
        
        sio.connect(url,socketio_path='/api/real-time/socket.io')
    
        thread = threading.Thread(target=sio.wait, args=())
        thread.setDaemon(True)
        thread.start()
        return stream

if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    job = cloudpss.currentJob()
    
    remoteAddr= job.args.get('remoteAddr','http://10.101.10.104/')
    
    inputKey= job.args.get('inputKey',None)
    inputValue= job.args.get('inputValue',None)
    
    print('inputKey',inputKey)
    print('inputValue',inputValue)
    if not remoteAddr.startswith('http://'):
        remoteAddr='http://'+remoteAddr
    
    
    
    os.environ['CLOUDPSS_API_URL'] = remoteAddr
    
    
    def exitCallback():
        stream.close()
        time.sleep(1)
        print('exit')
        job.exit(0)

    job.on_abort(exitCallback, args=(), kwargs={})
    

    stream = RealTimeSream.connect()
    stream.write({inputKey:float(inputValue)})
    time.sleep(1)
    stream.close()
   
    job.exit(0)