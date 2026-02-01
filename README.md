# 🚀 Auto-EDA — Automated Exploratory Data Analysis

Auto-EDA is a web-based application that transforms raw datasets into meaningful insights through fully automated Exploratory Data Analysis (EDA). It eliminates repetitive analysis code and enables fast, consistent, and accessible data understanding for technical and non-technical users.

---

## 🌍 Real-World Problem Addressed

Exploratory Data Analysis is a mandatory first step in every data-driven project. In real-world scenarios, teams face several challenges:

- Manual EDA requires repetitive boilerplate code
- Analysis is time-consuming and error-prone
- Non-technical users cannot easily explore data
- Visualization styles vary across projects
- Important data patterns may be overlooked
- Iteration becomes slow when working with multiple datasets

These challenges slow down decision-making and reduce productivity across data teams.

---

## ✅ Why Auto-EDA Is Important

Auto-EDA solves these problems by automating the entire EDA workflow:

- Converts datasets into insights in seconds
- Removes the need for manual coding
- Standardizes visual analysis
- Enables rapid experimentation
- Lowers the entry barrier to data exploration
- Improves early-stage data quality checks

This significantly reduces **time-to-insight** and improves data-driven decision making.

---

## ✨ Key Features

- Upload datasets in **CSV, XLSX, or JSON** format
- Automatic **Univariate Analysis**
- **Bivariate Analysis** for numerical features
- Optional **Target Column–aware EDA**
- **Correlation Heatmaps**
- **Outlier Detection** using IQR method
- **Dynamic color palette** (random theme per upload)
- Interactive UI with loading indicators
- Automatic cleanup of uploaded files and generated plots

---

## 🧠 How It Works

1. User uploads a dataset
2. Optionally specifies a target column
3. The system automatically:
   - Analyzes dataset structure
   - Generates statistical summaries
   - Creates feature-wise distributions
   - Explores feature relationships
   - Performs target-based analysis (if provided)
4. Results are displayed as clean, interpretable visualizations
5. Temporary files are automatically deleted for security and efficiency

---

## 🛠 Technology Stack

- **Backend:** Flask (Blueprint architecture)
- **Data Processing:** Pandas, NumPy
- **Visualization:** Seaborn, Matplotlib
- **Frontend:** Jinja2, Tailwind CSS
- **Storage:** Local (temporary, auto-cleaned)

---

## 📁 Project Structure

```text
Auto-EDA/
│
├── app/
│   ├── static/
│   │   └── plots/          # Generated plots (auto-deleted)
│   ├── templates/
│   │   ├── file_upload.html
│   │   ├── eda.html
│   │   └── base.html
│   ├── __init__.py
│   └── routes.py
│
├── uploads/                # User uploads (git-ignored)
├── run.py
├── requirements.txt
└── README.md
