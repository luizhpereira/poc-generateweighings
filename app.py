from flask import Flask, request
from flask_mqtt import Mqtt
from flask_cors import CORS
from threading import Timer, Thread
from util import *

app = Flask(__name__)
CORS(app)

##### ON START APP #####
# if __name__ == __name__:
#     Timer(1, onInit).start()

# use the free broker from HIVEMQ
app.config['MQTT_BROKER_URL'] = '192.168.2.152' #Virtual machine Cachapuz 192.168.2.163
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_CLIENT_ID'] = 'flask_mqtt'
# app.config['MQTT_USERNAME'] = ''  # set the username here if you need authentication for the broker
# app.config['MQTT_PASSWORD'] = ''  # set the password here if the broker demands authentication
# set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_KEEPALIVE'] = 5
# set TLS to disabled for testing purposes
app.config['MQTT_TLS_ENABLED'] = False

mqtt = Mqtt(app)

topicOther = 'dataScienceDataX/ds002/attrs'
topicWeight = 'dataScienceData/ds001/attrs'

##### ROUTES #####
@app.route('/', methods=['GET'])
def routeRoot():
    return "POC - Generate Weighings"

@app.route('/version', methods=['GET'])
def versionApp():
    return "POC - Generate Weighings 2022"

@app.route('/status', methods=['GET'])
def appStatus():
    return CELL_ATTR.toJSON()

@app.route('/ready', methods=['GET'])
def routeReady():
    result = onInit()
    return result.toJSON()

@app.route('/weighing', methods=['POST']) #start and stop weighing
def routeGetWeighing():
    body = request.get_json()
    if 'status' not in body:
        result = "'status' is a mandatory attribute in payload msg"
    else:
        uuid = idGenerator()
        cellThread = Thread(target=continuousCellRequest, args=[uuid])
        cellThread.start()      
        result = continuousRequest(body['status'], uuid)

    return result

@app.route('/payload', methods=['POST'])
def routePayloadDataSet():
    body = request.get_json()
    if 'type' not in body:
        result = "'type' is a mandatory attribute in payload msg. type=0 weighing payload, type=1 cell attributes payload and type=2 is the last weighing object"
    else:
        if body['type'] == 0:
            result = objToJSON(PAYLOAD_W)
        elif body['type'] == 1:
            result = objToJSON(PAYLOAD_C)
        elif body['type'] == 2:
            result = OBJ_RES.toJSON()
    return result

@app.route("/test", methods=['GET']) #ONLY FOR TEST
def teste():
    result = scaleStatus()
    # cellDataProcessing()
    # cellClassify(objRes)
    return result


##### MQTT FUNCTIONS #####
def sendMsgUl(index, payload):
    global PAYLOAD_W, PAYLOAD_C
    if index == 1:
        mqtt.publish(topicWeight, payload)
        PAYLOAD_W.append(payload)
    elif index == 2:
        mqtt.publish(topicOther, payload[:-1])
        PAYLOAD_C.append(payload[:-1])
    else: 
        ""


##### STREAMING WEIGHING FUNCTIONS #####
def continuousRequest(action, eid):
    global START_STOP, PAYLOAD_W, OBJ_RES
    OBJ_RES.status = action
    START_STOP = action
    result = action
    if START_STOP == "start":             
        clear(2)              
        payload = WeighingID + "|" + eid + "|"
        result = startGrossVerify()
        if int(result) != 0:
            weightObj = Weight_Gross()
            weightObj.weighingId = eid
            weightObj.totalWeight = result
            OBJ_RES.payload.append(weightObj) #set the first object with first weight obtained in startGrossVerify function
            payload = payload + TotalWeight+ "|" + result
            sendMsgUl(1, payload) #sends the payload with first weight obtained in startGrossVerify function
            result = getWeight(eid) #continuous process of weighing 
            if len(PAYLOAD_W) > 0 & int(result) == 0:
                if OBJ_RES.status == "start":
                    print("SUCCESS")
                    OBJ_RES.status = "finished"
                    OBJ_RES.ul_payload = PAYLOAD_W
                    OBJ_RES.ul_payloadCell = PAYLOAD_C
                    OBJ_RES.quantity = str(len(CELL_ATTR.serialN))
                    cellDataProcessing()
                    result = OBJ_RES.toJSON()
        else:
            if OBJ_RES.status == "start":
                print("FINISHED WEIGHT 0")
                OBJ_RES.status = "finished_weight_zero"
                OBJ_RES.ul_payload = PAYLOAD_W
                OBJ_RES.ul_payloadCell = PAYLOAD_C
                OBJ_RES.quantity = str(len(CELL_ATTR.serialN))
                cellDataProcessing()
                result = OBJ_RES.toJSON()
    else:
        print("SUCCESSFULLY STOPPED")
        OBJ_RES.status = "stopped"
        OBJ_RES.ul_payload = PAYLOAD_W
        OBJ_RES.ul_payloadCell = PAYLOAD_C
        OBJ_RES.quantity = str(len(CELL_ATTR.serialN))
        cellDataProcessing()
        result = OBJ_RES.toJSON()
    return result


def startGrossVerify(): # Verify if weighing gross is 0 or not
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    cmd = 'SX'
    cmd2 = '\r\n'
    MESSAGE = (cmd.encode('ascii') + cmd2.encode('ascii'))
    s.send(MESSAGE)
    data = s.recv(BUFFER_SIZE)
    d = str(data)
    d = d[3:12].lstrip()
    # d = "20" #TEST VARIABLE
    count = 0
    while int(d) <= 0:
        if count >= 80:
            cmd = 'EX'
            MESSAGE = (cmd.encode('ascii') + cmd2.encode('ascii'))
            s.send(MESSAGE)
            s.close()
            return d            
        data = s.recv(BUFFER_SIZE)
        d = str(data)
        d = d[3:12].lstrip()
        count += 1 
        print("attempt: " + str(count) + " GROSS: " + d) # CMD waiting count verify
        if START_STOP != "start":
            count = 50
            break
    else:
        cmd = 'EX'
        MESSAGE = (cmd.encode('ascii') + cmd2.encode('ascii'))
        s.send(MESSAGE)
        s.close()
    return d


