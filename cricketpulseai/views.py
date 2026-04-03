from rest_framework.decorators import api_view
from rest_framework.response import Response
from .ml_utils import predict_match

@api_view(["POST"])
def predict_api(request):
    data = request.data

    result = predict_match(data)

    return Response({
        "prediction": result["winner"],
        "confidence": result["confidence"]
    })