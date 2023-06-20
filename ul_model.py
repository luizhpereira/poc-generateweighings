from labbels import *
from util import *


def weighingStart():
    wUL = ""

    ### SET TotalWeight e WeighingID ###
    scaleArray = scaleStatus()  # GET Total Weight e Scale Status
    wUL += WeighingID + "|" + "w0003" + "|"
    wUL += ScaleStatus + "|" + scaleArray[1] + "|"
    wUL += TotalWeight + "|" + scaleArray[0] + "|"

    # Pedido Coeficiente de ajuste célula e carta de pesagem
    result = requestCellStatus('DC')
    print('Coeficiente angular celula e terminal')
    print(result)
    wUL = setCellsAttrs(wUL, ATTR_AC, AngularCoefficient, result)

    # Pedido de alimentação célula e extensometro
    result = requestCellStatus('DA')
    print('Alimentação externa (V)')
    print(result)
    wUL = setCellsAttrs(wUL, ATTR_EP, ExternalPower, result)

    result = requestCellStatus('DV')  # Pedido de versão software
    print('Ver. Software')
    print(result)
    wUL = setCellsAttrs(wUL, ATTR_F, Firmware, result)

    result = requestCellStatus('DP')  # Pedido de pontos internos
    print('Pontos internos')
    print(result)
    wUL = setCellsAttrs(wUL, ATTR_P, Point, result)

    result = requestCellStatus('DM')  # Pedido N/S célula e carta de pesagem
    print('N/S célula')
    print(result)
    wUL = setCellsAttrs(wUL, ATTR_SN, SerialNumber, result)

    result = requestCellStatus('DT')  # Pedido de temperatura
    print('Temperatura (ºC)')
    print(result)
    wUL = setCellsAttrs(wUL, ATTR_T, Temperature, result)

    print('Conversão de pontos em peso')
    wUL = setCellsAttrs(wUL, ATTR_W, Weight, result)

    return wUL[:-1]


def setCellsAttrs(input, attr, ulArray, result):
    n_cells = (int(len(result))+1)
    count = 1
    while count < n_cells:
        input += ulArray[count-1] + "|" + result[count-1] + "|"
        count += 1
    else:
        return input
