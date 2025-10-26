# Dockerfile for CiteConnect - Simple Version
FROM apache/airflow:2.9.2

USER airflow

# Copy and install requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy everything (except what's in .dockerignore)
COPY --chown=airflow:root . /opt/airflow/dags/project/

# Set Python path
ENV PYTHONPATH="/opt/airflow/dags/project:${PYTHONPATH}"