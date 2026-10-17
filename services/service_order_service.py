"""
Service Order Service
Handles service order-related business logic
"""

from datetime import datetime, date
from typing import Optional, List, Tuple, Dict
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import and_, select

from database.models import ServiceOrder, ServiceItem, OrderPart, Part
from utils.auto_generator import AutoGenerator


class ServiceOrderService:
    """Service class for service order operations"""
    
    STATUS_FLOW = ['pending', 'in_progress', 'waiting_parts', 'completed', 'invoiced', 'cancelled']
    
    def __init__(self, db: Session):
        self.db = db
        self.auto_generator = AutoGenerator(db)
    
    def generate_order_number(self) -> str:
        """Generate a unique order number using AutoGenerator"""
        return self.auto_generator.ensure_unique_order_number()
    
    def get_all(self, skip: int = 0, limit: int = 100, 
                status: str = None) -> List[ServiceOrder]:
        """Get all service orders with optional filtering"""
        query = self.db.query(ServiceOrder)
        
        if status:
            query = query.filter(ServiceOrder.status == status)
        
        return query.order_by(
            ServiceOrder.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_by_id(self, order_id: int) -> Optional[ServiceOrder]:
        """Get a service order by ID"""
        return self.db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    
    def get_by_number(self, order_number: str) -> Optional[ServiceOrder]:
        """Get a service order by order number"""
        return self.db.query(ServiceOrder).filter(
            ServiceOrder.order_number == order_number
        ).first()
    
    def get_by_customer(self, customer_id: int) -> List[ServiceOrder]:
        """Get all orders for a customer"""
        return self.db.query(ServiceOrder).filter(
            ServiceOrder.customer_id == customer_id
        ).order_by(ServiceOrder.created_at.desc()).all()
    
    def get_by_vehicle(self, vehicle_id: int) -> List[ServiceOrder]:
        """Get all orders for a vehicle"""
        return self.db.query(ServiceOrder).filter(
            ServiceOrder.vehicle_id == vehicle_id
        ).order_by(ServiceOrder.created_at.desc()).all()
    
    def get_by_technician(self, technician_id: int, 
                          active_only: bool = True) -> List[ServiceOrder]:
        """Get orders assigned to a technician"""
        query = self.db.query(ServiceOrder).filter(
            ServiceOrder.technician_id == technician_id
        )
        
        if active_only:
            query = query.filter(
                ServiceOrder.status.in_(['pending', 'in_progress', 'waiting_parts'])
            )
        
        return query.order_by(ServiceOrder.created_at.desc()).all()
    
    def create(self, customer_id: int, vehicle_id: int,
               complaint: str = None, technician_id: int = None,
               estimated_completion: date = None, notes: str = None
               ) -> Tuple[Optional[ServiceOrder], str]:
        """
        Create a new service order.
        Returns (order, message) tuple.
        """
        order = ServiceOrder(
            order_number=self.generate_order_number(),
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            technician_id=technician_id,
            complaint=complaint.strip() if complaint else None,
            estimated_completion=estimated_completion,
            notes=notes.strip() if notes else None,
            status='pending'
        )
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        return order, "Service order created successfully"
    
    def update_status(self, order_id: int, new_status: str,
                      diagnosis: str = None) -> Tuple[Optional[ServiceOrder], str]:
        """
        Update service order status.
        Returns (order, message) tuple.
        """
        order = self.get_by_id(order_id)
        if not order:
            return None, "Service order not found"
        
        if new_status not in self.STATUS_FLOW:
            return None, f"Invalid status. Valid options: {', '.join(self.STATUS_FLOW)}"
        
        order.status = new_status
        
        if diagnosis:
            order.diagnosis = diagnosis.strip()
        
        if new_status == 'completed':
            order.completed_at = datetime.utcnow()
            # Calculate final totals
            order.calculate_totals()
        
        self.db.commit()
        self.db.refresh(order)
        
        return order, f"Status updated to '{new_status}'"
    
    def assign_technician(self, order_id: int, 
                          technician_id: int) -> Tuple[Optional[ServiceOrder], str]:
        """Assign a technician to an order"""
        order = self.get_by_id(order_id)
        if not order:
            return None, "Service order not found"
        
        order.technician_id = technician_id
        self.db.commit()
        self.db.refresh(order)
        
        return order, "Technician assigned successfully"
    
    def add_service_item(self, order_id: int, service_type_id: int,
                         labor_hours: float = None, labor_rate: float = None,
                         description: str = None) -> Tuple[Optional[ServiceItem], str]:
        """Add a service item to an order"""
        order = self.get_by_id(order_id)
        if not order:
            return None, "Service order not found"
        
        # Calculate labor cost
        labor_cost = None
        if labor_hours and labor_rate:
            labor_cost = labor_hours * labor_rate
        
        item = ServiceItem(
            service_order_id=order_id,
            service_type_id=service_type_id,
            description=description,
            labor_hours=labor_hours,
            labor_rate=labor_rate,
            labor_cost=labor_cost,
            status='pending'
        )
        
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        
        # Update order totals
        order.calculate_totals()
        self.db.commit()
        
        return item, "Service item added successfully"
    
    def add_part(self, order_id: int, part_id: int, 
                 quantity: int = 1) -> Tuple[Optional[OrderPart], str]:
        """Add a part to an order with atomic stock deduction"""
        order = self.get_by_id(order_id)
        if not order:
            return None, "Service order not found"
        
        # ATOMIC: Lock the part row before checking/updating stock
        stmt = select(Part).where(Part.id == part_id).with_for_update()
        part = self.db.execute(stmt).scalar_one_or_none()
        
        if not part:
            return None, "Part not found"
        
        if part.stock_quantity < quantity:
            return None, f"Insufficient stock. Available: {part.stock_quantity}"
        
        # Calculate prices using Decimal
        unit_price = Decimal(str(part.selling_price))
        total_price = (unit_price * Decimal(str(quantity))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Create order part
        order_part = OrderPart(
            service_order_id=order_id,
            part_id=part_id,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price
        )
        
        # Deduct from inventory (row is locked, safe to update)
        part.stock_quantity -= quantity
        
        self.db.add(order_part)
        self.db.commit()
        self.db.refresh(order_part)
        
        # Update order totals
        order.calculate_totals()
        self.db.commit()
        
        return order_part, "Part added to order successfully"
    
    def remove_part(self, order_part_id: int) -> Tuple[bool, str]:
        """Remove a part from an order and return to inventory"""
        order_part = self.db.query(OrderPart).filter(
            OrderPart.id == order_part_id
        ).first()
        
        if not order_part:
            return False, "Order part not found"
        
        # Return to inventory
        part = order_part.part
        part.stock_quantity += order_part.quantity
        
        # Get order for recalculation
        order = order_part.service_order
        
        self.db.delete(order_part)
        self.db.commit()
        
        # Recalculate totals
        order.calculate_totals()
        self.db.commit()
        
        return True, "Part removed and returned to inventory"
    
    def update_order(self, order_id: int, **kwargs) -> Tuple[Optional[ServiceOrder], str]:
        """Update order details"""
        order = self.get_by_id(order_id)
        if not order:
            return None, "Service order not found"
        
        allowed_fields = ['complaint', 'diagnosis', 'notes', 'estimated_completion',
                          'technician_id']
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(order, key, value)
        
        self.db.commit()
        self.db.refresh(order)
        
        return order, "Order updated successfully"
    
    def delete(self, order_id: int) -> Tuple[bool, str]:
        """Delete a service order (only if pending)"""
        order = self.get_by_id(order_id)
        if not order:
            return False, "Service order not found"
        
        if order.status not in ['pending', 'cancelled']:
            return False, "Cannot delete orders that are in progress or completed"
        
        # Return parts to inventory
        for order_part in order.order_parts:
            order_part.part.stock_quantity += order_part.quantity
        
        self.db.delete(order)
        self.db.commit()
        
        return True, "Service order deleted successfully"
    
    def get_statistics(self, days: int = 30) -> Dict:
        """Get order statistics for dashboard"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        orders = self.db.query(ServiceOrder).filter(
            ServiceOrder.created_at >= start_date
        ).all()
        
        status_counts = {}
        for status in self.STATUS_FLOW:
            status_counts[status] = len([o for o in orders if o.status == status])
        
        total_revenue = sum(
            o.total_amount or 0 for o in orders 
            if o.status in ['completed', 'invoiced']
        )
        
        return {
            'total_orders': len(orders),
            'status_breakdown': status_counts,
            'total_revenue': total_revenue,
            'average_order_value': total_revenue / len(orders) if orders else 0,
            'period_days': days
        }
    
    def get_count(self, status: str = None) -> int:
        """Get order count"""
        query = self.db.query(ServiceOrder)
        if status:
            query = query.filter(ServiceOrder.status == status)
        return query.count()
    
    def get_active_count(self) -> int:
        """Get count of active orders"""
        return self.db.query(ServiceOrder).filter(
            ServiceOrder.status.in_(['pending', 'in_progress', 'waiting_parts'])
        ).count()
