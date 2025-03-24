import os
import re
import time
from dotenv import load_dotenv
from pyzeebe import ZeebeWorker, Job, create_camunda_cloud_channel, ZeebeClient
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Camunda 8 SaaS configuration
ZEEBE_ADDRESS = os.getenv('ZEEBE_ADDRESS')
ZEEBE_CLIENT_ID = os.getenv('ZEEBE_CLIENT_ID')
ZEEBE_CLIENT_SECRET = os.getenv('ZEEBE_CLIENT_SECRET')
ZEEBE_AUTHORIZATION_SERVER_URL = os.getenv('ZEEBE_AUTHORIZATION_SERVER_URL')
CAMUNDA_CLUSTER_ID = os.getenv('CAMUNDA_CLUSTER_ID')
CAMUNDA_REGION = os.getenv('CAMUNDA_REGION')

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return True  # Email is optional
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

async def handle_validate_lead(job: Job) -> Dict[str, Any]:
    """Handle lead validation task"""
    try:
        variables = job.variables
        lead_name = variables.get('leadName', '')
        email = variables.get('email', '')
        company = variables.get('company', '')

        logger.info(f"Validating lead: {lead_name}, {email}, {company}")

        # Validate required fields
        if not lead_name:
            return {
                'leadValid': False,
                'validationMessage': 'Lead name is required'
            }

        # Validate email format if provided
        if email and not validate_email(email):
            return {
                'leadValid': False,
                'validationMessage': 'Invalid email format'
            }

        # All validations passed
        return {
            'leadValid': True,
            'validationMessage': 'Lead data is valid'
        }

    except Exception as e:
        logger.error(f"Error validating lead: {str(e)}")
        return {
            'leadValid': False,
            'validationMessage': f'Error during validation: {str(e)}'
        }

async def handle_enrich_lead(job: Job) -> Dict[str, Any]:
    """Handle lead enrichment task"""
    try:
        variables = job.variables
        lead_name = variables.get('leadName', '')
        email = variables.get('email', '')
        company = variables.get('company', '')

        logger.info(f"Enriching lead: {lead_name}, {email}, {company}")

        # Simulate enrichment
        enriched_data = {
            "insights": f"Lead {lead_name} shows high potential in {company}",
            "score": 85
        }

        linkedin_data = {
            "profile": f"linkedin.com/in/{lead_name.lower().replace(' ', '-')}",
            "connections": 500
        }

        company_data = {
            "name": company,
            "industry": "Technology",
            "size": "50-200 employees"
        }

        return {
            'enrichedData': enriched_data,
            'linkedinData': linkedin_data,
            'companyData': company_data
        }

    except Exception as e:
        logger.error(f"Error enriching lead: {str(e)}")
        raise

async def handle_store_lead(job: Job) -> Dict[str, Any]:
    """Handle lead storage task"""
    try:
        variables = job.variables
        enriched_data = variables.get('enrichedData', {})
        linkedin_data = variables.get('linkedinData', {})
        company_data = variables.get('companyData', {})

        logger.info("Storing enriched lead data")
        # Simulate storage
        return {
            'storageSuccess': True
        }

    except Exception as e:
        logger.error(f"Error storing lead: {str(e)}")
        return {
            'storageSuccess': False
        }

async def handle_notify_success(job: Job) -> Dict[str, Any]:
    """Handle success notification task"""
    try:
        variables = job.variables
        lead_name = variables.get('leadName', '')
        enriched_data = variables.get('enrichedData', {})

        logger.info(f"Sending success notification for lead: {lead_name}")
        # Simulate notification
        return {
            'notificationSent': True
        }

    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return {
            'notificationSent': False
        }

async def main():
    # Create a channel to Camunda 8 SaaS
    channel = create_camunda_cloud_channel(
        client_id=ZEEBE_CLIENT_ID,
        client_secret=ZEEBE_CLIENT_SECRET,
        cluster_id=CAMUNDA_CLUSTER_ID,
        region=CAMUNDA_REGION
    )
    
    # Create a worker and client
    worker = ZeebeWorker(channel)
    client = ZeebeClient(channel)
    
    # Register task handlers
    @worker.task(task_type="validate-lead")
    async def validate_lead_task(job: Job) -> Dict[str, Any]:
        return await handle_validate_lead(job)
    
    @worker.task(task_type="lead-enrichment")
    async def enrich_lead_task(job: Job) -> Dict[str, Any]:
        return await handle_enrich_lead(job)
    
    @worker.task(task_type="store-lead")
    async def store_lead_task(job: Job) -> Dict[str, Any]:
        return await handle_store_lead(job)
    
    @worker.task(task_type="notify-success")
    async def notify_success_task(job: Job) -> Dict[str, Any]:
        return await handle_notify_success(job)
    
    logger.info("Starting worker...")
    await worker.work()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())