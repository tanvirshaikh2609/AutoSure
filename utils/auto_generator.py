"""
Auto-Generator Utilities
Generates unique identifiers for various entities (VIN, SKU, order numbers, invoice numbers)
"""

import random
import string
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Vehicle, Part, ServiceOrder, Invoice


class AutoGenerator:
    """Generates unique identifiers for entities."""
    
    def __init__(self, db_session: Session):
        """
        Initialize generator with database session.
        
        Args:
            db_session: SQLAlchemy session for uniqueness checks
        """
        self.db_session = db_session
    
    def generate_vin(self) -> str:
        """
        Generate a valid 17-character VIN-like identifier.
        
        Returns:
            17-character alphanumeric string
        
        Note:
            Format: 1HGBH41JXMN109186 (follows VIN structure)
            - Characters 1-3: World Manufacturer Identifier (WMI)
            - Characters 4-8: Vehicle Descriptor Section (VDS)
            - Character 9: Check digit
            - Character 10: Model year
            - Character 11: Plant code
            - Characters 12-17: Sequential number
        """
        # WMI (3 chars): Use 1HG for Honda-like format
        wmi = '1HG'
        
        # VDS (5 chars): Random alphanumeric (excluding I, O, Q)
        valid_chars = ''.join(c for c in string.ascii_uppercase + string.digits if c not in 'IOQ')
        vds = ''.join(random.choice(valid_chars) for _ in range(5))
        
        # Check digit (1 char): Use X as placeholder
        check_digit = 'X'
        
        # Model year (1 char): Use current year's last digit or letter code
        year_code = str(datetime.now().year)[-1]
        
        # Plant code (1 char): Random letter
        plant_code = random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')
        
        # Sequential number (6 chars): Random digits
        sequential = ''.join(random.choice(string.digits) for _ in range(6))
        
        vin = wmi + vds + check_digit + year_code + plant_code + sequential
        return vin
    
    def generate_sku(self, category: str = None) -> str:
        """
        Generate unique SKU/Product Code with category-based prefix and incremental count.
        Format: XXX-00# where XXX is 3-letter category prefix and 00# is incremental count.
        
        Args:
            category: Category name (e.g., "Fluids", "Filters", "Brakes")
        
        Returns:
            Unique SKU in format: OIL-001, BRK-005, etc.
        """
        # Category to prefix mapping
        category_prefixes = {
            'Electrical': 'ELC',
            'Exterior': 'EXT',
            'Filters': 'AIR',
            'Brakes': 'BRK',
            'Ignition': 'SPK',
            'Fluids': 'OIL'
        }
        
        # Get prefix from category or use generic
        if category and category in category_prefixes:
            prefix = category_prefixes[category]
        else:
            prefix = 'PRT'  # Generic part prefix
        
        # Find the highest existing number for this prefix
        existing_parts = self.db_session.query(Part).filter(
            Part.sku.like(f"{prefix}-%")
        ).all()
        
        # Extract numbers and find max
        max_num = 0
        for part in existing_parts:
            try:
                # Extract number from SKU (e.g., "OIL-005" -> 5)
                num_str = part.sku.split('-')[1]
                num = int(num_str)
                if num > max_num:
                    max_num = num
            except (IndexError, ValueError):
                continue
        
        # Increment for new SKU
        next_num = max_num + 1
        
        # Format with leading zeros (3 digits)
        sku = f"{prefix}-{next_num:03d}"
        return sku
    
    def generate_order_number(self) -> str:
        """
        Generate unique work order number.
        
        Returns:
            Unique order number in format: WO-YYYYMMDD-XXXX
        """
        date_str = datetime.now().strftime('%Y%m%d')
        sequence = ''.join(random.choice(string.digits) for _ in range(4))
        
        order_number = f"WO-{date_str}-{sequence}"
        return order_number
    
    def generate_invoice_number(self) -> str:
        """
        Generate unique invoice number.
        
        Returns:
            Unique invoice number in format: INV-YYYYMMDD-XXXX
        """
        date_str = datetime.now().strftime('%Y%m%d')
        sequence = ''.join(random.choice(string.digits) for _ in range(4))
        
        invoice_number = f"INV-{date_str}-{sequence}"
        return invoice_number
    
    def ensure_unique_vin(self, vin: str = None, max_attempts: int = 10) -> str:
        """
        Ensure VIN is unique, regenerate if needed.
        
        Args:
            vin: Proposed VIN (if None, generates new one)
            max_attempts: Maximum regeneration attempts
        
        Returns:
            Unique VIN
        
        Raises:
            ValueError: If cannot generate unique VIN after max_attempts with detailed message
        """
        if vin is None:
            vin = self.generate_vin()
        
        attempts = 0
        for attempt in range(max_attempts):
            attempts = attempt + 1
            
            # Check if VIN exists in database
            try:
                existing = self.db_session.query(Vehicle).filter(Vehicle.vin == vin).first()
                
                if not existing:
                    return vin
                
                # Regenerate if conflict found
                vin = self.generate_vin()
                
            except Exception as e:
                # Database query error
                raise ValueError(f"Database error while checking VIN uniqueness: {str(e)}")
        
        raise ValueError(
            f"Unable to generate unique VIN after {attempts} attempts. "
            f"This may indicate a system issue. Please try again or enter a VIN manually."
        )
    
    def ensure_unique_sku(self, sku: str = None, category: str = None, max_attempts: int = 10) -> str:
        """
        Ensure SKU is unique, regenerate if needed.
        Uses category-based prefix and incremental counting.
        
        Args:
            sku: Proposed SKU (if None, generates new one)
            category: Category for generation (e.g., "Fluids", "Filters")
            max_attempts: Maximum regeneration attempts
        
        Returns:
            Unique SKU in format XXX-00# (e.g., OIL-001, BRK-005)
        
        Raises:
            ValueError: If cannot generate unique SKU after max_attempts
        """
        if sku is None:
            sku = self.generate_sku(category)
        
        attempts = 0
        for attempt in range(max_attempts):
            attempts = attempt + 1
            
            # Check if SKU exists in database
            try:
                existing = self.db_session.query(Part).filter(Part.sku == sku).first()
                
                if not existing:
                    return sku
                
                # Regenerate if conflict found (should be rare with incremental logic)
                sku = self.generate_sku(category)
                
            except Exception as e:
                raise ValueError(f"Database error while checking SKU uniqueness: {str(e)}")
        
        raise ValueError(
            f"Unable to generate unique SKU after {attempts} attempts. "
            f"This may indicate a system issue. Please try again or enter a SKU manually."
        )
    
    def ensure_unique_order_number(self, order_number: str = None, max_attempts: int = 10) -> str:
        """
        Ensure order number is unique, regenerate if needed.
        
        Args:
            order_number: Proposed order number (if None, generates new one)
            max_attempts: Maximum regeneration attempts
        
        Returns:
            Unique order number
        
        Raises:
            ValueError: If cannot generate unique order number after max_attempts with detailed message
        """
        if order_number is None:
            order_number = self.generate_order_number()
        
        attempts = 0
        for attempt in range(max_attempts):
            attempts = attempt + 1
            
            # Check if order number exists in database
            try:
                existing = self.db_session.query(ServiceOrder).filter(
                    ServiceOrder.order_number == order_number
                ).first()
                
                if not existing:
                    return order_number
                
                # Regenerate if conflict found
                order_number = self.generate_order_number()
                
            except Exception as e:
                # Database query error
                raise ValueError(f"Database error while checking order number uniqueness: {str(e)}")
        
        raise ValueError(
            f"Unable to generate unique order number after {attempts} attempts. "
            f"This may indicate a system issue. Please try again or contact support."
        )
    
    def ensure_unique_invoice_number(self, invoice_number: str = None, max_attempts: int = 10) -> str:
        """
        Ensure invoice number is unique, regenerate if needed.
        
        Args:
            invoice_number: Proposed invoice number (if None, generates new one)
            max_attempts: Maximum regeneration attempts
        
        Returns:
            Unique invoice number
        
        Raises:
            ValueError: If cannot generate unique invoice number after max_attempts with detailed message
        """
        if invoice_number is None:
            invoice_number = self.generate_invoice_number()
        
        attempts = 0
        for attempt in range(max_attempts):
            attempts = attempt + 1
            
            # Check if invoice number exists in database
            try:
                existing = self.db_session.query(Invoice).filter(
                    Invoice.invoice_number == invoice_number
                ).first()
                
                if not existing:
                    return invoice_number
                
                # Regenerate if conflict found
                invoice_number = self.generate_invoice_number()
                
            except Exception as e:
                # Database query error
                raise ValueError(f"Database error while checking invoice number uniqueness: {str(e)}")
        
        raise ValueError(
            f"Unable to generate unique invoice number after {attempts} attempts. "
            f"This may indicate a system issue. Please try again or contact support."
        )
