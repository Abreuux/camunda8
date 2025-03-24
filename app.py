from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import json
import os
from dotenv import load_dotenv
import logging
from pyzeebe import ZeebeClient, create_camunda_cloud_channel
import asyncio
import nest_asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable nested event loops
nest_asyncio.apply()

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Create a global event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def run_async(coro):
    """Helper function to run async code in Flask routes"""
    try:
        # Create new event loop for this thread if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Error in run_async: {str(e)}")
        raise

def get_zeebe_client():
    """Create and return a new Zeebe client instance"""
    channel = create_camunda_cloud_channel(
        client_id=os.getenv('ZEEBE_CLIENT_ID'),
        client_secret=os.getenv('ZEEBE_CLIENT_SECRET'),
        cluster_id=os.getenv('CAMUNDA_CLUSTER_ID'),
        region=os.getenv('CAMUNDA_REGION')
    )
    return ZeebeClient(channel)

@app.route('/')
def index():
    """Render the frontend form"""
    return render_template('index.html')

@app.route('/api/leads', methods=['POST'])
def create_lead():
    """Create a new lead and start a process instance"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('leadName'):
            return jsonify({"error": "Lead name is required"}), 400
            
        # Create variables for the process
        variables = {
            "leadName": data.get('leadName'),
            "email": data.get('email', ''),
            "company": data.get('company', '')
        }
        
        logger.info(f"Starting process with variables: {json.dumps(variables)}")
        
        # Create a new client for this request
        client = get_zeebe_client()
        
        # Start process instance directly
        process_instance = run_async(
            client.run_process(
                bpmn_process_id="lead-enrichment",
                variables=variables
            )
        )
        
        logger.info(f"Process instance started: {process_instance}")
        
        return jsonify({
            "message": "Lead enrichment process started",
            "processInstanceId": str(process_instance),
            "status": "processing"
        })
        
    except Exception as e:
        logger.error(f"Error starting process: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": str(e)}), 500

def get_oauth_token():
    """Get OAuth token for Camunda API"""
    try:
        response = requests.post(
            os.getenv('ZEEBE_AUTHORIZATION_SERVER_URL'),
            data={
                'client_id': os.getenv('ZEEBE_CLIENT_ID'),
                'client_secret': os.getenv('ZEEBE_CLIENT_SECRET'),
                'audience': 'zeebe.camunda.io',
                'grant_type': 'client_credentials'
            }
        )
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        logger.error(f"Failed to get OAuth token: {str(e)}")
        raise

@app.route('/webhook/9024e879-8547-49d1-8a9a-4487e3184f9f', methods=['POST'])
def webhook_handler():
    """Handle webhook from Camunda"""
    try:
        # Log request details
        logger.info(f"Received webhook request")
        logger.info(f"Content-Type: {request.headers.get('Content-Type', 'Not specified')}")
        logger.info(f"Raw data: {request.get_data(as_text=True)}")
        
        # Parse webhook data
        if request.is_json:
            webhook_data = request.json
        else:
            return jsonify({"error": "Expected JSON data"}), 400
            
        logger.info(f"Webhook data received: {json.dumps(webhook_data)}")
        
        # Extract variables from webhook data
        variables = webhook_data.get('data', {})
        if not variables:
            return jsonify({"error": "No data found in webhook payload"}), 400
        
        # Create a new client for this request
        client = get_zeebe_client()
        
        # Start process instance
        process_instance_key = run_async(
            client.run_process(
                bpmn_process_id="lead-enrichment",
                variables=variables
            )
        )
        
        logger.info(f"Started process instance with key: {process_instance_key}")
        
        return jsonify({
            "message": "Lead enrichment process started",
            "processInstanceId": str(process_instance_key),
            "status": "processing"
        })
    except Exception as e:
        logger.error(f"Error in webhook handler: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": str(e)}), 500

@app.route('/api/leads/<process_id>', methods=['GET'])
def get_lead_status(process_id):
    """Get lead enrichment status"""
    try:
        # Create a new client for this request
        client = get_zeebe_client()
        
        # Get process instance topology
        topology = run_async(client.topology())
        logger.info(f"Zeebe topology: {topology}")
        
        # For now, return a simple status since we can't easily get detailed status
        return jsonify({
            "processId": process_id,
            "status": "ACTIVE",
            "variables": {}
        })
    except Exception as e:
        logger.error(f"Error getting lead status: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 