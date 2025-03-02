# SMS Messaging Server

A Python server that periodically sends text messages to a list of phone numbers stored in a JSON file. The server uses Twilio for sending and receiving messages and includes an opt-out mechanism.

## Features

- Send text messages to multiple recipients using Twilio
- Process incoming messages with opt-out/opt-in functionality
- Schedule messages to be sent every minute (configurable)
- Store recipient data in a JSON file

## Setup

### Prerequisites

- Python 3.7+
- Twilio account (Account SID, Auth Token, and a Twilio phone number)

### Installation

1. Clone this repository
2. Install dependencies:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on the `.env.example` file:
   ```
   cp .env.example .env
   ```
4. Update the `.env` file with your Twilio credentials:
   ```
   TWILIO_ACCOUNT_SID=your_account_sid_here
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_PHONE_NUMBER=+15551234567  # Your Twilio phone number with country code
   ```

## Usage

### Running the Server

Always make sure your virtual environment is activated before running the server:

```
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Then run the server with:

```
python app.py
```

If port 5000 is already in use (common on macOS), specify a different port:

```
PORT=5001 python app.py
```

The server will start on the specified port (5000 by default, configurable in the `.env` file).

### Webhook Configuration

To receive incoming messages, you'll need to configure your Twilio phone number to use the `/webhook/sms` endpoint as a webhook. If you're running the server locally, you can use a tool like ngrok to expose your local server:

1. Install ngrok
2. Run ngrok:
   ```
   ngrok http 5000  # Or whatever port you're using
   ```
3. Use the generated HTTPS URL in your Twilio phone number's webhook configuration:
   ```
   https://your-ngrok-url.ngrok.io/webhook/sms
   ```

### Managing Recipients

Recipients are stored in the `phone_numbers.json` file. Each entry includes:

- Phone number (key)
- Name
- Opt-out status
- Last message sent timestamp

Example:

```json
{
  "5512324519": {
    "name": "Test User",
    "opted_out": false,
    "last_message_sent": null
  }
}
```

### Opt-Out Mechanism

Recipients can opt out by texting "STOP" to your Twilio number. They can opt back in by texting "START".

## Customization

### Changing the Message Content

Edit the `send_scheduled_messages` function in `app.py` to customize the message:

```python
message = "Your custom message here. Reply STOP to opt out."
```

### Changing the Schedule

Modify the scheduler in the `setup_scheduler` function to change how frequently messages are sent:

```python
# Currently set to every minute
scheduler.add_job(send_scheduled_messages, 'interval', minutes=1)

# Other examples:
# Every 5 minutes
# scheduler.add_job(send_scheduled_messages, 'interval', minutes=5)

# Every hour
# scheduler.add_job(send_scheduled_messages, 'interval', hours=1)

# Daily at a specific time (e.g., 2:30 PM)
# scheduler.add_job(send_scheduled_messages, 'cron', hour=14, minute=30)
```

## License

MIT
