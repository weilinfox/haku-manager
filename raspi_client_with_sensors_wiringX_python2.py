#!/usr/bin/python2

# need root
# with pms sensors
# with 1602 screen
# wiringX python2 version
from wiringX import gpio
import commands, time, os
import requests
import traceback
import serial
import struct

# serial config
port = '/dev/ttyUSB0'
bps = 9600
bytesize = 8
parity = 'N'
stopbits = 1
timeout = 5
device = 0
try:
    device = serial.Serial(port,
                    baudrate=bps,
                    bytesize=bytesize,
                    parity=parity,
                    stopbits=stopbits,
                    timeout=timeout
                    )
    if not device.isOpen():
        device.open()
except Exception as e:
    print(e)
    exit(1)

# needed commands
if os.system('w -V'): exit(1)
if os.system('vmstat -V'): exit(1)
if os.system('cat /proc/cpuinfo| grep "processor"| wc -l'): exit(1)
cores = int(commands.getoutput('cat /proc/cpuinfo| grep "processor"| wc -l'))

# raspberrypi3
gpio.setup(gpio.RASPBERRYPI3)

# set pins
# GPIO.1 PIN12
# wiringX code just like wiringPi
FAN_GPIO = gpio.PIN1
INFRARED_GPIO = gpio.PIN0
# PIN21-PIN28 -> D0-D7
screen_data = [29, 28, 27, 26, 25, 24, 23, 22]
# 29 in pin map
screen_led = 21
screen_cs = gpio.PIN2
screen_rs = gpio.PIN3

# set GPIOs
gpio.pinMode(FAN_GPIO, gpio.PINMODE_OUTPUT)
gpio.pinMode(INFRARED_GPIO, gpio.PINMODE_INPUT)
gpio.pinMode(screen_led, gpio.PINMODE_OUTPUT)
gpio.pinMode(screen_cs, gpio.PINMODE_OUTPUT)
gpio.pinMode(screen_rs, gpio.PINMODE_OUTPUT)

# init GPIOs
gpio.digitalWrite(FAN_GPIO, gpio.LOW)
for pin in screen_data:
    gpio.pinMode(pin, gpio.PINMODE_OUTPUT)
    gpio.digitalWrite(pin, gpio.LOW)
gpio.digitalWrite(screen_led, gpio.LOW)
gpio.digitalWrite(screen_cs, gpio.HIGH)
gpio.digitalWrite(screen_rs, gpio.LOW)

# sensor data keys
keylist = ['c-pm1.0', 'c-pm2.5', 'c-pm10',
            'a-pm1.0', 'a-pm2.5', 'a-pm10',
            '>0.3um', '>0.5um', '>1.0um',
            '>2.5um', '>5.0um', '>10um',
            'voc', 'T', 'RH']

# screen control functions
# clear screen and reset cursor
def screen_set_clear():
    for pin in screen_data[1:]:
        gpio.digitalWrite(pin, gpio.LOW)
    gpio.digitalWrite(screen_data[0], gpio.HIGH)
    gpio.digitalWrite(screen_rs, gpio.LOW)
    gpio.digitalWrite(screen_cs, gpio.LOW)
    time.sleep(0.005)
    gpio.digitalWrite(screen_cs, gpio.HIGH)
# reset cursor
def screen_reset_cursor():
    for pin in screen_data[2:]:
        gpio.digitalWrite(pin, gpio.LOW)
    gpio.digitalWrite(screen_data[0], gpio.LOW)
    gpio.digitalWrite(screen_data[1], gpio.HIGH)
    gpio.digitalWrite(screen_rs, gpio.LOW)
    gpio.digitalWrite(screen_cs, gpio.LOW)
    time.sleep(0.005)
    gpio.digitalWrite(screen_cs, gpio.HIGH)
# set cursor (to row2 line1)
def screen_set_cursor():
    for pin in screen_data[0:-2]:
        gpio.digitalWrite(pin, gpio.LOW)
    gpio.digitalWrite(screen_data[6], gpio.HIGH)
    #gpio.digitalWrite(screen_data[4], gpio.HIGH)
    gpio.digitalWrite(screen_data[7], gpio.HIGH)
    gpio.digitalWrite(screen_rs, gpio.LOW)
    gpio.digitalWrite(screen_cs, gpio.LOW)
    time.sleep(0.005)
    gpio.digitalWrite(screen_cs, gpio.HIGH)
# display switch and cursor status
def screen_set_display(show, cursor, flash):
    for pin in screen_data[4:]:
        gpio.digitalWrite(pin, gpio.LOW)
    gpio.digitalWrite(screen_data[3], gpio.HIGH)
    if show: gpio.digitalWrite(screen_data[2], gpio.HIGH)
    else: gpio.digitalWrite(screen_data[2], gpio.LOW)
    if cursor: gpio.digitalWrite(screen_data[1], gpio.HIGH)
    else: gpio.digitalWrite(screen_data[1], gpio.LOW)
    if flash: gpio.digitalWrite(screen_data[0], gpio.HIGH)
    else: gpio.digitalWrite(screen_data[0], gpio.LOW)
    gpio.digitalWrite(screen_rs, gpio.LOW)
    gpio.digitalWrite(screen_cs, gpio.LOW)
    time.sleep(0.005)
    gpio.digitalWrite(screen_cs, gpio.HIGH)
