"""
Inventory Page
Parts/inventory management interface
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from services.inventory_service import InventoryService
from utils.access_control import check_page_access, show_permission_error
from utils.terminology import TerminologyMapper
from utils.auto_generator import AutoGenerator
from utils.search_history import SearchHistory

st.set_page_config(
    page_title="Inventory - AutoSure",
    page_icon="📦",
    layout="wide"
)

if not st.session_state.get('authenticated', False):
    st.warning("Please log in to access this page.")
    st.stop()


def render_inventory_page():
    # Check page access - allow both 'inventory' and 'view_inventory' permissions
    user = st.session_state.get('user', {})
    if not check_page_access(user, 'inventory'):
        show_permission_error('inventory')
        return
    
    # Initialize terminology mapper
    terminology = TerminologyMapper()
    
    st.title("📦 Inventory Management")
    
    db = SessionLocal()
    
    # Check if user has full inventory access or view-only
    user = st.session_state.get('user', {})
    user_role = user.get('role', '')
    has_full_access = user_role in ['admin', 'manager']
    is_view_only = user_role in ['technician', 'cashier']
    
    try:
        inventory_svc = InventoryService(db)
        
        # Alert for low stock
        low_stock = inventory_svc.get_low_stock()
        if low_stock:
            st.warning(f"⚠️ **{len(low_stock)} items** are below reorder level!")
        
        # Show different tabs based on permissions
        if has_full_access:
            tab1, tab2, tab3, tab4 = st.tabs(["📋 All Parts", "➕ Add Part", "⚠️ Low Stock", "📊 Summary"])
        else:
            # View-only users see limited tabs
            tab1, tab3, tab4 = st.tabs(["📋 All Parts", "⚠️ Low Stock", "📊 Summary"])
            tab2 = None  # No add part tab for view-only users
        
        with tab1:
            st.subheader("Parts Inventory")
            
            # Filter
            col_f1, col_f2 = st.columns([1, 3])
            with col_f1:
                categories = ['All'] + inventory_svc.get_categories()
                category_filter = st.selectbox("Category", categories)
            
            # Get parts
            if category_filter == 'All':
                parts = inventory_svc.get_all(limit=500)
            else:
                parts = inventory_svc.get_by_category(category_filter)
            
            if parts:
                import pandas as pd
                
                df_data = [{
                    'ID': p.id,
                    terminology.to_display('sku'): p.sku,
                    'Name': p.name,
                    'Category': p.category or '-',
                    'Stock': p.stock_quantity,
                    'Status': '⚠️ Low' if p.is_low_stock else '✅ OK',
                    'Price': f"₹{p.selling_price:.2f}",
                    'Location': p.location or '-'
                } for p in parts]
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Part actions - only for users with full access
                if has_full_access:
                    st.markdown("#### Part Actions")
                    col_a1, col_a2, col_a3 = st.columns([1, 1, 2])
                    
                    with col_a1:
                        part_id = st.number_input("Part ID", min_value=1, step=1)
                    
                    with col_a2:
                        action = st.selectbox("Action", ["View", "Adjust Stock", "Update Price", "Deactivate"])
                    
                    with col_a3:
                        if st.button("Execute"):
                            part = inventory_svc.get_by_id(part_id)
                            if part:
                                st.session_state['selected_part_id'] = part_id
                                st.session_state['part_action'] = action
                            else:
                                st.error("Part not found")
                    
                    # Display actions
                    if 'selected_part_id' in st.session_state:
                        part = inventory_svc.get_by_id(st.session_state['selected_part_id'])
                        action = st.session_state.get('part_action')
                        
                        if part:
                            st.markdown("---")
                            st.subheader(f"Part: {part.name}")
                            
                            if action == "View":
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"**{terminology.to_display('sku')}:** {part.sku}")
                                    st.markdown(f"**Category:** {part.category or 'N/A'}")
                                    st.markdown(f"**Description:** {part.description or 'N/A'}")
                                with col2:
                                    st.markdown(f"**Cost Price:** ₹{part.cost_price:.2f}" if part.cost_price else "**Cost Price:** N/A")
                                    st.markdown(f"**Selling Price:** ₹{part.selling_price:.2f}")
                                    st.markdown(f"**Stock:** {part.stock_quantity}")
                                    st.markdown(f"**Reorder Level:** {part.reorder_level}")
                                    st.markdown(f"**Location:** {part.location or 'N/A'}")
                                
                                if st.button("Close"):
                                    del st.session_state['selected_part_id']
                                    del st.session_state['part_action']
                                    st.rerun()
                            
                            elif action == "Adjust Stock":
                                st.markdown(f"**Current Stock:** {part.stock_quantity}")
                                adjustment = st.number_input("Adjustment (+/-)", value=0)
                                reason = st.text_input("Reason")
                                
                                if st.button("Apply Adjustment"):
                                    updated, msg = inventory_svc.adjust_stock(part_id, adjustment, reason)
                                    if updated:
                                        st.success(msg)
                                        del st.session_state['selected_part_id']
                                        del st.session_state['part_action']
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            
                            elif action == "Update Price":
                                new_price = st.number_input("New Selling Price", min_value=0.0, value=float(part.selling_price))
                                
                                if st.button("Update Price"):
                                    updated, msg = inventory_svc.update(part_id, selling_price=new_price)
                                    if updated:
                                        st.success(msg)
                                        del st.session_state['selected_part_id']
                                        del st.session_state['part_action']
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            
                            elif action == "Deactivate":
                                st.warning("This will deactivate the part. Continue?")
                                if st.button("Yes, Deactivate"):
                                    success, msg = inventory_svc.delete(part_id)
                                    if success:
                                        st.success(msg)
                                        del st.session_state['selected_part_id']
                                        del st.session_state['part_action']
                                        st.rerun()
                                    else:
                                        st.error(msg)
                else:
                    # View-only users see info message
                    st.info("ℹ️ You have view-only access to inventory. Contact your administrator for edit permissions.")
            else:
                st.info("No parts in inventory. Add parts to get started.")
        
        # Only show Add Part tab for users with full access
        if has_full_access and tab2:
            with tab2:
                st.subheader("Add New Part")
                
                with st.form("add_part_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Auto-generate SKU option
                        auto_generate_sku = st.checkbox(
                            f"Auto-generate {terminology.to_display('sku')}", 
                            value=False,
                            help="Automatically generate a unique Product Code"
                        )
                        
                        # Product Code field with tooltip
                        sku_label = f"{terminology.to_display('sku')}"
                        if not auto_generate_sku:
                            sku_label += " *"
                        sku_tooltip = terminology.get_tooltip('sku')
                        
                        if auto_generate_sku:
                            sku = st.text_input(
                                sku_label, 
                                placeholder="Will be generated automatically", 
                                help=sku_tooltip,
                                disabled=True
                            )
                        else:
                            sku = st.text_input(
                                sku_label, 
                                placeholder="e.g., OIL-001", 
                                help=sku_tooltip
                            )
                        name = st.text_input("Name *", placeholder="Part name")
                        
                        # Category dropdown with fixed options
                        category_options = [
                            "Electrical",
                            "Exterior",
                            "Filters",
                            "Brakes",
                            "Ignition",
                            "Fluids"
                        ]
                        category = st.selectbox("Category *", options=category_options, index=5)
                        
                        cost_price = st.number_input("Cost Price", min_value=0.0, value=0.0)
                    
                    with col2:
                        selling_price = st.number_input("Selling Price *", min_value=0.0, value=0.0)
                        stock_quantity = st.number_input("Initial Stock", min_value=0, value=0)
                        reorder_tooltip = terminology.get_tooltip('reorder_level')
                        reorder_level = st.number_input("Reorder Level", min_value=0, value=10, help=reorder_tooltip)
                        location = st.text_input("Location", placeholder="e.g., Aisle A-1")
                    
                    description = st.text_area("Description")
                    supplier = st.text_input("Supplier")
                    
                    submitted = st.form_submit_button("Add Part", use_container_width=True)
                    
                    if submitted:
                        if not name or selling_price <= 0:
                            st.error("Name and Selling Price are required")
                        elif not auto_generate_sku and not sku:
                            st.error(f"{terminology.to_display('sku')} is required (or enable auto-generate)")
                        else:
                            # Generate SKU if auto-generate is enabled
                            if auto_generate_sku:
                                try:
                                    auto_gen = AutoGenerator(db)
                                    sku = auto_gen.ensure_unique_sku(category=category if category else None)
                                    st.success(f"✓ Generated {terminology.to_display('sku')}: {sku}")
                                except ValueError as e:
                                    error_msg = str(e)
                                    if "Unable to generate unique" in error_msg:
                                        st.error(f"⚠️ Unable to generate {terminology.to_display('sku')} automatically after multiple attempts.")
                                        st.info("💡 Please uncheck 'Auto-generate' and enter a Product Code manually, then resubmit the form.")
                                    else:
                                        st.error(f"⚠️ {error_msg}")
                                        st.info("💡 Please uncheck 'Auto-generate' and enter a Product Code manually, then resubmit the form.")
                                    st.stop()
                                except Exception as e:
                                    st.error(f"⚠️ Error generating {terminology.to_display('sku')}: {str(e)}")
                                    st.info("💡 Please uncheck 'Auto-generate' and enter a Product Code manually, then resubmit the form.")
                                    st.stop()
                            
                            # Validate manual SKU entry for uniqueness
                            if sku and not auto_generate_sku:
                                # Check for duplicate SKU
                                existing = inventory_svc.get_by_sku(sku)
                                if existing:
                                    st.error(f"This {terminology.to_display('sku')} already exists. Please use a different one or try auto-generate.")
                                    st.stop()
                            
                            part, message = inventory_svc.create(
                                sku=sku,
                                name=name,
                                selling_price=selling_price,
                                category=category if category else None,
                                description=description if description else None,
                                cost_price=cost_price if cost_price > 0 else None,
                                stock_quantity=stock_quantity,
                                reorder_level=reorder_level,
                                location=location if location else None,
                                supplier=supplier if supplier else None
                            )
                            
                            if part:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
        
        with tab3:
            st.subheader("Low Stock Alert")
            
            low_stock_items = inventory_svc.get_low_stock()
            
            if low_stock_items:
                import pandas as pd
                
                df_data = [{
                    terminology.to_display('sku'): p.sku,
                    'Name': p.name,
                    'Current Stock': p.stock_quantity,
                    'Reorder Level': p.reorder_level,
                    'Shortage': p.reorder_level - p.stock_quantity,
                    'Location': p.location or '-'
                } for p in low_stock_items]
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.markdown("**Recommended Actions:**")
                for p in low_stock_items[:5]:
                    needed = max(p.reorder_level - p.stock_quantity, 1)
                    st.markdown(f"- Order at least **{needed}** units of {p.name} (Current: {p.stock_quantity}, Target: {p.reorder_level})")
            else:
                st.success("✅ All inventory levels are healthy!")
        
        with tab4:
            st.subheader("Inventory Summary")
            
            inv_value = inventory_svc.get_inventory_value()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Parts", inv_value['total_parts'])
            
            with col2:
                st.metric("Total Units", inv_value['total_units'])
            
            with col3:
                st.metric("Cost Value", f"₹{inv_value['cost_value']:,.2f}")
            
            with col4:
                st.metric("Retail Value", f"₹{inv_value['retail_value']:,.2f}")
            
            st.metric("Potential Profit", f"₹{inv_value['potential_profit']:,.2f}")
            
            # Category breakdown
            categories = inventory_svc.get_categories()
            if categories:
                st.markdown("#### By Category")
                for cat in categories:
                    parts = inventory_svc.get_by_category(cat)
                    total = len(parts)
                    value = sum(p.selling_price * p.stock_quantity for p in parts)
                    st.markdown(f"**{cat}:** {total} parts, ₹{value:,.2f} value")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    finally:
        db.close()


render_inventory_page()
