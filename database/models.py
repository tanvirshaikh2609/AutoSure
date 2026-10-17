"""
SQLAlchemy Models
Database models for AutoSure
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, DECIMAL, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from database.connection import Base


class User(Base):
    """System users with authentication and role-based access"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    technician_id = Column(Integer, ForeignKey('technicians.id', ondelete='SET NULL'), nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payments_received = relationship("Payment", back_populates="receiver")
    technician = relationship("Technician", foreign_keys=[technician_id])

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Customer(Base):
    """Customer profiles with contact information"""
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    customer_type = Column(String(20), default='regular')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vehicles = relationship("Vehicle", back_populates="customer")
    service_orders = relationship("ServiceOrder", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', type='{self.customer_type}')>"


class Vehicle(Base):
    """Vehicle records linked to customers"""
    __tablename__ = 'vehicles'

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=True)
    vin = Column(String(17), unique=True, nullable=True)
    license_plate = Column(String(20), nullable=True)
    color = Column(String(30), nullable=True)
    current_mileage = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="vehicles")
    service_orders = relationship("ServiceOrder", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle(id={self.id}, make='{self.make}', model='{self.model}', plate='{self.license_plate}')>"

    @property
    def display_name(self):
        """Return a formatted vehicle name"""
        year_str = str(self.year) if self.year else ""
        return f"{year_str} {self.make} {self.model}".strip()


class Technician(Base):
    """Workshop technicians/employees"""
    __tablename__ = 'technicians'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    employee_id = Column(String(20), unique=True, nullable=True)
    specialty = Column(String(100), nullable=True)
    hourly_rate = Column(DECIMAL(10, 2), nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    service_orders = relationship("ServiceOrder", back_populates="technician")

    def __repr__(self):
        return f"<Technician(id={self.id}, name='{self.name}', specialty='{self.specialty}')>"


class ServiceType(Base):
    """Catalog of available services"""
    __tablename__ = 'service_types'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    standard_hours = Column(DECIMAL(5, 2), default=1.0)
    base_price = Column(DECIMAL(10, 2), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    service_items = relationship("ServiceItem", back_populates="service_type")

    def __repr__(self):
        return f"<ServiceType(id={self.id}, name='{self.name}', hours={self.standard_hours})>"


class Part(Base):
    """Inventory parts with pricing and stock levels"""
    __tablename__ = 'parts'

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    cost_price = Column(DECIMAL(10, 2), nullable=True)
    selling_price = Column(DECIMAL(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    location = Column(String(50), nullable=True)
    supplier = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order_parts = relationship("OrderPart", back_populates="part")

    def __repr__(self):
        return f"<Part(id={self.id}, sku='{self.sku}', name='{self.name}', stock={self.stock_quantity})>"

    @property
    def is_low_stock(self):
        """Check if part is below reorder level"""
        return self.stock_quantity <= self.reorder_level


class ServiceOrder(Base):
    """Main service transaction tracking"""
    __tablename__ = 'service_orders'

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=True)
    technician_id = Column(Integer, ForeignKey('technicians.id', ondelete='SET NULL'), nullable=True)
    status = Column(String(20), default='pending')
    complaint = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    labor_total = Column(DECIMAL(10, 2), default=0)
    parts_total = Column(DECIMAL(10, 2), default=0)
    total_amount = Column(DECIMAL(10, 2), default=0)
    notes = Column(Text, nullable=True)
    estimated_completion = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="service_orders")
    vehicle = relationship("Vehicle", back_populates="service_orders")
    technician = relationship("Technician", back_populates="service_orders")
    service_items = relationship("ServiceItem", back_populates="service_order", cascade="all, delete-orphan")
    order_parts = relationship("OrderPart", back_populates="service_order", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="service_order", uselist=False)

    def __repr__(self):
        return f"<ServiceOrder(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"

    def calculate_totals(self):
        """Recalculate order totals from items and parts"""
        labor_total = sum(item.labor_cost or 0 for item in self.service_items)
        parts_total = sum(part.total_price or 0 for part in self.order_parts)
        self.labor_total = labor_total
        self.parts_total = parts_total
        self.total_amount = labor_total + parts_total
        return self.total_amount


class ServiceItem(Base):
    """Individual service line items"""
    __tablename__ = 'service_items'

    id = Column(Integer, primary_key=True, index=True)
    service_order_id = Column(Integer, ForeignKey('service_orders.id', ondelete='CASCADE'), nullable=False)
    service_type_id = Column(Integer, ForeignKey('service_types.id'), nullable=True)
    description = Column(Text, nullable=True)
    labor_hours = Column(DECIMAL(5, 2), nullable=True)
    labor_rate = Column(DECIMAL(10, 2), nullable=True)
    labor_cost = Column(DECIMAL(10, 2), nullable=True)
    status = Column(String(20), default='pending')

    # Relationships
    service_order = relationship("ServiceOrder", back_populates="service_items")
    service_type = relationship("ServiceType", back_populates="service_items")

    def __repr__(self):
        return f"<ServiceItem(id={self.id}, order_id={self.service_order_id}, cost={self.labor_cost})>"


class OrderPart(Base):
    """Parts used in service orders (junction table)"""
    __tablename__ = 'order_parts'

    id = Column(Integer, primary_key=True, index=True)
    service_order_id = Column(Integer, ForeignKey('service_orders.id', ondelete='CASCADE'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    total_price = Column(DECIMAL(10, 2), nullable=False)

    # Relationships
    service_order = relationship("ServiceOrder", back_populates="order_parts")
    part = relationship("Part", back_populates="order_parts")

    def __repr__(self):
        return f"<OrderPart(id={self.id}, part_id={self.part_id}, qty={self.quantity})>"


class Invoice(Base):
    """Generated invoices from completed orders"""
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(20), unique=True, nullable=False)
    service_order_id = Column(Integer, ForeignKey('service_orders.id'), nullable=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    subtotal = Column(DECIMAL(12, 2), nullable=False)
    tax_rate = Column(DECIMAL(5, 2), default=0)
    tax_amount = Column(DECIMAL(12, 2), default=0)
    discount_amount = Column(DECIMAL(12, 2), default=0)
    total_amount = Column(DECIMAL(12, 2), nullable=False)
    status = Column(String(20), default='unpaid')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(Date, nullable=True)

    # Relationships
    service_order = relationship("ServiceOrder", back_populates="invoice")
    customer = relationship("Customer", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice(id={self.id}, invoice_number='{self.invoice_number}', status='{self.status}')>"

    @property
    def amount_paid(self):
        """Calculate total amount paid using Decimal for precision"""
        from decimal import Decimal
        if not self.payments:
            return Decimal('0.00')
        return sum(Decimal(str(payment.amount)) for payment in self.payments)

    @property
    def balance_due(self):
        """Calculate remaining balance using Decimal for precision. Returns 0 if overpaid."""
        from decimal import Decimal
        balance = Decimal(str(self.total_amount)) - self.amount_paid
        return max(balance, Decimal('0.00'))
    
    @property
    def overpaid_amount(self):
        """Calculate overpaid amount (tips/extra payment). Returns 0 if not overpaid."""
        from decimal import Decimal
        balance = Decimal(str(self.total_amount)) - self.amount_paid
        return abs(min(balance, Decimal('0.00')))
    
    def update_status(self):
        """
        Automatically update invoice status based on balance.
        Call this after any payment or invoice modification.
        """
        from decimal import Decimal
        
        if self.status == 'cancelled':
            return  # Don't change cancelled invoices
        
        balance = self.balance_due.quantize(Decimal('0.01'))
        total_paid = self.amount_paid.quantize(Decimal('0.01'))
        
        if balance <= Decimal('0'):
            self.status = 'paid'
        elif total_paid > Decimal('0'):
            self.status = 'partial'
        else:
            self.status = 'unpaid'


class Payment(Base):
    """Payment records with partial payment support"""
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    payment_method = Column(String(20), nullable=False)
    reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    paid_at = Column(DateTime, default=datetime.utcnow)
    received_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    receiver = relationship("User", back_populates="payments_received")

    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount}, method='{self.payment_method}')>"
