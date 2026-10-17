"""
Customers Page
Customer management interface
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from services.customer_service import CustomerService
from utils.validators import validate_email, validate_phone
from utils.access_control import require_permission, _get_user_permissions
from utils.terminology import TerminologyMapper
from utils.search_history import SearchHistory
import config

# Page configuration
st.set_page_config(
    page_title="Customers - AutoSure",
    page_icon="👥",
    layout="wide"
)

# Check authentication
if not st.session_state.get('authenticated', False):
    st.warning("Please log in to access this page.")
    st.stop()


@require_permission('customers')
def render_customers_page():
    """Render the customers management page"""
    st.title("👥 Customer Management")
    
    # Create database session
    db = SessionLocal()
    
    # Initialize terminology mapper
    terminology = TerminologyMapper()
    
    try:
        customer_svc = CustomerService(db)
        
        # Action tabs
        tab1, tab2, tab3 = st.tabs(["📋 All Customers", "➕ Add Customer", "🔍 Search"])
        
        with tab1:
            st.subheader("Customer List")
            
            # Quick Add Customer button for admin/manager
            user = st.session_state.get('user', {})
            user_permissions = _get_user_permissions(user.get('role', ''))
            can_add = 'customers' in user_permissions or 'all' in user_permissions
            
            if can_add:
                if st.button("⚡ Quick Add Customer", type="primary", help="Add a customer with minimal required information"):
                    st.session_state['show_quick_add'] = True
            
            # Quick Add Customer Modal/Form
            if st.session_state.get('show_quick_add', False):
                with st.container():
                    st.markdown("---")
                    st.markdown("### ⚡ Quick Add Customer")
                    st.markdown("*Add a customer with just the essential information*")
                    
                    with st.form("quick_add_customer_form", clear_on_submit=True):
                        col_qa1, col_qa2 = st.columns(2)
                        
                        with col_qa1:
                            qa_name = st.text_input("Customer Name *", placeholder="Full name")
                            qa_phone = st.text_input("Phone", placeholder="Phone number")
                        
                        with col_qa2:
                            # Customer type dropdown with display names
                            qa_customer_type_display = st.selectbox(
                                "Customer Type",
                                options=['Standard', 'Business', 'Premium'],
                                help=terminology.get_tooltip('customer_type')
                            )
                        
                        col_submit1, col_submit2 = st.columns(2)
                        with col_submit1:
                            qa_submitted = st.form_submit_button("✅ Add Customer", use_container_width=True, type="primary")
                        with col_submit2:
                            qa_cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
                        
                        if qa_cancel:
                            st.session_state['show_quick_add'] = False
                            st.rerun()
                        
                        if qa_submitted:
                            # Validation
                            if not qa_name or not qa_name.strip():
                                st.error("Customer name is required")
                            else:
                                # Convert display type to database type
                                qa_customer_type = terminology.get_customer_type_database(qa_customer_type_display)
                                
                                # Create customer with minimal info
                                customer, message = customer_svc.create(
                                    name=qa_name,
                                    phone=qa_phone if qa_phone and qa_phone.strip() else None,
                                    email=None,
                                    address=None,
                                    customer_type=qa_customer_type,
                                    notes=None
                                )
                                
                                if customer:
                                    st.success(f"✅ {message}")
                                    st.session_state['show_quick_add'] = False
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                    
                    st.markdown("---")
            
            # Filter options
            col_filter1, col_filter2 = st.columns([1, 3])
            with col_filter1:
                # Create display options for customer types
                display_options = ['All', 'Standard', 'Business', 'Premium']
                db_type_map = {
                    'All': 'All',
                    'Standard': 'regular',
                    'Business': 'wholesale',
                    'Premium': 'vip'
                }
                
                filter_type_display = st.selectbox(
                    "Filter by Type",
                    options=display_options,
                    index=0,
                    help=terminology.get_tooltip('customer_type')
                )
                
                # Convert display type to database type
                filter_type = db_type_map[filter_type_display]
            
            # Get customers
            if filter_type == 'All':
                customers = customer_svc.get_all(limit=100)
            else:
                customers = customer_svc.get_by_type(filter_type)
            
            if customers:
                # Display as dataframe
                import pandas as pd
                
                df_data = [{
                    'ID': c.id,
                    'Name': c.name,
                    'Phone': c.phone or '-',
                    'Email': c.email or '-',
                    'Type': terminology.get_customer_type_display(c.customer_type),
                    'Vehicles': len(c.vehicles) if hasattr(c, 'vehicles') else 0,
                    'Created': c.created_at.strftime('%Y-%m-%d') if c.created_at else '-'
                } for c in customers]
                
                df = pd.DataFrame(df_data)
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'ID': st.column_config.NumberColumn('ID', width='small'),
                        'Name': st.column_config.TextColumn('Name', width='medium'),
                        'Type': st.column_config.TextColumn('Type', width='small'),
                    }
                )
                
                # Customer actions
                st.markdown("#### Customer Actions")
                col_action1, col_action2 = st.columns(2)
                
                # Get user permissions
                user = st.session_state.get('user', {})
                user_permissions = _get_user_permissions(user.get('role', ''))
                can_edit = 'customers' in user_permissions or 'all' in user_permissions
                can_delete = 'delete' in user_permissions or 'all' in user_permissions
                
                with col_action1:
                    selected_id = st.number_input("Enter Customer ID", min_value=1, step=1)
                
                with col_action2:
                    # Build action list based on permissions
                    actions = ["View Details"]
                    if can_edit:
                        actions.append("Edit")
                    if can_delete:
                        actions.append("Delete")
                    
                    action = st.selectbox("Action", actions)
                    
                    if st.button("Execute Action"):
                        customer = customer_svc.get_by_id(selected_id)
                        
                        if not customer:
                            st.error("Customer not found")
                        elif action == "View Details":
                            st.session_state['view_customer_id'] = selected_id
                        elif action == "Edit":
                            if can_edit:
                                st.session_state['edit_customer_id'] = selected_id
                            else:
                                st.error("You don't have permission to edit customers")
                        elif action == "Delete":
                            if can_delete:
                                success, msg = customer_svc.delete(selected_id)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                            else:
                                st.error("You don't have permission to delete customers")
                
                # View customer details
                if 'view_customer_id' in st.session_state:
                    customer = customer_svc.get_by_id(st.session_state['view_customer_id'])
                    if customer:
                        st.markdown("---")
                        st.subheader(f"Customer Details: {customer.name}")
                        
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            st.markdown(f"**Phone:** {customer.phone or 'N/A'}")
                            st.markdown(f"**Email:** {customer.email or 'N/A'}")
                            st.markdown(f"**Type:** {terminology.get_customer_type_display(customer.customer_type)}")
                        
                        with col_d2:
                            st.markdown(f"**Address:** {customer.address or 'N/A'}")
                            st.markdown(f"**Notes:** {customer.notes or 'N/A'}")
                            st.markdown(f"**Created:** {customer.created_at.strftime('%Y-%m-%d')}")
                        
                        # Service history summary
                        history = customer_svc.get_service_history(customer.id)
                        st.markdown(f"**Total Orders:** {history.get('total_orders', 0)}")
                        st.markdown(f"**Total Spent:** ₹{history.get('total_spent', 0):,.2f}")
                        
                        if st.button("Close Details"):
                            del st.session_state['view_customer_id']
                            st.rerun()
                
                # Edit customer details
                if 'edit_customer_id' in st.session_state:
                    customer = customer_svc.get_by_id(st.session_state['edit_customer_id'])
                    if customer:
                        st.markdown("---")
                        st.subheader(f"Edit Customer: {customer.name}")
                        
                        with st.form("edit_customer_form"):
                            col_e1, col_e2 = st.columns(2)
                            
                            with col_e1:
                                edit_name = st.text_input("Customer Name *", value=customer.name)
                                edit_phone = st.text_input("Phone", value=customer.phone or "")
                                
                                # Get current type display name
                                current_type_display = terminology.get_customer_type_display(customer.customer_type)
                                type_options = ['Standard', 'Business', 'Premium']
                                current_idx = type_options.index(current_type_display) if current_type_display in type_options else 0
                                
                                edit_type_display = st.selectbox(
                                    "Customer Type",
                                    options=type_options,
                                    index=current_idx,
                                    help=terminology.get_tooltip('customer_type')
                                )
                            
                            with col_e2:
                                edit_email = st.text_input("Email", value=customer.email or "")
                                edit_address = st.text_area("Address", value=customer.address or "", height=100)
                            
                            edit_notes = st.text_area("Notes", value=customer.notes or "")
                            
                            col_submit1, col_submit2 = st.columns(2)
                            with col_submit1:
                                submitted = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
                            with col_submit2:
                                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
                            
                            if cancel:
                                del st.session_state['edit_customer_id']
                                st.rerun()
                            
                            if submitted:
                                if not edit_name or not edit_name.strip():
                                    st.error("Customer name is required")
                                else:
                                    # Validate email if provided
                                    if edit_email and edit_email.strip():
                                        is_valid, msg = validate_email(edit_email)
                                        if not is_valid:
                                            st.error(msg)
                                            st.stop()
                                    
                                    # Convert display type to database type
                                    edit_type = terminology.get_customer_type_database(edit_type_display)
                                    
                                    # Update customer
                                    updated, message = customer_svc.update(
                                        customer.id,
                                        name=edit_name,
                                        phone=edit_phone if edit_phone and edit_phone.strip() else None,
                                        email=edit_email if edit_email and edit_email.strip() else None,
                                        address=edit_address if edit_address and edit_address.strip() else None,
                                        customer_type=edit_type,
                                        notes=edit_notes if edit_notes and edit_notes.strip() else None
                                    )
                                    
                                    if updated:
                                        st.success(f"✅ {message}")
                                        del st.session_state['edit_customer_id']
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
            else:
                st.info("No customers found. Add a new customer to get started.")
        
        with tab2:
            st.subheader("Add New Customer")
            
            # Check if user has permission to add customers
            user = st.session_state.get('user', {})
            user_permissions = _get_user_permissions(user.get('role', ''))
            can_add = 'customers' in user_permissions or 'all' in user_permissions
            
            if not can_add:
                st.warning("You don't have permission to add customers.")
            else:
                with st.form("add_customer_form", clear_on_submit=True):
                    col_form1, col_form2 = st.columns(2)
                    
                    with col_form1:
                        name = st.text_input("Customer Name *", placeholder="Full name")
                        phone = st.text_input("Phone", placeholder="Phone number")
                        
                        # Customer type dropdown with display names
                        customer_type_display = st.selectbox(
                            "Customer Type",
                            options=['Standard', 'Business', 'Premium'],
                            help=terminology.get_tooltip('customer_type')
                        )
                        # Convert display type to database type
                        customer_type = terminology.get_customer_type_database(customer_type_display)
                    
                    with col_form2:
                        email = st.text_input("Email (optional)", placeholder="Email address")
                        address = st.text_area("Address (optional)", placeholder="Full address", height=100)
                    
                    notes = st.text_area("Notes (optional)", placeholder="Additional notes about this customer")
                    
                    submitted = st.form_submit_button("Add Customer", use_container_width=True)
                    
                    if submitted:
                        # Validation
                        if not name or not name.strip():
                            st.error("Customer name is required")
                        else:
                            # Validate email if provided
                            if email and email.strip():
                                is_valid, msg = validate_email(email)
                                if not is_valid:
                                    st.error(msg)
                                    st.stop()
                            
                            # Create customer
                            customer, message = customer_svc.create(
                                name=name,
                                phone=phone if phone and phone.strip() else None,
                                email=email if email and email.strip() else None,
                                address=address if address and address.strip() else None,
                                customer_type=customer_type,
                                notes=notes if notes and notes.strip() else None
                            )
                            
                            if customer:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
        
        with tab3:
            st.subheader("Search Customers")
            
            # Initialize search history
            search_history = SearchHistory('customers', max_history=10)
            
            # Show recent searches dropdown
            recent_search = search_history.render_history_dropdown(
                label="Recent Searches",
                placeholder="Select a recent search..."
            )
            
            # Search input
            search_query = st.text_input(
                "Search by name, phone, or email",
                placeholder="Enter search term...",
                value=recent_search if recent_search else ""
            )
            
            if search_query:
                # Add to search history
                search_history.add_search(search_query)
                
                results = customer_svc.search(search_query)
                
                if results:
                    st.markdown(f"**Found {len(results)} result(s):**")
                    
                    for customer in results:
                        with st.expander(f"**{customer.name}** ({terminology.get_customer_type_display(customer.customer_type)})"):
                            col_s1, col_s2 = st.columns(2)
                            with col_s1:
                                st.markdown(f"**Phone:** {customer.phone or 'N/A'}")
                                st.markdown(f"**Email:** {customer.email or 'N/A'}")
                            with col_s2:
                                st.markdown(f"**Address:** {customer.address or 'N/A'}")
                                st.markdown(f"**ID:** {customer.id}")
                else:
                    st.info("No customers found matching your search.")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    finally:
        db.close()


# Run the page
render_customers_page()
