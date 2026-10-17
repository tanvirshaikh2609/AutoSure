"""
Inventory Service
Handles parts/inventory-related business logic
"""

from datetime import datetime
from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database.models import Part


class InventoryService:
    """Service class for inventory operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_sku(self, category: str) -> str:
        """Generate SKU based on category with auto-increment"""
        from config import app_config
        
        prefix = app_config.CATEGORY_CODE_MAP.get(category, 'GEN')
        
        # Count existing parts in category
        count = self.db.query(Part).filter(
            Part.sku.like(f"{prefix}-%")
        ).count() + 1
        
        return f"{prefix}-{count:03d}"
    
    def get_all(self, skip: int = 0, limit: int = 100,
                active_only: bool = True) -> List[Part]:
        """Get all parts with pagination"""
        query = self.db.query(Part)
        
        if active_only:
            query = query.filter(Part.is_active == True)
        
        return query.order_by(Part.name).offset(skip).limit(limit).all()
    
    def get_by_id(self, part_id: int) -> Optional[Part]:
        """Get a part by ID"""
        return self.db.query(Part).filter(Part.id == part_id).first()
    
    def get_by_sku(self, sku: str) -> Optional[Part]:
        """Get a part by SKU"""
        return self.db.query(Part).filter(Part.sku == sku.upper()).first()
    
    def search(self, query: str) -> List[Part]:
        """Search parts by SKU, name, or category"""
        search_term = f"%{query}%"
        return self.db.query(Part).filter(
            and_(
                Part.is_active == True,
                or_(
                    Part.sku.ilike(search_term),
                    Part.name.ilike(search_term),
                    Part.category.ilike(search_term)
                )
            )
        ).order_by(Part.name).all()
    
    def get_by_category(self, category: str) -> List[Part]:
        """Get parts by category"""
        return self.db.query(Part).filter(
            Part.category == category,
            Part.is_active == True
        ).order_by(Part.name).all()
    
    def get_categories(self) -> List[str]:
        """Get list of all categories"""
        return [row[0] for row in self.db.query(Part.category).distinct().all() if row[0]]
    
    def create(self, sku: str, name: str, selling_price: float,
               category: str = None, description: str = None,
               cost_price: float = None, stock_quantity: int = 0,
               reorder_level: int = 10, location: str = None,
               supplier: str = None) -> Tuple[Optional[Part], str]:
        """
        Create a new part.
        Returns (part, message) tuple.
        """
        # Validate required fields
        if not sku or not name:
            return None, "SKU and name are required"
        
        if selling_price is None or selling_price < 0:
            return None, "Valid selling price is required"
        
        # Check for duplicate SKU
        if self.get_by_sku(sku):
            return None, "A part with this SKU already exists"
        
        # Create part
        part = Part(
            sku=sku.upper().strip(),
            name=name.strip(),
            category=category.strip() if category else None,
            description=description.strip() if description else None,
            cost_price=cost_price,
            selling_price=selling_price,
            stock_quantity=stock_quantity,
            reorder_level=reorder_level,
            location=location.strip() if location else None,
            supplier=supplier.strip() if supplier else None,
            is_active=True
        )
        
        self.db.add(part)
        self.db.commit()
        self.db.refresh(part)
        
        return part, "Part created successfully"
    
    def update(self, part_id: int, **kwargs) -> Tuple[Optional[Part], str]:
        """
        Update part information.
        Returns (part, message) tuple.
        """
        part = self.get_by_id(part_id)
        if not part:
            return None, "Part not found"
        
        allowed_fields = ['name', 'category', 'description', 'cost_price',
                          'selling_price', 'stock_quantity', 'reorder_level',
                          'location', 'supplier', 'is_active']
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(part, key, value)
        
        part.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(part)
        
        return part, "Part updated successfully"
    
    def adjust_stock(self, part_id: int, quantity: int,
                     reason: str = None) -> Tuple[Optional[Part], str]:
        """
        Adjust stock quantity (positive or negative).
        Returns (part, message) tuple.
        """
        part = self.get_by_id(part_id)
        if not part:
            return None, "Part not found"
        
        new_quantity = part.stock_quantity + quantity
        
        if new_quantity < 0:
            return None, "Insufficient stock for this adjustment"
        
        part.stock_quantity = new_quantity
        part.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(part)
        
        direction = "added" if quantity > 0 else "removed"
        return part, f"Stock adjusted: {abs(quantity)} units {direction}"
    
    def get_low_stock(self) -> List[Part]:
        """Get parts that are at or below reorder level"""
        return self.db.query(Part).filter(
            Part.stock_quantity <= Part.reorder_level,
            Part.is_active == True
        ).order_by(Part.stock_quantity).all()
    
    def get_out_of_stock(self) -> List[Part]:
        """Get parts with zero stock"""
        return self.db.query(Part).filter(
            Part.stock_quantity <= 0,
            Part.is_active == True
        ).order_by(Part.name).all()
    
    def delete(self, part_id: int) -> Tuple[bool, str]:
        """Soft delete a part (deactivate)"""
        part = self.get_by_id(part_id)
        if not part:
            return False, "Part not found"
        
        # Check if part is used in any orders
        if part.order_parts:
            part.is_active = False
            self.db.commit()
            return True, "Part deactivated (has order history)"
        
        self.db.delete(part)
        self.db.commit()
        return True, "Part deleted successfully"
    
    def get_inventory_value(self) -> Dict:
        """Calculate total inventory value"""
        parts = self.db.query(Part).filter(Part.is_active == True).all()
        
        cost_value = sum(
            (p.cost_price or 0) * p.stock_quantity for p in parts
        )
        retail_value = sum(
            p.selling_price * p.stock_quantity for p in parts
        )
        
        return {
            'total_parts': len(parts),
            'total_units': sum(p.stock_quantity for p in parts),
            'cost_value': cost_value,
            'retail_value': retail_value,
            'potential_profit': retail_value - cost_value
        }
    
    def get_count(self, active_only: bool = True) -> int:
        """Get total part count"""
        query = self.db.query(Part)
        if active_only:
            query = query.filter(Part.is_active == True)
        return query.count()
    
    def bulk_import(self, parts_data: List[Dict]) -> Tuple[int, List[str]]:
        """
        Bulk import parts.
        Returns (success_count, error_messages) tuple.
        """
        success_count = 0
        errors = []
        
        for i, data in enumerate(parts_data):
            part, msg = self.create(**data)
            if part:
                success_count += 1
            else:
                errors.append(f"Row {i+1}: {msg}")
        
        return success_count, errors
