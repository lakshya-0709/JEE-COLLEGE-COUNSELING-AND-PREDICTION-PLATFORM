# JEE College Counseling & Prediction Platform

ML-powered web app for JEE candidates — predicts 2026 admission chances using JoSAA cutoff data (2021–2024).

---

## Features

- College Prediction — Gradient Boosting model on 81K+ records, groups results as Safe / Moderate / Dream with expected rank range
- Cutoff Trends — 4-year charts with trend direction and 2026 forecast
- College Comparison — Side-by-side cutoff chart + metrics + recommendation
- Cutoff Lookup — Search historical closing ranks by college, branch, category, gender, quota

## Tech Stack

- Backend: Python, FastAPI, Uvicorn
- ML: scikit-learn (Gradient Boosting), pandas, NumPy, joblib
- Frontend: HTML, CSS, JavaScript, Chart.js
- Data: JoSAA Excel files → JSON (81,131 records, 2021–2024)

---

## Project Structure

```
first/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Paths, thresholds, CORS
│   │   ├── database.py          # In-memory data store
│   │   ├── models/schemas.py    # Pydantic schemas
│   │   ├── routes/
│   │   │   ├── predict.py       # POST /api/predict
│   │   │   ├── trends.py        # GET  /api/trends
│   │   │   ├── compare.py       # POST /api/compare
│   │   │   └── colleges.py      # GET  /api/colleges/*
│   │   └── services/
│   │       └── prediction.py    # ML inference + guardrails
│   ├── ml/
│   │   ├── train_model.py
│   │   ├── model.joblib
│   │   └── preprocessor.joblib
│   └── data/
│       ├── process_data.py
│       ├── cutoffs_processed.json
│       └── metadata.json
├── frontend/
│   ├── index.html
│   ├── css/
│   │   ├── index.css
│   │   ├── components.css
│   │   └── animations.css
│   └── js/
│       ├── utils.js
│       ├── api.js
│       ├── app.js
│       ├── predict.js
│       ├── trends.js
│       ├── compare.js
│       └── cutoff_lookup.js
└── README.md
```

---

## Setup

1. Install dependencies
```powershell
python -m venv venv
.\venv\Scripts\Activate
pip install -r backend/requirements.txt
```

2. Process data and train model (skip if already done)
```powershell
python -X utf8 backend/data/process_data.py
python -X utf8 backend/ml/train_model.py
```

3. Start backend
```powershell
uvicorn backend.app.main:app --reload --port 8000
```

4. Open frontend
Open `frontend/index.html` in a browser or use VS Code Live Server.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/predict` | Predict colleges for a given rank |
| GET | `/api/trends` | Year-wise cutoff trend |
| POST | `/api/compare` | Compare two college+branch combos |
| GET | `/api/colleges` | Institute autocomplete search |
| GET | `/api/colleges/programs` | Programs for an institute |
| GET | `/api/colleges/branches` | Available branch names |
| GET | `/api/health` | Server and model status |

Swagger docs available at `http://localhost:8000/docs`

---

## ML Details

- Features: institute, branch, seat type, gender, quota, year
- Target: `log(closing_rank)` to reduce rank skew
- Batch inference for all combos in ~50ms
- ML output is clamped within ±12% of historical trend projection to prevent over-extrapolation
- Confidence range uses 1.5× standard deviation of historical closing ranks (~87% CI)

---

> Predictions are based on historical data and may not reflect actual 2026 cutoffs. Use as a reference only.
