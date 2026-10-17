"""
Work Orders Page
Work order management interface with service selection
"""

import streamlit as st
from datetime import date
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from services.service_order_service import ServiceOrderService
from services.customer_service import CustomerService
from services.vehicle_service import VehicleService
from services.technician_service import TechnicianService
from database.models import Technician, ServiceType
from utils.access_control import require_permission, check_page_access
from utils.terminology import TerminologyMapper
from utils.search_history import SearchHistory

# Initialize terminology mapper
terminology = TerminologyMapper()

st.set_page_config(
    page_title=f"{terminology.to_display('service_order')}s - AutoSure",
    page_icon="🔧",
    layout="wide"
)

if not st.session_state.get('authenticated', False):
    st.warning("Please log in to access this page.")
    st.stop()

# Check page access
user = st.session_state.get('user')
if not user:
    st.error("🔒 Please log in to access this page")
    st.stop()

if not check_page_access(user, 'service_orders'):
    from utils.access_control import show_permission_error
    show_permission_error('service_orders')
    st.stop()


def get_technicians(db):
    """Get all active technicians"""
    return db.query(Technician).filter(Technician.is_active == True).all()


def get_service_types(db):
    """Get all active service types"""
    return db.query(ServiceType).filter(ServiceType.is_active == True).order_by(ServiceType.category, ServiceType.name).all()


