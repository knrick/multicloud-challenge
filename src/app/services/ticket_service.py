import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from models.ticket import Ticket, Message
import os
import json
from datetime import datetime
import asyncio
import logging
from services.ai_service import AIService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TicketService:
    def __init__(self):
        try:
            self.dynamodb = boto3.resource('dynamodb')
            self.table = self.dynamodb.Table('cloudmart-tickets')
            self.ai_service = AIService()
            logger.info("TicketService initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing TicketService: {str(e)}")
            raise

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
            logger.error(f"Error getting ticket: {e.response['Error']['Message']}")
            return None

    async def create_ticket(self, message: str) -> Ticket:
        """Create a new ticket and start conversation"""
        try:
            # Create a new conversation with AI service
            thread_id = await self.ai_service.create_conversation()
            
            # Create new ticket
            new_ticket = Ticket(thread_id=thread_id)
            
            # Add initial message
            user_message = Message(role="user", content=message)
            new_ticket.messages.append(user_message)
            
            # Get AI response
            ai_response = await self.ai_service.send_message(thread_id, message)
            ai_message = Message(role="assistant", content=ai_response)
            new_ticket.messages.append(ai_message)
            
            # Save to DynamoDB
            self.table.put_item(Item=json.loads(new_ticket.model_dump_json()))
            return new_ticket
        except Exception as e:
            logger.error(f"Error creating ticket: {str(e)}")
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
            ai_response = await self.ai_service.send_message(ticket.thread_id, message)
            ai_message = Message(role="assistant", content=ai_response)
            ticket.messages.append(ai_message)
            
            # Update timestamp
            ticket.updated_at = datetime.utcnow()
            
            # Save to DynamoDB
            self.table.put_item(Item=json.loads(ticket.model_dump_json()))
            return ticket
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return None

    async def close_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Close a ticket"""
        try:
            ticket = await self.get_ticket(ticket_id)
            if not ticket:
                return None
            
            ticket.status = "closed"
            ticket.updated_at = datetime.utcnow()
            
            # Save the ticket
            ticket_data = json.loads(ticket.model_dump_json())
            self.table.put_item(Item=ticket_data)
            return ticket
        except ClientError as e:
            logger.error(f"Error closing ticket: {e.response['Error']['Message']}")
            return None

    async def update_ticket_sentiment(self, ticket_id: str, sentiment_data: dict) -> Optional[Ticket]:
        """Update ticket with sentiment analysis results"""
        try:
            ticket = await self.get_ticket(ticket_id)
            if not ticket:
                return None
            
            # Update sentiment data
            ticket.sentimentScores = sentiment_data['sentimentScores']
            ticket.overallSentiment = sentiment_data['overallSentiment']
            ticket.updated_at = datetime.utcnow()
            
            # Save the updated ticket
            ticket_data = json.loads(ticket.model_dump_json())
            self.table.put_item(Item=ticket_data)
            return ticket
        except ClientError as e:
            logger.error(f"Error updating ticket sentiment: {e.response['Error']['Message']}")
            return None

    async def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a ticket"""
        try:
            # First check if ticket exists
            ticket = await self.get_ticket(ticket_id)
            if not ticket:
                return False
            
            # Delete the ticket
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.table.delete_item(Key={'id': ticket_id})
            )
            return True
        except ClientError as e:
            logger.error(f"Error deleting ticket: {e.response['Error']['Message']}")
            return False 