# from weighing import Weighing
from statistics import mean
import pickle, warnings, socket, uuid, json, time
from labbels import *
from weighing import *

warnings.filterwarnings("ignore")

#Socket config
TCP_IP = '192.168.2.70'
TCP_PORT = 6001  # Porta aberta no terminal -> por defeito sempre 6001
TCP_PORT2 = 6002 # Porta aberta no terminal -> para obter atributos célula à célula
BUFFER_SIZE = 10240

#Global
FLASK_ADDRESS = '192.168.1.80'
FLASK_PORT = 5555
START_STOP = ""
PAYLOAD_W = []
PAYLOAD_C = []
G_EID = ""
CELL_ATTR = Cell_Ready()
OBJ_RES = Object_Response()

def onInit():    
    start = time.time()    
    clear(1)
    global CELL_ATTR 
    CELL_ATTR.serialN = requestCellStatus('DM')  # Pedido N/S célula e carta de pesagem
    cellObj = scaleStatus()
    count = 0
    while int(cellObj[0]) != 0:        
        cellObj = scaleStatus()
        count += 1
        if count > 20:
            CELL_ATTR.status = "Failure"
            CELL_ATTR.error = "Weight is not 0 on the scale"
            break
    if int(cellObj[0]) == 0:
        CELL_ATTR.pointN = requestCellStatus('DP')  # Pedido de pontos internos  
        CELL_ATTR.firmware = requestCellStatus('DV')  # Pedido de versão software            
        CELL_ATTR.cAngular = requestCellStatus('DC') # Pedido Coeficiente de ajuste célula e carta de pesagem
        if int(len(CELL_ATTR.pointN)) > 0:            
            CELL_ATTR.status = "Ready" 
    end = time.time()
    print(end - start)
    return CELL_ATTR


def requestCellStatus(inputCMD):
    result = []
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT2))
    cmd = 'DN' + '\r\n'
    MESSAGE = (cmd.encode('ascii'))
    s.send(MESSAGE)
    data = s.recv(BUFFER_SIZE)
    cell_tot = int(data) + 1
    n_cell = 1
    while n_cell != cell_tot:
        cell = str(n_cell)
        cmd = inputCMD + cell + '\r\n'
        MESSAGE = (cmd.encode('ascii'))
        s.send(MESSAGE)
        data = s.recv(BUFFER_SIZE)
        d = str(data.strip())
        d = d[2:-1]
        while b'\n' not in data:
            data = data + s.recv(BUFFER_SIZE)
            d = data
        else:
            result.append(d[0:35])
        n_cell += 1
    s.close()
    return result


def cellStatus():
    dataObject = {}
    result = requestCellStatus('DM')  # Pedido N/S célula e carta de pesagem
    print('N/S célula')
    print(result)
    dataObject['serial'] = result

    result = requestCellStatus('DP')  # Pedido de pontos internos
    print('Pontos internos')
    print(result)
    dataObject['point'] = result

    result = requestCellStatus('DT')  # Pedido de temperatura
    print('Temperatura (ºC)')
    print(result)
    dataObject['temperature'] = result

    # Pedido de alimentação célula e extensometro
    result = requestCellStatus('DA')
    print('Alimentação externa (V)')
    print(result)
    dataObject['externalpower'] = result

    # Pedido Coeficiente de ajuste célula e carta de pesagem
    result = requestCellStatus('DC')
    print('Coeficiente angular celula e terminal')
    print(result)
    dataObject['angularcoefficient'] = result

    result = requestCellStatus('DV')  # Pedido de versão software
    print('Ver. Software')
    print(result)
    dataObject['firmware'] = result
    # print ("\r\nEscrever Ler() para obter peso ou Celulas() para dados das células")
    return dataObject


def scaleStatus():
    result = []
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    cmd = 'Xn'
    cmd2 = '\r\n'
    MESSAGE = (cmd.encode('ascii') + cmd2.encode('ascii'))
    s.send(MESSAGE)
    data = s.recv(BUFFER_SIZE)
    d = str(data)
    while b'\n' not in data:
        data = data + s.recv(BUFFER_SIZE)
        d = data
    else:
        print("Peso: ", d[3:11].lstrip())
        result.append(d[3:11].lstrip())
        print("Estado balança: ", d[15:19].lstrip())
        result.append(d[15:19].lstrip())
    s.close()
    return result


def idGenerator():
    id = uuid.uuid4()
    return str(id)


def objToJSON(obj):
    to_json = json.dumps(obj)
    return to_json


def clear(option):
    global CELL_ATTR, OBJ_RES, G_EID, PAYLOAD_C, PAYLOAD_W
    if option == 0:
        G_EID = ""
    elif option == 1:
        PAYLOAD_C= []
        PAYLOAD_W = []
        CELL_ATTR.status = "NotReady"
        CELL_ATTR.error = ""
        CELL_ATTR.pointN = []
        CELL_ATTR.serialN = []
        CELL_ATTR.firmware =[]
        CELL_ATTR.cAngular =[]
    elif option == 2:
        PAYLOAD_C= []
        PAYLOAD_W = [] 
        OBJ_RES.payload = []
        OBJ_RES.ul_payload = ""
        OBJ_RES.payloadCell = []
        OBJ_RES.ul_payloadCell = ""
  

