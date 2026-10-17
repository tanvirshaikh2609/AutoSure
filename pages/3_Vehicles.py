"""
Vehicles Page
Vehicle management interface
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from services.vehicle_service import VehicleService
from services.customer_service import CustomerService
from utils.validators import validate_vin, validate_license_plate, validate_year
from utils.access_control import require_permission, _get_user_permissions
from utils.terminology import TerminologyMapper
from utils.auto_generator import AutoGenerator
from utils.search_history import SearchHistory

st.set_page_config(
    page_title="Vehicles - AutoSure",
    page_icon="🚗",
    layout="wide"
)

if not st.session_state.get('authenticated', False):
    st.warning("Please log in to access this page.")
    st.stop()


@require_permission('vehicles')
def render_vehicles_page():
    st.title("🚗 Vehicle Management")
    
    # Initialize terminology mapper
    term_mapper = TerminologyMapper()
    
    db = SessionLocal()
    
    # Get user permissions
    user = st.session_state.get('user', {})
    user_permissions = _get_user_permissions(user.get('role', ''))
    can_edit = 'vehicles' in user_permissions or 'all' in user_permissions
    
    try:
        vehicle_svc = VehicleService(db)
        customer_svc = CustomerService(db)
        
        # Create tabs based on permissions
        if can_edit:
            tab1, tab2, tab3 = st.tabs(["📋 All Vehicles", "➕ Add Vehicle", "🔍 Search"])
        else:
            tab1, tab3 = st.tabs(["📋 All Vehicles", "🔍 Search"])
            tab2 = None  # No add tab for view-only users
        
        with tab1:
            st.subheader("Vehicle List")
            
            vehicles = vehicle_svc.get_all(limit=100)
            
            if vehicles:
                import pandas as pd
                
                df_data = [{
                    'ID': v.id,
                    'Vehicle': v.display_name,
                    'License Plate': v.license_plate or '-',
                    term_mapper.to_display('vin'): (v.vin[:8] + '...') if v.vin else '-',
                    'Color': v.color or '-',
                    'Mileage': f"{v.current_mileage:,}" if v.current_mileage else '-',
                    'Owner': v.customer.name if v.customer else '-'
                } for v in vehicles]
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Vehicle details
                st.markdown("#### View Vehicle Details")
                selected_id = st.number_input("Enter Vehicle ID", min_value=1, step=1)
                
                if st.button("View Details"):
                    vehicle = vehicle_svc.get_by_id(selected_id)
                    if vehicle:
                        st.session_state['view_vehicle_id'] = selected_id
                    else:
                        st.error("Vehicle not found")
                
                if 'view_vehicle_id' in st.session_state:
                    vehicle = vehicle_svc.get_by_id(st.session_state['view_vehicle_id'])
                    if vehicle:
                        st.markdown("---")
                        st.subheader(f"Vehicle: {vehicle.display_name}")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"**Make:** {vehicle.make}")
                            st.markdown(f"**Model:** {vehicle.model}")
                            st.markdown(f"**Year:** {vehicle.year or 'N/A'}")
                        
                        with col2:
                            st.markdown(f"**License Plate:** {vehicle.license_plate or 'N/A'}")
                            st.markdown(f"**{term_mapper.to_display('vin')}:** {vehicle.vin or 'N/A'}")
                            st.markdown(f"**Color:** {vehicle.color or 'N/A'}")
                        
                        with col3:
                            st.markdown(f"**Mileage:** {vehicle.current_mileage:,}" if vehicle.current_mileage else "**Mileage:** N/A")
                            st.markdown(f"**Owner:** {vehicle.customer.name if vehicle.customer else 'N/A'}")
                            st.markdown(f"**Notes:** {vehicle.notes or 'N/A'}")
                        
                        # Service history
                        history = vehicle_svc.get_service_history(vehicle.id)
                        if history:
                            st.markdown("#### Service History")
                            for order in history[:5]:
                                st.markdown(f"- **{order.order_number}** ({order.status}) - {order.created_at.strftime('%Y-%m-%d')}")
                        
                        if st.button("Close"):
                            del st.session_state['view_vehicle_id']
                            st.rerun()
            else:
                st.info("No vehicles found. Add a new vehicle to get started.")
        
        if can_edit and tab2:
            with tab2:
                st.subheader("Add New Vehicle")
                
                # Get customers for dropdown
                customers = customer_svc.get_all(limit=1000)
                
                if not customers:
                    st.warning("No customers found. Please add a customer first.")
                else:
                    # Initialize auto-generation error state
                    if 'vin_auto_gen_error' not in st.session_state:
                        st.session_state.vin_auto_gen_error = None
                    
                    with st.form("add_vehicle_form", clear_on_submit=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            customer_options = {f"{c.name} (ID: {c.id})": c.id for c in customers}
                            customer_select = st.selectbox("Select Owner *", list(customer_options.keys()))
                            customer_id = customer_options[customer_select]
                            
                            make = st.text_input("Make *", placeholder="e.g., Toyota")
                            year = st.number_input("Year", min_value=1900, max_value=2030, value=2020)
                            
                            # Auto-generate VIN option
                            auto_generate_vin = st.checkbox(
                                f"Auto-generate {term_mapper.to_display('vin')}", 
                                value=False,
                                help="Automatically generate a unique 17-character Vehicle ID"
                            )
                            
                            if auto_generate_vin:
                                vin = st.text_input(
                                    f"{term_mapper.to_display('vin')}", 
                                    placeholder="Will be generated automatically", 
                                    disabled=True,
                                    help=term_mapper.get_tooltip('vin')
                                )
                            else:
                                vin = st.text_input(
                                    f"{term_mapper.to_display('vin')}", 
                                    placeholder="17-character identifier (optional)", 
                                    max_chars=17,
                                    help=term_mapper.get_tooltip('vin')
                                )
                        
                        with col2:
                            model = st.text_input("Model *", placeholder="e.g., Camry")
                            license_plate = st.text_input("License Plate", placeholder="e.g., ABC-1234")
                            color = st.text_input("Color", placeholder="e.g., Silver")
                            mileage = st.number_input("Current Mileage", min_value=0, value=0)
                        
                        notes = st.text_area("Notes")
                        
                        submitted = st.form_submit_button("Add Vehicle", use_container_width=True)
                        
                        if submitted:
                            # Clear previous auto-generation errors
                            st.session_state.vin_auto_gen_error = None
                            
                            if not make or not model:
                                st.error("Make and Model are required")
                            else:
                                # Generate VIN if auto-generate is enabled
                                if auto_generate_vin:
                                    try:
                                        auto_gen = AutoGenerator(db)
                                        vin = auto_gen.ensure_unique_vin()
                                        st.success(f"✓ Generated {term_mapper.to_display('vin')}: {vin}")
                                    except ValueError as e:
                                        error_msg = str(e)
                                        if "Unable to generate unique" in error_msg:
                                            st.error(f"⚠️ Unable to generate {term_mapper.to_display('vin')} automatically after multiple attempts.")
                                            st.info("💡 Please uncheck 'Auto-generate' and enter a Vehicle ID manually, then resubmit the form.")
                                        else:
                                            st.error(f"⚠️ {error_msg}")
                                            st.info("💡 Please uncheck 'Auto-generate' and enter a Vehicle ID manually, then resubmit the form.")
                                        st.stop()
                                    except Exception as e:
                                        st.error(f"⚠️ Error generating {term_mapper.to_display('vin')}: {str(e)}")
                                        st.info("💡 Please uncheck 'Auto-generate' and enter a Vehicle ID manually, then resubmit the form.")
                                        st.stop()
                                
                                # Validate VIN if manually entered
                                if vin and not auto_generate_vin:
                                    is_valid, msg = validate_vin(vin)
                                    if not is_valid:
                                        st.error(msg)
                                        st.stop()
                                    
                                    # Check for duplicate VIN
                                    existing = vehicle_svc.get_by_vin(vin)
                                    if existing:
                                        st.error(f"This {term_mapper.to_display('vin')} already exists. Please use a different one or try auto-generate.")
                                        st.stop()
                                
                                # Validate year
                                if year:
                                    is_valid, msg = validate_year(year)
                                    if not is_valid:
                                        st.error(msg)
                                        st.stop()
                                
                                vehicle, message = vehicle_svc.create(
                                    customer_id=customer_id,
                                    make=make,
                                    model=model,
                                    year=year if year else None,
                                    vin=vin if vin else None,
                                    license_plate=license_plate if license_plate else None,
                                    color=color if color else None,
                                    current_mileage=mileage if mileage else None,
                                    notes=notes if notes else None
                                )
                                
                                if vehicle:
                                    st.success(f"✅ {message}")
                                else:
                                    st.error(f"❌ {message}")
        
        with tab3:
            st.subheader("Search Vehicles")
            
            # Initialize search history
            search_history = SearchHistory('vehicles', max_history=10)
            
            # Show recent searches dropdown
            recent_search = search_history.render_history_dropdown(
                label="Recent Searches",
                placeholder="Select a recent search..."
            )
            
            # Search input
            search_query = st.text_input(
                f"Search by plate, {term_mapper.to_display('vin')}, make, or model", 
                placeholder="Enter search term...",
                value=recent_search if recent_search else ""
            )
            
            if search_query:
                # Add to search history
                search_history.add_search(search_query)
                
                results = vehicle_svc.search(search_query)
                
                if results:
                    st.markdown(f"**Found {len(results)} result(s):**")
                    
                    for vehicle in results:
                        with st.expander(f"**{vehicle.display_name}** - {vehicle.license_plate or 'No Plate'}"):
                            st.markdown(f"**Owner:** {vehicle.customer.name if vehicle.customer else 'N/A'}")
                            st.markdown(f"**{term_mapper.to_display('vin')}:** {vehicle.vin or 'N/A'}")
                            st.markdown(f"**Mileage:** {vehicle.current_mileage:,}" if vehicle.current_mileage else "**Mileage:** N/A")
                            st.markdown(f"**ID:** {vehicle.id}")
                else:
                    st.info("No vehicles found matching your search.")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    finally:
        db.close()


render_vehicles_page()
