import os
from dotenv import load_dotenv
from camunda_external_task_client_python3 import ExternalTaskWorker
from camunda_external_task_client_python3 import ExternalTask
import requests
import json
from openai import OpenAI
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI()  # Will automatically use OPENAI_API_KEY from environment

def validate_lead(task: ExternalTask):
    """Validate lead data"""
    variables = task.get_variables()
    lead_name = variables.get('leadName', '')
    email = variables.get('email', '')
    company = variables.get('company', '')

    # Validate required fields
    if not lead_name:
        return {
            'leadValid': False,
            'validationError': 'Lead name is required'
        }

    # Validate email format if provided
    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {
            'leadValid': False,
            'validationError': 'Invalid email format'
        }

    return {
        'leadValid': True,
        'validationMessage': 'Lead data is valid'
    }

def enrich_with_chatgpt(lead_name, company=None):
    """Enrich lead information using ChatGPT"""
    try:
        context = f"Company: {company}" if company else ""
        prompt = f"""Analyze the following lead and provide business insights:
        Lead Name: {lead_name}
        {context}
        
        Please provide:
        1. Industry sector (if apparent)
        2. Company size estimate
        3. Potential pain points
        4. Suggested approach for sales
        5. Key decision makers likely to be involved
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a business analyst specializing in lead analysis."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"ChatGPT enrichment failed: {str(e)}")
        return "Error: Failed to get ChatGPT insights"

def enrich_with_linkedin(lead_name):
    """Simulate LinkedIn data enrichment"""
    try:
        # In a real implementation, you would use LinkedIn's API
        return {
            "company_info": "Sample Company Info",
            "employee_count": "100-500",
            "industry": "Technology",
            "location": "San Francisco, CA"
        }
    except Exception as e:
        logger.error(f"LinkedIn enrichment failed: {str(e)}")
        return {"error": "Failed to get LinkedIn data"}

def enrich_with_company_data(lead_name):
    """Simulate company data enrichment from various sources"""
    try:
        # In a real implementation, you would integrate with company data providers
        return {
            "revenue_range": "$1M-$10M",
            "founded_year": "2015",
            "tech_stack": ["Python", "React", "AWS"],
            "growth_rate": "15%"
        }
    except Exception as e:
        logger.error(f"Company data enrichment failed: {str(e)}")
        return {"error": "Failed to get company data"}

def enrich_lead(task: ExternalTask):
    """Handle lead enrichment task"""
    try:
        variables = task.get_variables()
        lead_name = variables.get('leadName')
        company = variables.get('company')
        
        # Get ChatGPT insights
        chatgpt_insights = enrich_with_chatgpt(lead_name, company)
        
        # Simulate LinkedIn data
        linkedin_data = {
            "company_info": "Sample Company Info",
            "employee_count": "100-500",
            "industry": "Technology",
            "location": "San Francisco, CA"
        }
        
        # Simulate company data
        company_data = {
            "revenue_range": "$1M-$10M",
            "founded_year": "2015",
            "tech_stack": ["Python", "React", "AWS"],
            "growth_rate": "15%"
        }
        
        return {
            'enrichedData': {
                'chatgptInsights': chatgpt_insights,
                'linkedinData': linkedin_data,
                'companyData': company_data
            },
            'enrichmentStatus': 'completed'
        }
    except Exception as e:
        logger.error(f"Lead enrichment failed: {str(e)}")
        return {
            'enrichmentStatus': 'failed',
            'error': str(e)
        }

def store_lead(task: ExternalTask):
    """Store enriched lead data"""
    try:
        variables = task.get_variables()
        enriched_data = variables.get('enrichedData', {})
        
        # Here you would typically store the data in a database
        # For now, we'll just log it
        logger.info(f"Storing enriched lead data: {json.dumps(enriched_data, indent=2)}")
        
        return {
            'storageStatus': 'completed',
            'storedData': enriched_data
        }
    except Exception as e:
        logger.error(f"Failed to store lead data: {str(e)}")
        return {
            'storageStatus': 'failed',
            'error': str(e)
        }

def notify_success(task: ExternalTask):
    """Send success notification"""
    try:
        variables = task.get_variables()
        lead_name = variables.get('leadName')
        
        # Here you would typically send an email or notification
        # For now, we'll just log it
        logger.info(f"Lead enrichment completed successfully for: {lead_name}")
        
        return {
            'notificationStatus': 'sent',
            'message': f"Lead enrichment completed for {lead_name}"
        }
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        return {
            'notificationStatus': 'failed',
            'error': str(e)
        }

def main():
    try:
        # Configure worker
        worker = ExternalTaskWorker(
            worker_id="lead-enrichment-worker",
            base_url=os.getenv('CAMUNDA_CONSOLE_BASE_URL'),
            auth_basic={
                "username": os.getenv('CAMUNDA_CONSOLE_CLIENT_ID'),
                "password": os.getenv('CAMUNDA_CONSOLE_CLIENT_SECRET')
            }
        )
        
        # Subscribe to all topics
        worker.subscribe("validate-lead", validate_lead)
        worker.subscribe("lead-enrichment", enrich_lead)
        worker.subscribe("store-lead", store_lead)
        worker.subscribe("notify-success", notify_success)
        
        logger.info("Starting lead enrichment worker...")
        worker.start()
    except Exception as e:
        logger.error(f"Worker failed to start: {str(e)}")
        raise

if __name__ == "__main__":
    main() 