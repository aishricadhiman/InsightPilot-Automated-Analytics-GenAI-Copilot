# InsightPilot — Automated Analytics & GenAI Copilot

> git

InsightPilot demonstrates how repetitive parts of a traditional data analytics workflow can be automated:

**Raw Data → Data Quality → Cleaning → MySQL → SQL Analytics → GenAI → Interactive Insights**

The current implementation analyses hospital operations across admissions, readmissions, staffing, patient stay and financial data.

Rather than building an LLM directly on raw tables, the project first creates a **trusted analytics layer**. The LLM then converts user questions into SQL, queries that layer, and explains the returned results in business-friendly language.

The same architecture can be adapted to other structured-data domains such as finance, retail, insurance and e-commerce by replacing the domain-specific schemas, KPIs and business rules.

---

## What Did the Analysis Find?

The pipeline analysed five hospital datasets covering patients, admissions, readmissions, staffing and billed charges.

### Hospital Overview

| Metric | Result |
|---|---:|
| Total Admissions | 119,980 |
| Unique Patients | 61,137 |
| Average Length of Stay | 4.64 days |
| 30-Day Readmission Rate | 10.82% |
| Average Billed Amount / Admission | 10,921.98 |
| Insurance Coverage of Billed Charges | 76.72% |

### Emergency carries the highest operational load

Emergency recorded **29,777 admissions**, representing **24.82% of all admissions**.

It also had:

- highest patient-to-staff ratio: **4.56**
- highest 30-day readmission rate: **12.20%**
- lowest average length of stay: **2.86 days**

These metrics make Emergency a useful department for further operational investigation, although the analysis does not establish a causal relationship between workload and readmissions.

### Neurology patients stay the longest

Neurology recorded the highest average length of stay:

**6.05 days**

followed by:

| Department | Avg. LOS |
|---|---:|
| Neurology | 6.05 |
| Oncology | 5.89 |
| Nephrology | 5.77 |
| Cardiology | 5.53 |
| Surgery | 5.51 |

This highlights how operational patterns differ across departments: the department handling the most patients is not necessarily the department consuming beds for the longest period.

### Readmissions concentrate within the first two weeks

The hospital-wide eligible 30-day readmission rate was **10.82%**, with **12,780 recorded readmissions**.

| Readmission Window | Share |
|---|---:|
| 1–7 days | 31.29% |
| 8–14 days | 35.06% |
| 15–21 days | 19.05% |
| 22–30 days | 14.59% |

About **66% of recorded readmissions occurred within the first 14 days**.

The largest recorded reason was **clinical deterioration (29.92%)**, followed by infection and unplanned follow-up.

### Night shift has the highest workload ratio

Aggregate patient-to-staff ratios were:

| Shift | Patient-to-Staff Ratio |
|---|---:|
| Night | 3.54 |
| Evening | 3.48 |
| Day | 3.44 |

At department + shift level, **Emergency Night** reached a ratio of **4.66**, the highest among the examples analysed.

### Longer stays are associated with larger billed amounts

| Length of Stay | Avg. Billed Amount |
|---|---:|
| 1–3 days | 9,126.81 |
| 4–7 days | 11,489.52 |
| 8–14 days | 14,144.71 |
| 15+ days | 17,473.80 |

The observed data shows progressively higher average billed amounts for longer stay groups.

These values represent **billed charges**, not hospital revenue or profit.

---

# The Problem This Project Automates

A typical analyst repeatedly performs tasks such as:

1. inspect incoming data
2. identify quality issues
3. clean inconsistent records
4. load data into a database
5. write SQL for KPIs
6. aggregate results
7. answer stakeholder questions
8. rewrite similar SQL when a new question arrives
9. explain query outputs in business language

InsightPilot automates a large part of this workflow.

