__author__ = 'reggie'
import re
import threading
from threading import *
from socket import *
import PmkSeed

from PmkShared import *


class Head(object):

    def __init__(self, header):
        self.params_hash = {}
        self.params_list = []
        self.params_string = ""
        hd = re.findall(r"(GET|POST) (?P<value>.*?)\s", header)
        if len(hd[0][1].split("?")) > 1:
            parlist = hd[0][1].split("?")[1].split("&")
            for p in parlist:
                key = p.split("=")[0]
                value = p.split("=")[1]
                self.params_hash[key] = value
                self.params_list.append(value)
                self.params_string += str(value)+","

            self.params_string = self.params_string[:-1]

        serv = hd[0][1].split("?")[0].split("/")
        self.module = serv[len(serv)-2]
        self.method = serv[len(serv)-1]




class HttpServer(SThread):


    def __init__(self, context):
        SThread.__init__(self)
        self.context = context
        pass

    def run(self):

        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(5)
        s.bind((HTTP_TCP_IP, HTTP_TCP_PORT))
        s.listen(1)
        while 1:
            try:
                conn, addr = s.accept()
            except timeout:
                log.debug("Timeout")
                if self.stopped():
                    log.debug("Exiting thread "+self.__class__.__name__)
                    break
                else:
                    log.debug("HTTP timeout")
                    continue
            log.debug('HTTP Connection address:'+ str(addr))

            data = conn.recv(HTTP_BUFFER_SIZE)
            if not data: break
            log.debug("HTTP data: "+data)
            if "favicon" in data:
                conn.close()
                continue

            h = Head(data)
            if h.module in PmkSeed.hplugins.keys():
                klass = PmkSeed.hplugins[h.module](self.context)
                klass.on_load()
                if not h.params_string:
                    rt = getattr(klass, h.method)()
                else:
                    rt = getattr(klass, h.method)(h.params_string)
                #rt = klass.run(h.params_string)
                print rt
                conn.send(str(rt))
            else:
                log.warn("Trying to invoke module with HTTP: "+h.module+" but doe not exist.")

            conn.close()
        pass


