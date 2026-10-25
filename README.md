# AI Recipe Intelligence Platform

**Turn recipe websites, YouTube cooking videos, and Instagram Reels into structured recipes.**

A full-stack AI and machine-learning project built with **React, TypeScript, FastAPI, SQLite, Gemini, EasyOCR, and scikit-learn**. The application extracts cooking information, organizes ingredients and instructions, classifies recipes, and stores results for review.

> **Project status:** Working local prototype. Website URL extraction, CSV workflows, and direct YouTube/Instagram video-link extraction have been demonstrated locally. This repository is not a hosted public web application.

## Highlights

- **Paste a URL directly:** Enter a supported recipe website, public YouTube video, or public Instagram Reel link. No manual video download or conversion is needed.
- **Video-to-recipe generation:** Use Gemini to identify the dish, ingredients, and timestamped cooking instructions.
- **OCR-assisted verification:** Use EasyOCR to read visible video text and flag ingredients as text-corroborated, possible matches, or requiring review.
- **Recipe website extraction:** Collect available recipe details and normalize them into a consistent structure.
- **Bulk CSV workflows:** Process lists of recipe URLs and import structured recipe datasets.
- **Meal-type classification:** Predict Breakfast, Lunch, Dinner, Snack, or Dessert using a scikit-learn TF-IDF and Logistic Regression pipeline.
- **Feedback workflow:** Save user corrections for review and experimental candidate-model training.
- **Persistence and caching:** Store recipes in SQLite and reuse previously analyzed video-link results.
- **React dashboard:** Explore extracted recipes, imported datasets, classification feedback, and review items.

## How direct video-link extraction works

```text
YouTube / Instagram URL
          |
          v
    FastAPI backend
          |
          +----> SQLite URL cache ----> Return saved recipe (when available)
          |
          v
    Video download (yt-dlp)
          |
          +----> Gemini video analysis ----> Ingredients and cooking steps
          |
          +----> FFmpeg frames -> EasyOCR -> Visible-text evidence
          |                                  |
          +------------> Ingredient comparison
                                   |
                                   v
                         Structured recipe JSON
                                   |
                                   v
                           SQLite + React UI
```

The backend handles downloading and processing. Video extraction depends on the video's accessibility and the availability of the external Gemini API. OCR matches corroborate visible text; they are **not a guarantee** that every ingredient or quantity is correct.

## Features

### Recipe website URLs

Extract supported recipe pages, including available titles, descriptions, ingredients, cooking steps, preparation and cooking times, and servings. Normalize the result, predict a meal category, flag uncertain predictions, and save extracted recipes.

### YouTube and Instagram video URLs

Paste a public cooking-video URL into the extractor. The backend detects the platform, downloads a supported video, analyzes it using Gemini, extracts visible text using EasyOCR, and displays a structured recipe with ingredient evidence and timestamps. Previously analyzed links can return cached results.

Local end-to-end tests have successfully extracted recipes from both **YouTube** and **Instagram**. Processing time varies significantly with video length, OCR workload, and API response time.

### Video uploads

The project also includes a video-upload workflow for supported local cooking videos. Generated recipe details may need manual review.

### CSV processing

Two supported workflows:

1. **Recipe URL CSV:** Validate and process multiple recipe website links with per-row success/error results.
2. **Recipe dataset CSV:** Import structured recipes, normalize ingredients, detect duplicates, save them to SQLite, and browse/filter saved records.

### Machine-learning classification and feedback

The meal classifier uses **TF-IDF** features and **Logistic Regression** to predict five categories: Breakfast, Lunch, Dinner, Snack, and Dessert. Predictions include a confidence score and may be flagged for review.

Users can save category corrections. A separate **experimental candidate-model** workflow prepares feedback, checks for evaluation-set overlap, limits feedback contribution, and compares a candidate model with the active baseline.

> Saving feedback **does not automatically retrain or replace** the active classifier.

## Tech stack

| Layer | Technologies |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| UI | Tailwind CSS, shadcn/ui |
| Backend | Python, FastAPI |
| Storage | SQLite |
| Machine learning | scikit-learn, pandas, joblib |
| Classification | TF-IDF, Logistic Regression |
| Video retrieval | yt-dlp, FFmpeg |
| AI video analysis | Google Gemini API |
| OCR | EasyOCR, PyTorch |
| Website extraction | Requests, Beautiful Soup |
| Testing | pytest |
| API documentation | FastAPI Swagger UI |
| Version control | Git, GitHub |

## Screenshots

Screenshots are referenced below. Add the corresponding image files under `docs/screenshots/` if they are not already present in the repository.

| Dashboard | Recipe URL extraction |
| --- | --- |
| ![Dashboard](docs/screenshots/dashboard.png) | ![Recipe extractor](docs/screenshots/recipe-extractor.png) |

| Bulk CSV | Video-to-recipe extraction |
| --- | --- |
| ![Bulk CSV](docs/screenshots/bulk-csv.png) | ![Video to recipe](docs/screenshots/video-to-recipe.png) |

![Model review](docs/screenshots/model-review.png)

## Model evaluation

The project's documented baseline evaluation used **4,743 recipes** with a stratified 80/20 train/test split.

