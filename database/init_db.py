"""Create tables and seed demo data. Run once on a fresh database."""

import sys
import os
from decimal import Decimal
from passlib.context import CryptContext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, SessionLocal, Base
from database.models import (
    User, Customer, Vehicle, Technician, ServiceType, Part,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.\n")


def seed_users(db):
    print("Seeding users...")
    users = [
        ("admin", "admin@carservice.com", "Admin@123", "Rajesh Kumar", "admin"),
        ("manager", "manager@carservice.com", "Manager@123", "Priya Sharma", "manager"),
        ("cashier", "cashier@carservice.com", "Cashier@123", "Amit Patel", "cashier"),
        ("tech1", "tech1@carservice.com", "Tech@123", "Vikram Singh", "technician"),
        ("tech2", "tech2@carservice.com", "Tech@123", "Deepak Mehta", "technician"),
        ("tech3", "tech3@carservice.com", "Tech@123", "Suresh Rao", "technician"),
        ("tech4", "tech4@carservice.com", "Tech@123", "Anil Desai", "technician"),
        ("tech5", "tech5@carservice.com", "Tech@123", "Kiran Joshi", "technician"),
    ]
    for username, email, password, full_name, role in users:
        if db.query(User).filter(User.email == email).first():
            continue
        db.add(User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True,
        ))
    db.commit()
    print("Users seeded.\n")


def seed_technicians(db):
    print("Seeding technicians...")
    techs = [
        ("Vikram Singh", "TECH-001", "Engine & Transmission", Decimal("600.00"), "+91 98765 43201"),
        ("Deepak Mehta", "TECH-002", "Electrical & Electronics", Decimal("550.00"), "+91 98765 43202"),
        ("Suresh Rao", "TECH-003", "Brakes & Suspension", Decimal("500.00"), "+91 98765 43203"),
        ("Anil Desai", "TECH-004", "AC & Cooling Systems", Decimal("520.00"), "+91 98765 43204"),
        ("Kiran Joshi", "TECH-005", "General Service", Decimal("480.00"), "+91 98765 43205"),
    ]
    for name, emp_id, specialty, rate, phone in techs:
        if db.query(Technician).filter(Technician.employee_id == emp_id).first():
            continue
        db.add(Technician(name=name, employee_id=emp_id, specialty=specialty, hourly_rate=rate, phone=phone))
    db.commit()

    tech_users = db.query(User).filter(User.role == 'technician').all()
    technicians = db.query(Technician).all()
    for i, user in enumerate(tech_users):
        if i < len(technicians):
            user.technician_id = technicians[i].id
    db.commit()
    print("Technicians seeded.\n")


def seed_service_types(db):
    print("Seeding service catalog...")
    services = [
        ("Basic Car Wash", "Exterior wash and dry", "Cleaning", Decimal("0.5"), Decimal("200.00")),
        ("Engine Oil Change - Synthetic", "Synthetic oil change with filter", "Maintenance", Decimal("0.5"), Decimal("1200.00")),
        ("Brake Pad Replacement - Front", "Front brake pad replacement (labor)", "Brakes", Decimal("1.5"), Decimal("1200.00")),
        ("Tire Rotation", "Four tire rotation and pressure check", "Maintenance", Decimal("0.5"), Decimal("300.00")),
        ("Engine Diagnostic", "Computer diagnostic scan", "Diagnostics", Decimal("1.0"), Decimal("800.00")),
        ("AC Gas Recharge", "AC refrigerant recharge", "Climate Control", Decimal("1.0"), Decimal("1200.00")),
        ("Battery Replacement", "Battery test and replacement (labor)", "Electrical", Decimal("0.5"), Decimal("300.00")),
        ("Wheel Alignment", "Four-wheel alignment", "Suspension", Decimal("1.0"), Decimal("1000.00")),
    ]
    for name, desc, category, hours, price in services:
        if db.query(ServiceType).filter(ServiceType.name == name).first():
            continue
        db.add(ServiceType(name=name, description=desc, category=category, standard_hours=hours, base_price=price))
    db.commit()
    print("Service types seeded.\n")


