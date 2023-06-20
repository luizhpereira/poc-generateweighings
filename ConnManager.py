import socket

class CoonManager(object):
  def __init__(self):
    self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)

  def connStart(self, host, port):
    self._conn.connect((host, port))
  
  def connClose(self):
    self._conn.close()

  def connSend(self, msg):
    self._conn.send(msg)

  def connRes(self, buffer):
    self._conn.recv(buffer)