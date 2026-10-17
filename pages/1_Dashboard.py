"""
Dashboard Page
Main dashboard with overview statistics and quick actions
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from services.customer_service import CustomerService
from services.vehicle_service import VehicleService
from services.service_order_service import ServiceOrderService
from services.inventory_service import InventoryService
from services.invoice_service import InvoiceService
from utils.access_control import require_permission
from utils.ui_components import show_quick_actions
import config

# Page configuration
st.set_page_config(
    page_title="Dashboard - AutoSure",
    page_icon="📊",
    layout="wide"
)

# Check authentication
if not st.session_state.get('authenticated', False):
    st.warning("Please log in to access this page.")
    st.stop()


@require_permission('reports')
def render_dashboard():
    """Render the main dashboard"""
    st.title("📊 Dashboard")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Initialize services
        customer_svc = CustomerService(db)
        vehicle_svc = VehicleService(db)
        order_svc = ServiceOrderService(db)
        inventory_svc = InventoryService(db)
        invoice_svc = InvoiceService(db)
        
        # Key Metrics Row
        st.markdown("### Overview")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_customers = customer_svc.get_count()
            st.metric(label="👥 Total Customers", value=total_customers)
        
        with col2:
            total_vehicles = vehicle_svc.get_count()
            st.metric(label="🚗 Total Vehicles", value=total_vehicles)
        
        with col3:
            active_orders = order_svc.get_active_count()
            st.metric(label="🔧 Active Orders", value=active_orders)
        
        with col4:
            low_stock = len(inventory_svc.get_low_stock())
            st.metric(label="📦 Low Stock Items", value=low_stock, 
                     delta="Attention needed" if low_stock > 0 else None,
                     delta_color="inverse")
        
        with col5:
            unpaid_invoices = invoice_svc.get_count('unpaid') + invoice_svc.get_count('partial')
            st.metric(label="💰 Outstanding Invoices", value=unpaid_invoices)
        
        st.markdown("---")
        
        # Two-column layout for charts
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Service Orders by Status
            st.markdown("#### Service Orders by Status")
            order_stats = order_svc.get_statistics(days=30)
            
            if order_stats['status_breakdown']:
                status_data = order_stats['status_breakdown']
                
                # Filter out zero counts for cleaner chart
                status_data = {k: v for k, v in status_data.items() if v > 0}
                
                if status_data:
                    fig = px.pie(
                        values=list(status_data.values()),
                        names=list(status_data.keys()),
                        title="Order Status Distribution",
                        color_discrete_sequence=['#d97757', '#7c9a6d', '#7a8fa3', '#c85a54', '#6b6757', '#f0ede5']
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Space Grotesk', color='#3d3a2a'),
                        title_font=dict(size=16, color='#3d3a2a')
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No order data available")
            else:
                st.info("No orders in the last 30 days")
        
        with col_right:
            # Revenue Overview
            st.markdown("#### Revenue Overview (30 Days)")
            invoice_stats = invoice_svc.get_statistics(days=30)
            
            revenue_data = {
                'Category': ['Invoiced', 'Collected', 'Outstanding'],
                'Amount': [
                    invoice_stats['total_invoiced'],
                    invoice_stats['total_paid'],
                    invoice_stats['total_outstanding']
                ]
            }
            
            fig = go.Figure(data=[
                go.Bar(
                    x=revenue_data['Category'],
                    y=revenue_data['Amount'],
                    marker_color=['#d97757', '#7c9a6d', '#c85a54'],
                    text=[f"₹{v:,.0f}" for v in revenue_data['Amount']],
                    textposition='auto',
                    textfont=dict(color='#3d3a2a')
                )
            ])
            
            fig.update_layout(
                title="Financial Summary",
                xaxis_title="",
                yaxis_title="Amount (₹)",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Space Grotesk', color='#3d3a2a'),
                title_font=dict(size=16, color='#3d3a2a'),
                xaxis=dict(gridcolor='#f0ede5'),
                yaxis=dict(gridcolor='#f0ede5')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Alerts Section
        st.markdown("#### Alerts & Notifications")
            
        # Low stock alerts
        # Low stock alerts
        low_stock_items = inventory_svc.get_low_stock()[:5]
        if low_stock_items:
            st.warning(f"📦 **{len(inventory_svc.get_low_stock())} items** are below reorder level")
            for item in low_stock_items:
                st.markdown(f"- **{item.name}** (Stock: {item.stock_quantity}, Reorder: {item.reorder_level})")
        else:
            st.success("✅ All inventory levels are healthy")
        
        st.markdown("")
        
        # Overdue invoices
        overdue = invoice_svc.get_overdue()[:5]
        if overdue:
            st.error(f"💰 **{len(invoice_svc.get_overdue())} invoices** are overdue")
            for inv in overdue:
                st.markdown(f"- **{inv.invoice_number}** - ₹{inv.balance_due:.2f}")
        
        st.markdown("---")
        
        # Recent Activity
        col_recent1, col_recent2 = st.columns(2)
        
        with col_recent1:
            st.markdown("#### Recent Customers")
            recent_customers = customer_svc.get_recent(5)
            if recent_customers:
                for customer in recent_customers:
                    st.markdown(f"- **{customer.name}** - {customer.phone or 'No phone'}")
            else:
                st.info("No recent customers")
        
        with col_recent2:
            st.markdown("#### Recent Orders")
            recent_orders = order_svc.get_all(limit=5)
            if recent_orders:
                for order in recent_orders:
                    status_emoji = {
                        'pending': '⏳',
                        'in_progress': '🔧',
                        'waiting_parts': '📦',
                        'completed': '✅',
                        'invoiced': '📄',
                        'cancelled': '❌'
                    }.get(order.status, '○')
                    st.markdown(f"- {status_emoji} **{order.order_number}** - {order.status.replace('_', ' ').title()}")
            else:
                st.info("No recent orders")
        
        # Inventory Value Summary
        st.markdown("---")
        st.markdown("#### Inventory Summary")
        
        inv_value = inventory_svc.get_inventory_value()
        
        col_inv1, col_inv2, col_inv3, col_inv4 = st.columns(4)
        
        with col_inv1:
            st.metric("Total Parts", inv_value['total_parts'])
        
        with col_inv2:
            st.metric("Total Units", inv_value['total_units'])
        
        with col_inv3:
            st.metric("Cost Value", f"₹{inv_value['cost_value']:,.2f}")
        
        with col_inv4:
            st.metric("Retail Value", f"₹{inv_value['retail_value']:,.2f}")
    
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
    
    finally:
        db.close()


# Run the dashboard
render_dashboard()
