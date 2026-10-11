# TeleQuery: AI Assistant for Telecom Network Data

An end-to-end project that stores telecom network KPIs in a SQL database, detects anomalies with machine learning, and answers plain-English questions about the data using an LLM-powered text-to-SQL assistant.

## Planned Features
- SQL database of network KPIs (latency, throughput, signal strength, packet loss)
- ML-based anomaly detection (Isolation Forest)
- Natural-language to SQL assistant
- FastAPI backend and Streamlit dashboard
- Docker and CI

## Tech Stack
Python, pandas, scikit-learn, SQL, FastAPI, Streamlit, Docker

## Project Structure
```
data/        datasets and database files
src/         application source code
notebooks/   exploration and experiments
tests/       unit tests
```

## Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Status
In progress.
