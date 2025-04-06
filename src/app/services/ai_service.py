import os
import json
import boto3
import base64
import asyncio
import uuid
from openai import OpenAI
from typing import Dict, Any, List
from datetime import datetime, timedelta
from services.order_service import OrderService
import logging
from boto3.session import Session
from botocore.exceptions import ClientError
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # Initialize OpenAI
        try:
            self.openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.assistant_id = os.getenv('OPENAI_ASSISTANT_ID')
            
            # Verify the assistant exists and is accessible
            try:
                self.openai.beta.assistants.retrieve(self.assistant_id)
                logger.info(f"Successfully connected to existing assistant: {self.assistant_id}")
            except Exception as e:
                logger.error(f"Could not find assistant with ID {self.assistant_id}: {str(e)}")
                raise ValueError(f"Could not find assistant with ID {self.assistant_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise

        # Initialize Bedrock
        try:
            self.bedrock_client = boto3.client('bedrock-agent-runtime')
            self.agent_id = os.getenv('BEDROCK_AGENT_ID')
            self.agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
            
            if not self.agent_id or not self.agent_alias_id:
                logger.error("Bedrock agent configuration missing")
                raise ValueError("BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID must be set")
                
            logger.info("Bedrock client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Bedrock client: {str(e)}")
            raise

        # Initialize Azure Text Analytics
        try:
            azure_endpoint = os.getenv('AZURE_ENDPOINT')
            azure_key = os.getenv('AZURE_API_KEY')
            
            if not azure_endpoint or not azure_key:
                logger.error("Azure Text Analytics configuration missing")
                raise ValueError("AZURE_ENDPOINT and AZURE_API_KEY must be set")
            
            self.text_analytics_client = TextAnalyticsClient(
                endpoint=azure_endpoint,
                credential=AzureKeyCredential(azure_key)
            )
            logger.info("Azure Text Analytics client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Azure Text Analytics client: {str(e)}")
            raise
        
        # Initialize DynamoDB
        try:
            self.dynamodb = boto3.resource('dynamodb')
            self.tickets_table = self.dynamodb.Table('cloudmart-tickets')
            logger.info("DynamoDB client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing DynamoDB client: {str(e)}")
            raise
        
        self.order_service = OrderService()
    
    def _create_assistant(self) -> str:
        """Create an OpenAI assistant for customer support"""
        assistant = self.openai.beta.assistants.create(
            name="CloudMart Customer Support",
            instructions="""You are a customer support agent for CloudMart, an e-commerce platform.
            Your role is to assist customers with general inquiries, order issues, and provide helpful information about using the CloudMart platform.
            You don't have direct access to specific product or inventory information.
            Always be polite, patient, and focus on providing excellent customer service.
            If a customer asks about specific products or inventory, politely explain that you don't have access to that information and suggest they check the website or speak with a sales representative.""",
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

    def _cleanup_old_assistants(self) -> None:
        """Clean up old CloudMart assistants to avoid resource waste"""
        try:
            assistants = self.openai.beta.assistants.list(limit=100)
            for assistant in assistants.data:
                if assistant.name == "CloudMart Customer Support":
                    try:
                        logger.info(f"Deleting old assistant: {assistant.id}")
                        self.openai.beta.assistants.delete(assistant.id)
                    except Exception as e:
                        logger.error(f"Error deleting assistant {assistant.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error cleaning up assistants: {str(e)}")

    # OpenAI Methods
    async def create_conversation(self) -> str:
        """Create a new OpenAI conversation thread"""
        try:
            thread = await self.openai.beta.threads.create()
            return thread.id
        except Exception as e:
            logger.error(f"Error creating OpenAI thread: {str(e)}")
            raise

    async def send_message(self, thread_id: str, message: str) -> str:
        """Send a message to OpenAI assistant and get response"""
        try:
            # Create message
            await self.openai.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )

            # Create run with assistant's predefined tools
            run = await self.openai.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )

            # Wait for completion and handle tool calls
            while True:
                run_status = await self.openai.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run_status.status == "requires_action":
                    tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []

                    for tool_call in tool_calls:
                        args = json.loads(tool_call.function.arguments)
                        order_id = args.get("orderId")
                        result = None

                        try:
                            # Check if order exists
                            order = await self.order_service.get_order(order_id)
                            if not order:
                                result = f"Order with ID {order_id} does not exist."
                            elif tool_call.function.name == "delete_order":
                                success = await self.order_service.delete_order(order_id)
                                result = f"Order {order_id} has been successfully deleted." if success else f"Failed to delete order {order_id}."
                            elif tool_call.function.name == "cancel_order":
                                updated_order = await self.order_service.cancel_order(order_id)
                                result = f"Order {order_id} has been successfully canceled. New status: {updated_order['status']}" if updated_order else f"Failed to cancel order {order_id}."
                        except Exception as e:
                            logger.error(f"Error processing order {order_id}: {str(e)}")
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
                elif run_status.status == "completed":
                    break
                elif run_status.status == "failed":
                    logger.error(f"Assistant run failed: {run_status.last_error}")
                    return "I apologize, but I encountered an error while processing your request. Please try again."
                
                await asyncio.sleep(1)
            
            # Get the assistant's response
            messages = await self.openai.beta.threads.messages.list(thread_id=thread_id)
            for message in messages.data:
                if message.role == "assistant":
                    return message.content[0].text.value
            
            return "I apologize, but I couldn't generate a response. Please try again."
            
        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}")
            return "I apologize, but I encountered an error. Please try again."

    # Bedrock Methods
    async def create_bedrock_conversation(self) -> str:
        """Create a new Bedrock conversation ID using timestamp"""
        return str(int(datetime.now().timestamp() * 1000))

    async def send_bedrock_message(self, session_id: str, message: str) -> str:
        """Send a message to Bedrock agent and get response"""
        try:
            logger.info(f"Sending message to Bedrock agent: {message}")
            
            # Prepare request parameters
            params = {
                'agentId': self.agent_id,
                'agentAliasId': self.agent_alias_id,
                'sessionId': session_id,
                'inputText': message
            }
            logger.info(f"Request parameters: {params}")
            
            # Send request to Bedrock agent
            response = self.bedrock_client.invoke_agent(**params)
            logger.info(f"Raw response from Bedrock: {response}")
            
            # Process the event stream response
            full_message = ""
            event_stream = response['completion']
            
            for event in event_stream:
                # Log raw event for debugging
                logger.info(f"Raw event: {event}")
                
                # The event is already a dictionary containing the chunk
                if isinstance(event, dict) and 'chunk' in event:
                    chunk = event['chunk']
                    if isinstance(chunk, dict) and 'bytes' in chunk:
                        # The bytes field contains the actual message as a bytes object
                        message_bytes = chunk['bytes']
                        if isinstance(message_bytes, bytes):
                            full_message += message_bytes.decode('utf-8')
                        else:
                            full_message += str(message_bytes)
                    elif isinstance(chunk, str):
                        full_message += chunk
            
            logger.info(f"Final full message: {full_message}")
            
            if full_message:
                return full_message.strip()
            
            return "I'm sorry, but I couldn't generate a response at the moment. Please try again later."
            
        except Exception as e:
            logger.error(f"Error sending message to Bedrock: {str(e)}")
            raise 

    async def analyze_sentiment_and_save(self, thread: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of a conversation thread and save to DynamoDB"""
        try:
            # Extract all user messages from the thread
            user_messages = [
                message["content"] 
                for message in thread["messages"] 
                if message["role"] == "user"
            ]

            if not user_messages:
                raise ValueError("No user messages found in thread")

            # Analyze sentiment
            results = self.text_analytics_client.analyze_sentiment(
                documents=user_messages,
                show_opinion_mining=True
            )

            # Calculate average sentiment
            sentiment_scores = []
            for result in results:
                if result.is_error:
                    logger.error(f"Error in sentiment analysis: {result.error}")
                    continue
                sentiment_scores.append({
                    'positive': result.confidence_scores.positive,
                    'neutral': result.confidence_scores.neutral,
                    'negative': result.confidence_scores.negative
                })

            if not sentiment_scores:
                raise ValueError("No valid sentiment scores obtained")

            # Calculate averages
            avg_sentiment = {
                'positive': sum(score['positive'] for score in sentiment_scores) / len(sentiment_scores),
                'neutral': sum(score['neutral'] for score in sentiment_scores) / len(sentiment_scores),
                'negative': sum(score['negative'] for score in sentiment_scores) / len(sentiment_scores)
            }

            # Round sentiment scores to 3 decimal places
            avg_sentiment = {k: round(v, 3) for k, v in avg_sentiment.items()}

            # Determine overall sentiment
            if (avg_sentiment['positive'] > avg_sentiment['neutral'] and 
                avg_sentiment['positive'] > avg_sentiment['negative']):
                overall_sentiment = 'positive'
            elif (avg_sentiment['negative'] > avg_sentiment['neutral'] and 
                  avg_sentiment['negative'] > avg_sentiment['positive']):
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'

            # Prepare item for DynamoDB
            item = {
                'id': str(uuid.uuid4())[:8],
                'threadId': thread['id'],
                'conversation': json.dumps(thread['messages']),
                'sentimentScores': avg_sentiment,
                'overallSentiment': overall_sentiment,
                'createdAt': datetime.now().isoformat()
            }

            # Save to DynamoDB
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.tickets_table.put_item(Item=item)
            )

            return {
                'threadId': thread['id'],
                'sentimentScores': avg_sentiment,
                'overallSentiment': overall_sentiment,
                'id': item['id']
            }

        except Exception as e:
            logger.error(f"Error in analyze_sentiment_and_save: {str(e)}")
            raise 