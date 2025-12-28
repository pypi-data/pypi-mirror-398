from loclm.query2sequence import *
from loclm.sentence2query import *
import json
class Model():
    def __init__(self):
        self.filepath = ""
        
    def load(self):
        pass
            
    def predict(self, inputqry):
        model = self.load()
        return model.predict(inputqry)
    
class Qry2Seqmodel(Model):
            
    def __init__(self, model_name):
        if model_name == 'cellmech':
            self.filepath = 'q2smodel.json'
            
    def load(self):
        with resources.files('loclm').joinpath(self.filepath).open('rb') as f:
            inputparams = json.load(f)
            predictor = ContextSequenceLearner()
            predictor.load(inputparams)
            return predictor
        
class Sen2Qrymodel(Model):
    def __init__(self, model_name):
        if model_name == 'cellmech':
            self.filepath = 's2qmodel.json'
            
    def load(self):
        with resources.files('loclm').joinpath(self.filepath).open('rb') as f:
            inputparams = json.load(f)
            predictor = FastKernelRouter()
            predictor.load(inputparams)
            return predictor
        
        