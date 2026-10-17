"""
Reports Page
Business analytics and reporting
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from services.service_order_service import ServiceOrderService
from services.invoice_service import InvoiceService
from services.customer_service import CustomerService
from services.inventory_service import InventoryService
from utils.access_control import require_permission

st.set_page_config(
    page_title="Reports - AutoSure",
    page_icon="📊",
    layout="wide"
)

if not st.session_state.get('authenticated', False):
    st.warning("Please log in to access this page.")
    st.stop()


@require_permission('reports')
def render_reports_page():
    st.title("📊 Reports & Analytics")
    
    db = SessionLocal()
    
    try:
        order_svc = ServiceOrderService(db)
        invoice_svc = InvoiceService(db)
        customer_svc = CustomerService(db)
        inventory_svc = InventoryService(db)
        
        # Date range selector
        col_d1, col_d2, col_d3 = st.columns([1, 1, 2])
        
        with col_d1:
            st.selectbox("Time Period", [30], index=0, disabled=True, 
                        help="Time period selection temporarily disabled")
            days_range = 30
        
        with col_d2:
            start_date = date.today() - timedelta(days=days_range)
            st.markdown(f"**From:** {start_date}")
            st.markdown(f"**To:** {date.today()}")
        
        with col_d3:
            st.info("ℹ️ Time period selection is temporarily disabled due to a session persistence issue with the component library. This will be resolved in the next update. Thank you for your patience.")
        
        st.markdown("---")
        
        # Revenue Overview
        col_title, col_export = st.columns([3, 1])
        with col_title:
            st.subheader("💰 Revenue Overview")
        with col_export:
            if st.button("📄 Export PDF Report", use_container_width=True):
                st.session_state['generate_pdf'] = True
                st.toast("📄 Generating PDF... Scroll down to download!", icon="⬇️")
        
        invoice_stats = invoice_svc.get_statistics(days=days_range)
        order_stats = order_svc.get_statistics(days=days_range)
        
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        
        with col_r1:
            st.metric("Total Invoiced", f"₹{invoice_stats['total_invoiced']:,.2f}")
        
        with col_r2:
            st.metric("Total Collected", f"₹{invoice_stats['total_paid']:,.2f}")
        
        with col_r3:
            st.metric("Outstanding", f"₹{invoice_stats['total_outstanding']:,.2f}")
        
        with col_r4:
            st.metric("Collection Rate", f"{invoice_stats['collection_rate']:.1f}%")
        
        # Revenue chart
        st.markdown("#### Revenue vs Collection")
        
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
                textfont=dict(color='#3d3a2a'),
                hovertemplate='<b>%{x}</b><br>Amount: ₹%{y:,.2f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Space Grotesk', color='#3d3a2a'),
            yaxis_title="Amount (₹)",
            xaxis_title="Category",
            xaxis=dict(gridcolor='#f0ede5'),
            yaxis=dict(gridcolor='#f0ede5'),
            hoverlabel=dict(
                bgcolor="white",
                font_size=14,
                font_family="Space Grotesk"
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Service Orders Analysis
        st.subheader("🔧 Service Orders Analysis")
        
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            st.markdown("#### Order Statistics")
            st.metric("Total Orders", order_stats['total_orders'])
            st.metric("Average Order Value", f"₹{order_stats['average_order_value']:,.2f}")
            st.metric("Total Revenue", f"₹{order_stats['total_revenue']:,.2f}")
        
        with col_s2:
            st.markdown("#### Status Distribution")
            
            status_data = order_stats['status_breakdown']
            status_data = {k: v for k, v in status_data.items() if v > 0}
            
            if status_data:
                fig = px.pie(
                    values=list(status_data.values()),
                    names=list(status_data.keys()),
                    color_discrete_sequence=['#d97757', '#7c9a6d', '#c85a54', '#7a8fa3', '#6b6757', '#f0ede5']
                )
                fig.update_traces(
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Space Grotesk', color='#3d3a2a')
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Status breakdown table
        st.markdown("#### Status Breakdown")
        import pandas as pd
        
        status_df = pd.DataFrame([
            {'Status': k.replace('_', ' ').title(), 'Count': v}
            for k, v in order_stats['status_breakdown'].items()
        ])
        
        st.dataframe(status_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Customer Analytics
        st.subheader("👥 Customer Analytics")
        
        total_customers = customer_svc.get_count()
        recent_customers = len(customer_svc.get_recent(days_range))
        
        col_c1, col_c2, col_c3 = st.columns(3)
        
        with col_c1:
            st.metric("Total Customers", total_customers)
        
        with col_c2:
            st.metric(f"New ({days_range}d)", recent_customers)
        
        with col_c3:
            # Customer type breakdown
            regular = len(customer_svc.get_by_type('regular'))
            wholesale = len(customer_svc.get_by_type('wholesale'))
            vip = len(customer_svc.get_by_type('vip'))
            st.metric("Premium Customers", vip)
        
        # Customer type pie chart
        st.markdown("#### Customer Type Distribution")
        
        type_data = {
            'Type': ['Standard', 'Business', 'Premium'],
            'Count': [regular, wholesale, vip]
        }
        
        # Filter out zero values for cleaner pie chart
        filtered_types = [t for t, c in zip(type_data['Type'], type_data['Count']) if c > 0]
        filtered_counts = [c for c in type_data['Count'] if c > 0]
        
        if filtered_counts:
            fig = px.pie(
                values=filtered_counts,
                names=filtered_types,
                color_discrete_sequence=['#d97757', '#7c9a6d', '#6b6757']
            )
            fig.update_traces(
                hovertemplate='<b>%{label}</b><br>Customers: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Space Grotesk', color='#3d3a2a')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No customer data available")
        
        st.markdown("---")
        
        # Inventory Report
        st.subheader("📦 Inventory Report")
        
        inv_value = inventory_svc.get_inventory_value()
        low_stock_count = len(inventory_svc.get_low_stock())
        out_of_stock_count = len(inventory_svc.get_out_of_stock())
        
        col_i1, col_i2, col_i3, col_i4 = st.columns(4)
        
        with col_i1:
            st.metric("Total Parts", inv_value['total_parts'])
        
        with col_i2:
            st.metric("Total Units", inv_value['total_units'])
        
        with col_i3:
            st.metric("Inventory Value", f"₹{inv_value['retail_value']:,.2f}")
        
        with col_i4:
            st.metric("Low Stock Items", low_stock_count, delta="Attention needed" if low_stock_count > 0 else None, delta_color="inverse")
        
        # Inventory alerts
        if low_stock_count > 0:
            st.warning(f"⚠️ **{low_stock_count} items** are below reorder level")
            low_stock_items = inventory_svc.get_low_stock()[:10]
            
            df_low = pd.DataFrame([{
                'SKU': p.sku,
                'Name': p.name,
                'Stock': p.stock_quantity,
                'Reorder Level': p.reorder_level,
                'Shortage': p.reorder_level - p.stock_quantity
            } for p in low_stock_items])
            
            st.dataframe(df_low, use_container_width=True, hide_index=True)
        
        # PDF Generation
        if st.session_state.get('generate_pdf', False):
            st.markdown("---")
            st.subheader("📄 Generating PDF Report...")
            
            try:
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.lib import colors
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.enums import TA_CENTER, TA_RIGHT
                from io import BytesIO
                import plotly.io as pio
                
                # Create PDF buffer
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                elements = []
                styles = getSampleStyleSheet()
                
                # Title
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    textColor=colors.HexColor('#3d3a2a'),
                    spaceAfter=30,
                    alignment=TA_CENTER
                )
                elements.append(Paragraph("AutoSure", title_style))
                elements.append(Paragraph(f"Financial Report - {days_range} Days", styles['Heading2']))
                elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
                elements.append(Spacer(1, 0.3*inch))
                
                # Revenue Summary Table
                elements.append(Paragraph("Revenue Overview", styles['Heading2']))
                revenue_table_data = [
                    ['Metric', 'Amount (₹)'],
                    ['Total Invoiced', f"₹{invoice_stats['total_invoiced']:,.2f}"],
                    ['Total Collected', f"₹{invoice_stats['total_paid']:,.2f}"],
                    ['Outstanding', f"₹{invoice_stats['total_outstanding']:,.2f}"],
                    ['Collection Rate', f"{invoice_stats['collection_rate']:.1f}%"]
                ]
                
                revenue_table = Table(revenue_table_data, colWidths=[3*inch, 2*inch])
                revenue_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d97757')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(revenue_table)
                elements.append(Spacer(1, 0.3*inch))
                
                # Order Statistics
                elements.append(Paragraph("Work Order Statistics", styles['Heading2']))
                order_table_data = [
                    ['Metric', 'Value'],
                    ['Total Orders', str(order_stats['total_orders'])],
                    ['Average Order Value', f"₹{order_stats['average_order_value']:,.2f}"],
                    ['Total Revenue', f"₹{order_stats['total_revenue']:,.2f}"]
                ]
                
                order_table = Table(order_table_data, colWidths=[3*inch, 2*inch])
                order_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c9a6d')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(order_table)
                elements.append(Spacer(1, 0.3*inch))
                
                # Inventory Summary
                inv_value = inventory_svc.get_inventory_value()
                elements.append(Paragraph("Inventory Summary", styles['Heading2']))
                inv_table_data = [
                    ['Metric', 'Value'],
                    ['Total Parts', str(inv_value['total_parts'])],
                    ['Total Units', str(inv_value['total_units'])],
                    ['Cost Value', f"₹{inv_value['cost_value']:,.2f}"],
                    ['Retail Value', f"₹{inv_value['retail_value']:,.2f}"],
                    ['Potential Profit', f"₹{inv_value['potential_profit']:,.2f}"]
                ]
                
                inv_table = Table(inv_table_data, colWidths=[3*inch, 2*inch])
                inv_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c85a54')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(inv_table)
                
                # Build PDF
                doc.build(elements)
                buffer.seek(0)
                
                # Download button
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=buffer,
                    file_name=f"autosure_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.success("✅ PDF report generated successfully!")
                st.session_state['generate_pdf'] = False
                
            except Exception as pdf_error:
                st.error(f"Error generating PDF: {str(pdf_error)}")
                st.session_state['generate_pdf'] = False
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    finally:
        db.close()


render_reports_page()
