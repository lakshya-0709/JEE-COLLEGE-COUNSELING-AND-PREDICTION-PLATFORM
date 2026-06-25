# JEE College Counseling & Prediction Platform 🎓

ML-powered full-stack web app for JEE candidates — predicts 2026 admission chances using real JoSAA cutoff data (2021–2024) with confidence ranges, trend charts, and college comparisons.

---

## Features

| Feature | Description |
|---|---|
| **ML Prediction** | Gradient Boosting model on 81K+ records — groups results into Safe / Moderate / Dream with expected rank range |
| **Cutoff Trends** | 4-year interactive charts with trend direction (harder / easier / stable) and 2026 ML forecast |
| **College Comparison** | Side-by-side dual chart + metrics table + automated recommendation |
| **Cutoff Lookup** | Search historical closing ranks by college, branch, category, gender, and quota |

---

## Tech Stack

| Layer | Tools |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| ML | scikit-learn (Gradient Boosting), pandas, NumPy, joblib |
| Frontend | Vanilla HTML5 / CSS3 / JavaScript (ES6+), Chart.js |
| Data | JoSAA Excel → JSON (81,131 records, 2021–2024) |

---

## Project Structure

```
first/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app — mounts all routes
│   │   ├── config.py            # Paths, thresholds, CORS config
│   │   ├── database.py          # In-memory data store + query helpers
│   │   ├── models/schemas.py    # Pydantic request/response schemas
│   │   ├── routes/
│   │   │   ├── predict.py       # POST /api/predict
│   │   │   ├── trends.py        # GET  /api/trends
│   │   │   ├── compare.py       # POST /api/compare
│   │   │   └── colleges.py      # GET  /api/colleges/*
│   │   └── services/
│   │       └── prediction.py    # ML batch inference + guardrails
│   ├── ml/
│   │   ├── train_model.py       # Training script
│   │   ├── model.joblib         # Trained model
│   │   └── preprocessor.joblib  # Ordinal encoder
│   └── data/
│       ├── process_data.py      # Excel → JSON pipeline
│       ├── cutoffs_processed.json
│       └── metadata.json
├── frontend/
│   ├── index.html               # SPA shell
│   ├── css/
│   │   ├── index.css            # Design tokens, dark theme
│   │   ├── components.css       # UI components
│   │   └── animations.css       # Keyframes, micro-interactions
│   └── js/
│       ├── utils.js             # Shared helpers (formatRank, toast, debounce)
│       ├── api.js               # Centralized fetch client
│       ├── app.js               # Router, navbar, particle canvas
│       ├── predict.js           # Prediction page logic
│       ├── trends.js            # Trends chart + table
│       ├── compare.js           # Comparison chart + metrics
│       └── cutoff_lookup.js     # Cutoff Lookup search
└── README.md
```

---

## Setup

### 1. Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate
pip install -r backend/requirements.txt
```

### 2. Process Data & Train Model
> Skip if `cutoffs_processed.json` and `model.joblib` already exist.
```powershell
python -X utf8 backend/data/process_data.py
python -X utf8 backend/ml/train_model.py
```

### 3. Start Backend
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
API → `http://localhost:8000` | Swagger docs → `http://localhost:8000/docs`

### 4. Open Frontend
Open `frontend/index.html` directly in browser or use VS Code Live Server.

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/predict` | Predict colleges for a given rank |
| `GET` | `/api/trends` | Year-wise cutoff trend for a college+program combo |
| `POST` | `/api/compare` | Side-by-side comparison of two college+branch combos |
| `GET` | `/api/colleges` | Institute autocomplete search |
| `GET` | `/api/colleges/programs` | Programs list for an institute |
| `GET` | `/api/colleges/branches` | Branch names, filtered by institute type |
| `GET` | `/api/health` | Server status + data/model load check |

---

## How the ML Works

- **Features:** `institute`, `branch`, `seat_type`, `gender`, `quota`, `year`
- **Target:** `log(closing_rank)` — log-transform reduces rank skew
- **Inference:** Batch prediction for all eligible combos in ~50ms

**Guardrails:** ML output is clamped within ±12% of a historical linear projection to prevent over-extrapolation.

**Confidence Band:** Expected range = `min – predicted` using 1.5× standard deviation (~87% CI) of historical closing ranks.

---

> ⚠️ Predictions are based on historical data. Actual 2026 cutoffs may vary. Use as a reference guide only.
