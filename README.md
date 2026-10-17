# AI Recipe Intelligence Platform

An AI-powered recipe extraction, enrichment, and management platform built using FastAPI, React, TypeScript, SQLite, and machine learning.

This repository contains **Assignment 1: Recipe URL and CSV Intelligence**.

The platform extracts recipe information from supported websites, imports recipe datasets, normalizes ingredients, predicts meal categories, and provides a dashboard for viewing and reviewing saved recipes.

## Features

### 1. Recipe URL Extraction
- Extract recipe information from supported recipe websites.
- Retrieve available ingredients, cooking instructions, preparation times, and serving information.
- Normalize extracted recipe data into a consistent structure.
- Predict the recipe's meal category using machine learning.
- Save successfully extracted recipes.

### 2. CSV Recipe Import
- Import recipe data from CSV files.
- Validate incoming files and recipe records.
- Normalize ingredient information.
- Detect duplicate dataset records.
- Store imported recipes in SQLite.

### 3. Ingredient Normalization
- Extract ingredient names, quantities, and units.
- Handle common measurement formats, including fractions.
- Standardize recognized measurement units.
- Preserve original ingredient information when possible.

### 4. Machine Learning
- Uses a scikit-learn pipeline with TF-IDF vectorization and logistic regression.
- Predicts meal categories such as Breakfast, Lunch, Dinner, Snack, and Dessert.
- Returns a prediction confidence score.
- Flags low-confidence predictions for review.
- Includes a pretrained model at `app/ml/meal_classifier.joblib`.

The trained classifier previously achieved approximately **68.91% test accuracy** on the project's prepared recipe dataset. This is an evaluation result, not a guarantee of prediction accuracy on new recipes.

### 5. Dashboard and Recipe Management
- View saved recipes and dataset statistics.
- Inspect ingredients, instructions, and recipe details.
- Review machine-learning predictions.
- Save and inspect recipe classification feedback.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Styling | Tailwind CSS, shadcn/ui components |
| Backend | Python, FastAPI |
| Database | SQLite |
| Machine Learning | scikit-learn, pandas, joblib |
| Recipe Extraction | Requests, Beautiful Soup |
| API Documentation | Swagger UI |

## Project Structure

```text
ai-recipe-intelligence/
├── app/
│   ├── main.py
│   ├── ml/
│   ├── models/
│   ├── services/
│   └── scripts/
├── frontend/
├── data/
│   ├── processed/
│   └── raw/
├── samples/
├── tests/
├── requirements.txt
├── .gitignore
└── README.md
```

Local SQLite databases, backups, and the original large recipe dataset are excluded from version control.

## Installation

### Prerequisites

- Python 3.11 or later, with compatible dependencies
- Node.js and npm
- Git

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
cd ai-recipe-intelligence
```

Replace `YOUR_REPOSITORY_URL` with the GitHub repository URL.

### 2. Create a Python Virtual Environment

From the project root:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
python -m pip install -r requirements.txt
```

### 3. Start the Backend

From the project root:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

Backend:

`http://127.0.0.1:8001`

Interactive API documentation:

`http://127.0.0.1:8001/docs`

Health check:

`http://127.0.0.1:8001/health`

### 4. Start the Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open:

`http://localhost:5173`

The development frontend is configured to communicate with the local FastAPI backend.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Backend health check |
| GET | `/schema/recipe` | Recipe schema |
| POST | `/extract-recipe-url` | Extract and enrich a recipe from a URL |
| POST | `/extract-ingredients` | Extract structured ingredient information |
| POST | `/recipes/csv` | Process a CSV of recipe URLs |
| POST | `/recipes/import-csv` | Import a recipe dataset |
| GET | `/recipes/saved` | List saved URL recipes |
| GET | `/recipes/stats` | URL recipe statistics |
| GET | `/recipes/dataset/stats` | Imported dataset statistics |
| GET | `/recipes/dataset/saved` | List imported recipes |
| GET | `/recipes/dataset/saved/{recipe_id}` | Retrieve a dataset recipe |
| POST | `/feedback/recipe` | Save classification feedback |
| GET | `/feedback/recipes` | List classification feedback |
| DELETE | `/feedback/recipe/{feedback_id}` | Delete a feedback record |

Additional prototype routes may be visible in Swagger UI. The legacy `/recipes/url` and planned `/videos/upload` endpoints currently return HTTP 501 and are not part of Assignment 1's completed workflows.

## Running Tests

From the project root, with the virtual environment activated:

```powershell
python -m pytest -q
```

## Demonstration Workflow

1. Start the FastAPI backend and React frontend.
2. Open the dashboard.
3. Extract a recipe from a supported website URL.
4. Inspect its ingredients, instructions, and predicted meal category.
5. Import a supported CSV dataset.
6. View saved dataset recipes and their normalized ingredients.
7. Review dataset statistics and machine-learning predictions.

## Dataset and Model

The project uses a prepared Indian recipe dataset for model training and evaluation.

The original large dataset is not included in this repository. The pretrained model is included for prediction without retraining.

The training script is available at `app/ml/train_model.py`. Retraining requires the corresponding prepared training dataset.

## Current Limitations

- Recipe extraction depends on the structure and accessibility of external websites.
- Machine-learning predictions may be inaccurate and should be reviewed.
- Not all ingredient quantities or units can be reliably inferred.
- Local SQLite storage requires a persistence strategy for cloud deployment.
- The application has undergone manual end-to-end testing, but automated test coverage is limited.
- Video-to-recipe extraction is reserved for Assignment 2 and is not implemented in this version.

## Future Scope

Assignment 2 will explore video-based recipe extraction, including speech transcription, visual ingredient recognition, and structured recipe generation.

It may later be integrated with this platform while preserving Assignment 1 as a standalone submission.

## Project Status

**Assignment 1: Core implementation complete and locally tested.**

GitHub publication and cloud deployment are the next stages.