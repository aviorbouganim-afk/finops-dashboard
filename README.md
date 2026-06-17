# AI FinOps Command Center

An interactive Streamlit dashboard for monitoring, forecasting, and optimizing AI-related cloud and SaaS spending.

## Overview

AI FinOps Command Center helps teams understand where AI budget is going across vendors, teams, models, and cost models. The app includes built-in sample data and also supports uploading a custom CSV file with AI usage and cost data.

## Features

- Tracks AI spend, usage volume, token consumption, and seat utilization.
- Filters data by team, vendor, cost model, and month range.
- Visualizes monthly spend trends, budget burn rate, cost per 1K usage, token usage, seat utilization, and spend by cost model.
- Forecasts month-end spend based on recent growth patterns.
- Detects cost risks such as fast-growing spend, low license utilization, and budget exposure.
- Provides optimization recommendations with estimated monthly savings.
- Includes governance policy cards for AI APIs, seat-based tools, model routing, and procurement.
- Allows users to download a CSV template and export filtered data.

## Tech Stack

- Python
- Streamlit
- Pandas
- Altair

## Project Structure

```text
streamlit/
+-- streamlit_app.py      # Main Streamlit application
+-- requirements.txt      # Python dependencies
`-- README.md             # Project documentation
```

## Getting Started

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run the app

```powershell
streamlit run streamlit_app.py
```

The app will open in the browser, usually at:

```text
http://localhost:8501
```

## CSV Input Format

The app can run with the built-in sample dataset or with an uploaded CSV file.

Required columns:

- `date`
- `vendor`
- `team`
- `cost_model`
- `spend`
- `actions`

Optional columns:

- `service`
- `model`
- `input_tokens`
- `output_tokens`
- `seats`
- `active_users`
- `owner`
- `use_case`

## Example Use Cases

- Monitor monthly AI vendor spending.
- Identify teams or models driving cost growth.
- Compare token-based, usage-based, and seat-based cost models.
- Detect underused AI tool licenses.
- Prioritize cost-saving actions with estimated financial impact.
- Support executive reporting for AI budget governance.

## Resume Summary

Built an AI-powered FinOps dashboard to monitor cloud costs, usage trends, and budget performance. Designed a responsive Streamlit interface with actionable insights and executive-level financial visibility.
