"""
genie.model.bd.py
~~~~~~~~~

This file contains library for BD Access.
This implementation based on BD SDK and BD version X.X.

@copyright:	(c) 2013 SynergyLabs
@license:	UCSD License. See License file for details.
"""

import sys
import json
import httplib
import urllib

from datetime import timedelta, datetime
from dateutil import parser
from dateutil.tz import tzutc, tzlocal


# BD Configuration
BD_HOST = 'ob-ucsd-cse.ucsd.edu'
BD_USERS_PORT = '8000'
BD_DATAS_PORT = '8000'
BD_HTTPS = False
BD_DATAS_API_KEY = 'd81459cb-fbd3-479c-9070-8906427e0c45'


# Modify to reflect the location of the DataService JSON Interface
DATAS = "/dataservice/api"


class BuildingDepotService(object):
    """ Accessor to BD Services """
    def __init__(self):
        self.host = BD_HOST
        self.port = BD_USERS_PORT
        self.ssl = BD_HTTPS

        self.api_key = BD_DATAS_API_KEY
        #self.root_dir = DATAS
        
    """ Send request to BD """
    def send_request(self, url, body=None, method='GET', params=None):
        if self.ssl:
            conn = httplib.HTTPSConnection(self.host, self.port)
        else:
            conn = httplib.HTTPConnection(self.host, self.port)

        headers = {}
        headers['X-BD-Api-Key'] = self.api_key
        headers['X-BD-Auth-Token'] = None
        if body:
            headers['Content-Type'] = 'application/json'

        if body:
            body = json.dumps(body)

        if params:
            url = url + '?' + params
        
        url = DATAS + url
        
        is_success = False
        try:
            conn.request(method, url, body, headers)
            resp = conn.getresponse()
            if resp.status in range(200,299):
                is_success = True
            else:
                print 'Error Response'
                pass
                
            content = resp.read()
        except httplib.HTTPException, ex:
            print ex
            return is_success, None
        
        if content and resp.status != 500:
            return is_success, self.process_response(content)
        else:
            return is_success, None
        

    """ Process response from BD """
    def process_response(self, json_response):
        response = json.loads(json_response)
        status = response.get('status', None)

        if status not in [200, 201]:
            return None

        if not response:
            return None

        return response

    def get_sensors_by_context(self, context):
        
        ctxt_lst = ['%s=%s' % (key, context[key]) for key in context.keys()]
        ctxt_str = '+'.join(ctxt_lst)
        url = '/sensors/context/' + urllib.quote(ctxt_str)
        
        sensors = []
           
        page = 1
        sensor_num = 0
        while True:
            paging_str = urllib.urlencode({'page': page, 'count': 400})
            is_success,resp = self.send_request(url, params=paging_str)
            if is_success:
                total = resp.get('total')
                sensor_list = resp.get('sensors')
                sensors += sensor_list
                sensor_num += len(sensor_list)
                page += 1
                if sensor_num == total:
                    break
            else:
                print 'Error Reponse'
                break
        
        return sensors
    
    def get_sensortypes(self):
        
        url = '/sensortypes'
        is_success,resp = self.send_request(url)
        if is_success:
            types = resp['sensortypes']
            for type in types:
                print type,type['name'],'|',type['description']
    
    def get_datapoints(self, uuid, spname, timerange=None):
        """ Get data of Sensor Points """
        
        datapoints = []
        if timerange:
            url = '/sensors/%s/sensorpoints/%s/datapoints?' % (uuid , spname)
            end = timerange['end']
            while True:
                is_success,resp = self.send_request(url + urllib.urlencode(timerange))
                if is_success:
                    dps = resp['datapoints']
                    if len(dps) != 0:
                        fetch_end = dps[len(dps)-1].keys()[0]
                        start = parser.parse(fetch_end) + timedelta(minutes=1)
                        timerange = {'start':start.isoformat(),'end':end}
                        datapoints += dps
                        if start > parser.parse(end):
                            break
                    else:
                        break
                else:
                    break
        else:
            # try to read from cache
            read_from_bd = True
            key = str('latest_value-' + uuid + '-' + spname)
            current_time = datetime.now(tzutc()).astimezone(tzlocal())
            if usecache:
                dps_json = read(key,file=LATEST_DATAPOINT_CACHE)
                if dps_json:
                    dp = json.loads(dps_json)
                    try:
                        cacheupdate = parser.parse(dp['cacheupdate'])
                        #timestamp = parser.parse(dps[0].keys()[0])
                        td = timedelta(minutes=threshold)
                        
                        if current_time - cacheupdate > td:
                            print 'out of range', current_time, cacheupdate
                            read_from_bd = True
                        else:
                            datapoints = dp['latestpt']
                            read_from_bd = False
                    except Exception,ex:
                        read_from_bd = True
                else:
                    read_from_bd = True
            else:
                read_from_bd = True
            
            if read_from_bd:
                url = '/sensors/%s/sensorpoints/%s/datapoints' % (uuid , spname)
                is_success,resp = self.send_request(url)
                if is_success and resp['datapoints']:
                    datapoints += resp['datapoints']
                    if updatecache:
                        dp = {}
                        dp['cacheupdate'] = current_time.isoformat()
                        dp['latestpt'] = resp['datapoints']
                        store(key,json.dumps(dp),file=LATEST_DATAPOINT_CACHE)
        
        if len(datapoints) == 0:
            raise BDError(BDError.DATA_ACCESS,'Datapoints are not exist.')
            
        return datapoints
    
# if we are running directly from python then run the debug server
if __name__ == "__main__":
    start = parser.parse(datetime(2014,2,1,0,0,tzinfo=tzlocal()).isoformat())
    end = parser.parse(datetime(2014,8,31,0,0,tzinfo=tzlocal()).isoformat())
    timerange = {'start':start.isoformat(),'end':end.isoformat()}
    
    #
    #type = 'Zone Temperature'
    spname = 'PresentValue'
    #room = '2150'
    #room='B240'
    room=sys.argv[1]
    types=['Actual Cooling Setpoint', 'Actual Heating Setpoint', 'Warm/Cool Adjust','Actual Supply Flow','Damper Position','Occupied Command','Supply Vel Press','Zone Temperature','Cooling Max Flow']

    print room
    
    
    bd = BuildingDepotService()
    count=1;
    for type in types:
        print type
        ctx = {}
        ctx['room'] = 'Rm-' + room
        ctx['type'] = type
        sensors = bd.get_sensors_by_context(ctx)
        for sensor in sensors:
            print sensor['uuid']
            dps = bd.get_datapoints(sensor['uuid'],spname,timerange)
            if count==3:
                fname =  room + '_' + 'WarmCool Adjust' + '_' + spname + '.csv'
            else:
                fname =  room + '_' + type + '_' + spname + '.csv'
            f = open(fname, 'w')
            f.write('timestamp,value\n')
            for dp in dps:
                f.write(dp.keys()[0] + ',' + dp.values()[0] + '\n')
                #print dp.keys()[0] + ',' + dp.values()[0]
            f.close()
        count=count+1;
        
    
