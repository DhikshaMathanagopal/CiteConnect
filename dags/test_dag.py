from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.utils.email import send_email
from datetime import datetime, timedelta
import sys
import json
import os

# Add project to path
sys.path.insert(0, '/opt/airflow')

# Email settings
EMAIL_TO = ['anushasrini2001@gmail.com']  # Replace with your email

# Default arguments with email configuration
default_args = {
    'owner': 'citeconnect-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 10, 10),
    'email': EMAIL_TO,
    'email_on_failure': True,
    'email_on_retry': False,
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

def check_env_variables():
    semantic_scholar_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
    unpaywall_email = os.getenv('UNPAYWALL_EMAIL')
    core_api_key = os.getenv('CORE_API_KEY')

    print("Checking environment variables...")
    print(f"SEMANTIC_SCHOLAR_API_KEY: {'Set' if semantic_scholar_key else 'Not Set'}")
    print(f"UNPAYWALL_EMAIL: {'Set' if unpaywall_email else 'Not Set'}")
    print(f"CORE_API_KEY: {'Set' if core_api_key else 'Not Set'}")

def check_gcs_connection():
    from google.cloud import storage
    from google.auth import default
    gcp_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    gcs_bucket_name = os.getenv('GCS_BUCKET_NAME')
    gcs_project_id = os.getenv('GCS_PROJECT_ID')

    print("Checking GCS connection...")
    print(f"GOOGLE_APPLICATION_CREDENTIALS: {'Set' if gcp_credentials else 'Not Set'}")
    print(f"GCS_BUCKET_NAME: {'Set' if gcs_bucket_name else 'Not Set'}")

    with open(gcp_credentials, 'r') as f:
        cred_data = json.load(f)
        project_id = cred_data.get('project_id', 'Unknown')
        print(f"✅ Credentials file valid for project: {project_id}")

    client = storage.Client(project=gcs_project_id)
    print("✅ GCS Client initialized")

    bucket = client.bucket(gcs_bucket_name)
    print(f"✅ Bucket object created: {gcs_bucket_name}")

    bucket_exists = bucket.exists()
    print(f"Bucket exists: {'YES' if bucket_exists else 'NO'}")

    if bucket_exists:
        # List some files (first 5)
        blobs = list(client.list_blobs(gcs_bucket_name, max_results=5))
        print(f"Files in bucket: {len(blobs)}")
        
        for blob in blobs:
            print(f"  - {blob.name} ({blob.size} bytes)")

def run_unit_tests():
    """Run unit tests using pytest"""
    import subprocess
    import sys
    import os
    
    print("Running unit tests...")
    
    # Change to the project directory
    project_root = '/opt/airflow'
    os.chdir(project_root)
    
    # Add src to Python path for tests
    if '/opt/airflow/src' not in sys.path:
        sys.path.insert(0, '/opt/airflow/src')
    
    # Check if test directory exists
    test_dir = os.path.join(project_root, 'tests/Unit')
    if not os.path.exists(test_dir):
        print(f"Test directory not found: {test_dir}")
        return ValueError(f"Test directory not found: {test_dir}")
    
    # List test files
    test_files = []
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.relpath(os.path.join(root, file), project_root))
    
    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  - {test_file}")
    
    if not test_files:
        print("No test files found! Skipping unit tests.")
        return "no_tests_found"
    
    try:
        # Run pytest with your exact command
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/Unit/', 
            '-v'
        ], 
        capture_output=True, 
        text=True,
        cwd=project_root,
        timeout=300
        )
        
        # Print the output
        print("PYTEST STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("PYTEST STDERR:")
            print(result.stderr)
        
        # Parse basic results
        stdout = result.stdout
        passed_count = stdout.count(' PASSED')
        failed_count = stdout.count(' FAILED')
        skipped_count = stdout.count(' SKIPPED')
        error_count = stdout.count(' ERROR')
        
        print(f"\nTest Results Summary:")
        print(f"  Passed: {passed_count}")
        print(f"  Failed: {failed_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Errors: {error_count}")
        
        if result.returncode == 0:
            print("All unit tests passed!")
            return "tests_passed"
        else:
            print(f"Unit tests failed with return code: {result.returncode}")
            return ValueError(f"Unit tests failed. {failed_count} failures, {error_count} errors.")
            
    except subprocess.TimeoutExpired:
        return ValueError("Unit tests timed out after 5 minutes")
    except FileNotFoundError:
        return ValueError("pytest not found. Please add pytest to requirements.txt")
    except Exception as e:
        return ValueError(f"Error running unit tests: {e}")

def test_paper_collection():
    from src.DataPipeline.Ingestion.main import collect_papers_only
    import os
    
    # Get search terms from environment variable or use default
    search_terms_env = os.getenv('SEARCH_TERMS', 'machine learning,computer vision')
    search_terms = [term.strip() for term in search_terms_env.split(',')]
    limit = int(os.getenv('PAPERS_PER_TERM', '5'))
    
    print(f"🔍 Search terms: {search_terms}")
    print(f"📊 Papers per term: {limit}")
    
    results = collect_papers_only(
        search_terms=search_terms,
        limit=limit,
        output_dir="/tmp/test_data/raw"
    )
    
    print(f"Collection completed: {len(results)} terms processed")
    print("Files uploaded to GCS:")
    for result in results:
        print(f"  {result['search_term']}: {result['gcs_path']}")
    
    return results

def preprocess_papers(**context):
    print("Testing paper preprocessing...")

    ti = context['task_instance']
    collection_results = ti.xcom_pull(task_ids='test_paper_collection')
    
    if not collection_results:
        raise ValueError("No collection results received")
    
    from src.DataPipeline.Ingestion.main import process_collected_papers
    
    results = process_collected_papers(
        collection_results=collection_results,
        output_dir="/tmp/test_data/processed"
    )
    
    print(f"Processing completed: {len(results)} terms processed")
    print("Processed files uploaded to GCS:")
    for result in results:
        print(f"  {result['search_term']}: {result['processed_gcs']}")
    
    return results

def embed_stored_data():
    import sys
    if '/opt/airflow' not in sys.path:
        sys.path.insert(0, '/opt/airflow')

    from services.embedding_service import EmbeddingService
    
    service = EmbeddingService(
        bucket_name="citeconnect-test-bucket",
        gcs_prefix="raw/",
        flat_structure=True,
        gcs_project_id="strange-calling-476017-r5"
    )
    
    return service.process_domain("healthcare", batch_size=5, max_papers=10, use_streaming=True)


def generate_schema_and_stats(**context):
    """Generate schema and validate data quality"""
    from src.DataPipeline.Validation.schema_validator import validate_schema
    return validate_schema(**context)

def send_success_notification(**context):
    task_instance = context['task_instance']
    dag_run = context['dag_run']
    
    # Get schema validation results
    schema_results = task_instance.xcom_pull(task_ids='generate_schema_and_stats')
    
    # Build alert message if quality dropped
    alert_msg = ""
    if schema_results and schema_results.get('alert'):
        alert_msg = f"<p style='color: red;'><strong>⚠️ ALERT: {schema_results['alert']}</strong></p>"
    
    subject = f"CiteConnect Pipeline SUCCESS - {dag_run.execution_date}"
    
    quality_score = schema_results.get('quality_score', 'N/A') if schema_results else 'N/A'
    
    html_content = f"""
    <h2>CiteConnect Pipeline Completed Successfully!</h2>
    
    <h3>Pipeline Details:</h3>
    <ul>
        <li><strong>DAG:</strong> {dag_run.dag_id}</li>
        <li><strong>Execution Date:</strong> {dag_run.execution_date}</li>
        <li><strong>Start Date:</strong> {dag_run.start_date}</li>
        <li><strong>Duration:</strong> {dag_run.end_date - dag_run.start_date if dag_run.end_date else 'Running'}</li>
    </ul>
    
    <h3>Data Quality:</h3>
    <ul>
        <li><strong>Overall Quality Score:</strong> {quality_score}%</li>
        <li><strong>Total Papers:</strong> {schema_results.get('total_papers', 'N/A') if schema_results else 'N/A'}</li>
    </ul>
    
    {alert_msg}
    
    <h3>All Tasks Completed:</h3>
    <ul>
        <li>Environment check: SUCCESS</li>
        <li>GCS connection: SUCCESS</li>
        <li>Unit tests: SUCCESS</li>
        <li>Data collection: SUCCESS</li>
        <li>Preprocessing: SUCCESS</li>
        <li>Embedding: SUCCESS</li>
        <li>Schema validation: SUCCESS</li>
    </ul>
    
    <p><strong>Your CiteConnect pipeline is working perfectly!</strong></p>
    """
    
    # Try to send email, but don't fail if credentials are missing
    try:
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASSWORD')
        
        if smtp_user and smtp_pass:
            send_email(
                to=EMAIL_TO,
                subject=subject,
                html_content=html_content
            )
            print(f"✅ Success email sent to {EMAIL_TO}")
        else:
            print("⚠️ SMTP credentials not set. Skipping email notification.")
            print("   To enable emails, set SMTP_USER and SMTP_PASSWORD environment variables.")
    except Exception as e:
        print(f"⚠️ Email sending failed: {e}")
        print("   Pipeline completed successfully, but email notification was skipped.")
    
    return "pipeline_completed"


env_check_task = PythonOperator(
    task_id='check_env_variables',
    python_callable=check_env_variables,
    dag=dag
)

gcs_check_task = PythonOperator(
    task_id='check_gcs_connection',
    python_callable=check_gcs_connection,
    dag=dag
)

api_test_task = PythonOperator(
    task_id='test_api_connection',
    python_callable=run_unit_tests,
    dag=dag
)

collection_test_task = PythonOperator(
    task_id='test_paper_collection',
    python_callable=test_paper_collection,
    dag=dag
)

preprocess_task = PythonOperator(
    task_id='preprocess_papers',
    python_callable=preprocess_papers,
    provide_context=True,
    dag=dag
)

embed_task = PythonOperator(
    task_id='embed_stored_data',
    python_callable=embed_stored_data,
    dag=dag
)

schema_stats_task = PythonOperator(
    task_id='generate_schema_and_stats',
    python_callable=generate_schema_and_stats,
    provide_context=True,
    dag=dag
)

notification_task = PythonOperator(
    task_id='send_success_notification',
    python_callable=send_success_notification,
    dag=dag
)

# Set dependencies
env_check_task >> gcs_check_task >> api_test_task >> collection_test_task >> preprocess_task >> embed_task >> schema_stats_task >> notification_task
# env_check_task >> gcs_check_task >> api_test_task >> preprocess_task >> notification_task
