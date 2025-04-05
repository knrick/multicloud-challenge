import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from models.ticket import Ticket, Message
import os
import json
from datetime import datetime
from openai import OpenAI
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TicketService:
    def __init__(self):
        try:
            self.dynamodb = boto3.resource('dynamodb')
            self.table = self.dynamodb.Table('cloudmart-tickets')
            
            # Check if OPENAI_API_KEY is set
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.error("OPENAI_API_KEY environment variable is not set")
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            
            self.openai = OpenAI()
            logger.info("OpenAI client initialized successfully")
            
            # Initialize OpenAI assistant if not exists
            self.assistant_id = os.getenv('OPENAI_ASSISTANT_ID')
            if not self.assistant_id:
                logger.info("No assistant ID found, creating new assistant")
                self.assistant_id = self._create_assistant()
                logger.info(f"Created new assistant with ID: {self.assistant_id}")
        except Exception as e:
            logger.error(f"Error initializing TicketService: {str(e)}")
            raise
    
    def _create_assistant(self) -> str:
        """Create an OpenAI assistant for customer support"""
        assistant = self.openai.beta.assistants.create(
            name="CloudMart Customer Support",
            instructions="""You are a customer support agent for CloudMart, an e-commerce platform.
            Your role is to assist customers with general inquiries, order issues, and provide helpful information about using the CloudMart platform.
            You don't have direct access to specific product or inventory information.
            Always be polite, patient, and focus on providing excellent customer service.
            If a customer asks about specific products or inventory, politely explain that you don't have access to that information and suggest they check the website or speak with a sales representative.""",
            model="gpt-4-turbo-preview"
        )
        return assistant.id

    async def _get_ai_response(self, thread_id: str, message: str) -> str:
        """Get AI response for a message in a thread"""
        # Add the message to the thread
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
        
        # Wait for completion
        while run.status == "queued" or run.status == "in_progress":
            run = self.openai.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            await asyncio.sleep(1)
        
        # Get the assistant's response
        messages = self.openai.beta.threads.messages.list(thread_id=thread_id)
        for message in messages.data:
            if message.role == "assistant":
                return message.content[0].text.value
        
        return "No response generated"

    async def list_tickets(self) -> List[Ticket]:
        """List all tickets"""
        try:
            logger.info("Attempting to list tickets")
            response = self.table.scan()
            items = response.get('Items', [])
            logger.info(f"Found {len(items)} tickets")
            
            tickets = []
            for item in items:
                try:
                    ticket = Ticket(**item)
                    tickets.append(ticket)
                except Exception as e:
                    logger.error(f"Error parsing ticket: {str(e)}, Data: {item}")
                    continue
            
            return tickets
        except ClientError as e:
            logger.error(f"DynamoDB error scanning tickets: {e.response['Error']['Message']}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing tickets: {str(e)}")
            return []

    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get a specific ticket"""
        try:
            response = self.table.get_item(Key={'id': ticket_id})
            item = response.get('Item')
            return Ticket(**item) if item else None
        except ClientError as e:
            print(f"Error getting ticket: {e.response['Error']['Message']}")
            return None

    async def create_ticket(self, message: str) -> Ticket:
        """Create a new ticket and start conversation"""
        # Create a new thread
        thread = self.openai.beta.threads.create()
        
        # Create new ticket
        new_ticket = Ticket(thread_id=thread.id)
        
        # Add initial message
        user_message = Message(role="user", content=message)
        new_ticket.messages.append(user_message)
        
        # Get AI response
        ai_response = await self._get_ai_response(thread.id, message)
        ai_message = Message(role="assistant", content=ai_response)
        new_ticket.messages.append(ai_message)
        
        try:
            self.table.put_item(Item=json.loads(new_ticket.model_dump_json()))
            return new_ticket
        except ClientError as e:
            print(f"Error creating ticket: {e.response['Error']['Message']}")
            raise

    async def send_message(self, ticket_id: str, message: str) -> Optional[Ticket]:
        """Send a message in an existing ticket"""
        try:
            ticket = await self.get_ticket(ticket_id)
            if not ticket or ticket.status == "closed":
                return None
            
            # Add user message
            user_message = Message(role="user", content=message)
            ticket.messages.append(user_message)
            
            # Get AI response
            ai_response = await self._get_ai_response(ticket.thread_id, message)
            ai_message = Message(role="assistant", content=ai_response)
            ticket.messages.append(ai_message)
            
            # Update timestamp
            ticket.updated_at = datetime.utcnow()
            
            self.table.put_item(Item=json.loads(ticket.model_dump_json()))
            return ticket
        except ClientError as e:
            print(f"Error sending message: {e.response['Error']['Message']}")
            return None

    async def close_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Close a ticket"""
        try:
            ticket = await self.get_ticket(ticket_id)
            if not ticket:
                return None
            
            ticket.status = "closed"
            ticket.updated_at = datetime.utcnow()
            
            self.table.put_item(Item=json.loads(ticket.model_dump_json()))
            return ticket
        except ClientError as e:
            print(f"Error closing ticket: {e.response['Error']['Message']}")
            return None 