# init LCD mode
def screen_set_function(bitwide, dual, bits):
    gpio.digitalWrite(screen_data[0], gpio.LOW)
    gpio.digitalWrite(screen_data[1], gpio.LOW)
    gpio.digitalWrite(screen_data[5], gpio.HIGH)
    gpio.digitalWrite(screen_data[6], gpio.LOW)
    gpio.digitalWrite(screen_data[7], gpio.LOW)
    if bitwide: gpio.digitalWrite(screen_data[4], gpio.HIGH)
    else: gpio.digitalWrite(screen_data[4], gpio.LOW)
    if dual: gpio.digitalWrite(screen_data[3], gpio.HIGH)
    else: gpio.digitalWrite(screen_data[3], gpio.LOW)
    if bits: gpio.digitalWrite(screen_data[2], gpio.HIGH)
    else: gpio.digitalWrite(screen_data[2], gpio.LOW)
    gpio.digitalWrite(screen_rs, gpio.LOW)
    gpio.digitalWrite(screen_cs, gpio.LOW)
    time.sleep(0.005)
    gpio.digitalWrite(screen_cs, gpio.HIGH)
# trans string to byte list
def screen_string2data(str):
    ans = []
    for c in str:
        ans.append(ord(c))
    return ans
# write word(byte) list to LCD
def screen_write_data(words):
    gpio.digitalWrite(screen_rs, gpio.HIGH)
    for c in words:
        for i in range(0, 8):
            gpio.digitalWrite(screen_data[i], c%2)
            c //= 2
        gpio.digitalWrite(screen_cs, gpio.LOW)
        gpio.digitalWrite(screen_cs, gpio.HIGH)
        time.sleep(0.00005)
# init LCD word input mode
def screen_input_mode(cursor_right, word_move):
    for pin in screen_data[3:]:
        gpio.digitalWrite(pin, gpio.LOW)
    gpio.digitalWrite(screen_data[2], gpio.HIGH)
    if cursor_right: gpio.digitalWrite(screen_data[1], gpio.HIGH)
    else: gpio.digitalWrite(screen_data[1], gpio.LOW)
    if word_move: gpio.digitalWrite(screen_data[0], gpio.HIGH)
    else: gpio.digitalWrite(screen_data[0], gpio.LOW)
    gpio.digitalWrite(screen_rs, gpio.LOW)
    gpio.digitalWrite(screen_cs, gpio.LOW)
    time.sleep(0.005)
    gpio.digitalWrite(screen_cs, gpio.HIGH)
# init 1602 LCD
def screen_init():
    time.sleep(0.015)
    screen_set_clear()
    screen_set_function(True, True, False)
    screen_set_display(True, False, False)
    screen_input_mode(True, False)
# switch LCD backlight
def screen_light(on):
    if on: gpio.digitalWrite(screen_led, gpio.LOW)
    else: gpio.digitalWrite(screen_led, gpio.HIGH)
