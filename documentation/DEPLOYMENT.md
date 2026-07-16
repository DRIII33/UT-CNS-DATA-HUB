# Deployment Guide

## Prerequisites
1. Google Cloud Project with BigQuery enabled.
2. Python 3.10+ environment.
3. GCP Service Account with `BigQuery Admin` permissions.

## Step-by-Step Setup
1. **Clone Repository:** `git clone https://github.com/DRIII33/UT-CNS-DATA-HUB.git`
2. **Install Dependencies:** `pip install -r python/requirements.txt`
3. **GCP Auth:** Run `gcloud auth application-default login`
4. **Data Generation:** Execute `python python/data_generators.py` to create the 13k student record baseline.
5. **ETL Execution:** Run `python python/etl_pipeline.py` to ingest and transform data into the Star Schema.