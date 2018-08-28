import matplotlib
from django.conf import settings
import sys
sys.path.append(settings.WHALES_BACKEND)

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
        matplotlib.use("Agg")
        descriptions = {}
        parameters = {}
        options = {}
        tt = {}
        for a in self.data:
            instance = self.data[a]()
            descriptions[a] = instance.description
            params = parameters[a] = instance.parameters
            opts = options[a] = instance.parameters_options
            t = tt[a] = instance.type if hasattr(instance, "type") else None

            for p in params:
                params[p] = {"value": params[p],
                             "options": opts.get(p, [])}
                if type(params[p]["value"]) is bool:
                    params[p]["options"] = [True, False]
        res = [{
            "name": a,
            "description": descriptions[a],
            "parameters": parameters[a],
            "type": tt[a],
        } for a in descriptions]
        return res
