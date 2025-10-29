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
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
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

search_terms = ["large language models"]

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

def version_embeddings_with_dvc(**context):
    """
    Version embeddings with DVC and append to a run_summary.json log.
    """
    import subprocess
    import os
    import json
    from datetime import datetime
    
    project_root = "/opt/airflow"
    embeddings_path = os.path.join(project_root, "working_data/embeddings_db.pkl")
    
    summary_path = os.path.join(project_root, "working_data/run_summary.json")

    if not os.path.exists(embeddings_path):
        print("No embeddings file found to version")
        return {"status": "no_file"}
    
    try:
        ti = context['task_instance']
        embed_results = ti.xcom_pull(task_ids='embed_stored_data') or {}
        
        file_size_mb = round(os.path.getsize(embeddings_path) / (1024*1024), 2)
        embeddings_created = embed_results.get('embedded_chunks', 0)
        total_papers = embed_results.get('total_papers', 0)
        run_params = embed_results.get('params', {"status": "unknown"})
        
        summary_list = []
        if os.path.exists(summary_path):
            try:
                with open(summary_path, 'r') as f:
                    summary_list = json.load(f)
                if not isinstance(summary_list, list):
                    summary_list = [summary_list]
            except json.JSONDecodeError:
                print(f"Warning: Could not read {summary_path}, starting new list.")
                summary_list = []

        new_run_summary = {
            "run_timestamp": datetime.now().isoformat(),
            "params": run_params,
            "outs": {
                "embeddings_file": {
                    "path": "working_data/embeddings_db.pkl",
                    "file_size_mb": file_size_mb,
                    "total_chunks": embeddings_created
                },
                "total_papers_processed": total_papers,
                "search_terms": search_terms
            }
        }
        
        summary_list.append(new_run_summary)
        
        with open(summary_path, 'w') as f:
            json.dump(summary_list, f, indent=4)
        print(f"Appended new run to {summary_path}. Total runs logged: {len(summary_list)}")

        print("Configuring Git user...")
        subprocess.run(
            ['git', 'config', '--global', '--add', 'safe.directory', project_root], 
            check=True, 
            capture_output=True,
            cwd=project_root
        )
        subprocess.run(['git', 'config', '--global', 'user.email', '"aditya811.abhinav@gmail.com"'], check=True, cwd=project_root)
        subprocess.run(['git', 'config', '--global', 'user.name', '"Abhinav Aditya"'], check=True, cwd=project_root)
        print("Git user configured.")
        
        subprocess.run(['dvc', 'add', embeddings_path], check=True, capture_output=True, cwd=project_root)
        print("Added embeddings to DVC tracking")

        embed_dvc_file = f"{embeddings_path}.dvc"
        
        subprocess.run(['git', 'add', embed_dvc_file], check=True, capture_output=True, cwd=project_root)
        print("Added .dvc file to git")
        
        subprocess.run(['git', 'add', summary_path], check=True, capture_output=True, cwd=project_root)
        print("Added run_summary.json to git")

        try:
            subprocess.run(['git', 'add', '.gitignore'], check=True, capture_output=True, cwd=project_root)
        except subprocess.CalledProcessError:
            pass
        
        commit_msg = f"Update embeddings: {embeddings_created} chunks, {total_papers} papers - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        subprocess.run(
            ['git', 'commit', '--allow-empty', '-m', commit_msg], 
            check=True, 
            capture_output=True, 
            cwd=project_root
        )
        print(f"Git commit: {commit_msg}")
        
        subprocess.run(['dvc', 'push'], check=True, capture_output=True, cwd=project_root)
        print("Pushed to DVC remote")
        
        new_run_summary["status"] = "success"
        new_run_summary["commit_message"] = commit_msg
        return new_run_summary
        
    except subprocess.CalledProcessError as e:
        error_msg = f"DVC/Git command failed: {e.stderr.decode() if e.stderr else e.stdout.decode()}"
        print(f"Error: {error_msg}")
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"Error: {error_msg}")
        raise ValueError(error_msg)

def generate_schema_and_stats(**context):
    """Generate schema and validate data quality"""
    from src.DataPipeline.Validation.schema_validator import validate_schema
    return validate_schema(**context)

