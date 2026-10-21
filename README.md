# DataPilot — Data Analytics and AI-Generated Insights

DataPilot is a web-based data analytics application that helps users explore datasets through data processing, statistical analysis, data quality checks, and interactive visualizations. It integrates the Groq API to generate natural-language insights from relevant dataset information and analytical findings prepared by the backend.

**DataPilot combines conventional data analytics with AI-generated insights.** Data processing and analytical calculations are handled by Python and Pandas, while AI is used specifically to interpret the provided context and generate insights.

## Features

- **Dataset Upload:** Upload supported CSV and Excel files for analysis.
- **Data Processing:** Process uploaded datasets using Python and Pandas.
- **Data Quality Checks:** Identify missing values and duplicate records using application logic.
- **Statistical Analysis:** Calculate statistics and summarize relevant dataset characteristics.
- **Interactive Visualizations:** Present analytical results through Plotly charts.
- **AI-Generated Insights:** Generate natural-language explanations using the Groq API and relevant information prepared by the backend.
- **REST API Backend:** Handle frontend requests and backend processing through FastAPI.
- **Configurable Upload Limit:** Configure the maximum permitted file size through backend settings.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript |
| Backend | Python, FastAPI |
| Data Processing | Pandas |
| Data Visualization | Plotly |
| AI Integration | Groq API |
| Communication | REST APIs, JSON |

## How It Works

1. **Upload:** The user selects and uploads a supported dataset through the frontend.
2. **Validate:** The backend validates the uploaded file according to the application's supported formats and size limits.
3. **Process:** Python and Pandas load and process the dataset.
4. **Analyze:** The application performs data quality checks and statistical calculations.
5. **Visualize:** Plotly presents relevant analytical results as interactive charts.
6. **Generate Insights:** The backend prepares relevant dataset information and analytical findings and sends the context to the Groq API.
7. **Display:** The frontend presents the available analysis, visualizations, and AI-generated insights.

## How AI Is Used

AI is used specifically for generating natural-language insights. It does not perform every operation in DataPilot.

| Task | How it is handled |
|---|---|
| File validation | Backend application logic |
| Missing-value detection | Python and Pandas |
| Duplicate detection | Python and Pandas |
| Statistical calculations | Python and Pandas |
| Chart generation | Plotly |
| Natural-language insights | Groq API |

The backend prepares relevant information from the dataset and analytical results before sending it to the language model. The model uses this context to produce readable explanations and insights.

This separation keeps analytical calculations within the application's data-processing logic while using AI to help users interpret the results.

## System Architecture

```text
                 User
                  |
                  v
       React + TypeScript Frontend
                  |
             REST API
                  |
                  v
           FastAPI Backend
                  |
                  v
       Python + Pandas Processing
                  |
          +-------+-------+
          |               |
          v               v
    Data Analytics   Dataset Context
          |           Preparation
          v               |
     Plotly Charts         v
                      Groq API
                          |
                          v
                  AI-Generated Insights
                          |
          +---------------+
          |
          v
      Frontend Results
```

The frontend handles user interaction and presentation. FastAPI coordinates backend operations, Pandas performs data processing and analytics, Plotly visualizes results, and Groq generates natural-language insights.

## Getting Started

Follow these instructions to run the project locally. The commands assume the repository has separate `backend` and `frontend` directories; adjust them if your current repository structure differs.

### Prerequisites

- Python
- Node.js and npm
- Git
- A Groq API key for AI-generated insights

### 1. Clone the Repository

```bash
git clone https://github.com/Incharac16/DataPilot.git
cd DataPilot
```

### 2. Set Up the Backend

```bash
cd backend
python -m venv venv
```

Activate the virtual environment.

**Windows PowerShell**

```powershell
.\venv\Scripts\Activate.ps1
```

**macOS/Linux**

```bash
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Configure the Groq API key using the environment-variable name expected by the backend. Keep the key private and never commit it to GitHub.

Start the backend:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

This command assumes the FastAPI application is available at `app.main:app`.

### 3. Set Up the Frontend

Open a second terminal from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL displayed by the frontend development server. It is commonly `http://localhost:5173`.

### 4. Use the Application

1. Start the backend and frontend.
2. Open the frontend in your browser.
3. Upload a supported dataset.
4. Explore the available analytics and visualizations.
5. Review AI-generated insights when the Groq integration is configured and available.

## Configuration

The backend supports configuring the maximum upload size through the `MAX_UPLOAD_MB` setting.

For example:

```env
MAX_UPLOAD_MB=100
```

This configures a maximum upload size of 100 MiB, subject to the application's validation and any additional infrastructure limits.

Configure environment variables according to the backend's settings. Do not commit `.env` files, API keys, or other secrets to version control.

## Project Structure

The repository separates the frontend and backend to organize the user interface, API handling, and data-processing logic.

```text
DataPilot/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
└── README.md
```

This is a simplified illustration; refer to the repository for the actual file structure.

## Design Principles

- **Separation of responsibilities:** Data processing, visualization, AI integration, and frontend presentation have distinct roles.
- **Conventional analytics:** Data quality checks and statistical calculations are handled by application logic.
- **Context-based AI:** The language model receives relevant information prepared by the backend rather than automatically accessing the uploaded file.
- **Modular architecture:** Separate frontend and backend components support maintainability and future improvements.

## Future Improvements

Potential areas for future development include expanding analytical capabilities, improving insight evaluation, strengthening automated testing, and optimizing performance for larger datasets.

## Author

**Inchara C**

GitHub: [@Incharac16](https://github.com/Incharac16)

---

*DataPilot — Explore your data, understand the results, and gain insights with AI.*
