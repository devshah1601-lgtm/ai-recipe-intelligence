# AI Recipe Intelligence Platform

**An AI-powered recipe extraction, analysis, and management platform built with React, TypeScript, FastAPI, SQLite, computer vision, and machine learning.**

The AI Recipe Intelligence Platform converts recipe website URLs, CSV datasets, and cooking videos into structured cooking information. It combines recipe extraction, ingredient normalization, machine-learning classification, video analysis, and user feedback in a unified web application.

The project is designed to run locally and demonstrates full-stack development, machine-learning integration, database management, API development, and automated testing.

## Key Features

### Recipe URL Extraction

- Extract recipes from supported websites.
- Retrieve available titles, descriptions, ingredients, cooking instructions, preparation times, and serving information.
- Normalize recipe information into a consistent structure.
- Predict meal categories using machine learning.
- Flag uncertain predictions for manual review.
- Store extracted recipes for later reference.

### Bulk CSV Processing

Supports two workflows:

**Recipe URL CSV**
- Process multiple recipe URLs from a CSV file.
- Validate inputs and report individual processing results.

**Recipe Dataset CSV**
- Import structured recipe datasets.
- Normalize ingredient information.
- Detect duplicate records.
- Save imported recipes in SQLite.
- Browse and filter saved dataset recipes.

### AI Video-to-Recipe Extraction

Upload a supported cooking video and generate a structured recipe containing:

- Recipe title.
- Identified ingredients.
- Cooking instructions.
- Ingredient evidence from video text recognition.
- Video timestamps associated with ingredients and cooking steps.

The video-processing pipeline combines AI-based analysis with OCR-assisted ingredient verification.

Video processing time and availability may vary depending on the video, local processing resources, and external AI service availability.

### Machine-Learning Meal Classification

The platform includes a scikit-learn classification pipeline using:

- TF-IDF text vectorization.
- Logistic Regression.
- Five meal categories: Breakfast, Lunch, Dinner, Snack, and Dessert.

The classifier analyzes recipe text and ingredients to predict a meal category.

Predictions include a probability-based confidence value and a manual-review recommendation when the model is uncertain.

### Feedback and Candidate-Model Training

Users can submit corrections to predicted meal categories.

The platform stores these corrections for review and future training.

A separate experimental training pipeline supports:

- Preparing feedback as training examples.
- Filtering feedback that overlaps with held-out evaluation recipes.
- Limiting the amount of feedback added to training.
- Training a candidate model separately from the active model.
- Comparing candidate accuracy and macro F1 with the baseline.

**Candidate-model training is an experimental workflow. Saving a correction does not automatically retrain or replace the active model.**

### Dashboard and Recipe Management

The dashboard provides:

- Extracted recipe statistics.
- Recipes requiring review.
- Latest recipe information.
- Imported dataset statistics.
- Searchable saved dataset recipes.
- Classification feedback review.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Styling | Tailwind CSS, shadcn/ui |
| Backend | Python, FastAPI |
| Database | SQLite |
| Machine Learning | scikit-learn, pandas, joblib |
| ML Algorithms | TF-IDF, Logistic Regression |
| Video Analysis | Gemini API, OCR-assisted analysis |
| OCR | EasyOCR |
| Recipe Extraction | Requests, Beautiful Soup |
| API Documentation | Swagger UI |
| Testing | pytest |
| Version Control | Git, GitHub |


## Application Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### Recipe URL Extraction
![Recipe Extractor](docs/screenshots/recipe-extractor.png)

### Bulk CSV Processing
![Bulk CSV](docs/screenshots/bulk-csv.png)

### AI Video-to-Recipe Extraction
![Video to Recipe](docs/screenshots/video-to-recipe.png)

### Model Review
![Model Review](docs/screenshots/model-review.png)


## Machine-Learning Evaluation

The meal classifier was evaluated using a prepared dataset of 4,743 recipes.

| Metric | Result |
|---|---:|
| Total recipes | 4,743 |
| Training recipes | 3,794 |
| Evaluation recipes | 949 |
| Baseline test accuracy | 68.91% |
| Baseline macro F1 | 0.6788 |
| Categories | 5 |

The evaluation uses a stratified 80/20 train/test split.

### Experimental Feedback Training

In a controlled experiment, one synthetic correction was added to candidate-model training.