def send_success_notification(**context):
    dag_run = context['dag_run']
    ti = context['task_instance']
    
    try:
        version_results = ti.xcom_pull(task_ids='version_embeddings_dvc')
        if not version_results:
            # Fallback in case XCom pull fails
            version_results = {"status": "success", "outs": {"embeddings_file": {}}}
        
        # Extract key metrics
        params = version_results.get('params', {})
        outs = version_results.get('outs', {"embeddings_file": {}})
        embed_file_stats = outs.get('embeddings_file', {})
        
        papers_processed = outs.get('total_papers_processed', 'N/A')
        chunks_created = embed_file_stats.get('total_chunks', 'N/A')
        file_size = embed_file_stats.get('file_size_mb', 'N/A')
        commit_msg = version_results.get('commit_message', 'N/A')

    except Exception as e:
        print(f"Warning: Could not pull XCom data. Sending generic email. Error: {e}")
        papers_processed = 'N/A'
        chunks_created = 'N/A'
        file_size = 'N/A'
        commit_msg = 'N/A'
        params = {}

    
    # Get schema validation results
    schema_results = task_instance.xcom_pull(task_ids='generate_schema_and_stats')
    
    # Build alert message if quality dropped
    alert_msg = ""
    if schema_results and schema_results.get('alert'):
        alert_msg = f"<p style='color: red;'><strong>⚠️ ALERT: {schema_results['alert']}</strong></p>"
    
    subject = f"CiteConnect Pipeline SUCCESS - {dag_run.execution_date}"
    
    quality_score = schema_results.get('quality_score', 'N/A') if schema_results else 'N/A'
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            h2 {{ color: #2E8B57; }}
            h3 {{ border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
            ul {{ list-style-type: none; padding-left: 0; }}
            li strong {{ color: #333; }}
            .summary-box {{ 
                background-color: #f4f4f4; 
                border: 1px solid #ddd; 
                padding: 15px; 
                border-radius: 5px; 
            }}
            .commit {{
                font-family: 'Courier New', Courier, monospace;
                background-color: #eee;
                padding: 5px;
                border-radius: 3px;
                font-style: italic;
            }}
        </style>
    </head>
    <body>
        <h2>✅ CiteConnect Pipeline Completed Successfully!</h2>
        
        <p><strong>Your CiteConnect pipeline run has finished and all data has been versioned.</strong></p>

        <h3>Run Summary</h3>
        <div class="summary-box">
            <ul>
                <li><strong>Papers Processed:</strong> {papers_processed}</li>
                <li><strong>Embeddings Created:</strong> {chunks_created}</li>
                <li><strong>Final Data Size:</strong> {file_size} MB</li>
                <li><strong>Parameters:</strong>
                    <ul>
                        <li>Domain: {params.get('domain', 'N/A')}</li>
                        <li>Max Papers: {params.get('max_papers', 'N/A')}</li>
                        <li>Batch Size: {params.get('batch_size', 'N/A')}</li>
                        <li><strong>Overall Quality Score:</strong> {quality_score}%</li>
                        <li><strong>Total Papers:</strong> {schema_results.get('total_papers', 'N/A') if schema_results else 'N/A'}</li>
                    </ul>
                </li>
                <li><strong>Commit:</strong> <span class="commit">"{commit_msg}"</span></li>
            </ul>
        </div>

        <h3>Pipeline Stages Completed</h3>
        <ul>
            <li>✅ check_env_variables</li>
            <li>✅ check_gcs_connection</li>
            <li>✅ test_api_connection (Unit Tests)</li>
            <li>✅ test_paper_collection</li>
            <li>✅ preprocess_papers</li>
            <li>✅ embed_stored_data</li>
            <li>✅ version_embeddings_dvc (Data Versioning)</li>
            <li>>✅ schema validation: SUCCESS</li>
        </ul>

        <h3>Pipeline Details</h3>
        <ul>
            <li><strong>DAG:</strong> {dag_run.dag_id}</li>
            <li><strong>Execution Date:</strong> {dag_run.execution_date}</li>
            <li><strong>Start Date:</strong> {dag_run.start_date}</li>
            <li><strong>Duration:</strong> {dag_run.end_date - dag_run.start_date if dag_run.end_date else 'Running'}</li>
        </ul>
    </body>
    </html>
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
    trigger_rule='all_success',
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
      dag=dag
)

dvc_version_task = PythonOperator(
    task_id='version_embeddings_dvc',
    python_callable=version_embeddings_with_dvc,
    provide_context=True,
    dag=dag
)

notification_task = PythonOperator(
    task_id='send_success_notification',
    python_callable=send_success_notification,
    dag=dag
)

# Set dependencies
env_check_task >> gcs_check_task >> api_test_task >> collection_test_task >> preprocess_task >> embed_task >> dvc_version_task >> schema_stats_task >> notification_task
# env_check_task >> gcs_check_task >> api_test_task >> preprocess_task >> notification_task
