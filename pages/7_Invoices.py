"""
Invoices Page
Invoice management and payment tracking
"""

import streamlit as st
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from services.invoice_service import InvoiceService
from services.customer_service import CustomerService
from utils.access_control import require_permission

st.set_page_config(
    page_title="Invoices - AutoSure",
    page_icon="📄",
    layout="wide"
)

if not st.session_state.get('authenticated', False):
    st.warning("Please log in to access this page.")
    st.stop()


@require_permission('invoices')
def render_invoices_page():
    st.title("📄 Invoice Management")
    
    db = SessionLocal()
    
    try:
        invoice_svc = InvoiceService(db)
        customer_svc = CustomerService(db)
        
        # Summary metrics
        stats = invoice_svc.get_statistics(days=30)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Invoices (30d)", stats['total_invoices'])
        
        with col2:
            st.metric("Total Invoiced", f"₹{stats['total_invoiced']:,.2f}")
        
        with col3:
            st.metric("Collected", f"₹{stats['total_paid']:,.2f}")
        
        with col4:
            st.metric("Outstanding", f"₹{stats['total_outstanding']:,.2f}")
        
        st.markdown("---")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📋 All Invoices", "💰 Outstanding", "📅 Overdue", "🔍 Search"])
        
        with tab1:
            st.subheader("All Invoices")
            
            # Filter
            status_filter = st.selectbox("Status", ['All', 'unpaid', 'partial', 'paid', 'cancelled'])
            
            invoices = invoice_svc.get_all(
                limit=100,
                status=None if status_filter == 'All' else status_filter
            )
            
            if invoices:
                import pandas as pd
                
                status_colors = {
                    'paid': '✅',
                    'partial': '💵',
                    'unpaid': '💰',
                    'cancelled': '❌'
                }
                
                df_data = []
                for inv in invoices:
                    balance_display = f"₹{inv.balance_due:,.2f}"
                    if inv.overpaid_amount > 0:
                        balance_display = f"₹0.00 (Overpaid: ₹{inv.overpaid_amount:,.2f})"
                    
                    df_data.append({
                        'ID': inv.id,
                        'Invoice #': inv.invoice_number,
                        'Status': f"{status_colors.get(inv.status, '○')} {inv.status}",
                        'Customer': inv.customer.name if inv.customer else '-',
                        'Total': f"₹{inv.total_amount:,.2f}",
                        'Paid': f"₹{inv.amount_paid:,.2f}",
                        'Balance': balance_display,
                        'Created': inv.created_at.strftime('%Y-%m-%d')
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Invoice actions
                st.markdown("#### Invoice Actions")
                col_a1, col_a2 = st.columns([1, 2])
                
                with col_a1:
                    inv_id = st.number_input("Invoice ID", min_value=1, step=1)
                
                with col_a2:
                    if st.button("View Details"):
                        invoice = invoice_svc.get_by_id(inv_id)
                        if invoice:
                            st.session_state['view_invoice_id'] = inv_id
                        else:
                            st.error("Invoice not found")
                
                # View invoice details
                if 'view_invoice_id' in st.session_state:
                    invoice = invoice_svc.get_by_id(st.session_state['view_invoice_id'])
                    
                    if invoice:
                        st.markdown("---")
                        st.subheader(f"Invoice: {invoice.invoice_number}")
                        
                        col_d1, col_d2 = st.columns(2)
                        
                        with col_d1:
                            st.markdown(f"**Customer:** {invoice.customer.name if invoice.customer else 'N/A'}")
                            st.markdown(f"**Status:** {invoice.status.upper()}")
                            st.markdown(f"**Created:** {invoice.created_at.strftime('%Y-%m-%d')}")
                        
                        with col_d2:
                            st.markdown(f"**Subtotal:** ₹{invoice.subtotal:,.2f}")
                            st.markdown(f"**Tax:** ₹{invoice.tax_amount:,.2f}")
                            st.markdown(f"**Discount:** -₹{invoice.discount_amount:,.2f}")
                            st.markdown(f"**Total:** ₹{invoice.total_amount:,.2f}")
                        
                        # Payment history
                        st.markdown("#### Payment History")
                        
                        if invoice.payments:
                            for p in invoice.payments:
                                st.markdown(f"- **₹{p.amount:,.2f}** via {p.payment_method} on {p.paid_at.strftime('%Y-%m-%d %H:%M')}")
                        else:
                            st.info("No payments recorded")
                        
                        # Add payment
                        if invoice.status not in ['paid', 'cancelled']:
                            st.markdown("#### Record Payment")
                            
                            col_p1, col_p2, col_p3 = st.columns([1, 1, 2])
                            
                            with col_p1:
                                payment_amount = st.number_input("Amount", min_value=0.0, value=float(invoice.balance_due))
                            
                            with col_p2:
                                payment_method = st.selectbox("Method", ["cash", "card", "bank_transfer", "check"])
                            
                            with col_p3:
                                reference = st.text_input("Reference/Notes")
                            
                            if st.button("Record Payment"):
                                user = st.session_state.get('user', {})
                                payment, msg = invoice_svc.add_payment(
                                    invoice_id=invoice.id,
                                    amount=payment_amount,
                                    payment_method=payment_method,
                                    reference=reference,
                                    received_by=user.get('id')
                                )
                                
                                if payment:
                                    st.success(f"✅ {msg}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
                        
                        if st.button("Close"):
                            del st.session_state['view_invoice_id']
                            st.rerun()
            else:
                st.info("No invoices found.")
        
        with tab2:
            st.subheader("Outstanding Invoices")
            
            outstanding = invoice_svc.get_outstanding()
            
            if outstanding:
                import pandas as pd
                
                df_data = [{
                    'Invoice #': inv.invoice_number,
                    'Customer': inv.customer.name if inv.customer else '-',
                    'Total': f"₹{inv.total_amount:,.2f}",
                    'Paid': f"₹{inv.amount_paid:,.2f}",
                    'Balance': f"₹{inv.balance_due:,.2f}",
                    'Due Date': inv.due_date.strftime('%Y-%m-%d') if inv.due_date else 'N/A'
                } for inv in outstanding]
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                total_outstanding = sum(inv.balance_due for inv in outstanding)
                st.markdown(f"**Total Outstanding: ₹{total_outstanding:,.2f}**")
            else:
                st.success("✅ No outstanding invoices!")
        
        with tab3:
            st.subheader("Overdue Invoices")
            
            overdue = invoice_svc.get_overdue()
            
            if overdue:
                import pandas as pd
                
                df_data = [{
                    'Invoice #': inv.invoice_number,
                    'Customer': inv.customer.name if inv.customer else '-',
                    'Balance': f"₹{inv.balance_due:,.2f}",
                    'Due Date': inv.due_date.strftime('%Y-%m-%d'),
                    'Days Overdue': (date.today() - inv.due_date).days
                } for inv in overdue]
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.warning(f"⚠️ **{len(overdue)} overdue invoices** require attention!")
            else:
                st.success("✅ No overdue invoices!")
        
        with tab4:
            st.subheader("Search Invoices")
            
            search_type = st.radio("Search By", ["Invoice Number", "Customer"])
            
            if search_type == "Invoice Number":
                search_query = st.text_input("Enter Invoice Number", placeholder="e.g., INV-2024...")
            else:
                search_query = st.text_input("Enter Customer Name", placeholder="Customer name...")
            
            if search_query:
                if search_type == "Invoice Number":
                    invoice = invoice_svc.get_by_number(search_query)
                    results = [invoice] if invoice else []
                else:
                    customers = customer_svc.search(search_query)
                    results = []
                    for c in customers:
                        results.extend(invoice_svc.get_by_customer(c.id))
                
                if results:
                    st.markdown(f"**Found {len(results)} result(s):**")
                    
                    for inv in results:
                        if not inv:
                            continue
                        with st.expander(f"**{inv.invoice_number}** - {inv.status.upper()} - ₹{inv.total_amount:,.2f}"):
                            st.markdown(f"**Customer:** {inv.customer.name if inv.customer else 'N/A'}")
                            st.markdown(f"**Balance Due:** ₹{inv.balance_due:,.2f}")
                            st.markdown(f"**Created:** {inv.created_at.strftime('%Y-%m-%d')}")
                else:
                    st.info("No invoices found matching your search.")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    finally:
        db.close()


render_invoices_page()
