__author__ = 'reggie'


from PmkExternalDispatch import *
from PmkInternalDispatch import *

from PmkProcessGraph import *

class MainContext(object):
    def __init__(self,uuid, peer=None):
        self.__uuid = uuid
        self.__peer = peer
        self.__attrs = None
        self.__supernodes = []
        self.__threads = []
        self.rx = rx()
        self.tx = tx()
        self.registry = {}
        self.__ip = "127.0.0.1"
        self.endpoints = []
        self.__reg_update = False
        self.rlock = threading.RLock()
        self.proc_graph = ProcessGraph()
        self.__exec_context = None


        pass


    def setExecContext(self, cntx):
        self.__exec_contex = cntx
        pass
    def getExecContext(self):
        return self.__exec_contex

    def setLocalIP(self,ip):
        self.__ip = ip

        #FIXME dynamic configuration
        #self.endpoints.append( ("ipc://"+self.getUuid(), "zmq.ipc", "zmq.PULL" ) )
        #self.endpoints.append( ("ipc://"+self.getUuid(), "zmq.ipc", "zmq.PUB" ) )
        #self.endpoints.append(("tcp://"+str(ip)+":"+str(ZMQ_ENDPOINT_PORT), "zmq.tcp", "zmq.PULL"))

        pass

    def getEndpoint(self):
        if self.__attrs.eptype == "zmq.TCP":
            return "tcp://"+str(self.__ip)+":"+str(ZMQ_ENDPOINT_PORT)
        if self.__attrs.eptype == "zmq.IPC":
            return "ipc:///tmp/"+self.getUuid()

    def hasRx(self):
        return self.__attrs.rxdir

    def singleSeed(self):
        return self.__attrs.singleseed

    def getLocalIP(self):
        return self.__ip

    def getProcGraph(self):
        return self.proc_graph

    def funcExists(self, func_name):
        if func_name in self.registry.keys():
            return True

        return False

    def setAttributes(self, attributes):
        self.__attrs = attributes
        if attributes.debug:
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)

        epm = attributes.epmode
        ept = attributes.eptype
        prot = ept.split('.')[1].lower()
        if prot == "tcp":
            s = prot+"://"+self.__ip+":"+str(ZMQ_ENDPOINT_PORT)
        if prot == "ipc":
            s = prot+":///tmp/"+self.getUuid()
        if prot == "inproc":
            s = prot+"://"+self.getUuid()

        self.endpoints.append( (s, ept, epm) )

    def getUuid(self):
        return self.__uuid

    def getPeer(self):
        return self.__peer

    def getTaskDir(self):
        return self.__attrs.taskdir

    def hasShell(self):
        return self.__attrs.shell

    def isSupernode(self):
        return self.__attrs.supernode

    def isWithNoPlugins(self):
        return self.__attrs.noplugins

    def setSupernodeList(self, sn):
        self.__supernodes = sn

    def getSupernodeList(self):
        return self.__supernodes

    def addThread(self, th):
        self.__threads.append(th)

    def getThreads(self):
        return self.__threads

    def setMePeer(self, peer):
        self.__peer = peer

    def getMePeer(self):
        return self.__peer

    def getRx(self):
        return self.rx

    def getTx(self):
        return self.tx








