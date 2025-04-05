import os
import json
import boto3
from openai import OpenAI
from typing import Dict, Any, List
from datetime import datetime
from services.order_service import OrderService

class AIService:
    def __init__(self):
        self.openai = OpenAI()
        self.assistant_id = os.getenv('OPENAI_ASSISTANT_ID')
        self.bedrock_client = boto3.client('bedrock-agent-runtime')
        self.agent_id = os.getenv('BEDROCK_AGENT_ID')
        self.agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
        self.order_service = OrderService()
        
        # Create OpenAI assistant if not exists
        if not self.assistant_id:
            self.assistant_id = self._create_assistant()
    
    def _create_assistant(self) -> str:
        """Create an OpenAI assistant for customer support"""
        assistant = self.openai.beta.assistants.create(
            name="CloudMart Customer Support",
            instructions="""You are a customer support assistant for CloudMart, an e-commerce platform.
            Your role is to help customers with their inquiries and issues.
            Be professional, helpful, and empathetic. Focus on providing clear solutions.
            If a technical issue is reported, provide troubleshooting steps.
            For product-related questions, guide customers to the appropriate resources.
            For complex issues, explain that a human support agent will review the ticket.
            You can also help with order management, including canceling or deleting orders.""",
            model="gpt-4-turbo-preview",
            tools=[{
                "type": "function",
                "function": {
                    "name": "delete_order",
                    "description": "Delete an order by order ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "orderId": {
                                "type": "string",
                                "description": "The ID of the order to be deleted"
                            }
                        },
                        "required": ["orderId"]
                    }
                }
            }, {
                "type": "function",
                "function": {
                    "name": "cancel_order",
                    "description": "Cancel an order by changing its status to 'canceled'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "orderId": {
                                "type": "string",
                                "description": "The ID of the order to be canceled"
                            }
                        },
                        "required": ["orderId"]
                    }
                }
            }]
        )
        return assistant.id

    async def create_openai_conversation(self) -> str:
        """Create a new OpenAI thread"""
        thread = self.openai.beta.threads.create()
        return thread.id

    async def send_openai_message(self, thread_id: str, message: str) -> str:
        """Send a message to OpenAI conversation and handle function calls"""
        # Add user message to thread
        self.openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

        # Run the assistant
        run = self.openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id
        )

        # Wait for completion or handle function calls
        while True:
            run = self.openai.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run.status == "requires_action":
                # Handle function calls
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []
                
                for tool_call in tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    order_id = args["orderId"]
                    result = ""
                    
                    try:
                        order = await self.order_service.get_order(order_id)
                        if not order:
                            result = f"Order with ID {order_id} does not exist."
                        elif tool_call.function.name == "delete_order":
                            await self.order_service.delete_order(order_id)
                            result = f"Order {order_id} has been successfully deleted."
                        elif tool_call.function.name == "cancel_order":
                            updated_order = await self.order_service.cancel_order(order_id)
                            result = f"Order {order_id} has been successfully canceled. New status: {updated_order.status}"
                    except Exception as e:
                        result = f"An error occurred while processing the order: {str(e)}"
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": result
                    })
                
                # Submit tool outputs back to the assistant
                if tool_outputs:
                    await self.openai.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
            elif run.status == "completed":
                break
            elif run.status == "failed":
                raise Exception(f"Run failed: {run.last_error}")
            
            # Wait before checking again
            await asyncio.sleep(1)

        # Get the assistant's response
        messages = self.openai.beta.threads.messages.list(thread_id=thread_id)
        for message in messages.data:
            if message.role == "assistant":
                return message.content[0].text.value
        
        return "No response generated"

    async def create_bedrock_conversation(self) -> str:
        """Create a new Bedrock conversation ID"""
        return str(int(datetime.now().timestamp() * 1000))

    async def send_bedrock_message(self, session_id: str, message: str) -> str:
        """Send a message to Bedrock agent and get response"""
        try:
            response = self.bedrock_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=message
            )
            
            if not response.get('completion') or not response['completion'].get('messageStream'):
                return "I'm sorry, but I couldn't generate a response at the moment. Please try again later."
            
            # Process message stream
            message_stream = response['completion']['messageStream']
            full_message = ""
            
            for chunk in message_stream:
                if chunk and isinstance(chunk, dict) and chunk.get('body'):
                    body_bytes = bytes(chunk['body'])
                    try:
                        body_json = json.loads(body_bytes.decode('utf-8'))
                        if body_json.get('bytes'):
                            decoded_text = base64.b64decode(body_json['bytes']).decode('utf-8')
                            full_message += decoded_text
                    except json.JSONDecodeError:
                        print(f"Error decoding message chunk: {body_bytes}")
            
            return full_message or "No response generated"
            
        except Exception as e:
            print(f"Error sending message to Bedrock: {str(e)}")
            raise 