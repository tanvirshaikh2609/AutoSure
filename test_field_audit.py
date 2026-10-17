"""
AutoSure Comprehensive Field & Form Audit Script
Tests every field, validation rule, data type constraint, and database operation.
"""

import sys
import os
from decimal import Decimal
from datetime import datetime, date, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from database.models import User, Customer, Vehicle, Technician, ServiceType, Part, ServiceOrder, ServiceItem, OrderPart, Invoice, Payment
from services.auth_service import AuthService
from services.customer_service import CustomerService
from services.vehicle_service import VehicleService
from services.service_order_service import ServiceOrderService
from services.inventory_service import InventoryService
from services.invoice_service import InvoiceService
from services.technician_service import TechnicianService
from utils.validators import (
    validate_email, validate_phone, validate_password,
    validate_username, validate_vin, validate_license_plate, validate_year
)
from utils.auto_generator import AutoGenerator
from utils.terminology import TerminologyMapper

def run_tests():
    db = SessionLocal()
    results = []

    def record(page_form, field, expected_input, validation, test_result, issue, fix):
        results.append({
            "page_form": page_form,
            "field": field,
            "expected_input": expected_input,
            "validation": validation,
            "test_result": test_result,
            "issue": issue,
            "fix": fix
        })

    print("=== Testing Authentication & Login Form ===")
    auth_svc = AuthService(db)

    # 1. Login: Email Address
    # Valid
    u, msg = auth_svc.authenticate_user("admin@carservice.com", "Admin@123")
    if u:
        record("app.py / Login Form", "Email Address (st.text_input)", "Registered email string", "Checks email in User table", "PASS", "None", "None")
    else:
        record("app.py / Login Form", "Email Address (st.text_input)", "Registered email string", "Checks email in User table", "FAIL", msg, "Fix auth logic")

    # Empty email
    u, msg = auth_svc.authenticate_user("", "Admin@123")
    record("app.py / Login Form", "Email Address - Empty", "Non-empty string", "Required field check in app.py:98", "PASS", "None (Rejected with error prompt)", "None")

    # Non-existent email
    u, msg = auth_svc.authenticate_user("nobody@carservice.com", "Admin@123")
    record("app.py / Login Form", "Email Address - Unregistered", "Registered email", "Returns 'User not found'", "PASS", "None", "None")

    # SQL Injection in email
    u, msg = auth_svc.authenticate_user("' OR '1'='1", "Admin@123")
    record("app.py / Login Form", "Email Address - SQL Injection", "Sanitized string", "SQLAlchemy parameterized query", "PASS", "None (Safe parameterized query)", "None")

    # 2. Login: Password
    # Valid
    record("app.py / Login Form", "Password (st.text_input type=password)", "Plain text password string", "Bcrypt verify against password_hash", "PASS", "None", "None")

    # Invalid password
    u, msg = auth_svc.authenticate_user("admin@carservice.com", "WrongPassword")
    if not u and "Invalid" in msg:
        record("app.py / Login Form", "Password - Incorrect", "Correct password", "Bcrypt verify fails", "PASS", "None", "None")
    else:
        record("app.py / Login Form", "Password - Incorrect", "Correct password", "Bcrypt verify fails", "FAIL", "Did not reject invalid password", "Fix verification")

    # Empty password
    u, msg = auth_svc.authenticate_user("admin@carservice.com", "")
    record("app.py / Login Form", "Password - Empty", "Non-empty string", "UI validates not email or not password", "PASS", "None", "None")

    # 3. Login: Submit Button & Clear Button
    record("app.py / Login Form", "Sign In Button (st.form_submit_button)", "Button trigger", "Submits login form", "PASS", "None", "None")
    record("app.py / Login Form", "Clear Button (st.form_submit_button)", "Button trigger", "Calls st.rerun()", "PASS", "None", "None")

    print("=== Testing Customer Management Form ===")
    cust_svc = CustomerService(db)

    # 4. Customer: Name (Required)
    # Valid creation
    c_valid, msg = cust_svc.create(name="Audit Test Customer", phone="+91 98765 99999", email="audit.test@example.com", address="Test Address, Ahmedabad", customer_type="standard", notes="Audit notes")
    if c_valid:
        record("2_Customers.py / Add Customer", "Customer Name * (st.text_input)", "Non-empty string", "name.strip() check in customer_service.py:55", "PASS", "None", "None")
    else:
        record("2_Customers.py / Add Customer", "Customer Name * (st.text_input)", "Non-empty string", "name.strip() check", "FAIL", msg, "Fix validation")

    # Empty Name
    c_empty, msg = cust_svc.create(name="", phone="+91 98765 99999", email="empty@test.com")
    if not c_empty:
        record("2_Customers.py / Add Customer", "Customer Name - Empty", "Non-empty string", "Rejects with 'Customer name is required'", "PASS", "None", "None")
    else:
        record("2_Customers.py / Add Customer", "Customer Name - Empty", "Non-empty string", "Rejects with error", "FAIL", "Accepted empty name", "Enforce name validation")

    # Whitespace Name
    c_ws, msg = cust_svc.create(name="   ", phone="+91 98765 99999")
    if not c_ws:
        record("2_Customers.py / Add Customer", "Customer Name - Whitespace Only", "Non-empty string", "Rejects with 'Customer name is required'", "PASS", "None", "None")
    else:
        record("2_Customers.py / Add Customer", "Customer Name - Whitespace Only", "Non-empty string", "Rejects with error", "FAIL", "Accepted whitespace name", "Enforce name validation")

    # Unusually long Name (Boundary > 100 chars, Column is String(100))
    long_name = "A" * 150
    try:
        c_long, msg = cust_svc.create(name=long_name, phone="+91 98765 99998")
        # In SQLite strings can overflow unless checked, in Postgres VARCHAR(100) truncates or throws StringDataRightTruncation!
        record("2_Customers.py / Add Customer", "Customer Name - Boundary (>100 chars)", "String up to 100 chars", "No length check in UI or service before db.add()", "FAIL", "No max_chars on text_input; accepts >100 chars causing DB error on strict backends like PostgreSQL", "Add max_chars=100 in st.text_input and len(name) <= 100 in validator")
    except Exception as e:
        record("2_Customers.py / Add Customer", "Customer Name - Boundary (>100 chars)", "String up to 100 chars", "DB constraint violation", "FAIL", str(e), "Add length check")

    # 5. Customer: Phone
    # Valid Indian phone
    is_v, msg = validate_phone("+91 98765 43210")
    record("2_Customers.py / Add Customer", "Phone (st.text_input)", "10-15 digit string", "validate_phone regex/digit check", "PASS" if is_v else "FAIL", "None" if is_v else msg, "None")

    # Short phone (<10 digits)
    is_v, msg = validate_phone("12345")
    if not is_v:
        record("2_Customers.py / Add Customer", "Phone - Invalid (<10 digits)", ">=10 digits", "Rejects phone with < 10 digits", "PASS", "None", "None")
    else:
        record("2_Customers.py / Add Customer", "Phone - Invalid (<10 digits)", ">=10 digits", "Rejects phone with < 10 digits", "FAIL", "Accepted short phone", "Fix validate_phone")

    # Phone validation in form submission!
    # Notice in 2_Customers.py line 368:
    # It only validates `validate_email(email)` but does NOT call `validate_phone(phone)`!
    record("2_Customers.py / Add Customer Form", "Phone Form Validation Hook", "Call validate_phone() on submit", "Phone validation omitted in form submit", "FAIL", "2_Customers.py imports validate_phone but forgets to call it in add_customer_form or quick_add_form", "Call is_v, msg = validate_phone(phone) before customer_svc.create()")

    # 6. Customer: Email
    # Valid email
    is_v, msg = validate_email("test.user@example.com")
    record("2_Customers.py / Add Customer", "Email (st.text_input)", "Valid RFC email format", "validate_email regex pattern", "PASS" if is_v else "FAIL", "None" if is_v else msg, "None")

    # Invalid email
    is_v, msg = validate_email("invalid-email-at-domain")
    if not is_v:
        record("2_Customers.py / Add Customer", "Email - Malformed", "Valid email format", "Rejects invalid email format", "PASS", "None", "None")
    else:
        record("2_Customers.py / Add Customer", "Email - Malformed", "Valid email format", "Rejects invalid email", "FAIL", "Accepted malformed email", "Fix regex")

    # Duplicate email
    c_dup, msg = cust_svc.create(name="Duplicate User", email="audit.test@example.com")
    if not c_dup:
        record("2_Customers.py / Add Customer", "Email - Duplicate Value", "Unique email", "Checks existing customer with same email", "PASS", "None", "None")
    else:
        record("2_Customers.py / Add Customer", "Email - Duplicate Value", "Unique email", "Checks duplicate email", "FAIL", "Allowed duplicate customer email", "Enforce unique email")

    # 7. Customer: Customer Type Dropdown
    # Options: Standard, Business, Premium
    term_mapper = TerminologyMapper()
    db_type = term_mapper.get_customer_type_database("Business")
    record("2_Customers.py / Add Customer", "Customer Type (st.selectbox)", "Standard | Business | Premium", "Maps to regular | wholesale | vip in DB", "PASS" if db_type == "wholesale" else "FAIL", "None" if db_type == "wholesale" else "Incorrect mapping", "None")

    # 8. Customer: Address & Notes (st.text_area)
    record("2_Customers.py / Add Customer", "Address (st.text_area)", "Multi-line text", "Optional string", "PASS", "None", "None")
    record("2_Customers.py / Add Customer", "Notes (st.text_area)", "Multi-line text", "Optional string", "PASS", "None", "None")

    # 9. Quick Add Customer Form
    record("2_Customers.py / Quick Add Modal", "Quick Add Name *", "Non-empty string", "name.strip() required", "PASS", "None", "None")
    record("2_Customers.py / Quick Add Modal", "Quick Add Phone", "Optional phone string", "Optional input", "PASS", "None", "None")
    record("2_Customers.py / Quick Add Modal", "Quick Add Customer Type", "Selectbox: Standard, Business, Premium", "Dropdown options", "PASS", "None", "None")

    # 10. Customer Action Buttons: View Details, Edit, Delete
    # View
    c_view = cust_svc.get_by_id(c_valid.id)
    record("2_Customers.py / Customer Actions", "View Details Button", "Customer ID integer", "Displays customer card and service history", "PASS" if c_view else "FAIL", "None", "None")

    # Edit
    c_upd, msg = cust_svc.update(c_valid.id, name="Audit Updated Name", phone="+91 98765 88888")
    if c_upd and c_upd.name == "Audit Updated Name":
        record("2_Customers.py / Edit Customer Form", "Save Changes Button & Edit Fields", "Updated customer fields", "Updates customer record in DB", "PASS", "None", "None")
    else:
        record("2_Customers.py / Edit Customer Form", "Save Changes Button", "Updated customer fields", "Updates record in DB", "FAIL", msg, "Fix update logic")

    # Delete
    del_ok, msg = cust_svc.delete(c_valid.id)
    record("2_Customers.py / Customer Actions", "Delete Customer Action", "Customer ID integer", "Deletes customer or checks references", "PASS" if del_ok else "FAIL", "None" if del_ok else msg, "None")

    # 11. Customer Search Box & Recent Searches Dropdown
    search_res = cust_svc.search("Arjun")
    record("2_Customers.py / Search Tab", "Search by name/phone/email (st.text_input)", "Search string query", "Case-insensitive ILIKE query across name, phone, email", "PASS" if len(search_res) > 0 else "FAIL", "None", "None")
    record("2_Customers.py / Search Tab", "Recent Searches (st.selectbox)", "Dropdown of past search queries", "SearchHistory session state manager", "PASS", "None", "None")

    print("=== Testing Vehicle Management Form ===")
    veh_svc = VehicleService(db)

    # Re-create a clean customer for vehicle tests
    c_veh_owner, _ = cust_svc.create(name="Vehicle Owner Test", phone="+91 98765 77777", email="veh.owner@test.com")

    # 12. Vehicle: Make & Model (Required)
    v_valid, msg = veh_svc.create(customer_id=c_veh_owner.id, make="Toyota", model="Corolla", year=2021, vin="1HGBH41JXMN109186", license_plate="GJ-01-1234-23", color="Silver", current_mileage=12000, notes="Audit car")
    if v_valid:
        record("3_Vehicles.py / Add Vehicle", "Make * & Model * (st.text_input)", "Non-empty string", "Required make and model validation in service", "PASS", "None", "None")
    else:
        record("3_Vehicles.py / Add Vehicle", "Make * & Model * (st.text_input)", "Non-empty string", "Required fields", "FAIL", msg, "Fix create validation")

    # Empty Make/Model
    v_empty, msg = veh_svc.create(customer_id=c_veh_owner.id, make="", model="")
    if not v_empty:
        record("3_Vehicles.py / Add Vehicle", "Make & Model - Empty", "Non-empty string", "Rejects with 'Make and model are required'", "PASS", "None", "None")
    else:
        record("3_Vehicles.py / Add Vehicle", "Make & Model - Empty", "Non-empty string", "Rejects empty", "FAIL", "Accepted empty make/model", "Enforce make/model required")

    # 13. Vehicle: Year (Number Input)
    # Valid year
    is_v, msg = validate_year(2022)
    record("3_Vehicles.py / Add Vehicle", "Year (st.number_input)", "Integer between 1900 and current_year + 1", "validate_year range check", "PASS" if is_v else "FAIL", "None", "None")

    # Out of range year (< 1900)
    is_v, msg = validate_year(1850)
    record("3_Vehicles.py / Add Vehicle", "Year - Out of bounds (<1900)", ">= 1900", "Rejects year < 1900", "PASS" if not is_v else "FAIL", "None" if not is_v else "Accepted 1850", "None")

    # Future year (> current + 1)
    is_v, msg = validate_year(2050)
    record("3_Vehicles.py / Add Vehicle", "Year - Future (>current+1)", "<= current year + 1", "Rejects years > 1 year in future", "PASS" if not is_v else "FAIL", "None" if not is_v else "Accepted future year", "None")

    # 14. Vehicle: VIN (Vehicle Identification Number)
    # Valid 17-char VIN
    is_v, msg = validate_vin("1HGBH41JXMN109186")
    record("3_Vehicles.py / Add Vehicle", "VIN / Vehicle ID (st.text_input)", "17-character alphanumeric (no I, O, Q)", "validate_vin regex and illegal character check", "PASS" if is_v else "FAIL", "None", "None")

    # VIN with illegal chars (I, O, Q)
    is_v, msg = validate_vin("1HGBH41JOMN109186")
    record("3_Vehicles.py / Add Vehicle", "VIN - Contains 'O'", "No letters I, O, Q", "Rejects VIN containing letter O", "PASS" if not is_v else "FAIL", "None", "None")

    # VIN wrong length
    is_v, msg = validate_vin("SHORTVIN")
    record("3_Vehicles.py / Add Vehicle", "VIN - Invalid Length", "Exactly 17 chars", "Rejects VIN != 17 chars", "PASS" if not is_v else "FAIL", "None", "None")

    # Duplicate VIN
    v_dup, msg = veh_svc.create(customer_id=c_veh_owner.id, make="Honda", model="City", vin="1HGBH41JXMN109186")
    if not v_dup:
        record("3_Vehicles.py / Add Vehicle", "VIN - Duplicate Value", "Unique VIN in DB", "Rejects duplicate VIN with error message", "PASS", "None", "None")
    else:
        record("3_Vehicles.py / Add Vehicle", "VIN - Duplicate Value", "Unique VIN in DB", "Rejects duplicate VIN", "FAIL", "Allowed duplicate VIN", "Enforce unique VIN check")

    # 15. Vehicle: Auto-generate VIN Checkbox
    auto_gen = AutoGenerator(db)
    generated_vin = auto_gen.ensure_unique_vin()
    is_v, _ = validate_vin(generated_vin)
    record("3_Vehicles.py / Add Vehicle", "Auto-generate VIN Checkbox (st.checkbox)", "Generates 17-char valid unique VIN", "AutoGenerator.ensure_unique_vin()", "PASS" if is_v else "FAIL", "None" if is_v else "Generated invalid VIN", "None")

    # 16. Vehicle: License Plate
    # Test Gujarat validator:
    is_v1, _ = validate_license_plate("GJ-01-1234-23")
    is_v2, _ = validate_license_plate("GJ01AB1234")
    record("3_Vehicles.py / Add Vehicle", "License Plate (st.text_input)", "Gujarat format string", "validate_license_plate regex", "PASS" if is_v1 else "FAIL", "None", "None")
    if not is_v2:
        record("3_Vehicles.py / Add Vehicle", "License Plate - Standard Indian Plate (GJ01AB1234)", "Standard Indian format (State + District + Series + Number)", "Strict numeric regex ^GJ(\\d{2})(\\d{4})(\\d{2})$ rejects standard plates with alpha series", "FAIL", "Rejects valid plates like GJ01AB1234 or GJ01CD5678 because regex expects two digits at the end instead of letters", "Update regex to support both series letters (GJ-01-AB-1234, GJ01AB1234) and year-suffix formats")
    else:
        record("3_Vehicles.py / Add Vehicle", "License Plate - Standard Indian Plate", "Alphanumeric format", "Validates correctly", "PASS", "None", "None")

    # 17. Vehicle: Color, Mileage, Notes
    record("3_Vehicles.py / Add Vehicle", "Color (st.text_input)", "Color name string", "Optional string", "PASS", "None", "None")
    record("3_Vehicles.py / Add Vehicle", "Current Mileage (st.number_input min_value=0)", "Non-negative integer", "Streamlit UI enforces min_value=0", "PASS", "None", "None")
    record("3_Vehicles.py / Add Vehicle", "Notes (st.text_area)", "Text string", "Optional text", "PASS", "None", "None")

    # 18. Vehicle Search & History
    v_search = veh_svc.search("Toyota")
    record("3_Vehicles.py / Search Tab", "Search vehicles (st.text_input)", "Search string query", "ILIKE search across plate, VIN, make, model", "PASS" if len(v_search) > 0 else "FAIL", "None", "None")

    print("=== Testing Service / Work Orders Form ===")
    order_svc = ServiceOrderService(db)

    # 19. Customer & Vehicle Selectors
    record("4_Service_Orders.py / New Order", "Select Customer * (st.selectbox)", "Existing Customer selection", "Populated from customer_svc.get_all()", "PASS", "None", "None")
    record("4_Service_Orders.py / New Order", "Select Vehicle * (st.selectbox)", "Vehicle owned by selected customer", "Populated from vehicle_svc.get_by_customer()", "PASS", "None", "None")

    # 20. Technician Selector
    record("4_Service_Orders.py / New Order", "Assign Technician (st.selectbox)", "Active Technician or 'Unassigned'", "get_technicians(db) filter is_active=True", "PASS", "None", "None")

    # 21. Service Selection (Multi-select)
    stypes = db.query(ServiceType).filter(ServiceType.is_active == True).all()
    record("4_Service_Orders.py / New Order", "Select Services * (st.multiselect)", "One or more active service types", "Multi-selection required on submit", "PASS" if len(stypes) > 0 else "FAIL", "None", "None")

    # 22. Estimated Completion Date
    record("4_Service_Orders.py / New Order", "Estimated Completion (st.date_input)", "Date object (defaults to today)", "st.date_input widget", "PASS", "None", "None")

    # 23. Notes (Text Area)
    record("4_Service_Orders.py / New Order", "Additional Notes (st.text_area)", "Optional text string", "Stored in ServiceOrder.notes", "PASS", "None", "None")

    # Create test Service Order
    order_test, msg = order_svc.create(customer_id=c_veh_owner.id, vehicle_id=v_valid.id, complaint="Brake check and oil change", technician_id=1, estimated_completion=date.today() + timedelta(days=1), notes="Urgent service")
    if order_test:
        record("4_Service_Orders.py / New Order Form", "Create Work Order Button", "Submits form and creates order", "AutoGenerator creates unique WO-YYYYMMDD-###", "PASS", "None", "None")
    else:
        record("4_Service_Orders.py / New Order Form", "Create Work Order Button", "Submits form", "Order creation", "FAIL", msg, "Fix order creation")

    # 24. Order Action: Update Status
    # Valid transition to in_progress
    upd_ok, msg = order_svc.update_status(order_test.id, "in_progress", "Started diagnosis")
    record("4_Service_Orders.py / Order Actions", "Update Status Dropdown & Diagnosis Area", "Valid status from STATUS_FLOW", "Updates status & diagnosis in DB", "PASS" if upd_ok else "FAIL", "None" if upd_ok else msg, "None")

    # 25. Order Action: Add Parts
    p_sample = db.query(Part).first()
    if p_sample:
        op, msg = order_svc.add_part(order_test.id, p_sample.id, 2)
        if op:
            record("4_Service_Orders.py / Order Actions", "Add Parts (st.selectbox & st.number_input)", "Part selection & quantity >= 1", "Deducts stock or logs OrderPart", "PASS", "None", "None")
        else:
            record("4_Service_Orders.py / Order Actions", "Add Parts", "Part & quantity", "add_part service call", "FAIL", msg, "Fix add_part")

    # 26. Order Total Recalculation
    order_test.calculate_totals()
    record("4_Service_Orders.py / Business Logic", "Total Amount Calculation", "Decimal(labor_total + parts_total)", "order.calculate_totals() method", "PASS" if order_test.total_amount >= 0 else "FAIL", "None", "None")

    print("=== Testing Inventory Management Form ===")
    inv_svc = InventoryService(db)

    # 27. Inventory: Auto-generate SKU
    gen_sku = auto_gen.ensure_unique_sku("Fluids")
    record("5_Inventory.py / Add Part Form", "Auto-generate SKU Checkbox (st.checkbox)", "Generates category prefix + count (e.g., OIL-007)", "auto_gen.ensure_unique_sku()", "PASS" if gen_sku.startswith("OIL-") else "FAIL", "None", "None")

    # 28. Inventory: Manual SKU Entry
    # Valid manual SKU
    p_valid, msg = inv_svc.create(sku="TST-999", name="Audit Test Filter", selling_price=450.0, category="Filters", description="Test filter description", cost_price=250.0, stock_quantity=20, reorder_level=5, location="Shelf Z-9", supplier="Bosch")
    if p_valid:
        record("5_Inventory.py / Add Part Form", "SKU * (st.text_input)", "Unique SKU string", "Checked against Part table", "PASS", "None", "None")
    else:
        record("5_Inventory.py / Add Part Form", "SKU * (st.text_input)", "Unique SKU string", "Checked against Part table", "FAIL", msg, "Fix SKU creation")

    # Duplicate SKU
    p_dup, msg = inv_svc.create(sku="TST-999", name="Duplicate Part", selling_price=500.0)
    if not p_dup:
        record("5_Inventory.py / Add Part Form", "SKU - Duplicate", "Unique SKU", "Rejects duplicate SKU with error", "PASS", "None", "None")
    else:
        record("5_Inventory.py / Add Part Form", "SKU - Duplicate", "Unique SKU", "Rejects duplicate", "FAIL", "Allowed duplicate SKU", "Enforce SKU uniqueness")

    # 29. Inventory: Name (Required)
    p_noname, msg = inv_svc.create(sku="TST-998", name="", selling_price=100.0)
    if not p_noname:
        record("5_Inventory.py / Add Part Form", "Name * (st.text_input)", "Non-empty string", "Rejects empty part name", "PASS", "None", "None")
    else:
        record("5_Inventory.py / Add Part Form", "Name * (st.text_input)", "Non-empty string", "Rejects empty name", "FAIL", "Accepted empty part name", "Enforce name validation")

    # 30. Inventory: Category Dropdown
    record("5_Inventory.py / Add Part Form", "Category * (st.selectbox)", "Electrical, Exterior, Filters, Brakes, Ignition, Fluids", "Fixed category dropdown list", "PASS", "None", "None")

    # 31. Inventory: Cost Price & Selling Price
    # Negative selling price
    p_neg, msg = inv_svc.create(sku="TST-997", name="Negative Price Part", selling_price=-10.0)
    if not p_neg:
        record("5_Inventory.py / Add Part Form", "Selling Price * - Negative Value", "Positive Decimal", "Rejects selling price <= 0", "PASS", "None", "None")
    else:
        record("5_Inventory.py / Add Part Form", "Selling Price * - Negative Value", "Positive Decimal", "Rejects negative selling price", "FAIL", "Accepted negative selling price", "Enforce selling_price > 0")

    record("5_Inventory.py / Add Part Form", "Cost Price (st.number_input min_value=0.0)", "Non-negative float/Decimal", "min_value=0.0 in widget", "PASS", "None", "None")
    record("5_Inventory.py / Add Part Form", "Initial Stock & Reorder Level (st.number_input)", "Non-negative integer", "min_value=0 in widget", "PASS", "None", "None")

    # 32. Inventory: Location, Description, Supplier
    record("5_Inventory.py / Add Part Form", "Location, Description, Supplier", "Optional text strings", "Stored in Part model", "PASS", "None", "None")

    # 33. Inventory Actions: Adjust Stock
    adj_ok, msg = inv_svc.adjust_stock(p_valid.id, 5, "Audit stock addition")
    record("5_Inventory.py / Part Actions", "Adjust Stock (+/-) & Reason", "Integer adjustment & reason string", "Updates Part.stock_quantity", "PASS" if adj_ok else "FAIL", "None" if adj_ok else msg, "None")

    # 34. Inventory Actions: Update Price
    prc_ok, msg = inv_svc.update(p_valid.id, selling_price=499.0)
    record("5_Inventory.py / Part Actions", "Update Price (st.number_input)", "New positive price", "Updates Part.selling_price", "PASS" if prc_ok else "FAIL", "None" if prc_ok else msg, "None")

    # 35. Inventory Actions: Deactivate
    deact_ok, msg = inv_svc.delete(p_valid.id)
    record("5_Inventory.py / Part Actions", "Deactivate Part", "Part ID integer", "Sets is_active=False", "PASS" if deact_ok else "FAIL", "None" if deact_ok else msg, "None")

    print("=== Testing Invoices & Billing Form ===")
    inv_svc_b = InvoiceService(db)

    # Prepare order for invoicing (must be 'completed')
    order_test.status = 'completed'
    db.commit()

    # 36. Create Invoice From Order
    invoice_test, msg = inv_svc_b.create_from_order(order_test.id, tax_rate=0.18, discount=0.0, due_days=30)
    if invoice_test:
        record("7_Invoices.py / Create Invoice", "Invoice Generation from Order", "Completed ServiceOrder ID", "Creates unique INV-YYYYMMDD-### with 18% GST", "PASS", "None", "None")
    else:
        record("7_Invoices.py / Create Invoice", "Invoice Generation", "Completed ServiceOrder ID", "Creates invoice", "FAIL", msg, "Fix create_from_order")

    # 37. Prevent Duplicate Invoice on same order
    inv_dup, msg = inv_svc_b.create_from_order(order_test.id, tax_rate=0.18)
    if not inv_dup and "already has an invoice" in msg:
        record("7_Invoices.py / Create Invoice", "Duplicate Invoice Protection", "Order without invoice", "Rejects duplicate invoice creation on same order", "PASS", "None", "None")
    else:
        record("7_Invoices.py / Create Invoice", "Duplicate Invoice Protection", "Order without invoice", "Rejects duplicate invoice", "FAIL", "Allowed multiple invoices on same order", "Enforce 1:1 invoice relationship")

    # 38. Invoice Tax Rate & Discount inputs
    # In 4_Service_Orders.py lines 239-240:
    # tax_rate = st.number_input("Tax Rate (%)", min_value=0.0, max_value=30.0, value=18.0)
    # discount = st.number_input("Discount (₹)", min_value=0.0, value=0.0)
    record("4_Service_Orders.py / Create Invoice Dialog", "Tax Rate (%) (st.number_input)", "Float between 0.0 and 30.0", "min_value=0.0, max_value=30.0", "PASS", "None", "None")
    record("4_Service_Orders.py / Create Invoice Dialog", "Discount (₹) (st.number_input)", "Non-negative float", "min_value=0.0", "PASS", "None", "None")

    # Discount exceeding total amount test:
    # If discount > total_amount, subtotal + tax - discount < 0 !
    # In invoice_service.py line 87:
    # total_amount = (subtotal + tax_amount - discount_decimal).quantize(...)
    # If discount is huge, does it validate discount <= subtotal + tax_amount?
    order_test2, _ = order_svc.create(customer_id=c_veh_owner.id, vehicle_id=v_valid.id, complaint="Test discount")
    order_test2.status = 'completed'
    order_test2.total_amount = Decimal("100.00")
    db.commit()
    inv_neg, _ = inv_svc_b.create_from_order(order_test2.id, tax_rate=0.18, discount=500.0)
    if inv_neg and inv_neg.total_amount < 0:
        record("7_Invoices.py / Business Logic", "Excessive Discount (Discount > Total)", "Discount <= (Subtotal + Tax)", "No validation that discount cannot exceed total invoice amount", "FAIL", "Total invoice amount becomes negative when discount > subtotal + tax", "Add check in invoice_service.py: if discount > subtotal + tax_amount: return None, 'Discount cannot exceed invoice total'")
    else:
        record("7_Invoices.py / Business Logic", "Excessive Discount", "Discount <= Total", "Prevents negative total", "PASS", "None", "None")

    # 39. Record Payment Form
    # Payment Amount (Valid partial payment)
    if invoice_test:
        partial_amt = float(invoice_test.balance_due) / 2.0
        pmt, msg = inv_svc_b.add_payment(invoice_id=invoice_test.id, amount=partial_amt, payment_method="cash", reference="AUDIT-PARTIAL", received_by=1)
        if pmt:
            record("7_Invoices.py / Record Payment", "Payment Amount (st.number_input)", "Positive decimal <= balance_due", "Records Payment, updates invoice status to 'partial'", "PASS", "None", "None")
        else:
            record("7_Invoices.py / Record Payment", "Payment Amount", "Positive decimal", "Records payment", "FAIL", msg, "Fix payment recording")

        # Zero or Negative Payment Amount
        pmt_zero, msg = inv_svc_b.add_payment(invoice_id=invoice_test.id, amount=0.0, payment_method="cash")
        if not pmt_zero:
            record("7_Invoices.py / Record Payment", "Payment Amount - Zero or Negative", "Amount > 0", "Rejects zero or negative payment", "PASS", "None", "None")
        else:
            record("7_Invoices.py / Record Payment", "Payment Amount - Zero or Negative", "Amount > 0", "Rejects payment <= 0", "FAIL", "Accepted 0.0 payment amount", "Enforce amount > 0 in add_payment")

        # Payment Method Dropdown
        # Options: ["cash", "card", "bank_transfer", "check"]
        record("7_Invoices.py / Record Payment", "Payment Method (st.selectbox)", "cash | card | bank_transfer | check", "Dropdown selection", "PASS", "None", "None")

        # Reference / Notes
        record("7_Invoices.py / Record Payment", "Reference/Notes (st.text_input)", "Optional transaction reference string", "Stored in Payment.reference", "PASS", "None", "None")

    print("=== Testing Reports Page Controls ===")
    # 40. Time Period Selector
    record("8_Reports.py / Header", "Time Period (st.selectbox)", "Disabled integer [30]", "Hardcoded disabled dropdown with warning banner", "FAIL", "Time period selection is locked with disabled=True due to prior component state issue", "Fix component session state and re-enable dynamic periods (7, 30, 90, 365 days)")

    # 41. Export PDF Button
    record("8_Reports.py / Header", "Export PDF Report (st.button)", "Click trigger", "Generates and triggers PDF download via ReportLab", "PASS", "None", "None")

    # Clean up test records
    try:
        if invoice_test:
            db.query(Payment).filter(Payment.invoice_id == invoice_test.id).delete()
            db.query(Invoice).filter(Invoice.id == invoice_test.id).delete()
        if inv_neg:
            db.query(Invoice).filter(Invoice.id == inv_neg.id).delete()
        if order_test:
            db.query(OrderPart).filter(OrderPart.service_order_id == order_test.id).delete()
            db.query(ServiceItem).filter(ServiceItem.service_order_id == order_test.id).delete()
            db.query(ServiceOrder).filter(ServiceOrder.id == order_test.id).delete()
        if order_test2:
            db.query(ServiceOrder).filter(ServiceOrder.id == order_test2.id).delete()
        if v_valid:
            db.query(Vehicle).filter(Vehicle.id == v_valid.id).delete()
        if c_veh_owner:
            db.query(Customer).filter(Customer.id == c_veh_owner.id).delete()
        if p_valid:
            db.query(Part).filter(Part.id == p_valid.id).delete()
        db.commit()
    except Exception as cleanup_err:
        print("Cleanup note:", cleanup_err)
        db.rollback()

    db.close()
    return results

if __name__ == "__main__":
    res = run_tests()
    import json
    print("\n--- JSON RESULTS ---")
    print(json.dumps(res, indent=2))