| Metric | Documented result |
| --- | ---: |
| Total recipes | 4,743 |
| Training recipes | 3,794 |
| Evaluation recipes | 949 |
| Baseline test accuracy | 68.91% |
| Baseline macro F1 | 0.6788 |
| Meal categories | 5 |

### Experimental feedback training

In a controlled experiment, one **synthetic** correction was added to candidate-model training.

| Metric | Baseline | Candidate |
| --- | ---: | ---: |
| Accuracy | 68.9146% | 69.0200% |
| Macro F1 | 0.678754 | 0.679664 |

The candidate was saved separately without replacing the active model. This demonstrates the training workflow; **one synthetic correction is not evidence of a general performance improvement**.

## Getting started (local development)

### Prerequisites

- Python and a compatible environment for the project's dependencies
- Node.js and npm
- Git
- FFmpeg available on your system `PATH` for video processing
- A Gemini API key for AI video analysis
- Internet access for video retrieval and Gemini requests

For YouTube extraction, the current downloader also uses a supported JavaScript runtime (Node.js) through yt-dlp. Video accessibility and extractor compatibility can change over time.

### 1. Clone the repository

```powershell
git clone https://github.com/devshah1601-lgtm/ai-recipe-intelligence.git
cd ai-recipe-intelligence
```

### 2. Set up the Python backend

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

> EasyOCR/PyTorch installation can vary by operating system and hardware. The project has been run with CPU-based OCR; a CUDA GPU is not required.

### 3. Configure Gemini access

Create a `.env` file in the project root:

```dotenv
GEMINI_API_KEY=your_api_key_here
```

The backend loads this key from the environment. **Never commit your `.env` file or a real API key.** Gemini requests may be subject to quotas and rate limits; a free quota, when available, is not guaranteed.

### 4. Run the backend

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

- Backend: `http://127.0.0.1:8001`
- Interactive API docs: `http://127.0.0.1:8001/docs`

### 5. Run the frontend

In a **second terminal**, from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The frontend communicates with the local FastAPI backend. If you change ports, update the corresponding frontend proxy/API configuration.

## Example demonstration

1. Start the backend and frontend.
2. Paste a supported recipe website URL to generate a structured recipe.
3. Paste a public YouTube cooking-video or Instagram Reel URL to generate a recipe from video.
4. Review ingredients, text-verification badges, and timestamped instructions.
5. Reuse the same video URL to demonstrate caching.
6. Open the dashboard, CSV workflows, and model-review screens.
7. Save a classification correction and inspect it in the feedback workflow.

## Automated tests

The project includes backend tests for recipe processing, video input validation, Gemini response validation, ingredient verification, video storage/duplicate handling, and feedback-training safeguards.

The previous README reported **81 passing local tests**. Rerun the suite to confirm the current result:

```powershell
python -m pytest tests/ -q
```

Additional local experiment scripts may exist outside the tracked test suite.

## Project structure

```text
ai-recipe-intelligence/
├── app/
│   ├── main.py
│   ├── ml/
│   ├── models/
│   ├── services/
│   │   ├── gemini_video_analyzer.py
│   │   ├── ingredient_verifier.py
│   │   ├── recipe_store.py
│   │   ├── video_ocr.py
│   │   └── video_url_downloader.py
│   └── scripts/
├── frontend/
├── data/
├── docs/
├── samples/
├── tests/
├── requirements.txt
├── .gitignore
└── README.md
```

Some datasets, SQLite databases, credentials, model artifacts, and experimental files are intentionally excluded from version control. The `docs/` directory and screenshot files should be committed if the README references them.

## Current limitations

- Video-to-recipe extraction is **not instant**; OCR and Gemini processing can take minutes.
- Some video sources may be private, restricted, removed, or unsupported by the downloader.
- Gemini may omit or misinterpret ingredients, measurements, or cooking steps.
- OCR text evidence may miss brief on-screen labels, particularly when frames are sampled less frequently.
- Ingredient verification badges indicate text matching, not independently proven recipe correctness.
- Recipe websites differ in markup and may block scraping.
- Meal-category confidence scores are not calibrated guarantees of correctness.
- User corrections do not automatically retrain the active model.
- This is a **local portfolio prototype**, not a production-ready multi-user service.

## Roadmap

- [x] Recipe website URL extraction
- [x] CSV processing and dataset import
- [x] YouTube and Instagram link-to-recipe extraction
- [x] Gemini analysis with OCR-assisted ingredient verification
- [x] SQLite persistence and video-link caching
- [x] Meal classification and feedback storage
- [x] Experimental feedback-aware candidate training
- [ ] Evaluate faster OCR sampling against an accuracy baseline
- [ ] Improve video-processing progress feedback
- [ ] Add force re-analysis for cached links
- [ ] Add a recorded demo and verify all screenshots
- [ ] Prepare production deployment and multi-user safeguards

## Repository

**Source code:** https://github.com/devshah1601-lgtm/ai-recipe-intelligence

**Live demo:** Not deployed. Run locally using the instructions above.

---

*AI Recipe Intelligence Platform — a full-stack AI and machine-learning portfolio project.*
