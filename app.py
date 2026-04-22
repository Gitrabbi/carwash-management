"""
Car Wash Management System - Main Streamlit Application
A comprehensive dashboard for managing car wash operations with analytics and reporting
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import base64
import uuid
from database import Database, db
from analytics import CarWashAnalytics
from reports import ReportGenerator

# Page configuration
st.set_page_config(
    page_title="Car Wash Management System",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a365d;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #718096;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-card.green {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    .metric-card.orange {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .metric-card.blue {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-weight: 600;
    }
    div[data-testid="stHorizontalBlock"] > div {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables for persistent data across pages"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"
    if 'db' not in st.session_state:
        st.session_state.db = db
    if 'analytics' not in st.session_state:
        st.session_state.analytics = CarWashAnalytics(db)
    if 'reports' not in st.session_state:
        st.session_state.reports = ReportGenerator(db)


def sidebar_navigation():
    """Render sidebar navigation menu"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <span style="font-size: 3rem;">🚗</span>
            <h2 style="color: #1a365d; margin-top: 0.5rem;">Car Wash Pro</h2>
        </div>
        """, unsafe_allow_html=True)
        
        pages = {
            "📊 Dashboard": "Dashboard",
            "📋 Work Orders": "Work Orders",
            "🔧 Services": "Services",
            "👷 Workers": "Workers",
            "📈 Analytics": "Analytics",
            "📄 Reports": "Reports"
        }
        
        st.markdown("---")
        
        selected = st.radio(
            "Navigation",
            options=list(pages.keys()),
            index=list(pages.values()).index(st.session_state.current_page),
            label_visibility="collapsed"
        )
        
        st.session_state.current_page = pages[selected]
        
        st.markdown("---")
        
        with st.expander("⚙️ Settings", expanded=False):
            date_range = st.selectbox(
                "Default Date Range",
                ["Today", "Last 7 Days", "Last 30 Days", "All Time"]
            )
        
        return st.session_state.current_page


def render_dashboard():
    """Render main dashboard with key metrics and visualizations"""
    st.markdown('<h1 class="main-header">Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Real-time overview of your car wash operations</p>', unsafe_allow_html=True)
    
    # Initialize analytics
    analytics = CarWashAnalytics(db)
    
    # Date range selector
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        date_range = st.selectbox(
            "Select Date Range",
            ["Today", "Last 7 Days", "Last 30 Days", "This Month", "All Time"],
            label_visibility="collapsed"
        )
    
    # Calculate date range
    today = datetime.now().date()
    if date_range == "Today":
        date_from = date_to = today.strftime("%Y-%m-%d")
    elif date_range == "Last 7 Days":
        date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        date_to = today.strftime("%Y-%m-%d")
    elif date_range == "Last 30 Days":
        date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        date_to = today.strftime("%Y-%m-%d")
    elif date_range == "This Month":
        date_from = today.replace(day=1).strftime("%Y-%m-%d")
        date_to = today.strftime("%Y-%m-%d")
    else:
        date_from = date_to = None
    
    # Fetch data
    stats = db.get_order_statistics(date_from, date_to)
    worker_performance = db.get_worker_performance(date_from, date_to)
    service_popularity = db.get_service_popularity(date_from, date_to)
    daily_revenue = db.get_daily_revenue(days=30)
    
    # Key Metrics Cards
    st.markdown("### Key Metrics")
    
    metric_cols = st.columns(4)
    
    with metric_cols[0]:
        total_orders = stats.get('total_orders', 0)
        st.metric(
            "Total Orders",
            total_orders,
            delta=None
        )
    
    with metric_cols[1]:
        today_orders = stats.get('today_orders', 0)
        st.metric(
            "Today's Orders",
            today_orders,
            delta=None
        )
    
    with metric_cols[2]:
        total_revenue = stats.get('total_revenue', 0)
        st.metric(
            "Total Revenue",
            f"GHS {total_revenue:,.0f}",
            delta=None
        )
    
    with metric_cols[3]:
        today_revenue = stats.get('today_revenue', 0)
        st.metric(
            "Today's Revenue",
            f"GHS {today_revenue:,.0f}",
            delta=None
        )
    
    st.markdown("---")
    
    # Status Overview and Charts
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Order Status Distribution")
        
        status_data = stats.get('by_status', {})
        if status_data:
            status_df = pd.DataFrame([
                {'Status': status.title(), 'Count': data.get('count', 0), 'Revenue': data.get('revenue', 0)}
                for status, data in status_data.items()
            ])
            
            if not status_df.empty:
                fig = px.pie(
                    status_df,
                    values='Count',
                    names='Status',
                    color='Status',
                    color_discrete_map={
                        'pending': '#ffc107',
                        'in_progress': '#2196f3',
                        'completed': '#4caf50',
                        'cancelled': '#f44336'
                    }
                )
                fig.update_layout(
                    showlegend=True,
                    margin=dict(l=20, r=20, t=20, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No order data available for the selected period")
    
    with col2:
        st.markdown("### Revenue Trend")
        
        if daily_revenue:
            revenue_df = pd.DataFrame(daily_revenue)
            revenue_df['date'] = pd.to_datetime(revenue_df['date'])
            
            fig = px.line(
                revenue_df,
                x='date',
                y='revenue',
                markers=True,
                line_shape="spline"
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Revenue (GHS)",
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            fig.update_traces(line=dict(color='#4facfe', width=3))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No revenue data available")
    
    # Kanban Board
    st.markdown("### Work Orders Board")
    
    orders = db.get_all_work_orders(date_from=date_from, date_to=date_to)
    
    if orders:
        pending = [o for o in orders if o['status'] == 'pending']
        in_progress = [o for o in orders if o['status'] == 'in_progress']
        completed = [o for o in orders if o['status'] == 'completed']
        cancelled = [o for o in orders if o['status'] == 'cancelled']
        
        board_cols = st.columns(4)
        
        with board_cols[0]:
            st.markdown("#### 🟡 Pending")
            st.markdown(f"**{len(pending)} orders**")
            for order in pending[:5]:
                with st.container():
                    st.markdown(f"""
                    <div style="background: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #ffc107;">
                        <strong>{order['id'][-6:]}</strong><br>
                        {order['customer_name']}<br>
                        <span style="color: #666;">{order['vehicle_type']} - {order['plate_number']}</span><br>
                        <strong style="color: #4facfe;">GHS {order['total_cost']:,.0f}</strong>
                    </div>
                    """, unsafe_allow_html=True)
        
        with board_cols[1]:
            st.markdown("#### 🔵 In Progress")
            st.markdown(f"**{len(in_progress)} orders**")
            for order in in_progress[:5]:
                started = datetime.fromisoformat(order['started_at']) if order.get('started_at') else None
                elapsed = ""
                if started:
                    elapsed = datetime.now() - started
                    elapsed = f"{int(elapsed.total_seconds() / 60)}m"
                
                with st.container():
                    st.markdown(f"""
                    <div style="background: #cfe2ff; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #2196f3;">
                        <strong>{order['id'][-6:]}</strong><br>
                        {order['customer_name']}<br>
                        <span style="color: #666;">{order['vehicle_type']} - {order['plate_number']}</span><br>
                        <span style="color: #4caf50;">{order.get('assigned_worker_name', 'Unassigned')}</span>
                        {f"<br><span style='color: #f44336;'>⏱ {elapsed}</span>" if elapsed else ""}
                    </div>
                    """, unsafe_allow_html=True)
        
        with board_cols[2]:
            st.markdown("#### 🟢 Completed")
            st.markdown(f"**{len(completed)} orders**")
            for order in completed[:5]:
                with st.container():
                    rating_html = ""
                    if order.get('customer_rating'):
                        stars = "⭐" * int(order['customer_rating'])
                        rating_html = f"<br>{stars}"
                    
                    st.markdown(f"""
                    <div style="background: #d1e7dd; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #4caf50;">
                        <strong>{order['id'][-6:]}</strong><br>
                        {order['customer_name']}<br>
                        <span style="color: #666;">{order['vehicle_type']} - {order['plate_number']}</span><br>
                        <strong style="color: #4caf50;">GHS {order['total_cost']:,.0f}</strong>
                        {rating_html}
                    </div>
                    """, unsafe_allow_html=True)
        
        with board_cols[3]:
            st.markdown("#### 🔴 Cancelled")
            st.markdown(f"**{len(cancelled)} orders**")
            for order in cancelled[:5]:
                with st.container():
                    st.markdown(f"""
                    <div style="background: #f8d7da; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #f44336;">
                        <strong>{order['id'][-6:]}</strong><br>
                        {order['customer_name']}<br>
                        <span style="color: #666;">{order['vehicle_type']} - {order['plate_number']}</span><br>
                        <span style="color: #f44336;">Cancelled</span>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No orders found for the selected period. Create your first work order!")
    
    # Top Services
    st.markdown("---")
    st.markdown("### Most Popular Services")
    
    if service_popularity:
        services_df = pd.DataFrame(service_popularity[:10])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                services_df,
                x='count',
                y='name',
                orientation='h',
                color='count',
                color_continuous_scale='blues'
            )
            fig.update_layout(
                yaxis_title="",
                xaxis_title="Number of Orders",
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Top 5 Services")
            for i, service in enumerate(service_popularity[:5], 1):
                st.markdown(f"""
                **{i}. {service['name']}**
                - Orders: {service['count']}
                - Revenue: GHS {service['total_revenue']:,.0f}
                """)
    else:
        st.info("No service data available yet")


def render_work_orders():
    """Render work orders management page with full CRUD operations"""
    st.markdown('<h1 class="main-header">Work Orders</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Create and manage car wash work orders</p>', unsafe_allow_html=True)
    
    # Tabs for different sections
    tabs = st.tabs(["📝 New Order", "📋 Active Orders", "✅ Completed", "🔄 Reassign Jobs"])
    
    # Tab 1: Create New Order
    with tabs[0]:
        st.markdown("### Create New Work Order")
        
        with st.form("new_order_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Customer Information")
                customer_name = st.text_input("Customer Name *", placeholder="Enter customer name")
                customer_phone = st.text_input("Customer Phone", placeholder="Enter phone number")
                
                st.markdown("#### Vehicle Information")
                vehicle_type = st.selectbox("Vehicle Type *", 
                    [vt['name'] for vt in db.get_all_vehicle_types()])
                vehicle_make = st.text_input("Vehicle Make", placeholder="e.g., Toyota")
                vehicle_model = st.text_input("Vehicle Model", placeholder="e.g., Camry")
                plate_number = st.text_input("Plate Number *", placeholder="Enter plate number").upper()
            
            with col2:
                st.markdown("#### Services")
                
                # Get ALL services (don't filter by vehicle type)
                services = db.get_all_services()
                
                if services:
                    selected_services = []
                    service_costs = {}
                    
                    for service in services:
                        checked = st.checkbox(
                            f"{service['name']} - GHS {service['base_price']:.0f}",
                            value=False,
                            key=f"service_{service['id']}"
                        )
                        if checked:
                            selected_services.append(service['name'])
                            service_costs[service['name']] = service['base_price']
                    
                    total_cost = sum(service_costs.values())
                    
                    st.markdown("---")
                    st.markdown(f"**Total Cost: GHS {total_cost:.2f}**")
                else:
                    st.warning("No services available. Please add services first.")
                    selected_services = []
                    total_cost = 0
                
                st.markdown("#### Order Details")
                priority = st.selectbox("Priority", ["normal", "high", "low"])
                assigned_worker = st.selectbox("Assign Worker", 
                    ["None"] + [w['name'] for w in db.get_all_workers()])
            
            submitted = st.form_submit_button("Create Work Order", type="primary", use_container_width=True)
            
            if submitted:
                if not customer_name or not plate_number or not vehicle_type:
                    st.error("Please fill in all required fields")
                else:
                    worker_info = None
                    if assigned_worker != "None":
                        workers = db.get_all_workers()
                        worker = next((w for w in workers if w['name'] == assigned_worker), None)
                        if worker:
                            worker_info = (worker['id'], worker['name'])
                    
                    order_id = db.create_work_order(
                        customer_name=customer_name,
                        customer_phone=customer_phone,
                        vehicle_type=vehicle_type,
                        vehicle_make=vehicle_make or "",
                        vehicle_model=vehicle_model or "",
                        plate_number=plate_number,
                        services=selected_services,
                        total_cost=total_cost,
                        priority=priority,
                        assigned_worker_id=worker_info[0] if worker_info else None,
                        assigned_worker_name=worker_info[1] if worker_info else None
                    )
                    
                    st.success(f"Work Order {order_id} created successfully!")
                    st.balloons()
    
    # Tab 2: Active Orders
    with tabs[1]:
        st.markdown("### Active Orders")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                ["pending", "in_progress", "completed", "cancelled"],
                default=["pending", "in_progress"]
            )
        with col2:
            worker_filter = st.selectbox(
                "Filter by Worker",
                ["All Workers"] + [w['name'] for w in db.get_all_workers()]
            )
        with col3:
            search = st.text_input("Search Order ID or Customer", placeholder="Enter search term")
        
        # Fetch and filter orders
        orders = db.get_all_work_orders()
        
        if status_filter:
            orders = [o for o in orders if o['status'] in status_filter]
        
        if worker_filter != "All Workers":
            orders = [o for o in orders if o.get('assigned_worker_name') == worker_filter]
        
        if search:
            orders = [o for o in orders if 
             search.lower() in str(o['id']).lower() or 
             search.lower() in o['customer_name'].lower() or
             search.lower() in o['plate_number'].lower()]
        if orders:
            # Display orders
            for order in orders[:20]:
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{order['id']}**")
                        st.caption(f"📅 {datetime.fromisoformat(order['created_at']).strftime('%b %d, %H:%M')}")
                    
                    with col2:
                        st.markdown(f"""
                        **{order['customer_name']}** - {order['plate_number']}<br>
                        <span style="color: #666;">{order['vehicle_type']} | {order['services']}</span>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        status_colors = {
                            'pending': '🟡',
                            'in_progress': '🔵',
                            'completed': '🟢',
                            'cancelled': '🔴'
                        }
                        status_icon = status_colors.get(order['status'], '⚪')
                        st.markdown(f"{status_icon} {order['status'].replace('_', ' ').title()}")
                        
                        if order.get('assigned_worker_name'):
                            st.caption(f"👷 {order['assigned_worker_name']}")
                    
                    with col4:
                        st.markdown(f"**GHS {order['total_cost']:,.0f}**")
                        
                        # Action buttons
                        if order['status'] == 'pending':
                            if st.button("▶️ Start", key=f"start_{order['id']}"):
                                db.start_work_order(order['id'])
                                st.rerun()
                        
                        elif order['status'] == 'in_progress':
                            if st.button("✅ Complete", key=f"complete_{order['id']}"):
                                db.complete_work_order(order['id'])
                                st.rerun()
            
            st.markdown(f"Showing {min(20, len(orders))} of {len(orders)} orders")
        else:
            st.info("No active orders found matching your criteria")
    
    # Tab 3: Completed Orders
    with tabs[2]:
        st.markdown("### Completed Orders")
        
        completed_orders = [o for o in db.get_all_work_orders() if o['status'] == 'completed']
        
        if completed_orders:
            # Summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Completed", len(completed_orders))
            with col2:
                total_revenue = sum(o['total_cost'] for o in completed_orders)
                st.metric("Total Revenue", f"GHS {total_revenue:,.0f}")
            with col3:
                avg_rating = sum(o.get('customer_rating', 0) or 0 for o in completed_orders) / len(completed_orders)
                st.metric("Average Rating", f"{avg_rating:.1f} ⭐")
            
            # Display completed orders table
            df = pd.DataFrame(completed_orders)
            display_df = df[[
                'id', 'customer_name', 'plate_number', 'vehicle_type',
                'services', 'total_cost', 'assigned_worker_name', 'ended_at', 'customer_rating'
            ]].copy()
            display_df['ended_at'] = pd.to_datetime(display_df['ended_at']).dt.strftime('%b %d, %H:%M')
            display_df.columns = ['Order ID', 'Customer', 'Plate', 'Vehicle', 'Services', 
                                 'Total (GHS)', 'Worker', 'Completed At', 'Rating']
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No completed orders yet")
    
    # Tab 4: Reassign Jobs
    with tabs[3]:
        st.markdown("### Reassign Jobs")
        st.markdown("Transfer work orders between workers")
        
        # Get in-progress orders
        in_progress = [o for o in db.get_all_work_orders() if o['status'] in ['pending', 'in_progress']]
        
        if in_progress:
            order_options = {o['id']: f"{o['id']} - {o['customer_name']} ({o.get('assigned_worker_name', 'Unassigned')})" 
                           for o in in_progress}
            
            selected_order = st.selectbox("Select Order to Reassign", options=list(order_options.keys()),
                                        format_func=lambda x: order_options[x])
            
            if selected_order:
          order = next(o for o in in_progress if str(o['id']) == str(selected_order))
                
                col1, col2 = st.columns(2)
                
                with col1:
                    with col1:
    st.markdown("#### Current Assignment")
    
    try:
        order_id = order.get('id')
        customer = order.get('customer_name')
        worker = order.get('assigned_worker_name') or 'Unassigned'
    except Exception:
        st.error("Error reading order data")
        st.write(order)
        return

    st.info(f"""
    **Order:** {order_id}<br>
    **Customer:** {customer}<br>
    **Current Worker:** {worker}
    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("#### New Assignment")
                    workers = db.get_all_workers()
                    worker_options = {w['id']: f"{w['name']} ({w['role']})" for w in workers}
                    
                    new_worker_id = st.selectbox(
                        "Select New Worker",
                        options=list(worker_options.keys()),
                        format_func=lambda x: worker_options[x]
                    )
                    
                    if st.button("Reassign Job", type="primary"):
                        new_worker = next(w for w in workers if w['id'] == new_worker_id)
                        db.assign_worker_to_order(selected_order, new_worker['id'], new_worker['name'])
                        st.success(f"Order {selected_order} reassigned to {new_worker['name']}")
                        st.rerun()
        else:
            st.info("No orders available for reassignment")


def render_services():
    """Render services management page"""
    st.markdown('<h1 class="main-header">Services</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Manage car wash services and pricing</p>', unsafe_allow_html=True)
    
    tabs = st.tabs(["📋 All Services", "➕ Add Service", "🚗 Vehicle Types"])
    
    # Tab 1: All Services
    with tabs[0]:
        st.markdown("### Service Catalog")
        
        services = db.get_all_services()
        vehicle_types = db.get_all_vehicle_types()
        
        if services:
            # Group by vehicle type
            for vt in vehicle_types:
                vt_services = [s for s in services if s['vehicle_type'] == vt['name']]
                
                if vt_services:
                    with st.expander(f"🚗 {vt['name']} ({len(vt_services)} services)", expanded=True):
                        for service in vt_services:
                            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                            
                            with col1:
                                st.markdown(f"**{service['name']}**")
                                st.caption(service.get('description', ''))
                            
                            with col2:
                                st.markdown(f"⏱ {service['duration_minutes']} min")
                            
                            with col3:
                                st.markdown(f"**GHS {service['base_price']:.0f}**")
                            
                            with col4:
                                if st.button("🗑️", key=f"del_{service['id']}"):
                                    db.delete_service(service['id'])
                                    st.rerun()
        else:
            st.info("No services found. Add your first service!")
    
    # Tab 2: Add Service
    with tabs[1]:
        st.markdown("### Add New Service")
        
        with st.form("add_service_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Service Name *", placeholder="e.g., Premium Exterior Wash")
                description = st.text_area("Description", placeholder="Describe the service")
                vehicle_type = st.selectbox("Vehicle Type *", 
                    [vt['name'] for vt in db.get_all_vehicle_types()])
            
            with col2:
                base_price = st.number_input("Base Price (GHS) *", min_value=0.0, step=10.0)
                duration = st.number_input("Duration (minutes) *", min_value=5, step=5, value=30)
            
            submitted = st.form_submit_button("Add Service", type="primary", use_container_width=True)
            
            if submitted:
                if not name or not vehicle_type or base_price <= 0:
                    st.error("Please fill in all required fields")
                else:
                    service_id = db.add_service(name, description, base_price, duration, vehicle_type)
                    st.success(f"Service '{name}' added successfully!")
                    st.rerun()
    
    # Tab 3: Vehicle Types
    with tabs[2]:
        st.markdown("### Vehicle Types")
        
        vehicle_types = db.get_all_vehicle_types()
        
        for vt in vehicle_types:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #4facfe;">
                    <strong>{vt['name']}</strong><br>
                    <span style="color: #666;">{vt.get('description', 'No description')}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                services_count = len([s for s in db.get_all_services() if s['vehicle_type'] == vt['name']])
                st.metric("Services", services_count)
        
        st.markdown("---")
        
        with st.form("add_vehicle_type", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                name = st.text_input("New Vehicle Type Name *", placeholder="e.g., Sports Car")
                description = st.text_input("Description", placeholder="Brief description")
            
            with col2:
                st.markdown("")  # Spacing
                submitted = st.form_submit_button("Add Type", use_container_width=True)
            
            if submitted:
                if not name:
                    st.error("Please enter a vehicle type name")
                else:
                    db.add_vehicle_type(name, description)
                    st.success(f"Vehicle type '{name}' added!")
                    st.rerun()


def render_workers():
    """Render worker management page with full CRUD operations"""
    st.markdown('<h1 class="main-header">Workers</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Manage your car wash workforce</p>', unsafe_allow_html=True)
    
    tabs = st.tabs(["👷 All Workers", "➕ Add Worker", "📅 Attendance", "⏰ Clock In/Out"])
    
    # Tab 1: All Workers
    with tabs[0]:
        st.markdown("### Workforce Overview")
        
        workers = db.get_all_workers(active_only=False)
        performance = db.get_worker_performance()
        
        col1, col2, col3, col4 = st.columns(4)
        active = len([w for w in workers if w['is_active']])
        with col1:
            st.metric("Total Workers", len(workers))
        with col2:
            st.metric("Active", active)
        with col3:
            st.metric("Inactive", len(workers) - active)
        with col4:
            if performance:
                top_worker = max(performance, key=lambda x: x.get('completed_orders', 0))
                st.metric("Top Performer", top_worker.get('name', 'N/A'))
        
        st.markdown("---")
        
        # Worker cards
        for worker in workers:
            perf = next((p for p in performance if p['id'] == worker['id']), {})
            
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
                
                with col1:
                    status_emoji = "🟢" if worker['is_active'] else "🔴"
                    st.markdown(f"### {status_emoji} {worker['name']}")
                    st.caption(f"📧 {worker.get('email', 'No email')}")
                
                with col2:
                    st.markdown(f"**Role:** {worker['role']}")
                    st.caption(f"📅 Joined: {worker.get('hire_date', 'N/A')}")
                
                with col3:
                    st.markdown("**Performance**")
                    st.markdown(f"Orders: {perf.get('completed_orders', 0)}")
                    st.markdown(f"Revenue: GHS {perf.get('total_revenue', 0):,.0f}")
                
                with col4:
                    rating = perf.get('avg_rating', 0)
                    if rating > 0:
                        st.markdown(f"**Rating:** ⭐ {rating:.1f}")
                    else:
                        st.markdown("**Rating:** N/A")
                
                with col5:
                    if worker['is_active']:
                        if st.button("❌ Deactivate", key=f"deact_{worker['id']}"):
                            db.update_worker(worker['id'], is_active=0)
                            st.rerun()
                    else:
                        if st.button("✅ Activate", key=f"act_{worker['id']}"):
                            db.update_worker(worker['id'], is_active=1)
                            st.rerun()
                
                st.markdown("---")
    
    # Tab 2: Add Worker
    with tabs[1]:
        st.markdown("### Add New Worker")
        
        with st.form("add_worker_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name *", placeholder="Enter worker's full name")
                role = st.selectbox("Role *", 
                    ["Washer", "Senior Washer", "Detailing Specialist", "Supervisor", "Manager"])
                phone = st.text_input("Phone Number", placeholder="+233...")
                email = st.text_input("Email", placeholder="worker@example.com")
            
            with col2:
                hire_date = st.date_input("Hire Date", value=datetime.now().date())
                hourly_rate = st.number_input("Hourly Rate (GHS)", min_value=0.0, step=1.0, value=20.0)
                skills = st.text_area("Skills", placeholder="e.g., Exterior Wash, Interior Clean, Detailing")
            
            submitted = st.form_submit_button("Add Worker", type="primary", use_container_width=True)
            
            if submitted:
                if not name or not role:
                    st.error("Please fill in required fields")
                else:
                    worker_id = db.add_worker(
                        name=name,
                        role=role,
                        phone=phone,
                        email=email,
                        hire_date=hire_date.strftime("%Y-%m-%d"),
                        hourly_rate=hourly_rate,
                        skills=skills
                    )
                    st.success(f"Worker '{name}' added successfully!")
                    st.rerun()
    
    # Tab 3: Attendance
    with tabs[2]:
        st.markdown("### Attendance Records")
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input("From Date", value=datetime.now().date() - timedelta(days=30))
        with col2:
            date_to = st.date_input("To Date", value=datetime.now().date())
        
        # Get attendance data
        attendance = db.get_attendance_records(
            date_from=date_from.strftime("%Y-%m-%d"),
            date_to=date_to.strftime("%Y-%m-%d")
        )
        
        if attendance:
            df = pd.DataFrame(attendance)
            
            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                present = len([a for a in attendance if a['status'] == 'present'])
                st.metric("Days Present", present)
            with col2:
                absent = len([a for a in attendance if a['status'] == 'absent'])
                st.metric("Days Absent", absent)
            with col3:
                rate = present / len(attendance) * 100 if attendance else 0
                st.metric("Attendance Rate", f"{rate:.1f}%")
            
            # Display table
            workers_dict = {w['id']: w['name'] for w in db.get_all_workers()}
            df['worker_name'] = df['worker_id'].map(workers_dict)
            
            display_df = df[['worker_name', 'date', 'check_in', 'check_out', 'status', 'notes']]
            display_df.columns = ['Worker', 'Date', 'Check In', 'Check Out', 'Status', 'Notes']
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No attendance records found for the selected period")
    
    # Tab 4: Clock In/Out
    with tabs[3]:
        st.markdown("### Clock In/Out")
        st.markdown("Record worker attendance for today")
        
        workers = db.get_all_workers(active_only=True)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get today's attendance
        today_attendance = db.get_attendance_records(date_from=today, date_to=today)
        clocked_in = {a['worker_id']: a for a in today_attendance}
        
        for worker in workers:
            attendance = clocked_in.get(worker['id'])
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                status = "🟢 Clocked In" if attendance and attendance.get('check_in') else "⚪ Not Clocked In"
                st.markdown(f"**{worker['name']}** - {worker['role']}")
                st.caption(status)
            
            with col2:
                if attendance:
                    if attendance.get('check_in'):
                        st.markdown(f"Check In: {attendance['check_in'][:10]} {attendance['check_in'][11:16]}")
                    if attendance.get('check_out'):
                        st.markdown(f"Check Out: {attendance['check_out'][:10]} {attendance['check_out'][11:16]}")
            
            with col3:
                if not attendance or not attendance.get('check_in'):
                    if st.button("▶️ Clock In", key=f"in_{worker['id']}"):
                        now = datetime.now().isoformat()
                        db.record_attendance(worker['id'], today, check_in=now, status='present')
                        st.rerun()
                elif attendance and attendance.get('check_in') and not attendance.get('check_out'):
                    if st.button("⏹️ Clock Out", key=f"out_{worker['id']}"):
                        now = datetime.now().isoformat()
                        db.record_attendance(worker['id'], today, 
                                           check_in=attendance['check_in'],
                                           check_out=now, status='present')
                        st.rerun()
            
            st.markdown("---")


def render_analytics():
    """Render analytics and AI insights page"""
    st.markdown('<h1 class="main-header">Analytics & AI Insights</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Advanced analytics and predictive insights for your business</p>', unsafe_allow_html=True)
    
    analytics = CarWashAnalytics(db)
    
    tabs = st.tabs(["📊 Business Overview", "👷 Worker Analysis", "⏱️ Time Performance", "⭐ Customer Experience"])
    
    # Tab 1: Business Overview
    with tabs[0]:
        st.markdown("### Business Performance Overview")
        
        # Date range
        date_range = st.selectbox(
            "Select Analysis Period",
            ["Last 7 Days", "Last 30 Days", "This Month", "All Time"],
            key="business_date"
        )
        
        today = datetime.now().date()
        if date_range == "Last 7 Days":
            date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            date_to = today.strftime("%Y-%m-%d")
        elif date_range == "Last 30 Days":
            date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
            date_to = today.strftime("%Y-%m-%d")
        elif date_range == "This Month":
            date_from = today.replace(day=1).strftime("%Y-%m-%d")
            date_to = today.strftime("%Y-%m-%d")
        else:
            date_from = date_to = None
        
        # Generate insights
        insights = analytics.generate_business_insights(date_from, date_to)
        
        # Executive summary
        st.markdown("#### Executive Summary")
        st.info(insights.get('executive_summary', 'No data available'))
        
        # Key metrics
        metrics = insights.get('key_metrics', {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Orders", metrics.get('total_orders', 0))
        with col2:
            st.metric("Total Revenue", f"GHS {metrics.get('total_revenue', 0):,.0f}")
        with col3:
            st.metric("Avg Order Value", f"GHS {metrics.get('avg_order_value', 0):,.0f}")
        with col4:
            completion_rate = (
                metrics.get('by_status', {}).get('completed', {}).get('count', 0) / 
                max(metrics.get('total_orders', 1), 1) * 100
            )
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        st.markdown("---")
        
        # Top performers
        st.markdown("#### Top Performing Workers")
        top_performers = insights.get('top_performers', [])
        
        if top_performers:
            for i, worker in enumerate(top_performers, 1):
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**#{i}**")
                    with col2:
                        st.markdown(f"**{worker['name']}**")
                        st.caption(f"Role: {worker.get('role', 'N/A')}")
                    with col3:
                        st.markdown(f"Orders: {worker.get('orders_completed', 0)}")
                    with col4:
                        rating = worker.get('avg_rating')
                        if rating:
                            st.markdown(f"⭐ {rating}")
        
        st.markdown("---")
        
        # Strategic recommendations
        st.markdown("#### Strategic Recommendations")
        recommendations = insights.get('strategic_recommendations', [])
        
        for rec in recommendations:
            st.markdown(f"- {rec}")
    
    # Tab 2: Worker Analysis
    with tabs[1]:
        st.markdown("### Worker Performance Analysis")
        
        # Worker selection
        workers = db.get_all_workers()
        worker_options = ["All Workers"] + [f"{w['name']} ({w['role']})" for w in workers]
        selected_worker = st.selectbox("Select Worker", worker_options)
        
        worker_id = None
        if selected_worker != "All Workers":
            worker_id = next((w['id'] for w in workers if f"{w['name']} ({w['role']})" == selected_worker), None)
        
        # Run analysis
        analysis = analytics.analyze_worker_attendance(worker_id)
        
        # Display metrics
        metrics = analysis.get('metrics', {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Days Analyzed", metrics.get('total_days_analyzed', 0))
        with col2:
            st.metric("Days Present", metrics.get('days_present', 0))
        with col3:
            st.metric("Attendance Rate", f"{metrics.get('attendance_rate', 0):.1f}%")
        with col4:
            st.metric("Avg Hours/Day", f"{metrics.get('avg_work_hours', 0):.1f}")
        
        st.markdown("---")
        
        # Patterns
        st.markdown("#### Attendance Patterns")
        patterns = analysis.get('patterns', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Most Active Days:**")
            if patterns.get('most_active_days'):
                for day, count in list(patterns['most_active_days'].items())[:3]:
                    st.markdown(f"- {day}: {count} days")
            else:
                st.info("No pattern data available")
        
        with col2:
            st.markdown("**Trend:**")
            trend = patterns.get('trend', 'stable')
            if trend == 'improving':
                st.success("📈 Improving")
            elif trend == 'declining':
                st.warning("📉 Declining")
            else:
                st.info("➡️ Stable")
        
        # Predictions
        predictions = analysis.get('predictions', {})
        if predictions:
            st.markdown("---")
            st.markdown("#### Predictions")
            st.info(f"Next week attendance probability: {predictions.get('next_week_probability', 0):.1f}%")
        
        # Recommendations
        st.markdown("---")
        st.markdown("#### Recommendations")
        recommendations = analysis.get('recommendations', [])
        for rec in recommendations:
            st.markdown(f"- {rec}")
    
    # Tab 3: Time Performance
    with tabs[2]:
        st.markdown("### Time & Efficiency Analysis")
        
        # Get time analysis
        time_analysis = analytics.analyze_worker_time_performance()
        
        metrics = time_analysis.get('metrics', {})
        
        # Display metrics
        if 'total_orders' in metrics:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Orders", metrics.get('total_orders', 0))
            with col2:
                st.metric("Avg Completion", f"{metrics.get('avg_completion_time', 0):.0f} min")
            with col3:
                st.metric("Min Time", f"{metrics.get('min_completion_time', 0):.0f} min")
            with col4:
                st.metric("Max Time", f"{metrics.get('max_completion_time', 0):.0f} min")
        
        # Efficiency scores
        st.markdown("---")
        st.markdown("#### Worker Efficiency Scores")
        
        efficiency = time_analysis.get('efficiency_scores', {})
        
        if efficiency:
            # Create bar chart
            worker_names = [e['name'] for e in efficiency.values()]
            efficiency_scores = [e['efficiency_score'] for e in efficiency.values()]
            
            fig = px.bar(
                x=worker_names,
                y=efficiency_scores,
                color=efficiency_scores,
                color_continuous_scale='rdygn'
            )
            fig.update_layout(
                xaxis_title="Worker",
                yaxis_title="Efficiency Score",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Efficiency table
            st.markdown("**Detailed Efficiency Metrics:**")
            
            eff_data = []
            for wid, data in efficiency.items():
                eff_data.append({
                    'Worker': data['name'],
                    'Avg Time (min)': data['avg_completion_time'],
                    'Orders': data['orders_completed'],
                    'Revenue': f"GHS {data['total_revenue']:,.0f}",
                    'Rating': f"⭐ {data['avg_rating']}" if data['avg_rating'] else "N/A",
                    'Efficiency': f"{data['efficiency_score']:.0f}%"
                })
            
            st.dataframe(pd.DataFrame(eff_data), use_container_width=True, hide_index=True)
        else:
            st.info("No efficiency data available. Complete some orders first!")
        
        # Benchmarks
        benchmarks = time_analysis.get('benchmarks', {})
        if benchmarks:
            st.markdown("---")
            st.markdown("#### Service Time Benchmarks")
            
            bench_data = []
            for service, times in benchmarks.items():
                bench_data.append({
                    'Service': service,
                    'Avg Time': f"{times['avg_time']} min",
                    'Min': f"{times['min_time']} min",
                    'Max': f"{times['max_time']} min",
                    'Orders': times['order_count']
                })
            
            st.dataframe(pd.DataFrame(bench_data), use_container_width=True, hide_index=True)
        
        # Recommendations
        st.markdown("---")
        st.markdown("#### Recommendations")
        recommendations = time_analysis.get('recommendations', [])
        for rec in recommendations:
            st.markdown(f"- {rec}")
    
    # Tab 4: Customer Experience
    with tabs[3]:
        st.markdown("### Customer Experience Analysis")
        
        # Get customer analysis
        customer_analysis = analytics.analyze_customer_experience()
        
        metrics = customer_analysis.get('metrics', {})
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Orders", metrics.get('total_orders', 0))
        with col2:
            st.metric("Completion Rate", f"{metrics.get('completion_rate', 0):.1f}%")
        with col3:
            st.metric("Feedback Rate", f"{metrics.get('feedback_rate', 0):.1f}%")
        with col4:
            st.metric("Avg Rating", f"{metrics.get('avg_rating', 0):.1f} ⭐")
        
        st.markdown("---")
        
        # Patterns
        st.markdown("#### Customer Patterns")
        patterns = customer_analysis.get('patterns', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Repeat Customer Rate:** {patterns.get('repeat_customer_rate', 0):.1f}%")
            st.markdown(f"**Avg Order Value:** GHS {patterns.get('avg_order_value', 0):,.2f}")
        
        with col2:
            st.markdown("**Most Popular Services:**")
            popular = patterns.get('most_popular_services', {})
            for service, count in list(popular.items())[:3]:
                st.markdown(f"- {service}: {count} orders")
        
        # Sentiment analysis
        st.markdown("---")
        st.markdown("#### Feedback Sentiment Analysis")
        
        sentiment = customer_analysis.get('sentiment_analysis', {})
        
        if sentiment.get('summary') != 'No text feedback available for analysis':
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Positive", sentiment.get('positive_reviews', 0))
            with col2:
                st.metric("Neutral", sentiment.get('neutral_reviews', 0))
            with col3:
                st.metric("Negative", sentiment.get('negative_reviews', 0))
            
            sentiment_score = sentiment.get('sentiment_score', 0)
            
            if sentiment_score > 10:
                st.success(f"Overall Sentiment: Positive ({sentiment_score:+.1f}%)")
            elif sentiment_score < -10:
                st.error(f"Overall Sentiment: Negative ({sentiment_score:+.1f}%)")
            else:
                st.info(f"Overall Sentiment: Neutral ({sentiment_score:+.1f}%)")
        else:
            st.info("No customer feedback data available for sentiment analysis")
        
        # Recommendations
        st.markdown("---")
        st.markdown("#### Recommendations")
        recommendations = customer_analysis.get('recommendations', [])
        for rec in recommendations:
            st.markdown(f"- {rec}")


def render_reports():
    """Render reports and export page"""
    st.markdown('<h1 class="main-header">Reports</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate and export detailed reports</p>', unsafe_allow_html=True)
    
    report_gen = ReportGenerator(db)
    
    tabs = st.tabs(["📋 Work Orders", "👷 Workers", "💰 Financial", "📅 Attendance", "📆 Daily Summary"])
    
    # Work Orders Report
    with tabs[0]:
        st.markdown("### Work Orders Report")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            date_from = st.date_input("From Date", value=datetime.now().date() - timedelta(days=30), key="wo_from")
        with col2:
            date_to = st.date_input("To Date", value=datetime.now().date(), key="wo_to")
        with col3:
            status = st.selectbox("Status Filter", ["All", "pending", "in_progress", "completed", "cancelled"])
        
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox("Export Format", ["csv", "pdf"])
        with col2:
            generate_btn = st.button("Generate Report", type="primary", use_container_width=True)
        
        if generate_btn:
            with st.spinner("Generating report..."):
                report = report_gen.generate_work_orders_report(
                    date_from=date_from.strftime("%Y-%m-%d"),
                    date_to=date_to.strftime("%Y-%m-%d"),
                    status=None if status == "All" else status,
                    format=export_format
                )
            
            if report.get('success'):
                if export_format == 'csv':
                    st.download_button(
                        label="Download CSV",
                        data=report['data'],
                        file_name=f"{report['filename']}.csv",
                        mime="text/csv"
                    )
                else:
                    b64 = base64.b64decode(report['data'])
                    st.download_button(
                        label="Download PDF",
                        data=b64,
                        file_name=report['filename'],
                        mime="application/pdf"
                    )
            else:
                st.error(report.get('message', 'Error generating report'))
    
    # Worker Performance Report
    with tabs[1]:
        st.markdown("### Worker Performance Report")
        
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input("From Date", value=datetime.now().date() - timedelta(days=30), key="wp_from")
        with col2:
            date_to = st.date_input("To Date", value=datetime.now().date(), key="wp_to")
        
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox("Export Format", ["csv", "pdf"], key="wp_format")
        with col2:
            generate_btn = st.button("Generate Report", type="primary", use_container_width=True, key="wp_gen")
        
        if generate_btn:
            with st.spinner("Generating report..."):
                report = report_gen.generate_worker_performance_report(
                    date_from=date_from.strftime("%Y-%m-%d"),
                    date_to=date_to.strftime("%Y-%m-%d"),
                    format=export_format
                )
            
            if report.get('success'):
                if export_format == 'csv':
                    st.download_button(
                        label="Download CSV",
                        data=report['data'],
                        file_name=f"{report['filename']}.csv",
                        mime="text/csv"
                    )
                else:
                    b64 = base64.b64decode(report['data'])
                    st.download_button(
                        label="Download PDF",
                        data=b64,
                        file_name=report['filename'],
                        mime="application/pdf"
                    )
            else:
                st.error(report.get('message', 'Error generating report'))
    
    # Financial Report
    with tabs[2]:
        st.markdown("### Financial Report")
        
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input("From Date", value=datetime.now().date() - timedelta(days=30), key="fin_from")
        with col2:
            date_to = st.date_input("To Date", value=datetime.now().date(), key="fin_to")
        
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox("Export Format", ["csv", "pdf"], key="fin_format")
        with col2:
            generate_btn = st.button("Generate Report", type="primary", use_container_width=True, key="fin_gen")
        
        if generate_btn:
            with st.spinner("Generating report..."):
                report = report_gen.generate_financial_report(
                    date_from=date_from.strftime("%Y-%m-%d"),
                    date_to=date_to.strftime("%Y-%m-%d"),
                    format=export_format
                )
            
            if report.get('success'):
                if export_format == 'csv':
                    st.download_button(
                        label="Download CSV",
                        data=report['main_report'],
                        file_name=f"{report['filename']}.csv",
                        mime="text/csv"
                    )
                else:
                    b64 = base64.b64decode(report['data'])
                    st.download_button(
                        label="Download PDF",
                        data=b64,
                        file_name=report['filename'],
                        mime="application/pdf"
                    )
            else:
                st.error(report.get('message', 'Error generating report'))
    
    # Attendance Report
    with tabs[3]:
        st.markdown("### Attendance Report")
        
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input("From Date", value=datetime.now().date() - timedelta(days=30), key="att_from")
        with col2:
            date_to = st.date_input("To Date", value=datetime.now().date(), key="att_to")
        
        workers = db.get_all_workers()
        worker_options = ["All Workers"] + [w['name'] for w in workers]
        selected_worker = st.selectbox("Worker", worker_options, key="att_worker")
        
        worker_id = None
        if selected_worker != "All Workers":
            worker_id = next((w['id'] for w in workers if w['name'] == selected_worker), None)
        
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox("Export Format", ["csv", "pdf"], key="att_format")
        with col2:
            generate_btn = st.button("Generate Report", type="primary", use_container_width=True, key="att_gen")
        
        if generate_btn:
            with st.spinner("Generating report..."):
                report = report_gen.generate_attendance_report(
                    worker_id=worker_id,
                    date_from=date_from.strftime("%Y-%m-%d"),
                    date_to=date_to.strftime("%Y-%m-%d"),
                    format=export_format
                )
            
            if report.get('success'):
                if export_format == 'csv':
                    st.download_button(
                        label="Download CSV",
                        data=report['data'],
                        file_name=f"{report['filename']}.csv",
                        mime="text/csv"
                    )
                else:
                    b64 = base64.b64decode(report['data'])
                    st.download_button(
                        label="Download PDF",
                        data=b64,
                        file_name=report['filename'],
                        mime="application/pdf"
                    )
            else:
                st.error(report.get('message', 'Error generating report'))
    
    # Daily Summary
    with tabs[4]:
        st.markdown("### Daily Operations Summary")
        
        col1, col2 = st.columns(2)
        with col1:
            summary_date = st.date_input("Select Date", value=datetime.now().date(), key="daily_date")
        with col2:
            export_format = st.selectbox("Export Format", ["csv", "pdf"], key="daily_format")
        
        generate_btn = st.button("Generate Summary", type="primary", use_container_width=True)
        
        if generate_btn:
            with st.spinner("Generating summary..."):
                report = report_gen.generate_daily_summary_report(
                    date=summary_date.strftime("%Y-%m-%d"),
                    format=export_format
                )
            
            if report.get('success'):
                if export_format == 'csv':
                    st.download_button(
                        label="Download CSV",
                        data=report['data'],
                        file_name=f"{report['filename']}.csv",
                        mime="text/csv"
                    )
                else:
                    b64 = base64.b64decode(report['data'])
                    st.download_button(
                        label="Download PDF",
                        data=b64,
                        file_name=report['filename'],
                        mime="application/pdf"
                    )
            else:
                st.error(report.get('message', 'No data available for this date'))


def main():
    """Main application entry point"""
    initialize_session_state()
    page = sidebar_navigation()
    
    # Route to appropriate page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Work Orders":
        render_work_orders()
    elif page == "Services":
        render_services()
    elif page == "Workers":
        render_workers()
    elif page == "Analytics":
        render_analytics()
    elif page == "Reports":
        render_reports()


if __name__ == "__main__":
    main()
