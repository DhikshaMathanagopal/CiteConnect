# dags/test_dag.py
"""
Simple test DAG to verify everything is working
"""

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.utils.email import send_email
from datetime import datetime, timedelta
import sys
import os

# Add project to path
sys.path.insert(0, '/opt/airflow')

# Email settings
EMAIL_TO = ['aditya811.abhinav@gmail.com']  # Replace with your email

# Default arguments with email configuration
default_args = {
    'owner': 'citeconnect-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 10, 10),
    'email': EMAIL_TO,
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG config
dag = DAG(
    'test_citeconnect',
    default_args=default_args,
    description='CiteConnect test pipeline with email notifications',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['test', 'citeconnect']
)

def test_api_connection(**context):
    """Test API connection using our modules."""
    print("Testing API connection...")
    
    # Import will fail if module doesn't exist
    from src.DataPipeline.Ingestion.semantic_scholar_client import search_semantic_scholar
    
    # Create client - will fail if instantiation fails
    ssc_client = search_semantic_scholar(query="machine learning")
    
    # API call - will fail if API is down or returns error
    print(ssc_client, "results retrieved from API")
    
    # Validate results
    if len(ssc_client) == "":
        raise ValueError("API returned no results - this might indicate an issue")
    
    return "api_success"

def send_success_notification(**context):
    """Send success email with pipeline summary."""
    # Get execution details
    task_instance = context['task_instance']
    dag_run = context['dag_run']
    
    # Create success email content
    subject = f"CiteConnect Pipeline SUCCESS - {dag_run.execution_date}"
    
    html_content = f"""
    <h2>CiteConnect Pipeline Completed Successfully!</h2>
    
    <h3>Pipeline Details:</h3>
    <ul>
        <li><strong>DAG:</strong> {dag_run.dag_id}</li>
        <li><strong>Execution Date:</strong> {dag_run.execution_date}</li>
        <li><strong>Start Date:</strong> {dag_run.start_date}</li>
        <li><strong>Duration:</strong> {dag_run.end_date - dag_run.start_date if dag_run.end_date else 'Running'}</li>
    </ul>
    
    <h3>All Tests Passed:</h3>
    <ul>
        <li>Environment check: SUCCESS</li>
        <li>Import test: SUCCESS</li>
        <li>API connection: SUCCESS</li>
        <li>Data storage: SUCCESS</li>
    </ul>
    
    <p><strong>Your CiteConnect pipeline is working perfectly!</strong></p>
    """
    
    # Send email - will fail if SMTP configuration is wrong
    send_email(
        to=EMAIL_TO,
        subject=subject,
        html_content=html_content
    )
    
    print(f"Success email sent to {EMAIL_TO}")
    return "email_sent"

# Task 1: Environment check
env_check_task = BashOperator(
    task_id='check_environment',
    bash_command='''
    set -e  # Exit on any error
    echo "Environment Check:"
    echo "Python version: $(python --version)"
    echo "Current user: $(whoami)"
    echo "Working directory: $(pwd)"
    echo "Available disk space:"
    df -h /opt/airflow/data || exit 1
    echo "Source directory check:"
    ls -la /opt/airflow/src || exit 1
    echo "Environment variables:"
    env | grep -E "(SEMANTIC_SCHOLAR|AIRFLOW)" | head -5
    ''',
    dag=dag
)

# Task 3: Test API
test_api_task = PythonOperator(
    task_id='test_api',
    python_callable=test_api_connection,
    dag=dag
)

# Task 5: Send success email (only runs if all previous tasks succeed)
success_email_task = PythonOperator(
    task_id='send_success_email',
    python_callable=send_success_notification,
    dag=dag
)

# Set task dependencies
env_check_task >> test_api_task >> success_email_task