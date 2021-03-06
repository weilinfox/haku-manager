#!/usr/bin/python3

import subprocess, time, os
import requests
import traceback

if os.system('w -V'): exit(1)
if os.system('vmstat -V'): exit(1)
if os.system('cat /proc/cpuinfo| grep "processor"| wc -l'): exit(1)
cores = int(subprocess.getoutput('cat /proc/cpuinfo| grep "processor"| wc -l'))

# 状态上报
URL = '127.0.0.1'
PORT = 8080
NAME = 'linux'

# files
#tempFile = '/sys/class/thermal/thermal_zone0/temp'
netFile = '/proc/net/dev'
statusCom = 'w'
ditlCom = 'vmstat'

# 同样的错误半小时上报一次
#gpio_error_time = 0
#temp_exceed_time = 0

reportDelay = 60

while True:
    try:
        resp = requests.post(url=f'http://{URL}:{PORT}', json={'post_type':'haku-manager','server_name':NAME,'message_type':'heartBeat'})
    except Exception as e:
        print(e)
    else:
        if resp.status_code != 200:
            print(f'Send heartBeat returned: {resp.status_code}')
    reportDelay += 1

    # status 上报 10min
    if reportDelay >= 60:
        reportDelay = 0
        reportDict = {'post_type':'haku-manager','server_name':NAME,'message_type':'status','status':{'time':{'uptime':''},'temp':{'cpu_temp':0, 'sys_temp':0,'fan_status':1},'cpu':{'cpu_cores':cores, 'load_average':0.0, 'wa':0}, 'disk':{'bi':0, 'bo':0}, 'memory':{'free':0, 'buff':0, 'cache':0}, 'swap':{'si':0, 'so':0}, 'process':{'r':0, 'b':0}, 'net':{}}}
        try:
            wMsg = list(subprocess.getoutput(statusCom).split())
            if len(wMsg) > 8:
                uptime = ''
                getU = False
                for s in wMsg:
                    if getU and uptime and s[-1] != ',': break
                    elif getU: uptime += f' {s}'
                    if s == 'up': getU = True
                reportDict['status']['time']['uptime'] = uptime[:-1].strip()
                getU = False
                for s in wMsg:
                    if getU: 
                        reportDict['status']['cpu']['load_average'] =  float(s[:-1])
                        break
                    if s == 'average:': getU = True
            statMsg = list(subprocess.getoutput(ditlCom).split())
            if len(statMsg) == 40:
                reportDict['status']['process']['r'] = int(statMsg[23])
                reportDict['status']['process']['b'] = int(statMsg[24])
                reportDict['status']['memory']['free'] = int(statMsg[26])
                reportDict['status']['memory']['buff'] = int(statMsg[27])
                reportDict['status']['memory']['cache'] = int(statMsg[28])
                reportDict['status']['swap']['si'] = int(statMsg[29])
                reportDict['status']['swap']['so'] = int(statMsg[30])
                reportDict['status']['disk']['bi'] = int(statMsg[31])
                reportDict['status']['disk']['bo'] = int(statMsg[32])
                reportDict['status']['cpu']['wa'] = int(statMsg[38])
            fle = open(netFile, 'r')
            netMsg = fle.read()
            fle.close()
            netMsg = list(netMsg.split('\n', netMsg.count('\n')))
            for i in range(3, len(netMsg)):
                splt = netMsg[i].split()
                if len(splt) > 5: reportDict['status']['net'][splt[0][:-1]] = {'bytes':int(splt[1]),'packets':int(splt[2]),'errors':int(splt[3]),'drops':int(splt[4])}
        except:
            msg = traceback.format_exc()
            print(msg)
        else:
            #print(reportDict)
            try:
                requests.post(url=f'http://{URL}:{PORT}', json=reportDict)
            except Exception as e:
                print(e)
    time.sleep(10)

