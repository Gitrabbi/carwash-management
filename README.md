# 🚗 Car Wash Management System

A comprehensive Streamlit application for managing car wash operations with real-time analytics, worker management, and AI-powered insights.

## Features

- **📊 Dashboard** - Real-time overview with Kanban board and metrics
- **📋 Work Orders** - Create, manage, and track work orders with multi-service selection
- **🔧 Services** - Manage service catalog organized by vehicle type
- **👷 Workers** - Full workforce management with attendance tracking
- **📈 Analytics** - AI-powered insights for attendance, time performance, and customer experience
- **📄 Reports** - Generate and export professional reports (CSV/PDF)

## Quick Start

### Local Installation

1. **Install Python** (3.9 or newer)
   - Download from https://www.python.org/downloads/

2. **Clone or download this project**

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open in browser**
   - Go to: http://localhost:8501

### Online Deployment (Streamlit Cloud)

1. **Create a GitHub account** at https://github.com

2. **Upload this project to GitHub**
   - Create a new repository
   - Upload all files from this folder

3. **Deploy to Streamlit Cloud**
   - Go to https://streamlit.io/cloud
   - Sign up/login with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `app.py`
   - Click "Deploy!"

Your app will be live at: `https://yourusername-repo-name.streamlit.app`

## Project Structure

```
streamlit_carwash/
├── app.py              # Main Streamlit application
├── database.py         # SQLite database operations
├── analytics.py        # AI-powered analytics engine
├── reports.py          # Report generation (CSV/PDF)
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Tech Stack

- **Python 3.9+**
- **Streamlit** - Web framework
- **SQLite** - Database
- **Pandas** - Data manipulation
- **Plotly** - Interactive visualizations
- **ReportLab** - PDF generation

## Screenshots

### Dashboard
Real-time overview with order statistics, Kanban board, and revenue charts.

### Work Orders
Create and manage work orders with multi-service selection and automatic cost calculation.

### Analytics
AI-powered insights including:
- Worker attendance analysis and predictions
- Time performance and efficiency metrics
- Customer experience and sentiment analysis

## License

MIT License - Feel free to use and modify for your business!

---

Built with ❤️ for car wash businesses