```text
                    RAW DATA
                       │
                       ▼
              Data Profiling
                       │
                       ▼
              Quality Validation
                       │
                       ▼
                  Cleaning
                       │
                       ▼
              Processed Datasets
                       │
                       ▼
                     MySQL
                       │
                       ▼
              Analytical Views
                       │
              ┌────────┴────────┐
              ▼                 ▼
       Predefined SQL       GenAI Copilot
         Analytics               │
              │                  ▼
              │            Natural Language
              │                  │
              │                  ▼
              │              Text-to-SQL
              │                  │
              │                  ▼
              │           SQL Safety Check
              │                  │
              │                  ▼
              │                MySQL
              │                  │
              │                  ▼
              │             Query Result
              │                  │
              │                  ▼
              │           LLM Explanation
              │                  │
              └─────────┬────────┘
                        ▼
                 Interactive User
```

The goal is not to remove SQL or the analyst from the process.

It is to automate **repeatable analytical work while keeping the underlying SQL and database results inspectable**.

---

# Ask the Data Instead of Writing Another Query

Once the analytics layer is built, a user can ask questions such as:

> What are the top 5 departments by total admissions?

> Which department has the highest 30-day readmission rate?

> Compare patient-to-staff ratios across shifts.

> Which department has the longest average length of stay?

> Which departments have the highest billed amount?

The user does not need to know the underlying schema or write SQL manually.

For example:

### User

> What are the top 5 departments by total admissions?

### LLM-generated SQL

```sql
SELECT
    department,
    COUNT(DISTINCT admission_id) AS total_admissions
FROM vw_admission_metrics
GROUP BY department
ORDER BY total_admissions DESC
LIMIT 5;
```

### Database Result

| Department | Admissions |
|---|---:|
| Emergency | 29,777 |
| General Medicine | 20,277 |
| Cardiology | 13,213 |
| Orthopedics | 12,081 |
| Neurology | 8,494 |

The LLM then converts these database results into a readable response for the user.

So the answer is not generated from the model's internal knowledge:

```text
Question
   ↓
LLM generates SQL
   ↓
SQL is validated
   ↓
MySQL executes it
   ↓
Actual rows are returned
   ↓
LLM explains those rows
```

---

# How the LLM Understands the Analytics

Giving an LLM database column names is not enough.

For example, calculating readmission rate requires knowing which admissions had enough time to complete a full **30-day observation window**.

Similarly, aggregate staffing workload should use:

```sql
SUM(patient_count) / NULLIF(SUM(staff_count), 0)
```

rather than blindly averaging existing ratios.

InsightPilot therefore provides Qwen3-32B with a **semantic layer** containing:

- approved analytical views
- column meanings
- analytical grain
- KPI definitions
- readmission eligibility rules
- staffing aggregation rules
- financial terminology
- cross-domain join rules

This reduces the chance of generating SQL that is syntactically valid but analytically wrong.

---

# Safe Text-to-SQL Pipeline

LLM-generated SQL is treated as **untrusted input**.

The model cannot simply generate SQL and send it directly to MySQL.

```text
User Question
     ↓
Qwen3-32B
     ↓
Generated SQL
     ↓
SQLGlot Parser
     ↓
Read-only Validation
     ↓
Approved View Validation
     ↓
MySQL
     ↓
Result
```

The validator blocks operations such as:

`INSERT` `UPDATE` `DELETE` `DROP` `CREATE` `ALTER` `TRUNCATE`

The agent is restricted to four curated analytical views:

- `vw_admission_metrics`
- `vw_readmission_metrics`
- `vw_staffing_metrics`
- `vw_cost_metrics`

This creates a controlled boundary between the LLM and the underlying data.

---

# Automated Analytics Pipeline

The project does not start with GenAI.

Raw data first passes through a conventional analytics pipeline.

### 1. Profiling

Automatically examines:

- rows and columns
- data types
- missing values
- duplicate records
- numerical distributions

### 2. Data Quality Validation

Checks include:

- unique identifiers
- null values
- valid categories
- date consistency
- non-negative values
- financial consistency
- cross-table referential integrity

Validation results are stored as structured reports.

### 3. Cleaning

Detected issues are cleaned and processed datasets are generated separately from raw data.

### 4. MySQL Loading

Validated datasets are loaded into MySQL through SQLAlchemy.

### 5. Analytical Layer

Reusable views and business metrics are created once instead of rebuilding the same logic for every analysis.

### 6. Automated SQL Analysis

The project currently contains **46 predefined SQL analyses**, all of which completed successfully during pipeline verification.

