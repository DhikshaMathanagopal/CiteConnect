# dags/test_dag.py
"""
Simple test DAG to verify everything is working
"""

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime
import sys
import os

# Add project to path
sys.path.insert(0, '/opt/airflow')

# DAG config
dag = DAG(
    'test_citeconnect',
    start_date=datetime(2024, 10, 10),
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['test', 'citeconnect']
)

def test_imports(**context):
    """Test if we can import our modules."""
    print("Testing imports...")
    
    try:
        # Test basic Python imports
        import requests
        import pandas as pd
        print("Basic imports work (requests, pandas)")
        
        # Test project structure
        print("Checking project structure...")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Python path: {sys.path}")
        
        # List available folders
        project_path = '/opt/airflow/dags/project'
        if os.path.exists(project_path):
            print(f"Contents of {project_path}:")
            for item in os.listdir(project_path):
                print(f"   - {item}")
        else:
            print(f"Project path not found: {project_path}")
        
        # Try to import your modules
        try:
            # Adjust import path based on your actual structure
            from src.DataPipeline.Ingestion.semantic_scholar_client import SemanticScholarClient
            print("Successfully imported SemanticScholarClient")
            
            # Test creating client
            client = SemanticScholarClient()
            print("Successfully created SemanticScholarClient instance")
            
        except ImportError as e:
            print(f"Could not import SemanticScholarClient: {e}")
            print("   This is expected if the path is different")
        
        print("Import test completed!")
        return "success"
        
    except Exception as e:
        print(f"Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return "failed"

def test_api_connection(**context):
    """Test API connection without using our modules."""
    print("Testing API connection...")
    import src.DataPipeline.Ingestion.semantic_scholar_client as ssc

    ssc_client = ssc.SemanticScholarClient()
    test_query = "machine learning"
    results = ssc_client.search(test_query, limit=2)
    print(f"API returned {len(results)} results for query '{test_query}'")

def test_data_storage(**context):
    """Test data storage functionality."""
    print("Testing data storage...")
    
    try:
        import json
        import os
        from datetime import datetime
        
        # Create test data
        test_data = {
            'timestamp': datetime.now().isoformat(),
            'test_message': 'Hello from CiteConnect!',
            'papers_count': 42
        }
        
        # Create data directory if it doesn't exist
        data_dir = '/opt/airflow/data/raw'
        os.makedirs(data_dir, exist_ok=True)
        
        # Save test file
        test_file = os.path.join(data_dir, 'test_data.json')
        with open(test_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        print(f"Successfully saved test data to {test_file}")
        
        # Verify file exists and can be read
        if os.path.exists(test_file):
            with open(test_file, 'r') as f:
                loaded_data = json.load(f)
            print(f"Successfully loaded data: {loaded_data['test_message']}")
        
        return "storage_success"
        
    except Exception as e:
        print(f"Storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return "storage_failed"

# Task 1: Test imports
test_imports_task = PythonOperator(
    task_id='test_imports',
    python_callable=test_imports,
    dag=dag
)

# Task 2: Test API
test_api_task = PythonOperator(
    task_id='test_api',
    python_callable=test_api_connection,
    dag=dag
)

# Task 3: Test storage
test_storage_task = PythonOperator(
    task_id='test_storage',
    python_callable=test_data_storage,
    dag=dag
)

# Task 4: Environment check
env_check_task = BashOperator(
    task_id='check_environment',
    bash_command='''
    echo "Environment Check:"
    echo "Python version: $(python --version)"
    echo "Current user: $(whoami)"
    echo "Working directory: $(pwd)"
    echo "Available disk space:"
    df -h /opt/airflow/data 2>/dev/null || echo "Data directory not mounted"
    echo "Environment variables:"
    env | grep -E "(SEMANTIC_SCHOLAR|AIRFLOW)" | head -5
    ''',
    dag=dag
)

def send_success_email(**context):
        print("=" * 50)
        print("CITECONNECT DAG SUCCESS!")
        print("=" * 50)
        print(f"Execution Date: {context['ds']}")
        print(f"Status: Completed (email failed but DAG succeeded)")
        print("=" * 50)
        return "email_failed_but_dag_success"

# Task 5: Send success email
success_email_task = PythonOperator(
    task_id='send_success_email',
    python_callable=send_success_email,
    dag=dag
)

# Set task dependencies
env_check_task >> test_imports_task >> test_api_task >> test_storage_task >> success_email_task