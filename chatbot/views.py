from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from .utils import ChatBot
from item.models import Item
from .models import ChatSession, ChatMessage, TokenUsage
import uuid
import json
from django.db.models import Max

# Dictionary to store chatbot instances per user
chatbot_instances = {}

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def chat_with_ai(request):
    #test
    """Chat with AI assistant about waste management and recycling"""
    user = request.user
    user_id = user.id
    
    # Get or create a chatbot instance for this user
    if user_id not in chatbot_instances:
        chatbot_instances[user_id] = ChatBot(user_id)
        
        # Try to load the latest session for this user
        try:
            latest_session = ChatSession.objects.filter(user=user).latest('created_at')
            chatbot_instances[user_id].session_id = latest_session.session_id
            
            # Load the conversation history from this session
            session_messages = latest_session.messages.all().order_by('created_at')
            chatbot_instances[user_id].load_history_from_session(session_messages)
        except ChatSession.DoesNotExist:
            # Create a new session
            new_session = ChatSession.objects.create(
                user=user,
                session_id=str(uuid.uuid4())
            )
            chatbot_instances[user_id].session_id = new_session.session_id
    
    chatbot = chatbot_instances[user_id]
    
    # Get the message from the request
    message = request.data.get('message')
    if not message:
        return JsonResponse({"status": "error", "message": "Message is required"}, status=400)
    
    # Check if markdown format is requested (default to markdown now)
    format_type = request.data.get('format', 'markdown')
    
    # Optional: Get item context if provided
    item_id = request.data.get('item_id')
    item_context = ""
    
    if item_id:
        try:
            item = Item.objects.get(id=item_id)
            item_context = f"The user is asking about an item: {item.name}, category: {item.category}, " \
                          f"description: {item.description}, price: {item.price}."
        except Item.DoesNotExist:
            item_id = None  # Reset to None if item doesn't exist
            pass
    
    # Main system context
    context = f"""
    You are a helpful assistant for an eco-friendly waste management platform called ReCoil. 
    Your role is to help users with questions about waste management, recycling, the platform's features and etc.
    Keep responses friendly, informative, and focused on sustainability and environmental issues.
    {item_context}
    """
    
    # Get response based on format
    if format_type == 'markdown':
        response = chatbot.get_markdown_response(message, context)
    else:
        response = chatbot.get_response(message, context)
    
    if response["status"] == "error":
        return JsonResponse({"status": "error", "message": response["message"]}, status=500)
    
    # Save to database with the current session ID and item_id
    save_chat_to_db(user, message, response["message"], response.get("usage"), chatbot.session_id, item_id)
    
    # For markdown responses, we return the markdown content
    if format_type == 'markdown':
        return JsonResponse({
            "status": "success",
            "markdown_content": response["message"],
            "tokens_used": response.get("usage", {}).get("total_tokens", 0)
        })
    else:
        # Regular text response
        return JsonResponse({
            "status": "success",
            "message": response["message"],
            "tokens_used": response.get("usage", {}).get("total_tokens", 0)
        })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def reset_chat(request):
    """Reset the chat history for a user"""
    user = request.user
    user_id = user.id
    
    # Create a new session in the database
    new_session = ChatSession.objects.create(
        user=user,
        session_id=str(uuid.uuid4())
    )
    
    # Reset in-memory chatbot with the new session
    chatbot_instances[user_id] = ChatBot(user_id)
    chatbot_instances[user_id].session_id = new_session.session_id
    
    return JsonResponse({
        "status": "success",
        "message": "Chat history reset successfully",
        "session_id": new_session.session_id
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_history(request):
    """Get chat history for the current user"""
    user = request.user
    
    # Get session_id from query params, or use the most recent session
    session_id = request.GET.get('session_id')
    
    if session_id:
        try:
            session = ChatSession.objects.get(user=user, session_id=session_id)
        except ChatSession.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": "Session not found"
            }, status=404)
    else:
        # Get the most recent session
        try:
            session = ChatSession.objects.filter(user=user).latest('created_at')
        except ChatSession.DoesNotExist:
            return JsonResponse({
                "status": "success",
                "session_id": None,
                "messages": []
            })
    
    # Get all messages for this session, ordered by creation time
    messages = session.messages.all().order_by('created_at')
    
    # Format messages for the response
    message_list = []
    for msg in messages:
        message_list.append({
            'id': msg.id,
            'content': msg.content,
            'is_user': msg.is_user,
            'timestamp': msg.created_at.isoformat(),
            'item_id': msg.item_id  # Include item_id in the response
        })
    
    # Get all sessions for this user
    all_sessions = ChatSession.objects.filter(user=user).order_by('-created_at')
    session_list = []
    
    for sess in all_sessions:
        message_count = sess.messages.count()
        
        if message_count > 0:  # Only include sessions with messages
            # Get first user message for preview
            first_user_message = ChatMessage.objects.filter(
                session=sess,
                is_user=True
            ).order_by('created_at').first()
            
            # Set preview text
            if first_user_message:
                content = first_user_message.content
                preview = content[:50] + "..." if len(content) > 50 else content
            else:
                preview = "AI conversation"
            
            session_list.append({
                'session_id': sess.session_id,
                'created_at': sess.created_at.isoformat(),
                'message_count': message_count,
                'preview': preview,
                'is_current': sess.session_id == session.session_id
            })
    
    return JsonResponse({
        "status": "success",
        "current_session": {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
        },
        "messages": message_list,
        "all_sessions": session_list
    })

def save_chat_to_db(user, user_message, ai_message, usage=None, session_id=None, item_id=None):
    """Save chat messages to database with specific session if provided"""
    # If session_id is provided, use that specific session
    if session_id:
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            # Fallback to creating a new session if the ID is invalid
            session = ChatSession.objects.create(
                user=user,
                session_id=str(uuid.uuid4())
            )
    else:
        # Get or create a chat session (original behavior as fallback)
        session, created = ChatSession.objects.get_or_create(
            user=user,
            defaults={"session_id": str(uuid.uuid4())}
        )
    
    # Save the user message
    user_msg = ChatMessage.objects.create(
        session=session,
        is_user=True,
        content=user_message,
        item_id=item_id  # Save item_id for user message
    )
    
    # Save the AI response
    ai_msg = ChatMessage.objects.create(
        session=session,
        is_user=False,
        content=ai_message,
        item_id=item_id  # Save the same item_id for AI response
    )
    
    # Track token usage
    if usage:
        TokenUsage.objects.create(
            user=user,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0)
        )
    
    return session