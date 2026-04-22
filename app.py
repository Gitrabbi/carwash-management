import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

from database import db
from analytics import CarWashAnalytics
from reports import ReportGenerator

# ------------------ CONFIG ------------------ #
st.set_page_config(
    page_title="SmartWash Dashboard",
    page_icon="🚗",
    layout="wide"
)

# ------------------ MODERN CSS ------------------ #
st.markdown("""
<style>

/* Global */
body {
    background-color: #f5f7fb;
}

/* Header */
.header {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:10px 0;
}
.header h1 {
    margin:0;
    font-size:28px;
    color:#111827;
}
.header p {
    margin:0;
    color:#6b7280;
}

/* Cards */
.card {
    background:white;
    padding:20px;
    border-radius:14px;
    box-shadow:0px 4px 12px rgba(0,0,0,0.05);
    border:1px solid #e5e7eb;
}

/* Metrics */
.metric-title {
    font-size:14px;
    color:#6b7280;
}
.metric-value {
    font-size:28px;
    font-weight:700;
    color:#111827;
}

/* Section Titles */
.section-title {
    font-size:20px;
    font-weight:600;
    margin:20px 0 10px 0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color:#111827;
}
section[data-testid="stSidebar"] * {
    color:white !important;
}

</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------ #
st.markdown(f"""
<div class="header">
    <div>
        <h1>🚗 SmartWash Dashboard</h1>
        <p>Car Wash Operations & Analytics</p>
    </div>
    <div>{datetime.now().strftime("%A, %d %B %Y")}</div>
</div>
<hr>
""", unsafe_allow_html=True)

# ------------------ SIDEBAR ------------------ #
st.sidebar.title("🚗 SmartWash")

menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Operations", "Customers", "Reports"]
)

# ------------------ HELPERS ------------------ #
def metric_card(title, value):
    st.markdown(f"""
    <div class="card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# ------------------ DASHBOARD ------------------ #
if menu == "Dashboard":
    st.markdown('<div class="section-title">📊 Overview</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    # Dummy values (replace with real DB calls)
    total_cars = 45
    revenue = 2300
    active_jobs = 6
    completed = 39

    with col1:
        metric_card("Total Cars Today", total_cars)
    with col2:
        metric_card("Revenue (GHS)", f"{revenue}")
    with col3:
        metric_card("Active Jobs", active_jobs)
    with col4:
        metric_card("Completed", completed)

    # -------- CHART -------- #
    st.markdown('<div class="section-title">📈 Revenue Trend</div>', unsafe_allow_html=True)

    df = pd.DataFrame({
        "Day": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "Revenue": [400, 600, 500, 700, 900]
    })

    fig = px.line(df, x="Day", y="Revenue", markers=True)

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=30, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------ OPERATIONS ------------------ #
elif menu == "Operations":
    st.markdown('<div class="section-title">🧽 Wash Operations</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">Coming soon: Job tracking & workflow</div>', unsafe_allow_html=True)

# ------------------ CUSTOMERS ------------------ #
elif menu == "Customers":
    st.markdown('<div class="section-title">👥 Customers</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">Coming soon: Customer database</div>', unsafe_allow_html=True)

# ------------------ REPORTS ------------------ #
elif menu == "Reports":
    st.markdown('<div class="section-title">📄 Reports</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">Generate and download reports</div>', unsafe_allow_html=True)
