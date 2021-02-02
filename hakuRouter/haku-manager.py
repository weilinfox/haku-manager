
import threading, logging, time
import hakuData.status

myLogger = logging.getLogger('hakuBot')
statusLock = threading.Lock()
statusDict = {}
errorCount = 0
hakuData.status.regest_router('haku-manager', {'status':statusDict, "errors":errorCount})

def new_event(msgDict):
    global statusDict, errorCount
    timeNow = time.time()
    if msgDict['message_type'] == 'heartBeat':
        if msgDict['server_name'] in statusDict:
            statusDict[msgDict['server_name']]['time'] = timeNow
        else:
            statusDict[msgDict['server_name']] = {'status':{},'time':timeNow}
        hakuData.status.refresh_status('haku-manager')
    elif msgDict['message_type'] == 'error':
        myLogger.error(f"Error reported in {msgDict['server_name']}: {msgDict['message']}")
        errorCount += 1
        hakuData.status.refresh_status('haku-manager', {'status':statusDict, "errors":errorCount})
    elif msgDict['message_type'] == 'status':
        statusDict[msgDict['server_name']] = {'status':msgDict['status'],'time':timeNow}
        myLogger.debug(f"New status in {msgDict['server_name']}: {msgDict['status']}")
