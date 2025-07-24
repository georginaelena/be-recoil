from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.

def test_endpoint(request):
    """
    Simple test endpoint for deployment testing
    """
    return JsonResponse({
        'status': 'success',
        'message': 'Hello from BE_ReCoil API!',
        'timestamp': '2025-07-24',
        'method': request.method
    })
