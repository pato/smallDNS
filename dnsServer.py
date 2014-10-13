#!/usr/bin/python
from __future__ import print_function
from json import dumps, loads
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

PORT_NUMBER = 7979
DNS = dict()

"""
Used for handling requests

Valid Requests:
  /hosts - print the entries in DNS
  /ipaddr|name - update the entry for name with new ipaddr
"""
class RequestHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path == "/hosts":
      self.send_response(200)
      self.send_header('Content-type','text/plain')
      self.end_headers()
      self.wfile.write(strDNS())
      return
    if self.path == "/hostsjson":
      self.send_response(200)
      self.send_header('Access-Control-Allow-Origin', '*')
      self.send_header('Content-type','text/plain')
      self.end_headers()
      self.wfile.write(dumps(DNS))
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
      writeDNS()
    return

"""
Creates a string representation of the DNS entries
Useful because you can append it to /etc/hosts
"""
def strDNS():
  ret = ""
  for hostname, ipaddr in DNS.iteritems():
    ret += ipaddr + "\t" + hostname + "\n"
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

if __name__ == "__main__":
  try:
    server = HTTPServer(('', PORT_NUMBER), RequestHandler)
    loadDNS()
    print("Loaded previous DNS configuration")
    print(DNS)
    print("Started DNS server on port" , PORT_NUMBER)
    server.serve_forever()
  except KeyboardInterrupt:
    print("^C received, shutting down the web server")
    server.socket.close()
