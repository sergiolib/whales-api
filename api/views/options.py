from rest_framework.response import Response
from rest_framework.views import APIView
from api import getters


class GetScopeOptionsView(APIView):
    def get(self, request, scope):
        g = getters.GettersData(scope).to_list()
        return Response(g)
