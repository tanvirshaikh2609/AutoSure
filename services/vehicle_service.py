"""
Vehicle Service
Handles vehicle-related business logic
"""

from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.models import Vehicle, Customer


class VehicleService:
    """Service class for vehicle operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        """Get all vehicles with pagination"""
        return self.db.query(Vehicle).order_by(
            Vehicle.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        """Get a vehicle by ID"""
        return self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    def get_by_customer(self, customer_id: int) -> List[Vehicle]:
        """Get all vehicles for a customer"""
        return self.db.query(Vehicle).filter(
            Vehicle.customer_id == customer_id
        ).order_by(Vehicle.created_at.desc()).all()
    
    def search(self, query: str) -> List[Vehicle]:
        """Search vehicles by plate, VIN, make, or model"""
        search_term = f"%{query}%"
        return self.db.query(Vehicle).filter(
            or_(
                Vehicle.license_plate.ilike(search_term),
                Vehicle.vin.ilike(search_term),
                Vehicle.make.ilike(search_term),
                Vehicle.model.ilike(search_term)
            )
        ).all()
    
    def get_by_license_plate(self, plate: str) -> Optional[Vehicle]:
        """Get vehicle by license plate"""
        return self.db.query(Vehicle).filter(
            Vehicle.license_plate == plate.upper()
        ).first()
    
    def get_by_vin(self, vin: str) -> Optional[Vehicle]:
        """Get vehicle by VIN"""
        return self.db.query(Vehicle).filter(
            Vehicle.vin == vin.upper()
        ).first()
    
    def create(self, customer_id: int, make: str, model: str,
               year: int = None, vin: str = None, license_plate: str = None,
               color: str = None, current_mileage: int = None,
               notes: str = None) -> Tuple[Optional[Vehicle], str]:
        """
        Create a new vehicle.
        Returns (vehicle, message) tuple.
        """
        # Validate required fields
        if not make or not model:
            return None, "Make and model are required"
        
        # Check for duplicate VIN
        if vin:
            existing = self.get_by_vin(vin)
            if existing:
                return None, "A vehicle with this VIN already exists"
        
        # Check for duplicate license plate
        if license_plate:
            existing = self.get_by_license_plate(license_plate)
            if existing:
                return None, "A vehicle with this license plate already exists"
        
        # Validate year
        if year and (year < 1900 or year > datetime.now().year + 1):
            return None, "Invalid vehicle year"
        
        # Create vehicle
        vehicle = Vehicle(
            customer_id=customer_id,
            make=make.strip().title(),
            model=model.strip().title(),
            year=year,
            vin=vin.upper().strip() if vin else None,
            license_plate=license_plate.upper().strip() if license_plate else None,
            color=color.strip().title() if color else None,
            current_mileage=current_mileage,
            notes=notes.strip() if notes else None
        )
        
        self.db.add(vehicle)
        self.db.commit()
        self.db.refresh(vehicle)
        
        return vehicle, "Vehicle created successfully"
    
    def update(self, vehicle_id: int, **kwargs) -> Tuple[Optional[Vehicle], str]:
        """
        Update vehicle information.
        Returns (vehicle, message) tuple.
        """
        vehicle = self.get_by_id(vehicle_id)
        if not vehicle:
            return None, "Vehicle not found"
        
        # Update allowed fields
        allowed_fields = ['make', 'model', 'year', 'vin', 'license_plate', 
                          'color', 'current_mileage', 'notes', 'customer_id']
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                if isinstance(value, str):
                    value = value.strip()
                if key in ['vin', 'license_plate'] and value:
                    value = value.upper()
                if key in ['make', 'model', 'color'] and value:
                    value = value.title()
                setattr(vehicle, key, value)
        
        self.db.commit()
        self.db.refresh(vehicle)
        
        return vehicle, "Vehicle updated successfully"
    
    def update_mileage(self, vehicle_id: int, new_mileage: int) -> Tuple[bool, str]:
        """Update vehicle mileage"""
        vehicle = self.get_by_id(vehicle_id)
        if not vehicle:
            return False, "Vehicle not found"
        
        if new_mileage < (vehicle.current_mileage or 0):
            return False, "New mileage cannot be less than current mileage"
        
        vehicle.current_mileage = new_mileage
        self.db.commit()
        
        return True, "Mileage updated successfully"
    
    def delete(self, vehicle_id: int) -> Tuple[bool, str]:
        """
        Delete a vehicle.
        Returns (success, message) tuple.
        """
        vehicle = self.get_by_id(vehicle_id)
        if not vehicle:
            return False, "Vehicle not found"
        
        # Check for related service orders
        if vehicle.service_orders:
            return False, "Cannot delete vehicle with service history"
        
        self.db.delete(vehicle)
        self.db.commit()
        
        return True, "Vehicle deleted successfully"
    
    def get_service_history(self, vehicle_id: int) -> List:
        """Get service history for a vehicle"""
        vehicle = self.get_by_id(vehicle_id)
        if not vehicle:
            return []
        
        return vehicle.service_orders
    
    def get_count(self) -> int:
        """Get total vehicle count"""
        return self.db.query(Vehicle).count()
    
    def get_makes(self) -> List[str]:
        """Get list of unique makes in the system"""
        return [row[0] for row in self.db.query(Vehicle.make).distinct().all() if row[0]]
