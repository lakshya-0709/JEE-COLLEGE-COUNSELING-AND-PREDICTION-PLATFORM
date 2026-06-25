# JEE College Counseling & Prediction Platform 🎓🤖

An ML-powered full-stack web application that helps JEE candidates make smarter admission decisions using real **JoSAA cutoff data (2021–2024)**. Predicts 2026 closing ranks with confidence ranges, visualizes multi-year trends, and enables side-by-side college comparisons — all inside a premium dark-mode glassmorphic UI.

---

## 🚀 Features

### 🔮 ML-Based College Prediction
- Gradient Boosting Regressor trained on **81,000+ real JoSAA cutoff records**
- Predicts 2026 closing ranks for every IIT / NIT / IIIT / GFTI branch
- Groups results into **Safe / Moderate / Dream** chance categories
- Displays an **expected rank range** (confidence band) using 1.5× historical standard deviation (~87% confidence interval)
- **ML Guardrails:** Clamps ML output within ±12% of a historical linear trend projection — prevents the model from over-extrapolating on small datasets

### 📊 Cutoff Trends
- 4-year interactive line chart (opening + closing ranks) using Chart.js
- Automated trend direction analysis: *Getting Harder / Getting Easier / Stable*
- Predicted 2026 closing rank displayed alongside historical table

### ⚖️ College Comparison
- Side-by-side comparison of any two college+branch combinations
- Overlaid cutoff trend chart with dual datasets
- Automated counseling recommendation based on latest cutoff competitiveness

### 🔍 Cutoff Lookup
- Look up historical cutoff ranks for any institute + program + seat type + quota combination
- Shows predicted 2026 expected range with trend direction badge
- Filters by Category (OPEN / EWS / OBC-NCL / SC / ST), Gender, and Quota (AI / HS / OS)

### 🎨 Premium UI
- Dark-mode glassmorphism with animated particle canvas background
- Smooth scroll reveal animations and micro-interactions
- Fully responsive layout (mobile + desktop)
- Hash-based SPA routing — no page reloads

---

## 📁 Project Structure

```
first/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint — mounts all routes
│   │   ├── config.py            # Paths, thresholds, and CORS config
│   │   ├── database.py          # In-memory data store with query helpers
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic request/response schemas
│   │   ├── routes/
│   │   │   ├── predict.py       # POST /api/predict
│   │   │   ├── trends.py        # GET  /api/trends  (also powers Cutoff Lookup)
│   │   │   ├── compare.py       # POST /api/compare
│   │   │   └── colleges.py      # GET  /api/colleges (search, programs, branches)
│   │   └── services/
│   │       └── prediction.py    # Core ML prediction logic + batch inference
│   ├── ml/
│   │   ├── train_model.py       # Model training script (Gradient Boosting)
│   │   ├── model.joblib         # Trained model artifact
│   │   └── preprocessor.joblib  # Ordinal encoder artifact
│   ├── data/
│   │   ├── process_data.py      # Excel → JSON preprocessing pipeline
│   │   ├── cutoffs_processed.json  # 81,000+ processed cutoff records
│   │   └── metadata.json        # Institute/program lookup cache
│   └── requirements.txt
├── frontend/
│   ├── index.html               # Single-page app shell
│   ├── css/
│   │   ├── index.css            # Design tokens, variables, dark theme
│   │   ├── components.css       # Cards, tables, forms, layout components
│   │   └── animations.css       # Keyframes, scroll-reveal, micro-interactions
│   └── js/
│       ├── utils.js             # Shared helpers (formatRank, showToast, debounce, etc.)
│       ├── api.js               # Centralized API client (all fetch calls)
│       ├── app.js               # Router, navbar, particle canvas, stat counters
│       ├── predict.js           # Prediction page — form, results, trend modal
│       ├── trends.js            # Cutoff Trends page — chart + table
│       ├── compare.js           # College Comparison page — dual chart + metrics
│       └── cutoff_lookup.js     # Cutoff Lookup page — historical rank search
├── README.md
└── *.xlsx                       # Raw JoSAA Excel source files (2021–2024)
```

