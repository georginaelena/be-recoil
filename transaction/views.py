from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from member.models import Member, Waste
from agent.models import Agent
from item.models import Item
from .models import Cart, CartItem, Transaction, Offer, Message
from django.db import transaction as db_transaction
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def add_to_cart(request):
    member = request.user
    agent_id = request.data.get("agent_id")
    item_id = request.data.get("item_id")
    quantity = int(request.data.get("quantity", 1))

    if not agent_id or not item_id:
        return JsonResponse({"status": "error", "message": "agent_id and item_id are required."}, status=400)

    try:
        agent = Agent.objects.get(id=agent_id)
    except Agent.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Agent not found."}, status=404)

    try:
        item = Item.objects.get(id=item_id)
    except Item.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Item not found."},
            status=404
        )
    
    # Check stock availability here
    if quantity > item.stock:
        return JsonResponse(
            {"status": "error", "message": f"Not enough stock for {item.name}. Available: {item.stock}"},
            status=400
        )

    # Check if member already has a cart with items from a different agent
    existing_cart = Cart.objects.filter(member=member).exclude(agent_id=agent_id).first()
    if existing_cart:
        # Reset cart by deleting all items from other agent
        CartItem.objects.filter(cart=existing_cart).delete()
        # Delete the old cart
        existing_cart.delete()
    
    cart, _ = Cart.objects.get_or_create(member=member, agent=agent)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item)
    
    # When updating existing cart item, check if new total quantity exceeds stock
    new_quantity = quantity if created else cart_item.quantity + quantity
    if new_quantity > item.stock:
        return JsonResponse(
            {"status": "error", "message": f"Cannot add {quantity} more units. Only {item.stock} available in stock."},
            status=400
        )
    
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()
    return JsonResponse({
        "status": "success", 
        "cart_item_id": cart_item.id,
        "message": "Item added to cart successfully."
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def remove_from_cart(request):
    member = request.user
    item_id = request.data.get("item_id")
    
    if not item_id:
        return JsonResponse({"status": "error", "message": "item_id is required."}, status=400)
    
    try:
        cart = Cart.objects.get(member=member)
    except Cart.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Cart not found."}, status=404)
    
    try:
        cart_item = CartItem.objects.get(cart=cart, item_id=item_id)
    except CartItem.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Cart item not found."}, status=404)
    
    cart_item.delete()
    return JsonResponse({"status": "success", "message": "Item removed from cart."})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def view_cart(request):
    member = request.user
    
    try:
        cart = Cart.objects.filter(member=member).first()
        if not cart:
            return JsonResponse({"cart": [], "agent_info": None})
        
        items = [
            {
                "item_id": ci.item.id,
                "item_name": str(ci.item),
                "quantity": ci.quantity,
                "price": float(ci.item.price),
                "total": float(ci.item.price * ci.quantity)
            }
            for ci in cart.items.select_related("item")
        ]
        
        agent_info = {
            "agent_id": cart.agent.id,
            "agent_name": cart.agent.user.username,
            "agent_email": cart.agent.user.email
        }
        
        return JsonResponse({
            "cart": items,
            "agent_info": agent_info,
            "total_items": len(items),
            "total_value": sum(item["total"] for item in items)
        })
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@db_transaction.atomic
@csrf_exempt
def edit_cart_item_quantity(request):
    member = request.user
    item_id = request.data.get("item_id")
    new_quantity = request.data.get("quantity")

    if not item_id or new_quantity is None:
        return JsonResponse(
            {"status": "error", "message": "item_id and quantity are required."},
            status=400
        )
    
    new_quantity = int(new_quantity)
    
    try:
        cart = Cart.objects.get(member=member)
    except Cart.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Cart not found."}, status=404)
    
    try:
        cart_item = CartItem.objects.get(cart=cart, item_id=item_id)
    except CartItem.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Cart item not found."}, status=404)

    if new_quantity <= 0:
        cart_item.delete()
        
        remaining_items = cart.items.select_related("item")
        cart_total_price = sum(float(item.item.price * item.quantity) for item in remaining_items)

        return JsonResponse({
            "status": "success", 
            "message": "Item removed from cart.",
            "cart_total_price": cart_total_price,
            "item_count": remaining_items.count()
        })
    
    # Check stock availability
    if new_quantity > cart_item.item.stock:
        return JsonResponse(
            {"status": "error", "message": f"Not enough stock. Only {cart_item.item.stock} units available."},
            status=400
        )
    
    cart_item.quantity = new_quantity
    cart_item.save()
    
    # Recalculate cart total after quantity update
    cart_items = cart.items.select_related("item")
    cart_total_price = sum(float(item.item.price * item.quantity) for item in cart_items)
    
    return JsonResponse({
        "status": "success", 
        "message": "Cart item updated.",
        "item": {
            "item_id": cart_item.item.id,
            "item_name": str(cart_item.item),
            "quantity": cart_item.quantity,
            "price": float(cart_item.item.price),
            "total": float(cart_item.item.price * cart_item.quantity)
        },
        "cart_total_price": cart_total_price,
        "item_count": cart_items.count()
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def clear_cart(request):
    member = request.user
    
    try:
        cart = Cart.objects.get(member=member)
        cart.items.all().delete()
        return JsonResponse({"status": "success", "message": "Cart cleared successfully."})
    except Cart.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Cart not found."}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@db_transaction.atomic
@csrf_exempt
def checkout(request):
    member = request.user
    transaction_type = request.data.get("transaction_type", "buy")
    
    try:
        cart = Cart.objects.get(member=member)
    except Cart.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Cart not found."}, status=404)
    
    agent = cart.agent  # Agent is already associated with the cart
    
    cart_items = list(cart.items.select_related("item"))
    if not cart_items:
        return JsonResponse({"status": "error", "message": "Cart is empty."}, status=400)

    # Calculate total amount first
    total_amount = 0
    for ci in cart_items:
        if not hasattr(ci.item, "price"):
            return JsonResponse(
                {"status": "error", "message": f"Item {ci.item.id} has no price."},
                status=400
            )
        
        # Double-check stock one more time at checkout for safety
        if ci.quantity > ci.item.stock:
            return JsonResponse(
                {"status": "error", "message": f"Not enough stock for {ci.item.name}. Available: {ci.item.stock}"},
                status=400
            )
            
        total_price = ci.item.price * ci.quantity
        total_amount += total_price
    
    # Check wallet balance before creating transactions
    if member.wallet < total_amount:
        return JsonResponse({
            "status": "error", 
            "message": f"Insufficient wallet balance. Required: {total_amount}, Available: {member.wallet}"
        }, status=400)
    
    # Update wallet balances
    member.wallet -= total_amount
    agent.user.wallet += total_amount
    member.save()
    agent.user.save()

    transactions = []
    
    for ci in cart_items:
        total_price = ci.item.price * ci.quantity
        
        t = Transaction.objects.create(
            member=member,
            agent=agent,
            item=ci.item,
            transaction_type=transaction_type,
            quantity=ci.quantity,
            total_price=total_price,
        )
        
        # Update item stock
        ci.item.stock -= ci.quantity
        
        # Mark item as sold if stock reaches zero
        if ci.item.stock <= 0:
            ci.item.status = 'sold'
        
        ci.item.save()
        
        transactions.append(t)
    
    # After creating transactions, clear the cart items
    cart.items.all().delete()
    
    return JsonResponse({
        "status": "success", 
        "message": "Checkout successful!",
        "total_amount": float(total_amount),
        "transactions": [tr.id for tr in transactions],
        "remaining_balance": float(member.wallet)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def get_transaction_history(request):
    member = request.user
    
    # Get all transactions for this member
    transactions = Transaction.objects.filter(member=member).order_by('-created_at')
    
    result = []
    for t in transactions:
        result.append({
            "id": t.id,
            "transaction_type": t.transaction_type,
            "item_name": str(t.item),
            "quantity": t.quantity,
            "total_price": float(t.total_price),
            "agent_name": t.agent.user.username,
            "status": t.status,
            "date": t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "completed_at": t.completed_at.strftime("%Y-%m-%d %H:%M:%S") if t.completed_at else None
        })
    
    return JsonResponse({
        "transactions": result,
        "count": len(result)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def complete_transaction(request, transaction_id):
    """Allow buyer to mark a transaction as complete"""
    user = request.user
    is_agent = hasattr(user, 'agent')
    
    try:
        if is_agent:
            # Agent can complete transactions where they are the buyer (buying from member)
            transaction = Transaction.objects.get(
                id=transaction_id, 
                agent=user.agent,
                transaction_type='sell'  # Agent buying from member
            )
        else:
            # Member can complete transactions where they are the buyer (buying from agent)
            transaction = Transaction.objects.get(
                id=transaction_id, 
                member=user,
                transaction_type='buy'  # Member buying from agent
            )
    except Transaction.DoesNotExist:
        return JsonResponse({
            "status": "error", 
            "message": "Transaction not found or you don't have permission to complete it"
        }, status=404)
    
    # Check if transaction is already complete
    if transaction.status == 'complete':
        return JsonResponse({
            "status": "error", 
            "message": "Transaction is already complete"
        }, status=400)
    
    # Update transaction status
    transaction.status = 'complete'
    transaction.completed_at = timezone.now()
    transaction.save()
    
    return JsonResponse({
        "status": "success",
        "message": "Transaction marked as complete",
        "transaction_id": transaction.id,
        "completed_at": transaction.completed_at.strftime("%Y-%m-%d %H:%M:%S")
    })

# ================ OFFERS AND MESSAGE MANAGEMENT ================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def create_offer(request):
    """Create an offer for an item (agent only)"""
    user = request.user
    
    # Only agents can create offers
    if not hasattr(user, 'agent'):
        return JsonResponse({"status": "error", "message": "Only agents can make offers"}, status=403)
    
    agent = user.agent
    item_id = request.data.get('item_id')
    price = request.data.get('price')
    message = request.data.get('message', '')
    
    if not item_id or not price:
        return JsonResponse({"status": "error", "message": "item_id and price are required"}, status=400)
    
    try:
        item = Item.objects.get(id=item_id, member__isnull=False)
    except Item.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Item not found"}, status=404)
    
    # Use the item's quantity from member's listing
    quantity = item.stock
    
    # Create the offer
    offer = Offer.objects.create(
        member=item.member,
        agent=agent,
        item=item,
        quantity=quantity,
        price=float(price),
        message=message,
        sender_is_agent=True  # Initial offers are always from agents
    )
    
    return JsonResponse({
        "status": "success",
        "message": "Offer created successfully",
        "offer_id": offer.id
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def respond_to_offer(request, offer_id):
    """Accept, reject, or counter an offer"""
    user = request.user
    is_agent = hasattr(user, 'agent')
    
    action = request.data.get('action')
    if action not in ['accept', 'reject', 'counter']:
        return JsonResponse({"status": "error", "message": "Invalid action"}, status=400)
    
    try:
        if is_agent:
            offer = Offer.objects.get(id=offer_id, agent=user.agent)
        else:
            offer = Offer.objects.get(id=offer_id, member=user)
    except Offer.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Offer not found"}, status=404)
    
    # Check if user is allowed to respond (can't respond to your own offer)
    if (is_agent and offer.sender_is_agent) or (not is_agent and not offer.sender_is_agent):
        return JsonResponse({"status": "error", "message": "You cannot respond to your own offer"}, status=403)
    
    if action == 'counter':
        # Handle counter-offer
        new_price = request.data.get('price')
        message = request.data.get('message', '')
        
        if not new_price:
            return JsonResponse({"status": "error", "message": "Price is required for counter-offer"}, status=400)
        
        # Update current offer status
        offer.status = 'countered'
        offer.save()
        
        # Create new counter-offer
        counter = Offer.objects.create(
            member=offer.member,
            agent=offer.agent,
            item=offer.item,
            quantity=offer.quantity,  # Same quantity
            price=float(new_price),
            message=message,
            sender_is_agent=is_agent,  # Who created the counter
            parent_offer=offer
        )
        
        return JsonResponse({
            "status": "success",
            "message": "Counter-offer created",
            "offer_id": counter.id
        })
        
    else:  # accept or reject
        offer.status = f"{action}ed"  # accepted or rejected
        offer.save()
        
        if action == 'accept':
            # Check wallet balance before creating transaction
            if offer.agent.user.wallet < offer.price:
                return JsonResponse({
                    "status": "error",
                    "message": f"Insufficient wallet balance. Required: {offer.price}, Available: {offer.agent.user.wallet}"
                }, status=400)
            
            # Update wallet balances
            offer.agent.user.wallet -= offer.price
            offer.member.wallet += offer.price
            offer.agent.user.save()
            offer.member.save()
            
            # Create transaction record
            Transaction.objects.create(
                member=offer.member,
                agent=offer.agent,
                item=offer.item,  # Now using item directly
                transaction_type='sell',  # Member selling to agent
                quantity=int(offer.quantity),  # Converting to int for PositiveIntegerField
                total_price=offer.price
            )
            
            # Update item status to sold
            item = offer.item
            item.status = 'sold'
            item.save()
        
        return JsonResponse({
            "status": "success",
            "message": f"Offer {action}ed successfully"
        })
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def get_latest_accepted_offer(request, agent_id=None, member_id=None):
    """Get the latest accepted offer between a member and an agent"""
    user = request.user
    is_agent = hasattr(user, 'agent')
    
    # Determine which party we're looking for based on the current user
    if is_agent:
        # Agent is looking for offers with a specific member
        if not member_id:
            return JsonResponse({"status": "error", "message": "member_id is required"}, status=400)
        
        try:
            member = Member.objects.get(id=member_id)
            agent = user.agent
        except Member.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Member not found"}, status=404)
            
    else:
        # Member is looking for offers with a specific agent
        if not agent_id:
            return JsonResponse({"status": "error", "message": "agent_id is required"}, status=400)
        
        try:
            agent = Agent.objects.get(id=agent_id)
            member = user
        except Agent.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Agent not found"}, status=404)
    
    # Find the latest accepted offer
    latest_offer = Offer.objects.filter(
        member=member,
        agent=agent,
        status='accepted'
    ).order_by('-created_at').first()
    
    if not latest_offer:
        return JsonResponse({
            "status": "error", 
            "message": "No accepted offers found between these parties"
        }, status=404)
    
    # Return the offer ID and basic info
    return JsonResponse({
        "status": "success",
        "offer": {
            "id": latest_offer.id,
            "item_name": latest_offer.item.name,
            "price": float(latest_offer.price),
            "created_at": latest_offer.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "message_count": latest_offer.messages.count()
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def send_message(request, offer_id):
    """Send a message for an offer"""
    user = request.user
    is_agent = hasattr(user, 'agent')
    
    try:
        if is_agent:
            offer = Offer.objects.get(id=offer_id, agent=user.agent)
        else:
            offer = Offer.objects.get(id=offer_id, member=user)
    except Offer.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Offer not found"}, status=404)
    
    # Only allow messages on accepted offers
    if offer.status != 'accepted':
        return JsonResponse({"status": "error", "message": "Messages are only allowed for accepted offers"}, status=400)
    
    content = request.data.get('content')
    if not content:
        return JsonResponse({"status": "error", "message": "Message content is required"}, status=400)
    
    # Create the message
    message = Message.objects.create(
        offer=offer,
        sender_is_agent=is_agent,
        content=content
    )
    
    return JsonResponse({
        "status": "success",
        "message_id": message.id,
        "content": content,
        "created_at": message.created_at.strftime("%Y-%m-%d %H:%M:%S")
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def get_offer_with_messages(request, offer_id):
    """Get both offer details and messages in a single API call"""
    user = request.user
    is_agent = hasattr(user, 'agent')
    
    try:
        # Security check to ensure user is either the member or agent involved
        if is_agent:
            offer = Offer.objects.get(id=offer_id, agent=user.agent)
        else:
            offer = Offer.objects.get(id=offer_id, member=user)
            
    except Offer.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Offer not found or access denied"}, status=404)
    
    # Build negotiation history
    history = []
    current = offer
    
    # First, collect all parent offers going up the chain
    parent_chain = []
    while current.parent_offer:
        parent_chain.append(current.parent_offer)
        current = current.parent_offer
    
    # Sort history chronologically (oldest to newest)
    for parent in reversed(parent_chain):
        history.append({
            "id": parent.id,
            "price": float(parent.price),
            "message": parent.message,
            "status": parent.status,
            "sender_is_agent": parent.sender_is_agent,
            "created_at": parent.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # Add the current offer to the history
    history.append({
        "id": offer.id,
        "price": float(offer.price),
        "message": offer.message,
        "status": offer.status,
        "sender_is_agent": offer.sender_is_agent,
        "created_at": offer.created_at.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    item_info = {
        "id": offer.item.id,
        "name": offer.item.name,
        "category": offer.item.category,
        "quantity": float(offer.quantity),
        "description": offer.item.description,
        "location": offer.item.location or "",
        "price": float(offer.item.price)
    }
    
    if is_agent:
        user_info = {
            "member": {
                "id": offer.member.id,
                "username": offer.member.username,
                "email": offer.member.email
            }
        }
    else:
        user_info = {
            "agent": {
                "id": offer.agent.id,
                "name": offer.agent.user.username,
                "email": offer.agent.user.email
            }
        }
    
    result = {
        "id": offer.id,
        "item": item_info,
        "price": float(offer.price),
        "status": offer.status,
        "negotiation_history": history,
        "can_message": offer.status == 'accepted',
        **user_info
    }
    
    # If offer is accepted, include messages
    if offer.status == 'accepted': 
        # Get all messages
        messages = Message.objects.filter(offer=offer).order_by('created_at')
        
        chat_messages = []
        for message in messages:
            sender = offer.agent.user.username if message.sender_is_agent else offer.member.username
            chat_messages.append({
                "id": message.id,
                "content": message.content,
                "sender": sender,
                "sender_type": "agent" if message.sender_is_agent else "member",
                "created_at": message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            })
        
        result["messages"] = chat_messages
    
    return JsonResponse({
        "status": "success",
        "offer": result
    })