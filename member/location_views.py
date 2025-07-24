# Utility function for distance calculation
from math import radians, cos, sin, asin, sqrt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Member

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees)"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nearest_members(request):
    """Get nearest members based on user's location"""
    user = request.user
    if not user.latitude or not user.longitude:
        return Response({'error': 'Your location is not set.'}, status=400)
    
    members = Member.objects.exclude(id=user.id).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    results = []
    for member in members:
        dist = haversine(user.latitude, user.longitude, member.latitude, member.longitude)
        results.append({
            'id': member.id,
            'username': member.username,
            'email': member.email,
            'distance_km': round(dist, 2),
            'latitude': member.latitude,
            'longitude': member.longitude,
            'profile_picture': member.profile_picture,
            'gender': member.gender,
            'is_agent': hasattr(member, 'agent')
        })
    
    results.sort(key=lambda x: x['distance_km'])
    return Response({'nearest_members': results})
