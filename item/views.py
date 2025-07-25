from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Item
from agent.models import Agent
from member.models import Member
from django.views.decorators.csrf import csrf_exempt
from storages.backends.s3boto3 import S3Boto3Storage
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from math import radians, cos, sin, asin, sqrt

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
@permission_classes([AllowAny])
@csrf_exempt
def item_detail(request, item_id):
    """Get detailed information about a specific item"""
    try:
        item = Item.objects.get(id=item_id)
        
        # Build detailed response
        response = {
            "id": item.id,
            "name": item.name,
            "price": float(item.price),
            "stock": item.stock,
            "description": item.description,
            "category": item.category,
            "unit": item.unit,
            "image_url": item.image.url if item.image else None,
        }
        
        # Add owner information
        if item.agent:
            response["agent_id"] = item.agent.id
            response["owner_name"] = item.agent.user.username
        elif item.member:
            response["member_id"] = item.member.id
            response["owner_name"] = item.member.username
        
        return JsonResponse(response)
    
    except Item.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Item not found."}, status=404)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
@parser_classes([MultiPartParser, FormParser])
def add_item(request):
    user = request.user
    is_agent = hasattr(user, 'agent')
    is_member = isinstance(user, Member) and not is_agent
    if not isinstance(user, Member):
        return JsonResponse({"status": "error", "message": "Authentication required"}, status=403)
    try:
        name = request.data.get('product_title')
        description = request.data.get('description', '')
        price = request.data.get('price', 0)
        quantity = request.data.get('quantity')
        category = request.data.get('waste_category')
        unit = request.data.get('unit', 'L')
        image = request.FILES.get('image')
        if not name or not quantity or not category:
            return JsonResponse({"status": "error", "message": "Product title, quantity, and category are required"}, status=400)
        item = Item(
            name=name,
            description=description,
            price=price,
            stock=int(quantity),
            category=category,
            unit=unit,
            member=None if is_agent else user,
            agent=user.agent if is_agent else None
        )
        if image:
            storage = S3Boto3Storage()
            key = f"photos/{image.name}"
            saved_name = storage.save(key, image)
            item.image.name = saved_name
        item.save()
        return JsonResponse({"status": "success", "message": "Item added successfully", "item_id": item.id})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@csrf_exempt