def seed_parts(db):
    print("Seeding inventory...")
    parts = [
        ("OIL-001", "Engine Oil 5W-30 Synthetic (4L)", "Fluids", Decimal("1200.00"), Decimal("1800.00"), 50, 20),
        ("FLT-001", "Oil Filter - Standard", "Filters", Decimal("150.00"), Decimal("300.00"), 100, 30),
        ("BRK-001", "Brake Pads - Front Ceramic", "Brakes", Decimal("1200.00"), Decimal("2000.00"), 25, 10),
        ("ELC-001", "Car Battery 12V 65Ah", "Electrical", Decimal("3500.00"), Decimal("5500.00"), 12, 5),
        ("IGN-001", "Spark Plugs (Set of 4)", "Ignition", Decimal("600.00"), Decimal("1000.00"), 30, 10),
        ("EXT-001", "Wiper Blades (Pair)", "Exterior", Decimal("300.00"), Decimal("600.00"), 45, 15),
    ]
    for sku, name, category, cost, sell, stock, reorder in parts:
        if db.query(Part).filter(Part.sku == sku).first():
            continue
        db.add(Part(
            sku=sku, name=name, category=category,
            cost_price=cost, selling_price=sell,
            stock_quantity=stock, reorder_level=reorder,
            location="Shelf A-1", is_active=True,
        ))
    db.commit()
    print("Parts seeded.\n")


def seed_customers(db):
    print("Seeding customers...")
    customers = [
        ("Arjun Patel", "+91 98765 11111", "arjun.patel@email.com", "123 MG Road, Ahmedabad, Gujarat 380001", "regular"),
        ("Priya Desai", "+91 98765 22222", "priya.desai@email.com", "456 CG Road, Ahmedabad, Gujarat 380009", "vip"),
        ("Rahul Shah", "+91 98765 33333", "rahul.shah@email.com", "789 SG Highway, Ahmedabad, Gujarat 380015", "regular"),
        ("Neha Mehta", "+91 98765 44444", "neha.mehta@email.com", "321 Satellite Road, Ahmedabad, Gujarat 380015", "regular"),
        ("Gujarat Auto Parts Ltd", "+91 98765 55555", "orders@gujaratauto.com", "555 GIDC Estate, Vatva, Ahmedabad", "wholesale"),
    ]
    for name, phone, email, address, ctype in customers:
        if db.query(Customer).filter(Customer.email == email).first():
            continue
        db.add(Customer(name=name, phone=phone, email=email, address=address, customer_type=ctype))
    db.commit()
    print("Customers seeded.\n")


def seed_vehicles(db):
    print("Seeding vehicles...")
    customers = db.query(Customer).all()
    vehicles = [
        ("Maruti Suzuki", "Swift", 2022, "GJ01AB1234", "MA3EYD81S00123456", "Red", 15000),
        ("Hyundai", "Creta", 2021, "GJ01CD5678", "MALH11CKXM1234567", "White", 28000),
        ("Tata", "Nexon", 2023, "GJ01EF9012", "MAT622HPXN1234567", "Blue", 8000),
        ("Honda", "City", 2020, "GJ01GH3456", "MRHFB18120123456", "Silver", 45000),
        ("Mahindra", "Scorpio", 2019, "GJ01JK7890", "MA1TA2GKXJ1234567", "Black", 62000),
    ]
    for i, (make, model, year, plate, vin, color, mileage) in enumerate(vehicles):
        if i >= len(customers) or db.query(Vehicle).filter(Vehicle.license_plate == plate).first():
            continue
        db.add(Vehicle(
            customer_id=customers[i].id, make=make, model=model, year=year,
            license_plate=plate, vin=vin, color=color, current_mileage=mileage,
        ))
    db.commit()
    print("Vehicles seeded.\n")


def main():
    print("=" * 50)
    print("AutoSure — database setup")
    print("=" * 50 + "\n")

    create_tables()
    db = SessionLocal()
    try:
        seed_users(db)
        seed_technicians(db)
        seed_service_types(db)
        seed_parts(db)
        seed_customers(db)
        seed_vehicles(db)
        print("=" * 50)
        print("Done. Demo logins: admin@carservice.com / Admin@123")
        print("=" * 50)
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
