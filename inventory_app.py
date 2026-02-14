import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Global Inventory Command Center", layout="wide", page_icon="📦")

# --- CUSTOM CSS FOR STYLING ---
# We use !important to force the browser to override Streamlit's default dark text
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    
    /* 1. Sidebar Background Color */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
    }

    /* 2. Target ALL text in the sidebar: Titles, Labels, Markdown, and Spans */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
        font-weight: 600 !important;
    }

    /* 3. Specifically fix the Multiselect labels which are often hard to see */
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: white !important;
        font-size: 1.1rem !important;
    }

    /* 4. Make the progress bar text white */
    [data-testid="stSidebar"] .stProgress > label {
        color: white !important;
    }

    /* 5. Make the progress bar itself a bright cyan so it stands out */
    [data-testid="stSidebar"] div[role="progressbar"] > div {
        background-color: #00f2ff !important;
    }

    h1 { color: #1e293b; font-family: 'Inter', sans-serif; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv('Inventory.csv')
    df['OrderDate'] = pd.to_datetime(df['OrderDate'])
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading Inventory.csv: {e}")
    st.stop()

# --- SIDEBAR NAVIGATION & FILTERS ---
st.sidebar.title("🏢 IMS Enterprise")
st.sidebar.markdown("---")

# Feature 1: Dynamic Multi-Filters
region_filter = st.sidebar.multiselect("Select Regions", options=df['RegionName'].unique(), default=df['RegionName'].unique())
category_filter = st.sidebar.multiselect("Select Categories", options=df['CategoryName'].unique(), default=df['CategoryName'].unique())
status_filter = st.sidebar.multiselect("Order Status", options=df['Status'].unique(), default=df['Status'].unique())

# Apply Filters
filtered_df = df[
    (df['RegionName'].isin(region_filter)) & 
    (df['CategoryName'].isin(category_filter)) &
    (df['Status'].isin(status_filter))
]

# --- MAIN DASHBOARD ---
st.title("📦 Global Inventory & Operations Dashboard")
st.markdown(f"**Target Market:** {', '.join(region_filter)} | **Active Categories:** {len(category_filter)}")

# Feature 2: High-Level KPI Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_stock = filtered_df['TotalItemQuantity'].sum()
    st.metric("Total Warehouse Stock", f"{total_stock:,}")
with col2:
    total_val = (filtered_df['TotalItemQuantity'] * filtered_df['ProductListPrice']).sum()
    st.metric("Inventory Valuation", f"₹{total_val/1e6:.2f}M")
with col3:
    avg_profit = filtered_df['Profit'].mean()
    st.metric("Avg. Profit per Unit", f"₹{avg_profit:,.2f}")
with col4:
    active_warehouses = filtered_df['WarehouseName'].nunique()
    st.metric("Active Warehouses", active_warehouses)

st.markdown("---")

# --- VISUAL ANALYTICS SECTION ---
tab1, tab2, tab3 = st.tabs(["📊 Stock Analytics", "💰 Financial Insights", "👥 Workforce & Customers"])

with tab1:
    c1, c2 = st.columns(2)
    
    # Feature 3: Stock Levels by Category (Plotly)
    with c1:
        st.subheader("Inventory Distribution by Category")
        fig_stock = px.bar(filtered_df.groupby('CategoryName')['TotalItemQuantity'].sum().reset_index(), 
                           x='CategoryName', y='TotalItemQuantity', color='CategoryName',
                           template="plotly_white", text_auto='.2s')
        st.plotly_chart(fig_stock, use_container_width=True)

    # Feature 4: Low Stock Alert Intelligence
    with c2:
        st.subheader("⚠️ Critical Low Stock Alerts")
        low_stock_threshold = 50
        low_stock = filtered_df[filtered_df['TotalItemQuantity'] < low_stock_threshold][['ProductName', 'TotalItemQuantity', 'WarehouseName']]
        if not low_stock.empty:
            # Note: Requires 'matplotlib' to be in requirements.txt
            st.dataframe(low_stock.style.background_gradient(cmap='Reds'), use_container_width=True)
        else:
            st.success("All stock levels are optimal.")

with tab2:
    c3, c4 = st.columns(2)
    
    # Feature 5: Regional Profitability Analysis
    with c3:
        st.subheader("Profitability by Region")
        fig_profit = px.pie(filtered_df, values='Profit', names='RegionName', hole=0.4,
                            color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_profit, use_container_width=True)

    # Feature 6: Sales Trends (Time Series)
    with c4:
        st.subheader("Order Quantity Over Time")
        trend_df = filtered_df.groupby('OrderDate')['OrderItemQuantity'].sum().reset_index()
        fig_trend = px.line(trend_df, x='OrderDate', y='OrderItemQuantity', markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)

with tab3:
    # Feature 7: Employee Order Management Insight
    st.subheader("Employee Performance (Total Orders Handled)")
    emp_df = filtered_df.groupby(['EmployeeName', 'EmployeeJobTitle'])['OrderItemQuantity'].count().reset_index(name='OrdersHandled')
    st.table(emp_df.sort_values(by='OrdersHandled', ascending=False).head(10))

# --- DATA EXPLORER & EXPORT ---
st.markdown("---")
# Feature 8: Advanced Data Explorer
st.subheader("🔍 Deep Dive: Product Master Data")
search_query = st.text_input("Search Products, Warehouses, or Customers...")
if search_query:
    display_df = filtered_df[filtered_df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
else:
    display_df = filtered_df

# Feature 9: Formatted Data Table
st.dataframe(display_df[['ProductName', 'CategoryName', 'WarehouseName', 'TotalItemQuantity', 'ProductListPrice', 'Status', 'CustomerName']], use_container_width=True)

# Feature 10: One-Click Professional Report Export
csv = display_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Filtered Inventory Report",
    data=csv,
    file_name='Enterprise_Inventory_Report.csv',
    mime='text/csv',
)

# --- Feature 11: Status Progress Tracker ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 🚚 Order Pipeline Status")

status_counts = filtered_df['Status'].value_counts()
total_orders = len(filtered_df)

for status, count in status_counts.items():
    percentage = int((count / total_orders) * 100)
    # Using st.sidebar.write ensures it's wrapped in a tag the CSS can find
    st.sidebar.write(f"**{status}: {count}**")
    st.sidebar.progress(percentage)