| Metric | Baseline | Candidate |
|---|---:|---:|
| Accuracy | 68.9146% | 69.0200% |
| Macro F1 | 0.678754 | 0.679664 |

The candidate was trained and saved separately without replacing the active model.

These results demonstrate the operation of the feedback-training pipeline, **not a proven general improvement in predictive performance**. Further independent evaluation would be needed before production use.

## Automated Testing

The project includes automated backend tests covering:

- Recipe-processing foundations.
- Video API input validation and error handling.
- Gemini response validation.
- Ingredient verification.
- Video recipe database storage and duplicate handling.
- Feedback preparation and evaluation-overlap safeguards.

**Latest local test result: 81 tests passed.**

Run the test suite from the project root:

```powershell
python -m pytest tests/ -q
```

## Project Structure

```text
ai-recipe-intelligence/
├── app/
│   ├── main.py
│   ├── ml/
│   │   ├── recipe_classifier.py
│   │   ├── train_model.py
│   │   ├── feedback_training.py
│   │   └── train_candidate.py
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

Some local data files, generated artifacts, experimental files, and model backups are excluded from version control.

## Local Installation

### Prerequisites

- Python with compatible project dependencies.
- Node.js and npm.
- Git.
- A supported local environment for video processing.
- Gemini API access for AI-powered video analysis.

### 1. Clone the Repository

```powershell
git clone YOUR_REPOSITORY_URL
cd ai-recipe-intelligence
```

Replace `YOUR_REPOSITORY_URL` with the actual GitHub repository URL.

### 2. Set Up the Backend

### Configure Gemini API Access

The AI Video-to-Recipe feature uses the Gemini API for video analysis.

Set the `GEMINI_API_KEY` environment variable before starting the FastAPI backend.

For Windows PowerShell:

```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Replace `YOUR_GEMINI_API_KEY` with your own API key.

Then start the backend in the same PowerShell session:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

**Security:** Never commit API keys, `.env` files containing secrets, or private credentials to GitHub.

Gemini API access is subject to Google's available quotas and rate limits. The application can run locally, but AI-powered video extraction requires access to the external Gemini service.

### 3. Start the Backend

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

Backend URL:

`http://127.0.0.1:8001`

Interactive API documentation:

`http://127.0.0.1:8001/docs`

### 4. Start the Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open:

`http://localhost:5173`

The frontend communicates with the locally running FastAPI backend.

## Demonstration Workflow

1. Open the dashboard to view recipe statistics.
2. Extract a recipe using a supported website URL.
3. Review the extracted ingredients, instructions, and meal classification.
4. Submit a correction for an uncertain classification.
5. Open Model Review to inspect saved corrections.
6. Process a recipe URL CSV or import a structured recipe dataset.
7. Browse saved dataset recipes.
8. Upload a cooking video and view its extracted ingredients and timestamped cooking instructions.

## Demo Video

A recorded walkthrough of the locally running application will be added here.

The demonstration will cover the dashboard, URL extraction, CSV processing, video-to-recipe extraction, and model feedback.

**Demo link:** Coming soon.

## Current Limitations

- Recipe extraction depends on website accessibility and supported page structures.
- AI-generated video results may contain missing or incorrect ingredients and instructions.
- Video processing can be slower than URL extraction and may depend on Gemini API availability or quota.
- Meal-category predictions are imperfect, especially for recipes that fit multiple meal occasions.
- Classifier probabilities are not calibrated guarantees of correctness.
- Feedback does not automatically update the active model.
- Local database files and the complete training dataset are not included in the public repository.
- The application is intended for local demonstration and has not been prepared for public multi-user deployment.

## Project Status

**Core implementation complete and locally demonstrated.**

- Recipe URL extraction: Implemented.
- CSV processing: Implemented.
- Video-to-recipe extraction: Implemented.
- ML classification: Implemented.
- Classification feedback storage: Implemented.
- Experimental feedback-aware candidate training: Implemented.
- Automated backend testing: 81 tests passed.
- GitHub documentation and demonstration video: Final preparation.
- Cloud deployment: Deferred unless required.

## Future Improvements

Potential future work includes improved recipe classification, stronger ingredient verification, enhanced video processing, automatic retraining with model approval safeguards, authentication, and cloud deployment.

---

**AI Recipe Intelligence Platform — A full-stack AI and machine-learning portfolio project.**