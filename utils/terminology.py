"""
Terminology Mapper Module
Handles bidirectional mapping between business terms and user-friendly terms.
"""

from typing import Optional


# Default terminology mappings
# Maps business/database terms to user-friendly display terms
DEFAULT_MAPPINGS = {
    'sku': 'Product Code',
    'vin': 'Vehicle ID',
    'pos': 'Quick Sale',
    'service_order': 'Work Order',
    'wholesale': 'Business',
    'vip': 'Premium',
    'regular': 'Standard',
}

# Tooltips and help text for terms
TOOLTIPS = {
    'sku': 'Unique code to identify this part in inventory',
    'vin': 'Unique 17-character identifier for the vehicle',
    'product_code': 'Unique code to identify this part in inventory',
    'vehicle_id': 'Unique 17-character identifier for the vehicle',
    'reorder_level': 'Stock quantity that triggers a reorder alert',
    'customer_type': 'Business: wholesale pricing, Premium: VIP benefits, Standard: regular pricing',
    'work_order': 'Service request for vehicle maintenance or repair',
    'quick_sale': 'Fast checkout for parts and services',
}


class TerminologyMapper:
    """Maps business terminology to user-friendly terms and vice versa."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize mapper with default or custom terminology.
        
        Args:
            config_path: Optional path to custom terminology config JSON
        """
        self.mappings = DEFAULT_MAPPINGS.copy()
        self.tooltips = TOOLTIPS.copy()
        
        # Create reverse mapping for database lookups
        self._reverse_mappings = {v.lower(): k for k, v in self.mappings.items()}
        
        # Load custom configuration if provided
        if config_path:
            self._load_config(config_path)
    
    def _load_config(self, config_path: str):
        """
        Load custom terminology configuration from JSON file.
        
        Args:
            config_path: Path to configuration JSON file
        """
        try:
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Update mappings if provided
            if 'terminology' in config:
                self.mappings.update(config['terminology'])
                # Rebuild reverse mappings
                self._reverse_mappings = {v.lower(): k for k, v in self.mappings.items()}
            
            # Update tooltips if provided
            if 'tooltips' in config:
                self.tooltips.update(config['tooltips'])
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Fall back to defaults if config loading fails
            print(f"Warning: Could not load terminology config from {config_path}: {e}")
            print("Using default terminology mappings.")
    
    def to_display(self, term: str, context: Optional[str] = None) -> str:
        """
        Convert database/business term to display term.
        
        Args:
            term: Business term (e.g., 'sku', 'vin', 'pos')
            context: Optional context for disambiguation
        
        Returns:
            User-friendly term (e.g., 'Product Code', 'Vehicle ID')
        """
        if not term:
            return term
        
        # Normalize term to lowercase for lookup
        normalized_term = term.lower().strip()
        
        # Return mapped term or original if no mapping exists
        return self.mappings.get(normalized_term, term)
    
    def to_database(self, term: str) -> str:
        """
        Convert display term back to database field name.
        
        Args:
            term: Display term
        
        Returns:
            Database field name
        """
        if not term:
            return term
        
        # Normalize term to lowercase for lookup
        normalized_term = term.lower().strip()
        
        # Return reverse mapped term or original if no mapping exists
        return self._reverse_mappings.get(normalized_term, term)
    
    def get_tooltip(self, term: str) -> str:
        """
        Get tooltip/help text for a term.
        
        Args:
            term: Term to get help for
        
        Returns:
            Help text explaining the term
        """
        if not term:
            return ""
        
        # Normalize term to lowercase for lookup
        normalized_term = term.lower().strip()
        
        # Try to find tooltip for the term
        tooltip = self.tooltips.get(normalized_term, "")
        
        # If no tooltip found, try the display version of the term
        if not tooltip:
            display_term = self.to_display(term)
            tooltip = self.tooltips.get(display_term.lower(), "")
        
        return tooltip
    
    def get_customer_type_display(self, db_type: str) -> str:
        """
        Convert customer type to display format.
        
        Args:
            db_type: Database customer type ('wholesale', 'vip', 'regular')
        
        Returns:
            Display type ('Business', 'Premium', 'Standard')
        """
        if not db_type:
            return db_type
        
        # Use the general to_display method for customer types
        return self.to_display(db_type)
    
    def get_customer_type_database(self, display_type: str) -> str:
        """
        Convert display customer type to database format.
        
        Args:
            display_type: Display type
        
        Returns:
            Database type
        """
        if not display_type:
            return display_type
        
        # Use the general to_database method for customer types
        return self.to_database(display_type)