def getWeight(eid): # Get streaming weight and ends if gross hit 0
    global START_STOP, OBJ_RES  
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))  
    cmd = 'SX'
    cmd2 = '\r\n'
    MESSAGE = (cmd.encode('ascii') + cmd2.encode('ascii'))
    s.send(MESSAGE)
    data = s.recv(BUFFER_SIZE)
    d = str(data)
    d = d[3:12].lstrip()
    # d = "40" #TEST VARIABLE
    count = 0
    while int(d) > 0:        
        weightObj = Weight_Gross()
        #Set Ultralight payload
        payload = WeighingID + "|" + eid + "|"
        payload = payload + TotalWeight+ "|" + d
        sendMsgUl(1, payload)

        #Set object payload for the frond-end 
        weightObj.weighingId = eid
        weightObj.totalWeight = d
        OBJ_RES.payload.append(weightObj)

        data = s.recv(BUFFER_SIZE)
        d = str(data)
        d = d[3:12].lstrip()
        # d = str(int(d)+20) #TEST VARIABLE
        count += 1
        print(str(count) + ": " + payload)

        if START_STOP != "start":
            d = "0" 
            break
    else:
        payload = WeighingID + "|" + eid + "|"
        payload = payload + TotalWeight + "|" + d
        sendMsgUl(1, payload)
        cmd = 'EX'
        MESSAGE = (cmd.encode('ascii') + cmd2.encode('ascii'))
        s.send(MESSAGE)
        s.close()
    return d


##### GETTING LOADCELL ATTRIBUTES #####
def continuousCellRequest(eid):
    global CELL_ATTR
    start = time.time()
    if len(CELL_ATTR.serialN) == 0:
        CELL_ATTR = onInit()
    print("APP STATUS: " + CELL_ATTR.status)
    if CELL_ATTR.status == "Ready":
        cellAttrVerify(eid, CELL_ATTR.serialN)
    end = time.time()
    print(end - start)


def cellAttrVerify(eid, CSNArray):
    global OBJ_RES
    payload:string = ""
    cellTArray = requestCellStatus('DT')  # Pedido de temperatura  
    print("TEMPERATURE:")  
    print(cellTArray)
    cellVArray = requestCellStatus('DA') # Pedido de alimentação célula e extensometro
    print("VOLTAGE:")
    print(cellVArray)
    print("PROCESS STATUS : " + OBJ_RES.status)
    while OBJ_RES.status == "start":         
        payload:string = "" 
        cellPArray = requestCellStatus('DP')  # Pedido de pontos internos
        print("PONTOS:")
        print(cellPArray)
        for i, v in enumerate(CSNArray):
            objCell = Cell_Object()
            if i == 0:
                payload = WeighingID + "|" + eid + "|"
            else:
                payload = payload + WeighingID + "|" + eid + "|"                                  
            objCell.cellId = (i+1)
            objCell.weighingId = eid
            payload = payload + SerialNumber[i] + "|" + CSNArray[i] + "|" 
            objCell.serialNumber = CSNArray[i]
            payload = payload + Temperature[i] + "|" + cellTArray[i] + "|"
            objCell.temperature = cellTArray[i]
            payload = payload + ExternalPower[i] + "|" + cellVArray[i] + "|"
            objCell.voltage = cellVArray[i]  
            payload = payload + AngularCoefficient[i] + "|" + CELL_ATTR.cAngular[i] + "|"
            objCell.angularCoefficient = CELL_ATTR.cAngular[i]
            payload = payload + Firmware[i] + "|" + CELL_ATTR.firmware[i] + "|"  
            objCell.firmware = CELL_ATTR.firmware[i]         
            payload = payload + Point[i] + "|" + cellPArray[i] + "|" 
            objCell.point = cellPArray[i]   
            #Exclusive payload to the ge-weighings frontend (not needed in quanunmleap context)           
            payload = payload + Voltage[i] + "|" + cellVArray[i] + "|" 

            # classification = cellClassifyRecursive(cellPArray[i], cellTArray[i], cellVArray[i], CELL_ATTR.cAngular[i]) # Classificação a cada nova entrada de dados
            # objCell.classification = str(classification)
            result = cellWeightCalc(i, cellPArray[i], payload, objCell)          
            payload = result[0]
            objCell: Cell_Object = result[1]
            OBJ_RES.payloadCell.append(objCell)
        sendMsgUl(2, payload)


def cellWeightCalc(i, point, payload, objCell:Cell_Object):
    print("PONTOS: " + point[:-2] + " CP_0: " + CELL_ATTR.pointN[i][:-2])
    cellPoint = (int(point[:-2]) - int(CELL_ATTR.pointN[i][:-2]))
    coeffArray = CELL_ATTR.cAngular[i].split()
    # print(coeffArray)
    coeffValue = float(coeffArray[0].replace(',','.'))
    print("Coeficiente Angular: " + str(coeffValue))
    cellWeight = (cellPoint//5.7143) * coeffValue
    print("Peso célula: " + str(cellWeight))
    cellWeight = int(cellWeight)
    cellWeight = str(cellWeight)
    payload = payload + Weight[i] + "|" + cellWeight + "|"
    objCell.weight = cellWeight
    return [payload, objCell]
