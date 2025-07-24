import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatBot:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.conversation_history = []
        self.model = "gpt-4o"  # Update to GPT-4o which supports structured outputs
        self.session_id = None  # Track the current session ID
    
    def add_message(self, role, content):
        """Add a message to the conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        
        # Keep conversation history to a reasonable size (last 10 messages)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def get_response(self, prompt, context=None):
        """Get a response from OpenAI based on the prompt and conversation history"""
        # Add the user message to history
        self.add_message("user", prompt)
        
        # Add context if provided
        messages = self.conversation_history.copy()
        if context:
            # Insert context as a system message at the beginning
            messages.insert(0, {"role": "system", "content": context})
        
        try:
            # Make the API call using the new client.chat.completions.create method
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            # Get the assistant's message (updated syntax)
            assistant_message = response.choices[0].message.content
            
            # Add the assistant's response to history
            self.add_message("assistant", assistant_message)
            
            return {
                "status": "success",
                "message": assistant_message,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
            
    def get_markdown_response(self, prompt, context=None):
        """Get a response formatted as Markdown"""
        # Add the user message to history
        self.add_message("user", prompt)
        
        # Prepare context with markdown instructions
        md_context = context or ""
        md_context += """
        Format your response using Markdown. Include:
        - Headings with # and ##
        - Bullet points with * or -
        - Bold text with **bold**
        - Italic text with *italic*
        - Code blocks with ```
        - Tables where appropriate
        
        At the end of your response, include a section titled "## Suggested Actions" 
        with 3-5 concrete steps or actions the user might take related to the topic.
        
        If relevant, you may also include a "## References" section with useful resources.
        
        Make your response visually structured and easy to read.
        """
        
        # Add context if provided
        messages = self.conversation_history.copy()
        messages.insert(0, {"role": "system", "content": md_context})
        
        try:
            # Make the API call (no need for special response format)

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            # Get the assistant's message
            assistant_message = response.choices[0].message.content
            
            # Add the assistant's response to history
            self.add_message("assistant", assistant_message)
            
            return {
                "status": "success",
                "message": assistant_message,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def load_history_from_session(self, session_messages):
        """Load conversation history from database session messages"""
        self.conversation_history = []
        for msg in session_messages:
            role = "user" if msg.is_user else "assistant"
            self.add_message(role, msg.content)