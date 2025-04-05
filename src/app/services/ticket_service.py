import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from models.ticket import Ticket, TicketCreate, Message
import os
import json
from datetime import datetime
from openai import OpenAI
import asyncio

class TicketService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('cloudmart-tickets')
        self.openai = OpenAI()
        
        # Initialize OpenAI assistant if not exists
        self.assistant_id = os.getenv('OPENAI_ASSISTANT_ID')
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
            For complex issues, explain that a human support agent will review the ticket.""",
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
            response = self.table.scan()
            items = response.get('Items', [])
            return [Ticket(**item) for item in items]
        except ClientError as e:
            print(f"Error scanning tickets: {e.response['Error']['Message']}")
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

    async def create_ticket(self, ticket: TicketCreate) -> Ticket:
        """Create a new ticket and start conversation"""
        new_ticket = Ticket(**ticket.model_dump())
        
        # Create a new thread
        thread = self.openai.beta.threads.create()
        new_ticket.thread_id = thread.id
        
        # Add initial message
        initial_message = Message(
            role="user",
            content=f"Title: {ticket.title}\nDescription: {ticket.description}"
        )
        new_ticket.messages.append(initial_message)
        
        # Get AI response
        ai_response = await self._get_ai_response(thread.id, initial_message.content)
        ai_message = Message(role="assistant", content=ai_response)
        new_ticket.messages.append(ai_message)
        
        try:
            self.table.put_item(Item=json.loads(new_ticket.model_dump_json()))
            return new_ticket
        except ClientError as e:
            print(f"Error creating ticket: {e.response['Error']['Message']}")
            raise

    async def continue_conversation(self, ticket_id: str, message: str) -> Optional[Ticket]:
        """Continue conversation on an existing ticket"""
        try:
            ticket = await self.get_ticket(ticket_id)
            if not ticket:
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
            print(f"Error continuing conversation: {e.response['Error']['Message']}")
            return None

    async def update_ticket(self, ticket_id: str, status: str) -> Optional[Ticket]:
        """Update ticket status"""
        try:
            ticket = await self.get_ticket(ticket_id)
            if not ticket:
                return None
            
            # Update status and timestamp
            ticket.status = status
            ticket.updated_at = datetime.utcnow()
            
            self.table.put_item(Item=json.loads(ticket.model_dump_json()))
            return ticket
        except ClientError as e:
            print(f"Error updating ticket: {e.response['Error']['Message']}")
            return None 