---

## 🛠️ Setup & Installation

### Prerequisites
- **Python 3.10+**
- Any modern browser (Chrome / Edge / Firefox)

---

### Step 1 — Python Environment

```powershell
# Navigate to project root
cd C:\Users\VICTUS\Desktop\first

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install dependencies
pip install -r backend/requirements.txt
```

---

### Step 2 — Data Processing & Model Training

> Skip this step if `backend/data/cutoffs_processed.json` and `backend/ml/model.joblib` already exist.

```powershell
# Process raw JoSAA Excel files into a cleaned JSON dataset
python -X utf8 backend/data/process_data.py

# Train the Gradient Boosting Regressor on the processed data
python -X utf8 backend/ml/train_model.py
```

---

### Step 3 — Start the Backend

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

API runs at → `http://localhost:8000`  
Auto-generated Swagger docs → `http://localhost:8000/docs`

---

### Step 4 — Open the Frontend

The frontend is a pure Vanilla HTML/CSS/JS SPA — no build step needed.

- **Option A:** Double-click `frontend/index.html` in File Explorer
- **Option B:** Use VS Code Live Server (right-click → *Open with Live Server*)

---

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/predict` | Predict colleges for a given rank — returns Safe/Moderate/Dream lists |
| `GET` | `/api/trends` | Year-wise cutoff trend for a college+program+category+quota combo |
| `POST` | `/api/compare` | Side-by-side cutoff comparison of two college+branch combos |
| `GET` | `/api/colleges` | Search institutes by name (autocomplete) |
| `GET` | `/api/colleges/programs` | Get all programs offered by an institute |
| `GET` | `/api/colleges/branches` | Get all branch names, optionally filtered by institute type |
| `GET` | `/api/colleges/metadata` | Dataset metadata (categories, states, year range) |
| `GET` | `/api/health` | Health check — confirms data load and ML model status |

---

## 🧠 How the ML Prediction Works

1. **Data:** 81,131 JoSAA cutoff records across 2021–2024 (last round per year)
2. **Features:** `institute_short`, `branch_short`, `seat_type`, `gender`, `quota`, `year`
3. **Target:** `log(closing_rank)` — log-transform reduces skew from extreme ranks
4. **Model:** Gradient Boosting Regressor (scikit-learn) with Ordinal Encoding
5. **Inference:** Batch prediction for all eligible combos in ~50ms

### Guardrails (Prevents Over-Extrapolation)
The raw ML output is clamped using a historical reality-check:
- Compute a linear trend from the last 2 data points, projected to 2026 (with 50% dampening)
- Clamp ML prediction within **±12% of that historical projection**
- This prevents extreme predictions (e.g., IIT Delhi CSE jumping from 116 → 144)

### Confidence Band
The expected rank range shown in results uses:
- **Data-driven:** 1.5× historical standard deviation (~87% confidence) when 3+ years available
- **Fallback:** 8–10% percentage margin for sparse data
- Displayed as `min – predicted_rank` (optimistic-to-expected range)

---

## 📊 Data Source

| Source | Details |
|--------|---------|
| **JoSAA Official** | https://josaa.nic.in |
| **Years Covered** | 2021, 2022, 2023, 2024 |
| **Rounds Used** | Last round per year (Round 6 for 2021–2023, Round 5 for 2024) |
| **Institutes** | IITs, NITs, IIITs, GFTIs |
| **Total Records** | 81,131 cutoff entries |

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, FastAPI, Uvicorn |
| **ML** | scikit-learn (Gradient Boosting), pandas, NumPy, joblib |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (ES6+) |
| **Charts** | Chart.js |
| **Data Format** | JSON (processed from Excel via openpyxl) |

---

## ⚠️ Disclaimer

Predictions are based on historical JoSAA cutoff data and a machine learning model. Actual 2026 admission cutoffs may differ due to changes in seat availability, number of applicants, reservation policies, or other factors. Use this tool as a **reference guide**, not a guarantee of admission.
