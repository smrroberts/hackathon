from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import asyncio
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
import threading
import logging

# Import the shopping assistant components
from autogen_agentchat.agents import UserProxyAgent, AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'shopping-assistant-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Global storage
active_sessions = {}
shopping_results = {}

# Initialize model client
gpt4o_api_key = os.getenv("GPT4O_API_KEY")
model_client = AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-4o",
    model="gpt-4o",
    api_version="2024-06-01",
    azure_endpoint="https://ukiaidemo0068520892.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview",
    api_key=gpt4o_api_key,
)

class ShoppingAssistantManager:
    def __init__(self, session_id):
        self.session_id = session_id
        self.current_phase = "discovery"
        self.activity = ""
        self.shopping_list = []
        self.research_results = {}
        self.price_comparison = {}
        self.conversation_history = []
        
        # Initialize agents
        self.activity_discovery_agent = AssistantAgent(
            name="activity_discovery",
            model_client=model_client,
            system_message="""You are an Activity Discovery Agent. Your role is to understand what the human is planning to do.

Instructions:
1. Greet the user warmly and ask what activity or project they're planning
2. Ask follow-up questions to understand the context:
   - When will this activity take place?
   - Where will it happen?
   - Who else might be involved?
   - What's the main goal or purpose?
   - Any specific requirements or constraints?
3. Be conversational and encouraging
4. Once you have a clear understanding, summarize the activity
5. Always end your final message with: "ACTIVITY_DISCOVERED: [brief activity description]"

Example activities: camping trip, home office setup, cooking Italian dinner, garden renovation, fitness routine, etc.
""",
        )

        self.inspiration_agent = AssistantAgent(
            name="inspiration",
            model_client=model_client,
            system_message="""You are an Inspiration Agent. Your role is to help the human identify exactly 5 useful items they should buy for their planned activity.

Instructions:
1. Start by acknowledging the activity the human wants to do
2. Suggest potential items that would be useful for this activity
3. Ask the human for their preferences, budget considerations, and priorities
4. Discuss different options and alternatives
5. Help them think through what they really need vs. nice-to-have items
6. Iteratively refine the list based on their feedback
7. Once you have agreement on exactly 5 items, list them clearly
8. Always end your final message with: "FINAL_SHOPPING_LIST: [item1], [item2], [item3], [item4], [item5]"

Guidelines:
- Be creative and helpful in suggesting items
- Consider different price ranges
- Think about complementary items that work well together
- Ask about their existing equipment/items to avoid duplicates
- Be patient and collaborative in the discussion
""",
        )

        self.web_research_agent = MultimodalWebSurfer(
            name="web_researcher",
            model_client=model_client,
            headless=True,
            animate_actions=False,
        )

        self.price_comparison_agent = AssistantAgent(
            name="price_comparison",
            model_client=model_client,
            system_message="""You are a Price Comparison Agent. Your role is to analyze web research results and find the cheapest options for each item.

Instructions:
1. Review all the price information gathered by the web research agent
2. For each of the 5 items, identify the cheapest option found
3. Also note 1-2 alternative options with slightly higher prices for comparison
4. Consider shipping costs, delivery times, and retailer reliability
5. Present the results in a clear, organized format
6. Include links, prices, and brief descriptions
7. Highlight any special deals, discounts, or bulk buying opportunities
8. Provide a total estimated cost for all 5 items (cheapest options)
9. Always end your final message with: "SHOPPING_COMPLETE"

Output format:
=== BEST DEALS FOUND ===
Item 1: [name]
✅ Cheapest: £XX.XX at [retailer] - [link]
🔄 Alternative: £XX.XX at [retailer] - [link]

[Continue for all 5 items]

💰 Total Cost (cheapest options): £XXX.XX
🚚 Estimated delivery: X-X days
⭐ Recommended retailers: [list based on reliability/price]

SHOPPING_COMPLETE
""",
        )

        self.user_proxy = UserProxyAgent(name="user_proxy")

    async def process_user_message(self, message):
        """Process user message and get agent response"""
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })

            # Determine which agent should respond based on current phase
            if self.current_phase == "discovery":
                agent = self.activity_discovery_agent
            elif self.current_phase == "inspiration":
                agent = self.inspiration_agent
            elif self.current_phase == "research":
                agent = self.web_research_agent
            elif self.current_phase == "comparison":
                agent = self.price_comparison_agent
            else:
                agent = self.activity_discovery_agent

            # Get agent response
            response = await agent.run(task=message)
            
            # Process response and check for phase transitions
            response_text = str(response.messages[-1].content) if response.messages else "No response"
            
            # Add agent response to history
            self.conversation_history.append({
                "role": "agent",
                "agent_name": agent.name,
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            })

            # Check for phase transition signals
            if "ACTIVITY_DISCOVERED:" in response_text:
                self.activity = response_text.split("ACTIVITY_DISCOVERED:")[-1].strip()
                self.current_phase = "inspiration"
                
            elif "FINAL_SHOPPING_LIST:" in response_text:
                # Extract shopping list
                list_text = response_text.split("FINAL_SHOPPING_LIST:")[-1].strip()
                self.shopping_list = [item.strip() for item in list_text.split(",")]
                self.current_phase = "research"
                
            elif "SHOPPING_COMPLETE" in response_text:
                self.current_phase = "completed"

            return {
                "response": response_text,
                "phase": self.current_phase,
                "activity": self.activity,
                "shopping_list": self.shopping_list
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "phase": self.current_phase,
                "activity": self.activity,
                "shopping_list": self.shopping_list
            }

# Flask Routes
@app.route('/')
def index():
    return render_template('shopping_assistant.html')

@app.route('/api/start-session', methods=['POST'])
def start_session():
    """Start a new shopping assistant session"""
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = ShoppingAssistantManager(session_id)
    
    return jsonify({
        "session_id": session_id,
        "message": "Shopping assistant session started!",
        "phase": "discovery"
    })

@app.route('/api/send-message', methods=['POST'])
def send_message():
    """Send message to shopping assistant"""
    data = request.json
    session_id = data.get('session_id')
    message = data.get('message')
    
    if session_id not in active_sessions:
        return jsonify({"error": "Invalid session"}), 400
    
    assistant = active_sessions[session_id]
    
    # Process message in background and emit via SocketIO
    def process_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(assistant.process_user_message(message))
            socketio.emit('agent_response', result, room=session_id)
        except Exception as e:
            socketio.emit('error', {"message": str(e)}, room=session_id)
        finally:
            loop.close()
    
    thread = threading.Thread(target=process_async)
    thread.start()
    
    return jsonify({"status": "processing"})

@app.route('/api/get-conversation/<session_id>')
def get_conversation(session_id):
    """Get conversation history"""
    if session_id not in active_sessions:
        return jsonify({"error": "Invalid session"}), 400
    
    assistant = active_sessions[session_id]
    return jsonify({
        "conversation": assistant.conversation_history,
        "phase": assistant.current_phase,
        "activity": assistant.activity,
        "shopping_list": assistant.shopping_list
    })

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('join_session')
def handle_join_session(data):
    session_id = data['session_id']
    join_room(session_id)
    emit('joined', {"message": f"Joined session {session_id}"})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)