##### CLASSIFICATION #####
def cellClassifyRecursive(point, temp, voltage, coefficient):
    data = []
    attrs = []
    km_model = pickle.load(open("PMKM.sav", 'rb'))
    scaler = pickle.load(open('MAXMIN.sav', 'rb'))
    voltArray = voltage.split()
    coeffArray = coefficient.split() 
    attrs.append(float(point.replace(',','.')))
    attrs.append(float(temp.replace(',','.'))) 
    attrs.append(float(voltArray[0].replace(',','.')))
    attrs.append(float(voltArray[1].replace(',','.')))
    attrs.append(float(coeffArray[0].replace(',','.')))
    attrs.append(float(coeffArray[1].replace(',','.')))
    data.append(attrs)
    # data.append([12416.194170,5.000000,5.0,5.0,0.99931,0.99967]) #ERROR TEST VARIABLE    
    data = scaler.transform(data)   
    prediction = km_model.predict(data)
    output = prediction[0]
    return output


def setPrediction(indice, classificacao):
        global OBJ_RES
        objCell:Cell_Object
        for objCell in OBJ_RES.payloadCell:
            if objCell.cellId == indice:
                objCell.classification = classificacao


def cellDataProcessing():  
    cellObj = {}
    for i, v in enumerate(CELL_ATTR.serialN):
        cellObj[(i+1)] = []
    for i, v2 in enumerate(OBJ_RES.payloadCell):
        cellObj[v2.cellId].append(v2)
    cellClassify(cellObj)    


def cellClassify(cellObj):
    rf_model = pickle.load(open("RandomForest_v2.sav", 'rb'))
    scaler = pickle.load(open('scalling_model_v2.sav', 'rb'))
    for i in cellObj:
        Cls_Obj = Cell_Classify()
        for cell in cellObj[i]:
            Cls_Obj.cellId = i
            voltArray = cell.voltage.split()
            coeffArray = cell.angularCoefficient.split()
            Cls_Obj.point.append(float(cell.point.replace(',','.')))  
            Cls_Obj.weight.append(float(cell.weight.replace(',', '.')))  
            Cls_Obj.temp.append(float(cell.temperature.replace(',','.')))     
            Cls_Obj.angularCoefficient0.append(float(coeffArray[0].replace(',', '.')))
            Cls_Obj.angularCoefficient1.append(float(coeffArray[1].replace(',', '.')))
            Cls_Obj.voltage12.append(float(voltArray[0].replace(',', '.')))
            Cls_Obj.voltage5.append(float(voltArray[1].replace(',', '.')))

        Cls_Obj.point_min = min(Cls_Obj.point)
        Cls_Obj.point_avg = mean(Cls_Obj.point)
        Cls_Obj.point_max = max(Cls_Obj.point)
        Cls_Obj.temp_min = min(Cls_Obj.temp)
        Cls_Obj.temp_avg = mean(Cls_Obj.temp)
        Cls_Obj.temp_max = max(Cls_Obj.temp)
        Cls_Obj.weight_min = min(Cls_Obj.weight)
        Cls_Obj.weight_avg = mean(Cls_Obj.weight)
        Cls_Obj.weight_max = max(Cls_Obj.weight)
        Cls_Obj.voltage12_min = min(Cls_Obj.voltage12)
        Cls_Obj.voltage12_avg = mean(Cls_Obj.voltage12)
        Cls_Obj.voltage12_max = max(Cls_Obj.voltage12)
        Cls_Obj.voltage5_min = min(Cls_Obj.voltage5)
        Cls_Obj.voltage5_avg = mean(Cls_Obj.voltage5)
        Cls_Obj.voltage5_max = max(Cls_Obj.voltage5)
        Cls_Obj.angularCoefficient0_min = min(Cls_Obj.angularCoefficient0)
        Cls_Obj.angularCoefficient0_avg = mean(Cls_Obj.angularCoefficient0)
        Cls_Obj.angularCoefficient0_max = max(Cls_Obj.angularCoefficient0)
        Cls_Obj.angularCoefficient1_min = min(Cls_Obj.angularCoefficient1)
        Cls_Obj.angularCoefficient1_avg = mean(Cls_Obj.angularCoefficient1)
        Cls_Obj.angularCoefficient1_max = max(Cls_Obj.angularCoefficient1) 

        data = []
        data = [Cls_Obj.angularCoefficient0_max, Cls_Obj.angularCoefficient1_max, Cls_Obj.point_max, Cls_Obj.temp_max, Cls_Obj.voltage12_max, Cls_Obj.voltage5_max, Cls_Obj.weight_max,
        Cls_Obj.angularCoefficient0_avg, Cls_Obj.angularCoefficient1_avg, Cls_Obj.point_avg, Cls_Obj.temp_avg, Cls_Obj.voltage12_avg, Cls_Obj.voltage5_avg, Cls_Obj.weight_avg,
        Cls_Obj.angularCoefficient0_min, Cls_Obj.angularCoefficient1_min, Cls_Obj.point_min, Cls_Obj.temp_min, Cls_Obj.voltage12_min, Cls_Obj.voltage5_min, Cls_Obj.weight_min]
        
        dataArray = []
        dataArray.append(data)

        data = scaler.transform(dataArray)   
        prediction = rf_model.predict(data)   
        output = int(prediction[0])    
        setPrediction(i, output)