# show page1
def screen_page1(t, rh, nt):
    screen_reset_cursor()
    line = ''
    tmp = '{:+.1f}'.format(t)
    for _ in range(5-len(tmp)): line = line + ' '
    line = line + tmp + '\xdfC   net:'
    if nt: line = line + '\xe8 '
    else: line = line + 'X '
    screen_write_data(screen_string2data(line))
    screen_set_cursor()
    line = ''
    tmp = '{:.1f}'.format(rh)
    for _ in range(4-len(tmp)): line = line + ' '
    line = line + tmp + '%   '
    tm = int(time.time()+8*3600) % 86400
    tmp = '{:02d}:{:02d}:{:02d}'.format(tm//3600, (tm%3600)//60, tm%60)
    screen_write_data(screen_string2data(line+tmp))
# show page2
def screen_page2(pm, pm10):
    screen_reset_cursor()
    tmp = '{:.1f}'.format(pm)
    line = 'pm2.5:'
    for _ in range(4-len(tmp)): line = line + ' '
    line = line + tmp + '\xe4g/m3 '
    screen_write_data(screen_string2data(line))
    screen_set_cursor()
    tmp = '{:.1f}'.format(pm10)
    line = ' pm10:'
    for _ in range(4-len(tmp)): line = line + ' '
    line = line + tmp + '\xe4g/m3 '
    screen_write_data(screen_string2data(line))
# show page3
def screen_page3(voc):
    screen_reset_cursor()
    line = ' voc:'
    tmp = '{:1.3f}'.format(voc)
    for _ in range(5-len(tmp)): line = line + ' '
    line = line + tmp + 'mg/m3 '
    screen_write_data(screen_string2data(line))
    screen_set_cursor()
    line = '                '
    screen_write_data(screen_string2data(line))

# upload status
URL = 'http://127.0.0.1:10004'
NAME = 'raspi-arch'

# files
tempFile = '/sys/class/thermal/thermal_zone0/temp'
netFile = '/proc/net/dev'
statusCom = 'w'
ditlCom = 'vmstat'

# global data
cpu_temp = 0
fan_status = 1
lcd_status = 1
net_status = 1
infrared_last = 0
senser_data = dict()
upload_data = dict()

# the same error report once in half an hour
#gpio_error_time = 0
#temp_exceed_time = 0

onceDelay = 0.5
#hearbeatDelay = 10.0
systemDelay = 5.0
lcdpageDelay = 0
lcdlightDelay = 0

print('Init finished.')
print('Sleep for five seconds...')
time.sleep(5)
# set device mode
device.write(b'\x42\x4d\xe1\x00\x00\x01\x70')
time.sleep(0.1)
device.write(b'\x42\x4d\xe1\x00\x00\x01\x70')
print('Settint sensor to negtive mode.')
print('Set! Wait for five seconds')
time.sleep(5)
screen_init()
print('Start service')

while True:
    try:
        resp = requests.post(url=URL, json={'post_type':'haku-manager','server_name':NAME,'message_type':'heartBeat'})
    except Exception as e:
        print(e)
        net_status = 0
    else:
        if resp.status_code != 200:
            print('Send heartBeat returned: ' + str(resp.status_code))
        else:
            net_status = 1

    # get sensor data
    try:
        device.flushInput()
        device.write(b'\x42\x4d\xe2\x00\x00\x01\x71')
        sheader = device.read(2)
        if sheader == b'\x42\x4d':
            chksum = 0x42 + 0x4d
            sizebyte = device.read(2)
            sizeint = struct.unpack('>H', sizebyte)[0]
            chksum += sizeint//0x100 + sizeint%0x100
            databyte = device.read(sizeint-6)
            ansdict = dict()
            for i in range(0, sizeint-6, 2):
                dataint = struct.unpack('>H', databyte[i:i+2])[0]
                chksum += dataint//0x100 + dataint%0x100
                ansdict.update({keylist[i//2]: dataint})
                #print(dataint//0x100, dataint%0x100, dataint)
            if 'voc' in ansdict.keys():
                ansdict['voc'] /= 1000.0
            if 'T' in ansdict.keys():
                ansdict['T'] /= 10.0
            if 'RH' in ansdict.keys():
                ansdict['RH'] /= 10.0

            chkbyte = device.read(4)
            errcode = struct.unpack('>HH', chkbyte)
            chksum += errcode[0]//0x100 + errcode[0]%0x100
            version = errcode[1]//0x100
            errcode = errcode[1]%0x100
            chksum += version + errcode
            ansdict.update({'errcode': errcode, 'version': version})

            chkbyte = device.read(2)
            if chksum == struct.unpack('>H', chkbyte)[0]:
                senser_data = ansdict
            else:
                senser_data = dict()
                senser_data.update({'ERROR':'senser data checksum error'})
        else:
            senser_data = dict()
            senser_data.update({'ERROR':'senser read error'})
    except Exception as e:
        print(e)

    # infrared sensor
    infdata = gpio.digitalRead(INFRARED_GPIO)
    if infdata == gpio.HIGH:
        infrared_last = time.time() + 8*3600
        lcdlightDelay = 10
    ansdict.update({'infrared_last': infrared_last})
    if lcd_status:
        lcdlightDelay -= onceDelay
        if lcdlightDelay <= 0:
            lcd_status = 0
            screen_light(False)
    else:
        if lcdlightDelay > 0:
            lcd_status = 1
            screen_light(True)

    # lcd show
    lcdpageDelay += onceDelay
    if lcdpageDelay >= 9:
        lcdpageDelay = 0
    if lcdpageDelay < 3:
        screen_page1(senser_data.get('T', 0), senser_data.get('RH', 0), net_status)
    elif lcdpageDelay < 6:
        screen_page2(senser_data.get('a-pm2.5', 0), senser_data.get('a-pm10', 0))
    elif lcdpageDelay < 9:
        screen_page3(senser_data.get('voc', 0))

    # get system data
    systemDelay += onceDelay
    if systemDelay >= 5.0:
        systemDelay = 0.0
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
            if not fan_status and (cpu_temp >= 55.0 or cpu_temp < 0):
                gpio.digitalWrite(FAN_GPIO, gpio.LOW)
                fan_status = 1
                print('turn on fan')
            if fan_status and cpu_temp >= 0 and cpu_temp < 45.0:
                gpio.digitalWrite(FAN_GPIO, gpio.HIGH)
                fan_status = 0
                print('turn off fan')
        except:
            msg = traceback.format_exc()
            print(msg)
            requests.post(url=URL, json={'post_type':'haku-manager','server_name':NAME,'message_type':'error','message':'Switch fan failed!\n'+msg})

        # get status
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
            upload_data.update(reportDict)


    upload_data['status'].update({'env_data':senser_data})
    # upload
    try:
        requests.post(url=URL, json=upload_data)
    except Exception as e:
        print(e)
    time.sleep(onceDelay)