### 7. GenAI Analysis

For questions outside predefined analyses, the LLM dynamically generates SQL against the same trusted analytics layer.

---

# Interactive Analytics

The Streamlit interface provides a conversational layer over the analytics system.

Users can:

- ask analytical questions in natural language
- receive business-readable answers
- inspect generated SQL
- inspect the database result behind the answer
- ask questions across admissions, readmissions, staffing and financial analytics

This creates two ways to consume the same analytics infrastructure:

```text
               Analytics Layer
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   Standard Analytics      GenAI Analytics
          │                     │
   Known KPIs/reports      Ad-hoc questions
```

A Power BI dashboard is planned as an additional presentation layer for fixed KPI monitoring and visual exploration.

---

# Why This Architecture Is Reusable

The current implementation uses hospital data, but the automation pattern is not limited to healthcare.

```text
Domain Data
    ↓
Domain Validation Rules
    ↓
Database
    ↓
Analytical Views
    ↓
Business/KPI Definitions
    ↓
Same GenAI Engine
```

For a financial analytics use case, for example, hospital-specific components could be replaced with:

```text
Admissions       → Transactions
Departments      → Business Units
Readmission KPI  → Default / Risk KPI
Billed Amount    → Revenue / Transaction Value
```

The domain-specific:

- datasets
- validation rules
- SQL views
- KPIs
- semantic definitions

would change.

But the reusable architecture for:

**LLM integration → Text-to-SQL → validation → database execution → response generation → interactive UI**

can remain largely the same.

---

# Project at a Glance

| Component | Implementation |
|---|---|
| Data Sources | 5 operational datasets |
| Patients | 80,000 |
| Admissions | 119,980 |
| SQL Analyses | 46 |
| Curated LLM Views | 4 |
| Database | MySQL |
| LLM | Qwen3-32B |
| LLM Provider | Hugging Face |
| SQL Validation | SQLGlot |
| Application | Streamlit |
| BI Dashboard | Power BI — planned |

---

# Tech Stack

**Data & Analytics**

`Python` `Pandas` `SQL` `MySQL` `SQLAlchemy`

**GenAI**

`Qwen3-32B` `Hugging Face Inference Providers` `Prompt Engineering` `Text-to-SQL`

**Safety & Engineering**

`SQLGlot` `Semantic Layer` `Environment Variables`

**Interface**

`Streamlit`

---

# Project Structure

```text
InsightPilot/
│
├── app.py
├── requirements.txt
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── data/
│   │   ├── profile_data.py
│   │   └── clean_data.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   └── database_load.py
│   │
│   ├── analysis/
│   │   └── run_analysis.py
│   │
│   └── agent/
│       ├── config.py
│       ├── llm.py
│       ├── schema.py
│       ├── prompts.py
│       ├── sql_generator.py
│       ├── sql_validator.py
│       ├── database_tools.py
│       ├── response_generator.py
│       └── agent.py
│
├── sql/
│
└── reports/
    ├── data_quality/
    └── analysis/
```

---

# Run Locally

```bash
git clone <repository-url>
cd InsightPilot

py -3.10 -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

Create `.env`:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=hospital_analytics

HF_TOKEN=your_huggingface_token
HF_MODEL=Qwen/Qwen3-32B
```

Run the GenAI agent:

```bash
python -m src.agent.agent
```

Launch Streamlit:

```bash
python -m streamlit run app.py
```

---

# Current Scope & Next Steps

The current version implements the data pipeline, MySQL analytics layer, predefined SQL analytics, Text-to-SQL agent, SQL safety layer, grounded response generation and Streamlit interface.

Planned improvements include:

- Power BI dashboard
- dedicated read-only database user
- multi-turn conversational context
- automatic SQL retry/correction
- Text-to-SQL evaluation suite
- Dockerisation
- deployment
- query logging and monitoring

---

## Core Idea

**Build the analytical logic once, automate repetitive analysis around it, and let users interact with trusted data using natural language.**

InsightPilot explores how traditional analytics engineering and GenAI can work together: **SQL remains the analytical engine, while the LLM becomes the interface between users and the data.**