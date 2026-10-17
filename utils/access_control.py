"""
Access Control Module
Provides decorators and functions for enforcing role-based access control.
"""

import streamlit as st
from functools import wraps
from typing import Callable


# Permission mapping for pages
# Maps page names to required permissions
PAGE_PERMISSIONS = {
    'dashboard': ['all', 'reports', 'view_orders'],  # All roles
    'customers': ['all', 'customers'],                # Admin, Manager
    'vehicles': ['all', 'vehicles'],                  # Admin, Manager
    'service_orders': ['all', 'orders', 'view_orders'],  # Admin, Manager, Technician
    'inventory': ['all', 'inventory', 'view_inventory'],  # Admin, Manager, Technician (view)
    'pos': ['all', 'pos'],                            # Admin, Manager, Cashier
    'invoices': ['all', 'invoices'],                  # Admin, Manager, Cashier
    'reports': ['all', 'reports'],                    # Admin, Manager
}


def check_page_access(user: dict, page_name: str) -> bool:
    """
    Check if user has access to a specific page.
    
    Args:
        user: User dict from session state with 'role' key
        page_name: Name of the page (e.g., 'dashboard', 'customers')
    
    Returns:
        True if user has access, False otherwise
    """
    if not user or 'role' not in user:
        return False
    
    # Normalize page name to lowercase and remove spaces
    page_name = page_name.lower().replace(' ', '_')
    
    # Get required permissions for the page
    required_permissions = PAGE_PERMISSIONS.get(page_name, [])
    
    # If no permissions defined, deny access by default
    if not required_permissions:
        return False
    
    # Admin role has 'all' permission
    if user['role'] == 'admin':
        return True
    
    # Check if user has any of the required permissions
    # This uses the auth_service.has_permission logic
    from services.auth_service import AuthService
    
    # Create a mock User object for permission checking
    # We need to check against the permission system
    user_permissions = _get_user_permissions(user['role'])
    
    # Check if user has any of the required permissions
    for permission in required_permissions:
        if permission in user_permissions:
            return True
    
    return False


def _get_user_permissions(role: str) -> list:
    """
    Get list of permissions for a role.
    Internal helper function.
    
    Args:
        role: User role (admin, manager, technician, cashier)
    
    Returns:
        List of permission strings
    """
    permissions = {
        'admin': ['all', 'manage_users', 'delete', 'reports', 'settings', 
                  'customers', 'vehicles', 'orders', 'inventory', 'pos', 'invoices'],
        'manager': ['reports', 'customers', 'vehicles', 'orders', 'inventory', 
                    'pos', 'invoices', 'view_all_orders'],
        'technician': ['view_orders', 'update_order_status', 'view_inventory'],
        'cashier': ['pos', 'invoices', 'view_orders', 'customer_search']
    }
    
    return permissions.get(role, [])


def get_accessible_pages(user: dict) -> list:
    """
    Get list of pages accessible to user based on role.
    
    Args:
        user: User dict from session state
    
    Returns:
        List of page names user can access
    """
    if not user or 'role' not in user:
        return []
    
    accessible = []
    for page_name in PAGE_PERMISSIONS.keys():
        if check_page_access(user, page_name):
            accessible.append(page_name)
    
    return accessible


def show_permission_error(page_name: str = None):
    """
    Display friendly permission denied message.
    
    Args:
        page_name: Name of the page user tried to access (optional)
    """
    st.error("🚫 Access Denied")
    st.warning(
        "You don't have permission to access this page. "
        "Contact your administrator if you need access."
    )
    
    if page_name:
        st.info(f"Attempted to access: **{page_name.replace('_', ' ').title()}**")
    
    # Show accessible pages
    if 'user' in st.session_state:
        accessible = get_accessible_pages(st.session_state.user)
        if accessible:
            st.markdown("### Pages you can access:")
            for page in accessible:
                st.markdown(f"- {page.replace('_', ' ').title()}")
    
    st.stop()


def require_permission(permission: str) -> Callable:
    """
    Decorator for page-level access control.
    
    Args:
        permission: Permission string to check (e.g., 'orders', 'pos', 'manage_users')
    
    Returns:
        Decorator function that checks permission before rendering page
    
    Raises:
        Stops Streamlit execution if user lacks permission
    
    Example:
        @require_permission('customers')
        def main():
            st.title("Customers")
            # Page content here
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if user is logged in
            if 'user' not in st.session_state:
                st.error("🔒 Please log in to access this page")
                st.stop()
                return
            
            user = st.session_state.user
            
            # Check if user has the required permission
            user_permissions = _get_user_permissions(user.get('role', ''))
            
            # Admin has all permissions
            if 'all' in user_permissions:
                return func(*args, **kwargs)
            
            # Check if user has the specific permission
            if permission not in user_permissions:
                # Try to determine page name from function or module
                page_name = func.__name__ if func.__name__ != 'wrapper' else permission
                show_permission_error(page_name)
                return
            
            # User has permission, execute the function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
