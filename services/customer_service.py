"""
Customer Service
Handles customer-related business logic
"""

from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.models import Customer


class CustomerService:
    """Service class for customer operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Get all customers with pagination"""
        return self.db.query(Customer).order_by(
            Customer.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        """Get a customer by ID"""
        return self.db.query(Customer).filter(Customer.id == customer_id).first()
    
    def search(self, query: str) -> List[Customer]:
        """Search customers by name, phone, or email"""
        search_term = f"%{query}%"
        return self.db.query(Customer).filter(
            or_(
                Customer.name.ilike(search_term),
                Customer.phone.ilike(search_term),
                Customer.email.ilike(search_term)
            )
        ).order_by(Customer.name).all()
    
    def quick_customer_search(self, query: str) -> List[Customer]:
        """Quick search for customers (for POS)"""
        if not query:
            return self.get_all(limit=20)
        return self.search(query)
    
    def create(self, name: str, phone: str = None, email: str = None,
               address: str = None, customer_type: str = 'standard',
               notes: str = None) -> Tuple[Optional[Customer], str]:
        """
        Create a new customer.
        Returns (customer, message) tuple.
        """
        # Validate required fields
        if not name or not name.strip():
            return None, "Customer name is required"
        
        # Check for duplicate email
        if email:
            existing = self.db.query(Customer).filter(
                Customer.email == email.strip()
            ).first()
            if existing:
                return None, "A customer with this email already exists"
        
        # Validate customer type
        valid_types = ['standard', 'business', 'premium']
        if customer_type not in valid_types:
            customer_type = 'standard'
        
        # Create customer
        customer = Customer(
            name=name.strip(),
            phone=phone.strip() if phone else None,
            email=email.strip() if email else None,
            address=address.strip() if address else None,
            customer_type=customer_type,
            notes=notes.strip() if notes else None
        )
        
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        
        return customer, "Customer created successfully"
    
    def update(self, customer_id: int, **kwargs) -> Tuple[Optional[Customer], str]:
        """
        Update customer information.
        Returns (customer, message) tuple.
        """
        customer = self.get_by_id(customer_id)
        if not customer:
            return None, "Customer not found"
        
        # Update allowed fields
        allowed_fields = ['name', 'phone', 'email', 'address', 'customer_type', 'notes']
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                if isinstance(value, str):
                    value = value.strip()
                setattr(customer, key, value)
        
        customer.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(customer)
        
        return customer, "Customer updated successfully"
    
    def delete(self, customer_id: int) -> Tuple[bool, str]:
        """
        Delete a customer.
        Returns (success, message) tuple.
        """
        customer = self.get_by_id(customer_id)
        if not customer:
            return False, "Customer not found"
        
        # Check for related records
        if customer.vehicles:
            return False, "Cannot delete customer with associated vehicles"
        
        if customer.service_orders:
            return False, "Cannot delete customer with service history"
        
        self.db.delete(customer)
        self.db.commit()
        
        return True, "Customer deleted successfully"
    
    def get_by_type(self, customer_type: str) -> List[Customer]:
        """Get customers by type"""
        return self.db.query(Customer).filter(
            Customer.customer_type == customer_type
        ).order_by(Customer.name).all()
    
    def get_service_history(self, customer_id: int) -> dict:
        """Get customer's service history summary"""
        customer = self.get_by_id(customer_id)
        if not customer:
            return {}
        
        orders = customer.service_orders
        invoices = customer.invoices
        
        total_orders = len(orders)
        total_spent = sum(order.total_amount or 0 for order in orders)
        total_paid = sum(
            sum(p.amount for p in invoice.payments) 
            for invoice in invoices
        )
        
        return {
            'customer': customer,
            'total_orders': total_orders,
            'total_spent': total_spent,
            'total_paid': total_paid,
            'balance': total_spent - total_paid,
            'orders': orders,
            'invoices': invoices
        }
    
    def get_count(self) -> int:
        """Get total customer count"""
        return self.db.query(Customer).count()
    
    def get_recent(self, limit: int = 10) -> List[Customer]:
        """Get recently added customers"""
        return self.db.query(Customer).order_by(
            Customer.created_at.desc()
        ).limit(limit).all()
