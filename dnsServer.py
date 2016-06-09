#!/usr/bin/python
from __future__ import print_function
from json import dumps, loads
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from os import system
from threading import Thread, Event

PORT_NUMBER = 7979
DNS = dict()

UPDATE_PERIOD = 20 # in seconds

"""
alive is only stored in memory (as opposed to also being written to disk like DNS)
because it is refreshed periodically and would be stale by the time the
program has started again.
"""
alive = dict()



"""
Used for handling requests

Valid Requests:
  /hosts        print the entries in DNS
  /hostsalive   print the active entries in DNS
  /hostsjson    print the entries in DNS as JSON
  /ipaddr~name  update the entry for name with new ipaddr
"""
class RequestHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path == "/hosts":
      self.send_response(200)
      self.send_header('Content-type','text/plain')
      self.end_headers()
      self.wfile.write(strDNS(False))
      return
    if self.path == "/hostsalive":
      self.send_response(200)
      self.send_header('Content-type','text/plain')
      self.end_headers()
      self.wfile.write(strDNS(True))
      return
    if self.path == "/hostsjson":
      self.send_response(200)
      self.send_header('Access-Control-Allow-Origin', '*')
      self.send_header('Content-type','text/plain')
      self.end_headers()
      self.wfile.write(dumps(DNS))
      return
    if self.path == "/hostsalivejson":
      self.send_response(200)
      self.send_header('Content-type','text/plain')
      self.end_headers()
      self.wfile.write(dumps(getFilteredDNS()))
      return
    if "/" not in self.path or "~" not in self.path:
      self.send_response(400)
      self.send_header("Content-type","text/html")
      self.end_headers()
      self.wfile.write("Bad Request")
    else:
      _, getvars = self.path.split("/")
      ipaddr, hostname = getvars.split("~")
      self.send_response(200)
      self.send_header('Content-type','text/html')
      self.end_headers()
      self.wfile.write("Updating " + hostname + " to " + ipaddr)
      DNS[hostname] = ipaddr
      alive[hostname] = thread.ping(ipaddr)
      writeDNS()
    return

"""
Thread object to periodically update alive dict.
Once started, it runs every UPDATE_PERIOD seconds
and stops when the event (passed in as an arg)
is set.
Based on http://stackoverflow.com/a/12435256
"""
class AliveUpdaterThread(Thread):
  def __init__(self, event):
    Thread.__init__(self)
    self.stopped = event

  def run(self):
    updateAlive() #updates upon thread start
    while not self.stopped.wait(UPDATE_PERIOD):
      updateAlive()

  def ping(self, ipaddr):
    return pingHost(ipaddr)

"""
Updates alive dict
Depends on name and IP from DNS
"""
def updateAlive():
  print("updating alive")
  for hostname, ipaddr in DNS.iteritems():
    if pingHost(ipaddr):
      alive[hostname] = True
    else:
      alive[hostname] = False


"""
Creates a string representation of the DNS entries
Useful because you can append it to /etc/hosts
"""
def strDNS(checkAlive):
  ret = ""
  for hostname, ipaddr in DNS.iteritems():
    if checkAlive:
      if alive[hostname]:
        ret += ipaddr + "\t" + hostname + "\n"
    else:
        ret += ipaddr + "\t" + hostname + "\n"
  return ret

"""
Returns a filtered DNS list, only those that are alive
"""
def getFilteredDNS():
  ret = dict()
  for hostname, ipaddr in DNS.iteritems():
      if alive[hostname]:
          ret[hostname] = ipaddr
  return ret


"""
Serialized the current DNS entries as json
"""
def writeDNS():
  localDNS = open(".localDNS", "w+")
  print(dumps(DNS), file=localDNS)
  localDNS.close()

"""
Deserialize the DNS entries saved on disk
"""
def loadDNS():
  try:
    localDNS = open(".localDNS", "r")
  except IOError:
      return
  global DNS
  DNS = loads(localDNS.read())
  localDNS.close()

"""
Check if a host is alive
"""
def pingHost(ipaddr):
    print("pinging " + ipaddr + "...",)
    response = system("ping -c 1 -w 2 " + ipaddr + " > /dev/null")
    if response == 0:
      print(" success.")
      return True
    else:
      print(" failed.")
      return False

if __name__ == "__main__":
  try:
    server = HTTPServer(('', PORT_NUMBER), RequestHandler)
    loadDNS()
    print("Loaded previous DNS configuration")
    print(DNS)

    #initializes alive with False to prevent KeyError
    for hostname, ipaddr in DNS.iteritems():
        alive[hostname] = False

    stopFlag = Event() #signals a stop for AliveUpdaterThread

    thread = AliveUpdaterThread(stopFlag)
    thread.setDaemon(True)
    thread.start()

    print("Started DNS server on port" , PORT_NUMBER)
    server.serve_forever()

  except KeyboardInterrupt:
    print("^C received, shutting down the web server")
    stopFlag.set()
    server.socket.close()
