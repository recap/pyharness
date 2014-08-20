__author__ = 'reggie'


###START-CONF
##{
##"object_name": "tracula",
##"object_poi": "tracula-1234",
##"auto-load": true,
##"parameters": [
##                  {
##                      "name": "tracula_input",
##                      "type": "Composite",
##                      "state" : "MRI_BRAINSEGMENT&DTI_PREPROC&DTI_FIBER"
##                  }
## ],
##"return": [
##              {
##                      "name": "tracula_ouput",
##                      "type": "Composite",
##                      "state" : "BRAIN_REGION_TRACK"
##               }
##
##          ] }
##END-CONF



from subprocess import call
from pumpkin import *

class tracula(PmkSeed.Seed):

    def __init__(self, context, poi=None):
        PmkSeed.Seed.__init__(self, context,poi)
        self.home = os.path.expanduser("~")+"/"
        self.wd = self.context.getWorkingDir()
        self.script = "tracula.sh"
        self.dav_rel = "/traculadav/"
        self.dav_dir = self.home+self.dav_rel


        # self.state_tr = {}
        # self.state_tr["MRI_BRAINSEGMENT"] = False
        # self.state_tr["DTI_PREPROC"] = False
        # self.state_tr["DTI_FIBER"] = False
        #
        # self.ifiles = {}
        # self.ifiles["MRI_BRAINSEGMENT"] = None
        # self.ifiles["DTI_PREPROC"] = None
        # self.ifiles["DTI_FIBER"] = None

        self.patients = {}


        pass



    def state_barrier(self, id):
        s = True
        if id in self.patients.keys():
            state_tr = self.patients[id][0]
            for k in state_tr.keys():
                if state_tr[k] == False:
                    s = False
                    break
        else:
            s= False

        return s

    def new_patient(self, id):
        state_tr = {}
        state_tr["MRI_BRAINSEGMENT"] = False
        state_tr["DTI_PREPROC"] = False
        state_tr["DTI_FIBER"] = False

        ifiles = {}
        ifiles["MRI_BRAINSEGMENT"] = None
        ifiles["DTI_PREPROC"] = None
        ifiles["DTI_FIBER"] = None

        if id not in self.patients.keys():
            self.patients[id] = []
            self.patients[id].append(copy.copy(state_tr))
            self.patients[id].append(copy.copy(ifiles))


        return (self.patients[id][0], self.patients[id][1])




    def run(self, pkt, data):

        ship_id = self.get_ship_id(pkt)
        stag = self.get_last_stag(pkt)

        state_tr, ifiles = self.new_patient(ship_id)

        state_tr[stag] = True
        ifiles[stag] = self.copy_file_to_wd(data[0])

        if self.state_barrier(ship_id):
            print "Go Ahead"

            script_path = self.wd+self.copy_file_to_wd(self.dav_dir+self.script, 0755)
            conf_file = self.wd+self.copy_file_to_wd(self.dav_dir+"tracula.conf", 0644)

            output_file = "output-"+self.get_name()+"-"+ship_id+".tar.gz"

            call([script_path, "-config_file", conf_file,\
                  "-freesurfer_data", ifiles["MRI_BRAINSEGMENT"],\
                  "-predti_data", ifiles["DTI_PREPROC"],\
                  "-bedpostx_data", ifiles["DTI_FIBER"],\
                  "-outfile", output_file,\
                  "-fsversion","5.3.0",\
                  "-fsl_version", "5.0.5"], cwd=self.context.getWorkingDir())


            dav_wd = self.dav_dir+ship_id
            dav_re = self.dav_rel+ship_id
            self._ensure_dir(dav_wd)
            shutil.move(self.wd+"/"+output_file,dav_wd+"/"+output_file)

            message = dav_re+"/"+output_file

            print "RESULT: "+message

            #self.dispatch(pkt, message, "DTI_FIBER")
        pass
