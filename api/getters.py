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
        for a in self.data:
            short_names[a] = self.data[a]().short_name
            descriptions[a] = self.data[a]().description
            params = parameters[a] = self.data[a]().parameters

            # Check that parameters are showable

            for p in list(params.keys()):
                if type(params[p]) in [str, int, float, bool, list, dict]:
                    params[p] = {"value": params[p],
                                 "type": type(params[p]).__name__}
                else:
                    del params[p]

        res = {a: {
            "short_name": short_names[a],
            "description": descriptions[a],
            "parameters": parameters[a],
        } for a in self.data}
        return res