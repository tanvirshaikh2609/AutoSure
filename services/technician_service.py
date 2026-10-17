"""
Technician Service
Business logic for technician management
"""

from sqlalchemy.orm import Session
from database.models import Technician
from typing import List, Optional, Tuple


class TechnicianService:
    """Service class for technician operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_technicians(self, active_only: bool = True) -> List[Technician]:
        """Get all technicians"""
        query = self.db.query(Technician)
        if active_only:
            query = query.filter(Technician.is_active == True)
        return query.order_by(Technician.name).all()
    
    def get_technician_by_id(self, technician_id: int) -> Optional[Technician]:
        """Get technician by ID"""
        return self.db.query(Technician).filter(Technician.id == technician_id).first()
    
    def get_technician_by_employee_id(self, employee_id: str) -> Optional[Technician]:
        """Get technician by employee ID"""
        return self.db.query(Technician).filter(Technician.employee_id == employee_id).first()
    
    def create_technician(self, name: str, employee_id: str, specialty: str = None,
                         hourly_rate: float = None, phone: str = None) -> Tuple[bool, str, Optional[Technician]]:
        """Create a new technician"""
        try:
            # Check if employee_id already exists
            existing = self.get_technician_by_employee_id(employee_id)
            if existing:
                return False, "Employee ID already exists", None
            
            technician = Technician(
                name=name,
                employee_id=employee_id,
                specialty=specialty,
                hourly_rate=hourly_rate,
                phone=phone,
                is_active=True
            )
            
            self.db.add(technician)
            self.db.commit()
            self.db.refresh(technician)
            
            return True, "Technician created successfully", technician
        
        except Exception as e:
            self.db.rollback()
            return False, f"Error creating technician: {str(e)}", None
    
    def update_technician(self, technician_id: int, **kwargs) -> Tuple[bool, str]:
        """Update technician information"""
        try:
            technician = self.get_technician_by_id(technician_id)
            if not technician:
                return False, "Technician not found"
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(technician, key) and value is not None:
                    setattr(technician, key, value)
            
            self.db.commit()
            return True, "Technician updated successfully"
        
        except Exception as e:
            self.db.rollback()
            return False, f"Error updating technician: {str(e)}"
    
    def deactivate_technician(self, technician_id: int) -> Tuple[bool, str]:
        """Deactivate a technician"""
        try:
            technician = self.get_technician_by_id(technician_id)
            if not technician:
                return False, "Technician not found"
            
            technician.is_active = False
            self.db.commit()
            
            return True, "Technician deactivated successfully"
        
        except Exception as e:
            self.db.rollback()
            return False, f"Error deactivating technician: {str(e)}"
    
    def activate_technician(self, technician_id: int) -> Tuple[bool, str]:
        """Activate a technician"""
        try:
            technician = self.get_technician_by_id(technician_id)
            if not technician:
                return False, "Technician not found"
            
            technician.is_active = True
            self.db.commit()
            
            return True, "Technician activated successfully"
        
        except Exception as e:
            self.db.rollback()
            return False, f"Error activating technician: {str(e)}"
    
    def search_technicians(self, search_term: str) -> List[Technician]:
        """Search technicians by name or employee ID"""
        search_pattern = f"%{search_term}%"
        return self.db.query(Technician).filter(
            (Technician.name.ilike(search_pattern)) |
            (Technician.employee_id.ilike(search_pattern))
        ).all()
