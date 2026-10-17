"""
Invoice Service
Handles invoice and payment operations
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple, Dict
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session

from database.models import Invoice, Payment, ServiceOrder, Customer


class InvoiceService:
    """Service class for invoice operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_invoice_number(self) -> str:
        """Generate a unique invoice number"""
        today = datetime.now().strftime('%Y%m%d')
        prefix = f"INV-{today}-"
        
        count = self.db.query(Invoice).filter(
            Invoice.invoice_number.like(f"{prefix}%")
        ).count() + 1
        
        return f"{prefix}{count:03d}"
    
    def get_all(self, skip: int = 0, limit: int = 100,
                status: str = None) -> List[Invoice]:
        """Get all invoices with optional filtering"""
        query = self.db.query(Invoice)
        
        if status:
            query = query.filter(Invoice.status == status)
        
        invoices = query.order_by(
            Invoice.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        # Ensure all invoice statuses are correct
        for invoice in invoices:
            invoice.update_status()
        
        self.db.commit()
        
        return invoices
    
    def get_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Get an invoice by ID"""
        return self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    def get_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get an invoice by invoice number"""
        return self.db.query(Invoice).filter(
            Invoice.invoice_number == invoice_number
        ).first()
    
    def create_from_order(self, order_id: int, tax_rate: float = 0,
                          discount: float = 0, due_days: int = 30
                          ) -> Tuple[Optional[Invoice], str]:
        """
        Create an invoice from a completed service order.
        Returns (invoice, message) tuple.
        """
        order = self.db.query(ServiceOrder).filter(
            ServiceOrder.id == order_id
        ).first()
        
        if not order:
            return None, "Service order not found"
        
        if order.status != 'completed':
            return None, "Service order must be completed before invoicing"
        
        if order.invoice:
            return None, "This order already has an invoice"
        
        # Calculate amounts using Decimal
        subtotal = Decimal(str(order.total_amount))
        tax_rate_decimal = Decimal(str(tax_rate))
        discount_decimal = Decimal(str(discount))
        
        tax_amount = (subtotal * tax_rate_decimal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_amount = (subtotal + tax_amount - discount_decimal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Create invoice
        invoice = Invoice(
            invoice_number=self.generate_invoice_number(),
            service_order_id=order_id,
            customer_id=order.customer_id,
            subtotal=subtotal,
            tax_rate=tax_rate_decimal,
            tax_amount=tax_amount,
            discount_amount=discount_decimal,
            total_amount=total_amount,
            status='unpaid',
            due_date=date.today() + timedelta(days=due_days)
        )
        
        # Update order status
        order.status = 'invoiced'
        
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        
        return invoice, "Invoice created successfully"
    
    def add_payment(self, invoice_id: int, amount: float,
                    payment_method: str, reference: str = None,
                    notes: str = None, received_by: int = None
                    ) -> Tuple[Optional[Payment], str]:
        """
        Add a payment to an invoice.
        Returns (payment, message) tuple.
        """
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return None, "Invoice not found"
        
        if invoice.status == 'cancelled':
            return None, "Cannot add payment to cancelled invoice"
        
        if amount <= 0:
            return None, "Payment amount must be positive"
        
        # Convert to Decimal for precise financial calculations
        amount_decimal = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Create payment
        payment = Payment(
            invoice_id=invoice_id,
            amount=amount_decimal,
            payment_method=payment_method,
            reference=reference,
            notes=notes,
            paid_at=datetime.utcnow(),
            received_by=received_by
        )
        
        self.db.add(payment)
        self.db.flush()
        
        # Automatically update status based on balance
        invoice.update_status()
        
        self.db.commit()
        self.db.refresh(payment)
        
        return payment, f"Payment of ₹{amount:.2f} recorded"
    
    def get_by_customer(self, customer_id: int) -> List[Invoice]:
        """Get all invoices for a customer"""
        return self.db.query(Invoice).filter(
            Invoice.customer_id == customer_id
        ).order_by(Invoice.created_at.desc()).all()
    
    def get_overdue(self) -> List[Invoice]:
        """Get overdue invoices"""
        return self.db.query(Invoice).filter(
            Invoice.status.in_(['unpaid', 'partial']),
            Invoice.due_date < date.today()
        ).order_by(Invoice.due_date).all()
    
    def get_outstanding(self) -> List[Invoice]:
        """Get all outstanding (unpaid/partial) invoices"""
        return self.db.query(Invoice).filter(
            Invoice.status.in_(['unpaid', 'partial'])
        ).order_by(Invoice.created_at).all()
    
    def update_invoice(self, invoice_id: int, **kwargs
                       ) -> Tuple[Optional[Invoice], str]:
        """Update invoice details"""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return None, "Invoice not found"
        
        if invoice.status == 'paid':
            return None, "Cannot modify paid invoice"
        
        allowed_fields = ['discount_amount', 'notes', 'due_date']
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(invoice, key, value)
        
        # Recalculate total if discount changed
        if 'discount_amount' in kwargs:
            invoice.total_amount = invoice.subtotal + invoice.tax_amount - invoice.discount_amount
        
        # Update status based on new balance
        invoice.update_status()
        
        self.db.commit()
        self.db.refresh(invoice)
        
        return invoice, "Invoice updated successfully"
    
    def cancel_invoice(self, invoice_id: int, reason: str = None
                       ) -> Tuple[bool, str]:
        """Cancel an invoice"""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return False, "Invoice not found"
        
        if invoice.status == 'paid':
            return False, "Cannot cancel paid invoice"
        
        if invoice.payments:
            return False, "Cannot cancel invoice with payments"
        
        invoice.status = 'cancelled'
        invoice.notes = f"CANCELLED: {reason or 'No reason provided'}"
        
        # Update order status back to completed
        if invoice.service_order:
            invoice.service_order.status = 'completed'
        
        self.db.commit()
        
        return True, "Invoice cancelled successfully"
    
    def get_statistics(self, days: int = 30) -> Dict:
        """Get invoice statistics"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        invoices = self.db.query(Invoice).filter(
            Invoice.created_at >= start_date,
            Invoice.status != 'cancelled'
        ).all()
        
        total_invoiced = sum(i.total_amount for i in invoices)
        total_paid = sum(i.amount_paid for i in invoices)
        total_outstanding = total_invoiced - total_paid
        
        status_counts = {
            'paid': len([i for i in invoices if i.status == 'paid']),
            'partial': len([i for i in invoices if i.status == 'partial']),
            'unpaid': len([i for i in invoices if i.status == 'unpaid'])
        }
        
        return {
            'total_invoices': len(invoices),
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'total_outstanding': total_outstanding,
            'status_breakdown': status_counts,
            'collection_rate': (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0,
            'period_days': days
        }
    
    def get_count(self, status: str = None) -> int:
        """Get invoice count"""
        query = self.db.query(Invoice)
        if status:
            query = query.filter(Invoice.status == status)
        return query.count()
    
    def get_revenue(self, start_date: date = None, end_date: date = None) -> float:
        """Get total revenue for a period"""
        query = self.db.query(Invoice).filter(
            Invoice.status != 'cancelled'
        )
        
        if start_date:
            query = query.filter(Invoice.created_at >= start_date)
        if end_date:
            query = query.filter(Invoice.created_at <= end_date)
        
        return sum(i.amount_paid for i in query.all())
