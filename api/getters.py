import matplotlib
import sys
sys.path.append('../ballenas/src/')

from whales.modules.pipelines import getters as backend_getters
straight_forward = ['formatters', 'pre_processing', 'features_extractors', 'pipelines', 'data_files',
                    'machine_learning', 'performance_indicators']


class GettersData:
    def __init__(self, src='formatters'):
        self.src = src
        self.data = {}
        if src in straight_forward:
            self.data = eval(f'backend_getters.get_available_{src}()')

    def to_list(self):
        descriptions = {}
        parameters = {}
        options = {}
        t = {}
        for a in self.data:
            matplotlib.use("Agg")
            if type(self.data[a]) is not dict:
                instance = self.data[a]()
                descriptions[a] = instance.description
                params = parameters[a] = instance.parameters
                opts = options[a] = instance.parameters_options

                # Check that parameters are showable
                for p in list(params.keys()):
                    t = type(params[p])
                    if t in [str, int, float, bool, list, dict]:
                        params[p] = {"value": params[p],
                                     "type": p if t not in [str, int, float, bool] else t.__name__,
                                     "options": opts[p] if p in opts else None}
                    else:
                        del params[p]
            else:
                for b in self.data[a]:
                    instance = self.data[a][b]()
                    descriptions[b] = instance.description
                    params = parameters[b] = instance.parameters
                    opts = options[b] = instance.parameters_options

                    # Check that parameters are showable
                    for p in list(params.keys()):
                        if type(params[p]) in [str, int, float, bool, list, dict]:
                            params[p] = {"value": params[p],
                                         "type": type(params[p]).__name__,
                                         "options": opts[p] if p in opts else None}
                        else:
                            del params[p]

        res = [{
            "name": a,
            "description": descriptions[a],
            "parameters": parameters[a],
        } for a in descriptions]
        return res
