"""This module implements the TFTP Server functionality. Instantiate an
instance of the server, and then run the listen() method to listen for client
requests. Logging is performed via a standard logging object set in
TftpShared."""

import os, time, socket
import select
from TftpShared import *
from TftpPacketTypes import *
from TftpPacketFactory import TftpPacketFactory
from TftpContexts import TftpContextServer

class TftpMessageQueue(TftpSession):
    """This class implements a tftp server object. Run the listen() method to
    listen for client requests.  It takes two optional arguments. tftproot is
    the path to the tftproot directory to serve files from and/or write them
    to. dyn_file_func is a callable that must return a file-like object to
    read from during downloads. This permits the serving of dynamic
    content."""

    def __init__(self, tftproot='/tftpboot', dyn_file_func=None):
        self.listenip = None
        self.listenport = None
        self.sock = None
        # FIXME: What about multiple roots?
        self.root = os.path.abspath(tftproot)
        self.dyn_file_func = dyn_file_func
        # A dict of sessions, where each session is keyed by a string like
        # ip:tid for the remote end.
        self.sessions = {}

        self.shutdown_gracefully = False
        self.shutdown_immediately = False

        if self.dyn_file_func:
            if not callable(self.dyn_file_func):
                raise TftpException, "A dyn_file_func supplied, but it is not callable."
        elif os.path.exists(self.root):
            log.debug("tftproot %s does exist" % self.root)
            if not os.path.isdir(self.root):
                raise TftpException, "The tftproot must be a directory."
            else:
                log.debug("tftproot %s is a directory" % self.root)
                if os.access(self.root, os.R_OK):
                    log.debug("tftproot %s is readable" % self.root)
                else:
                    raise TftpException, "The tftproot must be readable"
                if os.access(self.root, os.W_OK):
                    log.debug("tftproot %s is writable" % self.root)
                else:
                    log.warning("The tftproot %s is not writable" % self.root)
        else:
            raise TftpException, "The tftproot does not exist."

    def bytes2addr( self, bytes ):
        """Convert a hash to an address pair."""
        if len(bytes) != 6:
                raise ValueError, "invalid bytes"
        host = socket.inet_ntoa( bytes[:4] )
        port, = struct.unpack( "H", bytes[-2:] )
        return host, port

    def bytes2addrIP( self, bytes ):
        """Convert a hash to an address pair."""
        if len(bytes) != 6:
                raise ValueError, "invalid bytes"
        host = socket.inet_ntoa( bytes[:4] )
        return host

    def bytes2addrPort( self, bytes ):
        """Convert a hash to an address pair."""
        if len(bytes) != 6:
                raise ValueError, "invalid bytes"
        port, = struct.unpack( "H", bytes[-2:] )
        return port

    def declare(self,
			qname):
	fileqname = self.root + "/" + qname
	fileobj = open(fileqname, "wb");
	pass

    def open(self,
             rvserverip="",
             rvserverport=DEF_RVSERVER_PORT,
	     rvserverpool="23",
	     timeout=SOCK_TIMEOUT):
	"""This function is used to connect TFTP in a P2P mode. The open() function connects to a rendezvous server for exchanging IP and 
	port number. The open() will receive the peer's IP and UDP PORT and communication can start. This method should traverse most
	NATs and firwalls."""
	tftp_factory = TftpPacketFactory()
        rvmaster = (rvserverip, int(rvserverport))
        try:
	  self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	  self.sock.sendto(rvserverpool, rvmaster)
	  data, addr = self.sock.recvfrom(len(rvserverpool)+3 )
	  if data != "ok "+rvserverpool:
          	log.error("Unable to request!")
          	sys.exit(1)
          self.sock.sendto("ok", rvmaster)
          data, addr = self.sock.recvfrom( 6 )
          target = self.bytes2addr(data)
	  #self.sock.setalttarget(target)
          log.info("Connected to %s:%d" % target)
	  #ip = self.bytes2addrIP(data)
	  #port = self.bytes2addrPort(data)
	  #ip, port = self.sock.getpeername()
	  #log.debug("IP is %s" % ip)
	  #log.debug("Port is %d" % port) 
	  #self.sock.bind(('145.18.220.16', 57004))
	  #self.sock.sendtoalt('#HAIL#')

            #time.sleep(1)
            #self.sock.sendto('#HAIL#',target)
          #self.sock.sendto('OK',target)
          #time.sleep(1)
          #self.sock.sendto('OK',target)
	  
        except socket.error, err:
            # Reraise it for now.
            raise
        log.info("Starting receive loop...")
        while True:
            if self.shutdown_immediately:
                log.warn("Shutting down now. Session count: %d" % len(self.sessions))
                self.sock.close()
                for key in self.sessions:
                    self.sessions[key].end()
                self.sessions = []
                break

            elif self.shutdown_gracefully:
                if not self.sessions:
                    log.warn("In graceful shutdown mode and all sessions complete.")
                    self.sock.close()
                    break

            # Build the inputlist array of sockets to select() on.
            inputlist = []
            inputlist.append(self.sock)
	    connections = {}
	    connections[self.sock] = target
            
            for key in self.sessions:
                inputlist.append(self.sessions[key].sock)

            # Block until some socket has input on it.
            log.debug("Performing select on this inputlist: %s" % inputlist)
            readyinput, readyoutput, readyspecial = select.select(inputlist,
                                                                  [],
                                                                  [],
                                                                  SOCK_TIMEOUT)

            deletion_list = []

            # Handle the available data, if any. Maybe we timed-out.
            for readysock in readyinput:
		log.debug("here 1")
                # Is the traffic on the main server socket? ie. new session?
                if readysock == self.sock:
                    log.debug("Data ready on our main socket")
                    buffer, (raddress, rport) = self.sock.recvfrom(MAX_BLKSIZE)

                    log.debug("Read %d bytes" % len(buffer))

                    if self.shutdown_gracefully:
                        log.warn("Discarding data on main port, in graceful shutdown mode")
                        continue

                    # Forge a session key based on the client's IP and port,
                    # which should safely work through NAT.
                    key = "%s:%s" % (raddress, rport)

                    if not self.sessions.has_key(key):
                        log.debug("Creating new server context for "
                                     "session key = %s" % key)
                        self.sessions[key] = TftpContextServer(raddress,
                                                               rport,
                                                               timeout,
                                                               self.root,
                                                               self.dyn_file_func,
							       self.sock)
                        try:
                            self.sessions[key].start(buffer)
                        except TftpException, err:
                            deletion_list.append(key)
                            log.error("Fatal exception thrown from "
                                      "session %s: %s" % (key, str(err)))
                    else:
                        log.warn("received traffic on main socket for "
                                 "existing session??")
                    log.info("Currently handling these sessions:")
                    for session_key, session in self.sessions.items():
                        log.info("    %s" % session)

                else:
                    # Must find the owner of this traffic.
                    for key in self.sessions:
                        if readysock == self.sessions[key].sock:
                            log.info("Matched input to session key %s"
                                % key)
                            try:
                                self.sessions[key].cycle()
                                if self.sessions[key].state == None:
                                    log.info("Successful transfer.")
                                    deletion_list.append(key)
                            except TftpException, err:
                                deletion_list.append(key)
                                log.error("Fatal exception thrown from "
                                          "session %s: %s"
                                          % (key, str(err)))
                            # Break out of for loop since we found the correct
                            # session.
                            break

                    else:
                        log.error("Can't find the owner for this packet. "
                                  "Discarding.")

	    log.debug("Looping on idle sessions to send HAIL packets")
	    for sok in connections:
	    	log.debug("Hailing %s:%d" % connections[sok])
	    	sok.sendto("OK", connections[sok] )
		

            log.debug("Looping on all sessions to check for timeouts")
            now = time.time()
            for key in self.sessions:
		log.debug("here 2")
                try:
                    self.sessions[key].checkTimeout(now)
                except TftpTimeout, err:
                    log.error(str(err))
                    self.sessions[key].retry_count += 1
                    if self.sessions[key].retry_count >= TIMEOUT_RETRIES:
                        log.debug("hit max retries on %s, giving up"
                            % self.sessions[key])
                        deletion_list.append(key)
                    else:
                        log.debug("resending on session %s"
                            % self.sessions[key])
                        self.sessions[key].state.resendLast()

            log.debug("Iterating deletion list.")
            for key in deletion_list:
                log.info('')
                log.info("Session %s complete" % key)
                if self.sessions.has_key(key):
                    log.debug("Gathering up metrics from session before deleting")
                    self.sessions[key].end()
                    metrics = self.sessions[key].metrics
                    if metrics.duration == 0:
                        log.info("Duration too short, rate undetermined")
                    else:
                        log.info("Transferred %d bytes in %.2f seconds"
                            % (metrics.bytes, metrics.duration))
                        log.info("Average rate: %.2f kbps" % metrics.kbps)
                    log.info("%.2f bytes in resent data" % metrics.resent_bytes)
                    log.info("%d duplicate packets" % metrics.dupcount)
                    log.debug("Deleting session %s" % key)
                    del self.sessions[key]
                    log.debug("Session list is now %s" % self.sessions)
                else:
                    log.warn("Strange, session %s is not on the deletion list"
                        % key)

        log.debug("server returning from while loop")
        self.shutdown_gracefully = self.shutdown_immediately = False
	return
	   

    def stop(force=False):
        """Stop the server gracefully. Do not take any new transfers,
        but complete the existing ones. If force is True, drop everything
        and stop. Note, immediately will not interrupt the select loop, it
        will happen when the server returns on ready data, or a timeout.
        ie. SOCK_TIMEOUT"""
        if force:
            log.info("Server instructed to shut down immediately.")
            self.shutdown_immediately = True
        else:
            log.info("Server instructed to shut down gracefully.")
            self.shutdown_gracefully = True