@parser_classes([MultiPartParser, FormParser])
def update_item(request, item_id):
    user = request.user
    is_agent = hasattr(user, 'agent')
    is_member = isinstance(user, Member) and not is_agent
    try:
        if is_agent:
            item = Item.objects.get(id=item_id, agent=user.agent)
        elif is_member:
            item = Item.objects.get(id=item_id, member=user)
        else:
            return JsonResponse({"status": "error", "message": "Access denied"}, status=403)
        if 'product_title' in request.data:
            item.name = request.data.get('product_title')
        if 'description' in request.data:
            item.description = request.data.get('description')
        if 'price' in request.data:
            item.price = request.data.get('price')
        if 'quantity' in request.data:
            item.stock = int(request.data.get('quantity'))
        if 'waste_category' in request.data:
            item.category = request.data.get('waste_category')
        if 'unit' in request.data:
            item.unit = request.data.get('unit')
        image = request.FILES.get('image')
        if image:
            storage = S3Boto3Storage()
            key = f"photos/{image.name}"
            saved_name = storage.save(key, image)
            item.image.name = saved_name
        item.save()
        return JsonResponse({"status": "success", "message": "Item updated successfully"})
    except Item.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Item not found or you don't have permission to edit it"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def delete_item(request, item_id):
    """Allow a member or agent to delete their item listing"""
    user = request.user
    
    # Check if user is an agent first (takes priority)
    is_agent = hasattr(user, 'agent')
    # Only consider as regular member if not an agent
    is_member = isinstance(user, Member) and not is_agent
    
    try:
        # Get the item and verify ownership based on user type
        if is_agent:
            item = Item.objects.get(id=item_id, agent=user.agent)
        elif is_member:
            item = Item.objects.get(id=item_id, member=user)
        else:
            return JsonResponse({"status": "error", "message": "Access denied"}, status=403)
        
        # Delete the item
        item.delete()
        
        return JsonResponse({
            "status": "success",
            "message": "Item deleted successfully"
        })
        
    except Item.DoesNotExist:
        return JsonResponse({
            "status": "error", 
            "message": "Item not found or you don't have permission to delete it"
        }, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def my_items(request):
    """Get all items for the logged-in user (member or agent)"""
    user = request.user
    
    # Check if user is an agent first (takes priority)
    is_agent = hasattr(user, 'agent')
    # Only consider as regular member if not an agent
    is_member = isinstance(user, Member) and not is_agent
    
    if not isinstance(user, Member):
        return JsonResponse({"status": "error", "message": "Authentication required"}, status=403)
    
    # Query items based on user type
    if is_agent:
        items = Item.objects.filter(agent=user.agent)
    else:  # is_member
        items = Item.objects.filter(member=user)
    
    items_list = []
    for item in items:
        item_data = {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "price": float(item.price),
            "stock": item.stock,
            "category": item.category,
            "unit": item.unit,
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(item, 'created_at') else None,
            "image_url": item.image.url if item.image else None,
        }
        
        # Add owner information
        if item.agent:
            item_data["agent_id"] = item.agent.id
        elif item.member:
            item_data["member_id"] = item.member.id
            
        items_list.append(item_data)
    
    return JsonResponse({
        "status": "success",
        "items": items_list,
        "count": len(items_list)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def get_all_items(request):
    """Get marketplace items - members see agent products, agents see member products, sorted by distance"""
    user = request.user
    
    # Check if user has location set
    if not user.latitude or not user.longitude:
        return JsonResponse({'error': 'Your location is not set.'}, status=400)
    
    # Check if user is an agent first (takes priority)
    is_agent = hasattr(user, 'agent')
    # Only consider as regular member if not an agent
    is_member = isinstance(user, Member) and not is_agent
    
    if not isinstance(user, Member):
        return JsonResponse({"status": "error", "message": "Authentication required"}, status=403)
    
    items_list = []
    
    # Query items based on user type
    if is_agent:
        # Agents see member items (only those with valid location)
        items = Item.objects.filter(
            member__isnull=False,
            member__latitude__isnull=False,
            member__longitude__isnull=False
        ).select_related('member')
        
        for item in items:
            # Calculate distance between user and item owner
            dist = haversine(
                user.latitude, user.longitude, 
                item.member.latitude, item.member.longitude
            )
            
            items_list.append({
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "price": float(item.price),
                "stock": item.stock,
                "member_id": item.member.id,
                "member_name": item.member.username,
                "category": item.category,
                "unit": item.unit if hasattr(item, 'unit') else None,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(item, 'created_at') else None,
                "image_url": item.image.url if item.image else None,
                "distance_km": round(dist, 2),
            })
    else:  # is_member
        # Members see agent items (only those with valid location)
        items = Item.objects.filter(
            agent__isnull=False,
            agent__user__latitude__isnull=False,
            agent__user__longitude__isnull=False
        ).select_related('agent')
        
        for item in items:
            # Calculate distance between user and item owner (agent)
            dist = haversine(
                user.latitude, user.longitude, 
                item.agent.user.latitude, item.agent.user.longitude
            )
            
            items_list.append({
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "price": float(item.price),
                "stock": item.stock,
                "agent_id": item.agent.id,
                "agent_name": item.agent.user.username,
                "category": item.category,
                "unit": item.unit if hasattr(item, 'unit') else None,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(item, 'created_at') else None,
                "image_url": item.image.url if item.image else None,
                "distance_km": round(dist, 2),

            })
    
    # Sort by distance (nearest first)
    items_list.sort(key=lambda x: x['distance_km'])
    
    return JsonResponse({
        "status": "success",
        "items": items_list,
        "count": len(items_list)
    })