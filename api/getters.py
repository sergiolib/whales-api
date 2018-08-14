import matplotlib
import sys
sys.path.append('../ballenas/src/')

from whales.modules.pipelines import getters as backend_getters
straight_forward = ['formatters', 'pre_processing', 'features_extractors', 'pipelines', 'data_files', 'supervised_methods',
                    'unsupervised_methods', 'semi_supervised_methods', 'performance_indicators']


class GettersData:
    def __init__(self, src='formatters'):
        self.src = src
        self.data = {}
        if src in straight_forward:
            self.data = eval(f'backend_getters.get_available_{src}()')

    def to_list(self):
        short_names = {}
        descriptions = {}
        parameters = {}
        options = {}
        for a in self.data:
            matplotlib.use("Agg")
            instance = self.data[a]()
            print(a)
            short_names[a] = instance.short_name
            descriptions[a] = instance.description
            params = parameters[a] = instance.parameters
            opts = options[a] = instance.parameters_options

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
            "short_name": short_names[a],
            "description": descriptions[a],
            "parameters": parameters[a],
        } for a in self.data]
        return res
