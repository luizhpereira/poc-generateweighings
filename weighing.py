from array import array
import json
import string

class Cell_Ready: #Check App Status Object, Scale at Weight 0
  def __init__(self):
    self.status:string = "NotReady"
    self.error:string = ""
    self.serialN:array = []
    self.pointN:array = []
    self.firmware:array = []
    self.cAngular:array = []

  def toJSON(self):
      return json.dumps(self, default=lambda o: o.__dict__)


class Object_Response: #Weighing Process Object Response
  def __init__(self):
    self.quantity = ""
    self.status:string = "start"
    self.ul_payload:string = ""
    self.ul_payloadCell:string = ""
    self.payload = []
    self.payloadCell = []

  def toJSON(self):
      return json.dumps(self, default=lambda o: o.__dict__)
  

class Cell_Object:
  def __init__(self):    
    self.cellId = ""
    self.classification = ""
    self.weighingId = ""
    self.serialNumber = ""    
    self.temperature = ""
    self.voltage = ""      
    self.angularCoefficient = ""
    self.firmware = ""
    self.point = ""  
    self.weight = ""

  def toJSON(self):
      return json.dumps(self, default=lambda o: o.__dict__)


class Cell_Classify:
  def __init__(self): 
    self.cellId = ""
    self.point = []
    self.weight = []
    self.temp = [] 
    self.voltage5 = []
    self.voltage12 = []
    self.angularCoefficient0 = []
    self.angularCoefficient1 = []
    self.temp_avg = ""
    self.temp_min = ""
    self.temp_max = ""
    self.angularCoefficient0_avg = ""
    self.angularCoefficient1_avg = ""
    self.angularCoefficient0_min = ""
    self.angularCoefficient1_min = ""
    self.angularCoefficient0_max = ""
    self.angularCoefficient1_max = ""
    self.voltage5_avg = ""
    self.voltage5_min = ""
    self.voltage5_max = ""
    self.voltage12_avg = ""
    self.voltage12_min = ""
    self.voltage12_max = ""
    self.point_avg = ""
    self.point_min = ""
    self.point_max = ""
    self.weight_avg = ""
    self.weight_min = ""
    self.weight_max = ""  

  def toJSON(self):
      return json.dumps(self, default=lambda o: o.__dict__)


class Weight_Gross:
  def __init__(self):
    self.weighingId = ""
    self.totalWeight = ""

  def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)