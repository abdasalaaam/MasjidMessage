import os
import json
import logging
from datetime import datetime
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# JSON file path
PHONE_NUMBERS_FILE = "phone_numbers.json"

# Create Twilio client
try:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logger.info("Twilio client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Twilio client: {e}")
    twilio_client = None


def load_phone_numbers():
    """Load phone numbers from JSON file."""
    try:
        with open(PHONE_NUMBERS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.warning(f"Phone numbers file not found: {PHONE_NUMBERS_FILE}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in phone numbers file: {PHONE_NUMBERS_FILE}")
        return {}


def save_phone_numbers(phone_numbers):
    """Save phone numbers to JSON file."""
    try:
        with open(PHONE_NUMBERS_FILE, 'w') as file:
            json.dump(phone_numbers, file, indent=4)
        logger.info(f"Phone numbers saved to {PHONE_NUMBERS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save phone numbers: {e}")


def send_message(to_number, message):
    """Send a text message using Twilio API."""
    if not twilio_client:
        logger.error("Twilio client not initialized, cannot send message")
        return False

    try:
        # Format the phone number to include the '+' prefix if missing
        if not to_number.startswith('+'):
            to_number = f"+{to_number}"
            
        message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        logger.info(f"Message sent to {to_number}: {message.sid}")
        
        # Update the last message sent timestamp
        phone_numbers = load_phone_numbers()
        stripped_number = to_number.lstrip('+')
        if stripped_number in phone_numbers:
            phone_numbers[stripped_number]["last_message_sent"] = datetime.now().isoformat()
            save_phone_numbers(phone_numbers)
            
        return True
    except Exception as e:
        logger.error(f"Failed to send message to {to_number}: {e}")
        return False


def send_scheduled_messages():
    """Send scheduled messages to all non-opted-out numbers."""
    logger.info("Sending scheduled messages")
    phone_numbers = load_phone_numbers()
    message = "This is a scheduled message from our service. Reply STOP to opt out."
    
    sent_count = 0
    skipped_count = 0
    
    for number, data in phone_numbers.items():
        if data.get("opted_out", False):
            logger.info(f"Skipping {number} (opted out)")
            skipped_count += 1
            continue
            
        if send_message(number, message):
            sent_count += 1
    
    logger.info(f"Scheduled messages sent: {sent_count}, skipped: {skipped_count}")


@app.route("/webhook/sms", methods=["POST"])
def sms_webhook():
    """Handle incoming SMS messages."""
    # Get the incoming message details
    from_number = request.values.get("From", "").lstrip('+')
    body = request.values.get("Body", "").strip().lower()
    
    logger.info(f"Received message from {from_number}: {body}")
    
    # Create a TwiML response
    resp = MessagingResponse()
    
    # If the message is "stop", mark the number as opted out
    if body == "stop":
        phone_numbers = load_phone_numbers()
        
        if from_number in phone_numbers:
            phone_numbers[from_number]["opted_out"] = True
            save_phone_numbers(phone_numbers)
            logger.info(f"Marked {from_number} as opted out")
            resp.message("You have been unsubscribed from our messages. Reply START to resubscribe.")
        else:
            # Add the number if it doesn't exist
            phone_numbers[from_number] = {
                "name": "Unknown",
                "opted_out": True,
                "last_message_sent": None
            }
            save_phone_numbers(phone_numbers)
            logger.info(f"Added {from_number} as opted out")
            resp.message("You have been unsubscribed from our messages. Reply START to resubscribe.")
    
    # If the message is "start", mark the number as opted in
    elif body == "start":
        phone_numbers = load_phone_numbers()
        
        if from_number in phone_numbers:
            phone_numbers[from_number]["opted_out"] = False
            save_phone_numbers(phone_numbers)
            logger.info(f"Marked {from_number} as opted in")
            resp.message("You have been resubscribed to our messages. Reply STOP to unsubscribe.")
        else:
            # Add the number if it doesn't exist
            phone_numbers[from_number] = {
                "name": "Unknown",
                "opted_out": False,
                "last_message_sent": None
            }
            save_phone_numbers(phone_numbers)
            logger.info(f"Added {from_number} as opted in")
            resp.message("You have been subscribed to our messages. Reply STOP to unsubscribe.")
    
    return str(resp)


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


def setup_scheduler():
    """Set up the scheduler for tasks."""
    scheduler = BackgroundScheduler()
    # Schedule the message to run every minute
    scheduler.add_job(send_scheduled_messages, 'interval', minutes=1)
    scheduler.start()
    logger.info("Scheduler started - messages will be sent every minute")
    return scheduler


if __name__ == "__main__":
    # Set up the scheduler
    scheduler = setup_scheduler()
    
    # Start the Flask app
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False) 