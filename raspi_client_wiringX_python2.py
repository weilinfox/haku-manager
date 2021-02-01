#!/usr/bin/python2

# need root
# wiringX python2 version
from wiringX import gpio
import commands, time, os
import requests
import traceback

if os.system('w -V'): exit(1)
if os.system('vmstat -V'): exit(1)
cores = int(os.system('cat /proc/cpuinfo| grep "processor"| wc -l'))

# raspberrypi3
gpio.setup(gpio.RASPBERRYPI3)
# GPIO.1 PIN12
# wiringX code just like wiringPi
FAN_GPIO = gpio.PIN1
fan_status = 0
# set FAN_GPIO output
gpio.pinMode(FAN_GPIO, gpio.PINMODE_OUTPUT)

# upload status
URL = 'http://127.0.0.1:8080'
NAME = 'raspi'

# files
tempFile = '/sys/class/thermal/thermal_zone0/temp'
netFile = '/proc/net/dev'
statusCom = 'w'
ditlCom = 'vmstat'

# the same error report once in half an hour
#gpio_error_time = 0
#temp_exceed_time = 0

reportDelay = 60

while True:
    try:
        resp = requests.post(url=URL, json={'post_type':'haku-manager','server_name':NAME,'message_type':'heartBeat'})
    except Exception as e:
        print(e)
    else:
        if resp.status_code != 200:
            print('Send heartBeat returned: ' + str(resp.status_code))
    reportDelay += 1
    # get CPU temperature
    try:
        tempF = open(tempFile, 'r')
        tempData = tempF.read()
        tempF.close()
    except:
        tempData = -1
        msg = traceback.format_exc()
        print(msg)
        try:
            requests.post(url=URL, json={'post_type':'haku-manager','server_name':NAME,'message_type':'error','message':'Get pi temperature failed!\n'+msg})
        except Exception as e:
            print(e)
    finally:
        cpu_temp = int(tempData) / 1000

    try:
        # low on, high off
        if not fan_status and (cpu_temp >= 50.0 or cpu_temp < 0):
            gpio.digitalWrite(FAN_GPIO, gpio.LOW)
            fan_status = 1
        if fan_status and cpu_temp >= 0 and cpu_temp < 45.0:
            gpio.digitalWrite(FAN_GPIO, gpio.HIGH)
            fan_status = 0
    except:
        msg = traceback.format_exc()
        print(msg)
        requests.post(url=URL, json={'post_type':'haku-manager','server_name':NAME,'message_type':'error','message':'Switch fan failed!\n'+msg})

    # status upload duration:10min
    if reportDelay >= 60:
        reportDelay = 0
        reportDict = {'post_type':'haku-manager','server_name':NAME,'message_type':'status','status':{'time':{'uptime':''}, 'temp':{'cpu_temp':cpu_temp, 'sys_temp':cpu_temp, 'fan_status':fan_status}, 'cpu':{'cpu_cores':cores, 'load_average':0.0, 'wa':0}, 'disk':{'bi':0, 'bo':0}, 'memory':{'free':0, 'buff':0, 'cache':0}, 'swap':{'si':0, 'so':0}, 'process':{'r':0, 'b':0}, 'net':{}}}
        try:
            wMsg = list(commands.getoutput(statusCom).split())
            if len(wMsg) > 8:
                uptime = ''
                getU = False
                for s in wMsg:
                    if getU and uptime and s[-1] != ',': break
                    elif getU: uptime += ' ' + s
                    if s == 'up': getU = True
                reportDict['status']['time']['uptime'] = uptime[:-1].strip()
                getU = False
                for s in wMsg:
                    if getU: 
                        reportDict['status']['cpu']['load_average'] =  float(s[:-1])
                        break
                    if s == 'average:': getU = True
            statMsg = list(commands.getoutput(ditlCom).split())
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
                requests.post(url=URL, json=reportDict)
            except Exception as e:
                print(e)
    time.sleep(10) 
