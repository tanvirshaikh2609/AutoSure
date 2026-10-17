-- ============================================
-- Car Service Management & POS System
-- PostgreSQL Database Schema
-- Version: 1.0
-- ============================================

-- Drop existing tables if they exist (in correct order due to FKs)
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS order_parts CASCADE;
DROP TABLE IF EXISTS service_items CASCADE;
DROP TABLE IF EXISTS service_orders CASCADE;
DROP TABLE IF EXISTS parts CASCADE;
DROP TABLE IF EXISTS service_types CASCADE;
DROP TABLE IF EXISTS technicians CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================
-- 1. USERS TABLE
-- System authentication and role management
-- ============================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'manager', 'technician', 'cashier')),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. CUSTOMERS TABLE
-- Customer information and classification
-- ============================================
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    customer_type VARCHAR(20) DEFAULT 'regular' CHECK (customer_type IN ('regular', 'wholesale', 'vip')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 3. VEHICLES TABLE
-- Vehicle records linked to customers
-- ============================================
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INTEGER,
    vin VARCHAR(17) UNIQUE,
    license_plate VARCHAR(20),
    color VARCHAR(30),
    current_mileage INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 4. TECHNICIANS TABLE
-- Workshop employees/technicians
-- ============================================
CREATE TABLE technicians (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    employee_id VARCHAR(20) UNIQUE,
    specialty VARCHAR(100),
    hourly_rate DECIMAL(10, 2),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 5. SERVICE TYPES TABLE
-- Catalog of available services
-- ============================================
CREATE TABLE service_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    standard_hours DECIMAL(5, 2) DEFAULT 1.0,
    base_price DECIMAL(10, 2),
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================
-- 6. PARTS TABLE (Inventory)
-- Parts inventory with pricing and stock
-- ============================================
CREATE TABLE parts (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(50),
    description TEXT,
    cost_price DECIMAL(10, 2),
    selling_price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    reorder_level INTEGER DEFAULT 10,
    location VARCHAR(50),
    supplier VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 7. SERVICE ORDERS TABLE
-- Main transaction table for service work
-- ============================================
CREATE TABLE service_orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(20) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(id),
    vehicle_id INTEGER REFERENCES vehicles(id),
    technician_id INTEGER REFERENCES technicians(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN 
        ('pending', 'in_progress', 'waiting_parts', 'completed', 'invoiced', 'cancelled')),
    complaint TEXT,
    diagnosis TEXT,
    labor_total DECIMAL(10, 2) DEFAULT 0,
    parts_total DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) DEFAULT 0,
    notes TEXT,
    estimated_completion DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ============================================
-- 8. SERVICE ITEMS TABLE
-- Individual service line items per order
-- ============================================
CREATE TABLE service_items (
    id SERIAL PRIMARY KEY,
    service_order_id INTEGER REFERENCES service_orders(id) ON DELETE CASCADE,
    service_type_id INTEGER REFERENCES service_types(id),
    description TEXT,
    labor_hours DECIMAL(5, 2),
    labor_rate DECIMAL(10, 2),
    labor_cost DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed'))
);

-- ============================================
-- 9. ORDER PARTS TABLE
-- Parts used in service orders (junction table)
-- ============================================
CREATE TABLE order_parts (
    id SERIAL PRIMARY KEY,
    service_order_id INTEGER REFERENCES service_orders(id) ON DELETE CASCADE,
    part_id INTEGER REFERENCES parts(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL
);

-- ============================================
-- 10. INVOICES TABLE
-- Generated invoices from completed orders
-- ============================================
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(20) UNIQUE NOT NULL,
    service_order_id INTEGER REFERENCES service_orders(id),
    customer_id INTEGER REFERENCES customers(id),
    subtotal DECIMAL(12, 2) NOT NULL,
    tax_rate DECIMAL(5, 2) DEFAULT 0,
    tax_amount DECIMAL(12, 2) DEFAULT 0,
    discount_amount DECIMAL(12, 2) DEFAULT 0,
    total_amount DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'unpaid' CHECK (status IN ('unpaid', 'partial', 'paid', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date DATE
);

-- ============================================
-- 11. PAYMENTS TABLE
-- Payment records with partial payment support
-- ============================================
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(id),
    amount DECIMAL(12, 2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN 
        ('cash', 'card', 'bank_transfer', 'check')),
    reference VARCHAR(100),
    notes TEXT,
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    received_by INTEGER REFERENCES users(id)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_name ON customers(name);
CREATE INDEX idx_customers_type ON customers(customer_type);
CREATE INDEX idx_vehicles_customer ON vehicles(customer_id);
CREATE INDEX idx_vehicles_license ON vehicles(license_plate);
CREATE INDEX idx_vehicles_vin ON vehicles(vin);
CREATE INDEX idx_service_orders_customer ON service_orders(customer_id);
CREATE INDEX idx_service_orders_vehicle ON service_orders(vehicle_id);
CREATE INDEX idx_service_orders_status ON service_orders(status);
CREATE INDEX idx_service_orders_date ON service_orders(created_at);
CREATE INDEX idx_service_orders_technician ON service_orders(technician_id);
CREATE INDEX idx_parts_sku ON parts(sku);
CREATE INDEX idx_parts_category ON parts(category);
CREATE INDEX idx_parts_stock ON parts(stock_quantity);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_date ON invoices(created_at);
CREATE INDEX idx_invoices_customer ON invoices(customer_id);
CREATE INDEX idx_payments_invoice ON payments(invoice_id);
CREATE INDEX idx_payments_date ON payments(paid_at);

-- ============================================
-- TRIGGER FOR UPDATED_AT
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_parts_updated_at BEFORE UPDATE ON parts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_service_orders_updated_at BEFORE UPDATE ON service_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================
COMMENT ON TABLE users IS 'System users with authentication credentials and role-based access';
COMMENT ON TABLE customers IS 'Customer profiles with contact information and classification';
COMMENT ON TABLE vehicles IS 'Vehicle records linked to customer accounts';
COMMENT ON TABLE technicians IS 'Workshop technicians/employees with specialty and rates';
COMMENT ON TABLE service_types IS 'Catalog of available services with standard labor hours';
COMMENT ON TABLE parts IS 'Inventory items with pricing, stock levels, and supplier info';
COMMENT ON TABLE service_orders IS 'Main service transaction tracking work on vehicles';
COMMENT ON TABLE service_items IS 'Individual service line items within a service order';
COMMENT ON TABLE order_parts IS 'Parts used in service orders (junction table)';
COMMENT ON TABLE invoices IS 'Generated invoices from completed service orders';
COMMENT ON TABLE payments IS 'Payment records supporting multiple payment methods';

-- Schema creation complete
SELECT 'Schema created successfully!' AS message;
