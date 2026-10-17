"""
Authentication Service
Handles user authentication, session management, and role-based access
"""

from datetime import datetime
from typing import Optional, Tuple
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database.models import User

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def authenticate_user(self, email: str, password: str) -> Tuple[Optional[User], str]:
        """
        Authenticate a user by email and password.
        Returns (user, message) tuple.
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            return None, "User not found"
        
        if not user.is_active:
            return None, "User account is deactivated"
        
        if not self.verify_password(password, user.password_hash):
            return None, "Invalid password"
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        return user, "Authentication successful"
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def create_user(self, username: str, email: str, password: str, 
                    full_name: str, role: str = 'cashier') -> Tuple[Optional[User], str]:
        """
        Create a new user.
        Returns (user, message) tuple.
        """
        # Check if email exists
        if self.get_user_by_email(email):
            return None, "Email already registered"
        
        # Check if username exists
        if self.get_user_by_username(username):
            return None, "Username already taken"
        
        # Validate role
        valid_roles = ['admin', 'manager', 'technician', 'cashier']
        if role not in valid_roles:
            return None, f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user, "User created successfully"
    
    def update_user(self, user_id: int, **kwargs) -> Tuple[Optional[User], str]:
        """
        Update user information.
        Returns (user, message) tuple.
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None, "User not found"
        
        # Update allowed fields
        allowed_fields = ['full_name', 'phone', 'role', 'is_active']
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user, "User updated successfully"
    
    def change_password(self, user_id: int, current_password: str, 
                        new_password: str) -> Tuple[bool, str]:
        """
        Change user password.
        Returns (success, message) tuple.
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        if not self.verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect"
        
        user.password_hash = self.hash_password(new_password)
        self.db.commit()
        
        return True, "Password changed successfully"
    
    def deactivate_user(self, user_id: int) -> Tuple[bool, str]:
        """Deactivate a user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        user.is_active = False
        self.db.commit()
        
        return True, "User deactivated successfully"
    
    def get_all_users(self, active_only: bool = True) -> list:
        """Get all users"""
        query = self.db.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        return query.order_by(User.created_at.desc()).all()
    
    def get_users_by_role(self, role: str) -> list:
        """Get users by role"""
        return self.db.query(User).filter(
            User.role == role,
            User.is_active == True
        ).all()
    
    def has_permission(self, user: User, permission: str) -> bool:
        """
        Check if user has a specific permission.
        Permission levels: admin > manager > technician/cashier
        """
        permissions = {
            'admin': ['all', 'manage_users', 'delete', 'reports', 'settings', 
                      'customers', 'vehicles', 'orders', 'inventory', 'pos', 'invoices'],
            'manager': ['reports', 'customers', 'vehicles', 'orders', 'inventory', 
                        'pos', 'invoices', 'view_all_orders'],
            'technician': ['view_orders', 'update_order_status', 'view_inventory'],
            'cashier': ['pos', 'invoices', 'view_orders', 'customer_search']
        }
        
        user_permissions = permissions.get(user.role, [])
        return 'all' in user_permissions or permission in user_permissions