def render_service_orders_page():
    st.title(f"🔧 {terminology.to_display('service_order')}s")
    
    db = SessionLocal()
    user = st.session_state.get('user')
    user_role = user.get('role', '') if user else ''
    
    # Check permissions
    has_full_access = user_role in ['admin', 'manager']
    is_technician = user_role == 'technician'
    
    try:
        order_svc = ServiceOrderService(db)
        customer_svc = CustomerService(db)
        vehicle_svc = VehicleService(db)
        
        tab1, tab2, tab3 = st.tabs([f"📋 All {terminology.to_display('service_order')}s", f"➕ New {terminology.to_display('service_order')}", "🔍 Search"])
        
        with tab1:
            st.subheader(f"{terminology.to_display('service_order')}s")
            
            # Filter
            col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
            with col_f1:
                status_filter = st.selectbox(
                    "Filter by Status",
                    ['All', 'pending', 'in_progress', 'waiting_parts', 'completed', 'invoiced', 'cancelled']
                )
            
            # Add "My Orders" filter for technicians
            with col_f2:
                if is_technician:
                    my_orders_only = st.checkbox(f"My {terminology.to_display('service_order')}s Only", value=False)
                else:
                    my_orders_only = False
            
            # Get orders
            orders = order_svc.get_all(
                limit=100,
                status=None if status_filter == 'All' else status_filter
            )
            
            # Filter for technician's orders if "My Orders" is checked
            if is_technician and my_orders_only and user:
                from database.models import User as UserModel
                db_user = db.query(UserModel).filter(UserModel.username == user.get('username')).first()
                if db_user and db_user.technician_id:
                    orders = [o for o in orders if o.technician_id == db_user.technician_id]
            
            if orders:
                import pandas as pd
                
                status_colors = {
                    'pending': '⏳',
                    'in_progress': '🔧',
                    'waiting_parts': '📦',
                    'completed': '✅',
                    'invoiced': '📄',
                    'cancelled': '❌'
                }
                
                df_data = [{
                    'ID': o.id,
                    f'{terminology.to_display("service_order")} #': o.order_number,
                    'Status': f"{status_colors.get(o.status, '○')} {o.status}",
                    'Customer': o.customer.name if o.customer else '-',
                    'Vehicle': o.vehicle.display_name if o.vehicle else '-',
                    'Technician': o.technician.name if o.technician else 'Unassigned',
                    'Total': f"₹{o.total_amount:,.2f}",
                    'Created': o.created_at.strftime('%Y-%m-%d')
                } for o in orders]
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Order details
                st.markdown(f"#### {terminology.to_display('service_order')} Actions")
                col_a1, col_a2, col_a3 = st.columns([1, 1, 2])
                
                with col_a1:
                    selected_id = st.number_input(f"{terminology.to_display('service_order')} ID", min_value=1, step=1)
                
                with col_a2:
                    if is_technician:
                        action = st.selectbox("Action", ["View Details", "Update Status", "Add Parts"])
                    else:
                        action = st.selectbox("Action", ["View Details", "Update Status", "Add Parts", "Create Invoice"])
                
                with col_a3:
                    if st.button("Execute"):
                        order = order_svc.get_by_id(selected_id)
                        if order:
                            st.session_state['selected_order_id'] = selected_id
                            st.session_state['order_action'] = action
                        else:
                            st.error(f"{terminology.to_display('service_order')} not found")
                
                # Display selected order details
                if 'selected_order_id' in st.session_state:
                    order = order_svc.get_by_id(st.session_state['selected_order_id'])
                    action = st.session_state.get('order_action', 'View Details')
                    
                    if order:
                        st.markdown("---")
                        st.subheader(f"{terminology.to_display('service_order')}: {order.order_number}")
                        
                        if action == "View Details":
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**Customer:** {order.customer.name if order.customer else 'N/A'}")
                                st.markdown(f"**Vehicle:** {order.vehicle.display_name if order.vehicle else 'N/A'}")
                                st.markdown(f"**Technician:** {order.technician.name if order.technician else 'Unassigned'}")
                                st.markdown(f"**Status:** {order.status}")
                            
                            with col2:
                                st.markdown(f"**Complaint:** {order.complaint or 'N/A'}")
                                st.markdown(f"**Diagnosis:** {order.diagnosis or 'N/A'}")
                                st.markdown(f"**Notes:** {order.notes or 'N/A'}")
                            
                            st.markdown("#### Financial Summary")
                            st.markdown(f"**Labor Total:** ₹{order.labor_total:,.2f}")
                            st.markdown(f"**Parts Total:** ₹{order.parts_total:,.2f}")
                            st.markdown(f"**Grand Total:** ₹{order.total_amount:,.2f}")
                            
                            if st.button("Close"):
                                del st.session_state['selected_order_id']
                                del st.session_state['order_action']
                                st.rerun()
                        
                        elif action == "Update Status":
                            new_status = st.selectbox(
                                "New Status",
                                order_svc.STATUS_FLOW,
                                index=order_svc.STATUS_FLOW.index(order.status) if order.status in order_svc.STATUS_FLOW else 0
                            )
                            diagnosis = st.text_area("Diagnosis/Notes", value=order.diagnosis or "")
                            
                            if st.button("Update"):
                                updated, msg = order_svc.update_status(selected_id, new_status, diagnosis)
                                if updated:
                                    st.success(msg)
                                    del st.session_state['selected_order_id']
                                    del st.session_state['order_action']
                                    st.rerun()
                                else:
                                    st.error(msg)
                        
                        elif action == "Add Parts":
                            from services.inventory_service import InventoryService
                            inventory_svc = InventoryService(db)
                            
                            parts = inventory_svc.get_all(active_only=True)
                            
                            if parts:
                                part_options = {f"{p.sku} - {p.name} (₹{p.selling_price})": p for p in parts}
                                selected_part = st.selectbox("Select Part", list(part_options.keys()))
                                quantity = st.number_input("Quantity", min_value=1, value=1)
                                
                                if st.button("Add Part"):
                                    part = part_options[selected_part]
                                    order_part, msg = order_svc.add_part(selected_id, part.id, quantity)
                                    if order_part:
                                        st.success(msg)
                                    else:
                                        st.error(msg)
                            else:
                                st.warning("No parts in inventory")
                        
                        elif action == "Create Invoice":
                            from services.invoice_service import InvoiceService
                            import config
                            invoice_svc = InvoiceService(db)
                            
                            if order.status != 'completed':
                                st.warning(f"{terminology.to_display('service_order')} must be completed before creating an invoice")
                            else:
                                st.markdown(f"**{terminology.to_display('service_order')} Total:** ₹{order.total_amount:,.2f}")
                                
                                default_tax_rate = float(config.app_config.TAX_RATE)
                                tax_rate = st.number_input("Tax Rate (%)", min_value=0.0, max_value=30.0, value=default_tax_rate * 100) / 100
                                discount = st.number_input("Discount (₹)", min_value=0.0, value=0.0)
                                
                                if st.button("Create Invoice"):
                                    invoice, msg = invoice_svc.create_from_order(selected_id, tax_rate, discount)
                                    if invoice:
                                        st.success(f"Invoice created: {invoice.invoice_number}")
                                        del st.session_state['selected_order_id']
                                        del st.session_state['order_action']
                                        st.rerun()
                                    else:
                                        st.error(msg)
            else:
                st.info(f"No {terminology.to_display('service_order').lower()}s found. Create a new {terminology.to_display('service_order').lower()} to get started.")
        
        with tab2:
            st.subheader(f"Create New {terminology.to_display('service_order')}")
            
            if not has_full_access:
                st.warning(f"⚠️ You don't have permission to create new {terminology.to_display('service_order').lower()}s.")
                st.info(f"Contact your manager or administrator if you need to create a new {terminology.to_display('service_order').lower()}.")
            else:
                customers = customer_svc.get_all(limit=1000)
                
                if not customers:
                    st.warning("No customers found. Please add a customer first.")
                else:
                    # Customer selection OUTSIDE form for dynamic vehicle updates
                    st.markdown("#### Select Customer & Vehicle")
                    col_pre1, col_pre2 = st.columns(2)
                    
                    with col_pre1:
                        customer_options = {f"{c.name} (ID: {c.id})": c for c in customers}
                        customer_select = st.selectbox("Select Customer *", list(customer_options.keys()), key="customer_selector")
                        selected_customer = customer_options[customer_select]
                    
                    with col_pre2:
                        # Get vehicles for selected customer - updates dynamically
                        vehicles = vehicle_svc.get_by_customer(selected_customer.id)
                        if vehicles:
                            vehicle_options = {f"{v.display_name} ({v.license_plate or 'No Plate'})": v for v in vehicles}
                            vehicle_select = st.selectbox("Select Vehicle *", list(vehicle_options.keys()), key="vehicle_selector")
                            selected_vehicle = vehicle_options[vehicle_select]
                        else:
                            st.warning("This customer has no vehicles. Add a vehicle first.")
                            st.stop()
                    
                    st.markdown("---")
                    st.markdown("#### Work Order Details")
                    
                    with st.form("new_order_form", clear_on_submit=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Display selected customer and vehicle (read-only in form)
                            st.info(f"👤 Customer: {selected_customer.name}")
                            st.info(f"🚗 Vehicle: {selected_vehicle.display_name} ({selected_vehicle.license_plate or 'No Plate'})")
                            
                            technicians = get_technicians(db)
                            if technicians:
                                tech_options = {"Unassigned": None} | {t.name: t for t in technicians}
                                tech_select = st.selectbox("Assign Technician", list(tech_options.keys()))
                            else:
                                tech_select = "Unassigned"
                        
                        with col2:
                            # Service selection with searchable dropdown
                            service_types = get_service_types(db)
                            if service_types:
                                service_options = {f"{s.name} - ₹{s.base_price:.2f} ({s.category})": s for s in service_types}
                                selected_services = st.multiselect(
                                    "Select Services *",
                                    options=list(service_options.keys()),
                                    help="Select one or more services for this work order"
                                )
                                
                                if selected_services:
                                    total_labor = sum(service_options[s].base_price for s in selected_services)
                                    st.info(f"💰 Estimated Labor Total: ₹{total_labor:.2f}")
                            else:
                                st.error("No service types available. Contact administrator.")
                                st.stop()
                            
                            estimated_date = st.date_input(
                                "Estimated Completion", 
                                value=date.today(),
                                help="Expected completion date"
                            )
                            
                            notes = st.text_area("Additional Notes", placeholder="Any special instructions or observations")
                        
                        submitted = st.form_submit_button("Create Work Order", use_container_width=True)
                        
                        if submitted:
                            if not selected_services:
                                st.error("Please select at least one service")
                            else:
                                technician_id = None
                                if technicians and tech_select != "Unassigned":
                                    technician_id = tech_options[tech_select].id if tech_options[tech_select] else None
                                
                                # Create complaint text from selected services
                                complaint = "Services requested: " + ", ".join([s.split(" - ")[0] for s in selected_services])
                                
                                order, message = order_svc.create(
                                    customer_id=selected_customer.id,
                                    vehicle_id=selected_vehicle.id,
                                    complaint=complaint,
                                    technician_id=technician_id,
                                    estimated_completion=estimated_date,
                                    notes=notes if notes else None
                                )
                                
                                if order:
                                    # Add service items to the order
                                    from database.models import ServiceItem
                                    for service_key in selected_services:
                                        service = service_options[service_key]
                                        service_item = ServiceItem(
                                            service_order_id=order.id,
                                            service_type_id=service.id,
                                            description=service.name,
                                            labor_hours=service.standard_hours,
                                            labor_rate=Decimal(str(service.base_price)) / Decimal(str(service.standard_hours)) if service.standard_hours > 0 else Decimal('0'),
                                            labor_cost=Decimal(str(service.base_price)),
                                            status='pending'
                                        )
                                        db.add(service_item)
                                    
                                    db.flush()
                                    
                                    # Recalculate order totals
                                    order.calculate_totals()
                                    db.commit()
                                    db.refresh(order)
                                    
                                    st.success(f"✅ {terminology.to_display('service_order')} created: {order.order_number} - Total: ₹{order.total_amount:,.2f}")
                                    st.session_state['selected_customer_id'] = selected_customer.id
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
        
        with tab3:
            st.subheader(f"Search {terminology.to_display('service_order')}s")
            
            search_type = st.radio("Search By", [f"{terminology.to_display('service_order')} Number", "Customer"])
            
            search_context = 'service_orders_number' if search_type == f"{terminology.to_display('service_order')} Number" else 'service_orders_customer'
            search_history = SearchHistory(search_context, max_history=10)
            
            recent_search = search_history.render_history_dropdown(
                label="Recent Searches",
                placeholder="Select a recent search..."
            )
            
            if search_type == f"{terminology.to_display('service_order')} Number":
                search_query = st.text_input(
                    f"Enter {terminology.to_display('service_order')} Number", 
                    placeholder="e.g., WO-2024...",
                    value=recent_search if recent_search else ""
                )
            else:
                search_query = st.text_input(
                    "Enter Customer Name", 
                    placeholder="Customer name...",
                    value=recent_search if recent_search else ""
                )
            
            if search_query:
                search_history.add_search(search_query)
                
                if search_type == f"{terminology.to_display('service_order')} Number":
                    order = order_svc.get_by_number(search_query)
                    results = [order] if order else []
                else:
                    customers = customer_svc.search(search_query)
                    results = []
                    for c in customers:
                        results.extend(order_svc.get_by_customer(c.id))
                
                if results:
                    st.markdown(f"**Found {len(results)} result(s):**")
                    
                    for order in results:
                        if not order:
                            continue
                        with st.expander(f"**{order.order_number}** - {order.status}"):
                            st.markdown(f"**Customer:** {order.customer.name if order.customer else 'N/A'}")
                            st.markdown(f"**Vehicle:** {order.vehicle.display_name if order.vehicle else 'N/A'}")
                            st.markdown(f"**Complaint:** {order.complaint or 'N/A'}")
                            st.markdown(f"**Total:** ₹{order.total_amount:,.2f}")
                            st.markdown(f"**Created:** {order.created_at.strftime('%Y-%m-%d %H:%M')}")
                else:
                    st.info(f"No {terminology.to_display('service_order').lower()}s found matching your search.")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    finally:
        db.close()


render_service_orders_page()
