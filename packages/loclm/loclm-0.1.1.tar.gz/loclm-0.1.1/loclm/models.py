from loclm.query2sequence import *
from loclm.sentence2query import *

import pickle
class Model():
    def __init__(self):
        self.pklfile = ""
            
    def predict(self, inputqry):
        with open(self.pklfile, 'rb') as file:
            model = pickle.load(file)
        return model.predict(inputqry)
    
class Qry2Seqmodel(Model):
    def __init__(self, model_name):
        if model_name == 'cellmech':
            self.pklfile = 'loclm/q2smodel.pkl'
        
class Sen2Qrymodel(Model):
    def __init__(self, model_name):
        if model_name == 'cellmech':
            self.pklfile = 'loclm/s2qmodel.pkl'
    
# with open('q2smodel.pkl', 'rb') as file:
#     q2smodel = pickle.load(file)
    
# with open('s2qmodel.pkl', 'rb') as file:
#     s2qmodel = pickle.load(file)