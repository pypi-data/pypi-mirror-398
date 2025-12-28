from loclm.query2sequence import *
from loclm.sentence2query import *

import pickle
class Model():
    def __init__(self):
        self.pklfile = ""
            
    def predict(self, inputqry):
        with resources.files('loclm').joinpath(self.pklfile).open('rb') as file:
            model = pickle.load(file)
        return model.predict(inputqry)
    
class Qry2Seqmodel(Model):
    def __init__(self, model_name):
        if model_name == 'cellmech':
            self.pklfile = 'q2smodel.pkl'
        
class Sen2Qrymodel(Model):
    def __init__(self, model_name):
        if model_name == 'cellmech':
            self.pklfile = 's2qmodel.pkl'
    