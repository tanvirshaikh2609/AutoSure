"""
AutoSure - Auto Service Management System
Main Application Entry Point
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="AutoSure",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "AutoSure - Auto Service Management System v1.0",
        'Get Help': None,
        'Report a Bug': None
    }
)

def load_css():
    """Load custom CSS styling"""
    css_path = Path(__file__).parent / "static" / "styles.css"
    if css_path.exists():
        with open(css_path, 'r') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        :root {
            --primary-accent: #d97757;
            --background-color: #fbfaf8;
            --text-color: #3d3a2a;
        }
        .stButton button[kind="primary"] {
            background-color: #d97757 !important;
            color: #fbfaf8 !important;
        }
        h1, h2, h3 {
            font-family: 'Space Grotesk', sans-serif !important;
            color: #3d3a2a !important;
        }
        </style>
        """, unsafe_allow_html=True)

load_css()

from database.connection import SessionLocal
from services.auth_service import AuthService
import config


def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None


def login_page():
    """Render the login page"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background-color: #fbfaf8;">
        <h1 style="color: #3d3a2a; font-family: 'Space Grotesk', sans-serif; border: none;">
            🚗 Welcome to AutoSure
        </h1>
        <p style="color: #6b6757; font-family: 'Space Grotesk', sans-serif;">
            Sign in to access the system
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email Address", placeholder="Enter your email", key="login_email")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                submit = st.form_submit_button("Sign In", width="stretch")
            with col_b:
                clear = st.form_submit_button("Clear", width="stretch")
            
            if clear:
                st.rerun()
            
            if submit:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    db = SessionLocal()
                    try:
                        auth_service = AuthService(db)
                        user, message = auth_service.authenticate_user(email, password)
                        
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user = {
                                'id': user.id,
                                'username': user.username,
                                'email': user.email,
                                'full_name': user.full_name,
                                'role': user.role,
                                'technician_id': user.technician_id
                            }
                            
                            st.success(f"Welcome, {user.full_name}!")
                            st.rerun()
                        else:
                            st.error(f"Login failed: {message}")
                    except Exception as e:
                        st.error(f"Connection error: {str(e)}")
                    finally:
                        db.close()
        
        st.markdown("---")
        st.markdown("""
        <details>
            <summary style="cursor: pointer; color: #3d3a2a; font-weight: 500;">
                📋 Demo Credentials
            </summary>
            <div style="margin-top: 1rem; padding: 1rem; background-color: #f0ede5; border-radius: 8px; color: #3d3a2a;">
                <p style="margin: 0.25rem 0; color: #3d3a2a;"><strong>Admin:</strong> admin@carservice.com / Admin@123</p>
                <p style="margin: 0.25rem 0; color: #3d3a2a;"><strong>Manager:</strong> manager@carservice.com / Manager@123</p>
                <p style="margin: 0.25rem 0; color: #3d3a2a;"><strong>Cashier:</strong> cashier@carservice.com / Cashier@123</p>
                <p style="margin: 0.25rem 0; color: #3d3a2a;"><strong>Technicians:</strong> tech1@carservice.com to tech5@carservice.com / Tech@123</p>
            </div>
        </details>
        """, unsafe_allow_html=True)


def logout():
    """Handle user logout"""
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    st.rerun()


def render_sidebar():
    """Render the sidebar with user info and logout"""
    with st.sidebar:
        user = st.session_state.user
        st.markdown(f"""
        <div style="padding: 1rem; background-color: #f0ede5; border-radius: 8px; margin-bottom: 1rem; border: 1px solid rgba(61, 58, 42, 0.15);">
            <p style="color: #d97757; font-weight: 500; margin: 0;">{user['full_name']}</p>
            <p style="color: #3d3a2a; font-size: 0.85rem; margin: 0;">{user['role'].title()}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("### Quick Actions")
        
        if st.button("🔄 Refresh", width="stretch"):
            st.rerun()
        
        if st.button("🚪 Logout", width="stretch"):
            logout()
        
        st.markdown("---")
        st.markdown(f"""
        <div style="padding: 0.5rem; font-size: 0.75rem; color: #6b6757;">
            <p style="margin: 0.25rem 0;">{config.app_config.COMPANY_NAME}</p>
            <p style="margin: 0.25rem 0;">Version {config.app_config.APP_VERSION}</p>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main application function"""
    init_session_state()
    
    if not st.session_state.authenticated:
        login_page()
        return
    
    render_sidebar()
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background-color: #fbfaf8;">
        <h1 style="color: #3d3a2a;">Welcome to AutoSure</h1>
        <p style="color: #6b6757;">Select an option from the sidebar to get started.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Quick Overview")
    
    db = SessionLocal()
    try:
        from database.models import ServiceOrder, Part, Invoice
        from datetime import date
        
        today_orders = db.query(ServiceOrder).filter(
            ServiceOrder.created_at >= date.today()
        ).count()
        
        pending_orders = db.query(ServiceOrder).filter(
            ServiceOrder.status.in_(['pending', 'in_progress'])
        ).count()
        
        low_stock = db.query(Part).filter(
            Part.stock_quantity <= Part.reorder_level,
            Part.is_active == True
        ).count()
        
        unpaid_invoices = db.query(Invoice).filter(
            Invoice.status.in_(['unpaid', 'partial'])
        ).count()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(label="Today's Orders", value=today_orders)
        
        with col2:
            st.metric(label="Pending Orders", value=pending_orders)
        
        with col3:
            st.metric(label="Low Stock Items", value=low_stock)
        
        with col4:
            st.metric(label="Unpaid Invoices", value=unpaid_invoices)
    
    except Exception as e:
        st.error(f"Error loading stats: {e}")
    finally:
        db.close()
    
    st.info("Navigate to specific pages using the sidebar menu for detailed operations.")


if __name__ == "__main__":
    from database.connection import test_connection
    success, message = test_connection()
    if not success:
        st.error(f"Database connection failed: {message}")
        st.info("Please check your database configuration in the .env file.")
    
    main()
