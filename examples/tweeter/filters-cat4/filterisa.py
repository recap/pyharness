__author__ = 'reggie'


###START-CONF
##{
##"object_name": "filterisa",
##"object_poi": "qpwo-2345",
##"parameters": [
##                 {
##                      "name": "tweet",
##                      "description": "english tweets",
##                      "required": true,
##                      "type": "TweetString",
##                      "format": "",
##                      "state" : "ENGLISH"
##                  }
##              ],
##"return": [
##              {
##                      "name": "tweet",
##                      "description": "has a relation  tweet",
##                      "required": true,
##                      "type": "TweetString",
##                      "format": "",
##                      "state" : "ISA|NO_ISA"
##                  }
##
##          ] }
##END-CONF



import re

from pumpkin import PmkSeed


class filterisa(PmkSeed.Seed):

    def __init__(self, context, poi=None):
        PmkSeed.Seed.__init__(self, context,poi)
        pass

    def on_load(self):
        print "Loading: " + self.__class__.__name__
        pass


    def run(self, pkt, tweet):
        m = re.search('W(\s+)(.*)(\n)', tweet, re.S)
        if m:
            tw = m.group(2)
            if not self.is_a(tw):
                self.dispatch(pkt, tweet, "NO_ISA")
                pass
            else:
                self.dispatch(pkt, self.is_a(tw), "ISA")

        pass


    def is_a(self,text):
        m = re.search('([A-Z]+[A-Za-z]+\s*[A-Za-z]*\s(is an|is a)\s[A-Z]+[A-Za-z]+\s[A-Z]*[A-Za-z]*)', text, re.S)
        if m:
            tw = m.group(0)
            return tw
        return False