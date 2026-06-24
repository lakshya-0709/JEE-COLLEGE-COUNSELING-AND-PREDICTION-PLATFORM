# JEE College Counseling & Prediction Platform 🎓🤖

An advanced, ML-powered full-stack web application designed to help JEE candidates predict college admission chances (Safe, Moderate, Dream) based on historical JoSAA/CSAB cutoff data (2021–2024). Features beautiful dark-mode glassmorphic layouts, dynamic cutoff trends, comparisons, and choice-filling preference generators.

---

## 🚀 Key Features

* **ML-Based Prediction:** Uses a Gradient Boosting machine learning model trained on **81,000+** real cutoff data points to predict the 2026 closing ranks and categorizes admission chances as *Safe*, *Moderate*, or *Dream*.
* **Interactive Cutoff Trends:** Displays 4-year historical opening/closing cutoff trends using interactive Chart.js line charts.
* **Side-by-Side Comparison:** Compare two college-branch combinations side by side, overlaid on a single chart with automated counseling recommendations.
* **Choice-Filling Preference Generator:** Automatically creates a recommended JoSAA preference order based on priority preferences (College vs. Branch focus) and risk tolerance (Safe, Balanced, Aggressive). Supports drag-and-drop custom reordering and TXT/CSV exporting.
* **Frosted Glass UI:** Premium visual aesthetics using responsive vanilla CSS layouts, smooth animations, and interactive particle background effects.

---

## 📁 Project Directory Layout

```
c:\Users\VICTUS\Desktop\first\
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entrypoint
│   │   ├── config.py               # Core constants, paths, and CORS configuration
│   │   ├── database.py             # Optimized in-memory dataset querying layer
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py          # Pydantic validation request/response schemas
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── predict.py          # /api/predict POST route
│   │   │   ├── trends.py           # /api/trends GET route
│   │   │   ├── compare.py          # /api/compare POST route
│   │   │   ├── preference.py       # /api/preference-list POST route
│   │   │   └── colleges.py         # /api/colleges lookup routes
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── prediction.py       # Core prediction algorithms & ML integration
│   │       └── preference_gen.py   # Preference list optimization logic
│   ├── ml/
│   │   ├── train_model.py          # Machine learning model training script (Scikit-Learn)
│   │   ├── model.joblib            # Serialized Gradient Boosting Regressor model
│   │   └── preprocessor.joblib     # Serialized Ordinal Encoder pipeline
│   ├── data/
│   │   ├── process_data.py         # Data preprocessing pipeline (Excel -> JSON)
│   │   ├── cutoffs_processed.json  # Preprocessed historical JoSAA cutoff dataset
│   │   └── metadata.json           # Cached college & program lookup tables
│   └── requirements.txt            # Python backend dependency manifest
├── frontend/
│   ├── index.html                  # Single-page dashboard container
│   ├── css/
│   │   ├── index.css               # Core variables, fonts, and dark theme tokens
│   │   ├── components.css          # Styled UI components (cards, tables, buttons, etc.)
│   │   └── animations.css          # Transition keyframes, glowing borders & pulsing triggers
│   └── js/
│       ├── app.js                  # Main controller, scrollspy, navbar & background particles
│       ├── api.js                  # API client module connecting frontend and backend
│       ├── predict.js              # Prediction dashboard logic and modals
│       ├── trends.js               # Cutoff trends dashboard with line charts
│       ├── compare.js              # College-to-college side-by-side comparisons
│       └── utils.js                # Utilities (counters, toasts, state list)
└── README.md                       # Documentation and startup guide
```

---

## 🛠️ Installation & Setup

Follow these steps to set up and run the platform locally on Windows.

### Prerequisites
* **Python 3.10+** installed.
* Web Browser (Chrome, Edge, Firefox).

---

### Step 1: Set up the Python Backend

1. **Open PowerShell/Terminal** and navigate to the project directory:
   ```powershell
   cd c:\Users\VICTUS\Desktop\first
   ```

2. **Create and Activate a Virtual Environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```

3. **Install Dependencies:**
   ```powershell
   pip install -r backend/requirements.txt
   ```

---

### Step 2: Run Data Preprocessing & Model Training

If the processed JSON dataset (`backend/data/cutoffs_processed.json`) and trained model files are not present or you want to retrain them, execute the following:

1. **Process JoSAA Excel Files:**
   *(Combines all raw JoSAA spreadsheets into a cleaned dataset)*
   ```powershell
   python -X utf8 backend/data/process_data.py
   ```

2. **Train the ML Predictor:**
   *(Trains a Gradient Boosting Regressor model to predict 2026 closing ranks)*
   ```powershell
   python -X utf8 backend/ml/train_model.py
   ```

---

### Step 3: Start the Backend Server

Launch the FastAPI application with Uvicorn:
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
*The API will start running at:* `http://localhost:8000`

---

### Step 4: Open the Frontend

Since the frontend is built using pure modern Vanilla HTML, CSS, and JS (SPA architecture), you can open it directly:
* Double-click on `frontend/index.html` inside your explorer.
* Or run it using a local VS Code "Live Server" extension on port `5500`.

---

## 🔗 API Documentation Summary

FastAPI automatically generates interactive Swagger API docs at `http://localhost:8000/docs`.

### Key Endpoints:
* **`POST /api/predict`** - Takes rank, category, gender, quota, preferred branches, and returns categorized list of Safe, Moderate, and Dream admissions.
* **`GET /api/trends`** - Takes institute name, program, seat type, and quota, and returns 4-year cutoff records.
* **`POST /api/compare`** - Compares two programs side by side, returning cutoff comparison arrays and a text recommendation.
* **`POST /api/preference-list`** - Generates an optimized list of choices based on candidate rank and preferences.
* **`GET /api/colleges`** - Search/Autocomplete endpoint for institute names.
