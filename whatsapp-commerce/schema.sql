-- =====================================================================
-- MULTI-TENANT WHATSAPP COMMERCE SAAS PLATFORM DATABASE SCHEMA (SQLITE / POSTGRESQL)
-- =====================================================================

PRAGMA foreign_keys = ON;

-- 1. PLATFORM LEVEL IDENTITY
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. TENANT ROOT
CREATE TABLE IF NOT EXISTS businesses (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    owner_id VARCHAR(36) NOT NULL,
    currency VARCHAR(3) DEFAULT 'GHS' NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    logo_url TEXT,
    status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,
    plan VARCHAR(20) DEFAULT 'FREE' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_businesses_slug ON businesses(slug);

-- 3. RBAC & MEMBERSHIP
CREATE TABLE IF NOT EXISTS business_members (
    id VARCHAR(36) PRIMARY KEY,
    business_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) DEFAULT 'STAFF' NOT NULL, -- OWNER, ADMIN, MANAGER, STAFF
    invited_by VARCHAR(36),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (invited_by) REFERENCES users(id),
    CONSTRAINT uq_member UNIQUE (business_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_members_business ON business_members(business_id);
CREATE INDEX IF NOT EXISTS idx_members_user ON business_members(user_id);

-- 4. WHATSAPP ACCOUNT BINDING (Multi-tenant Channel Routing)
CREATE TABLE IF NOT EXISTS business_whatsapp_accounts (
    id VARCHAR(36) PRIMARY KEY,
    business_id VARCHAR(36) NOT NULL UNIQUE,
    phone_number_id VARCHAR(100) NOT NULL UNIQUE,
    display_phone_number VARCHAR(30) NOT NULL,
    waba_id VARCHAR(100) NOT NULL,
    access_token_encrypted TEXT,
    webhook_verify_token VARCHAR(255),
    quality_rating VARCHAR(50) DEFAULT 'UNKNOWN',
    status VARCHAR(20) DEFAULT 'CONNECTED' NOT NULL, -- CONNECTED, DISCONNECTED, PENDING
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_waba_phone_id ON business_whatsapp_accounts(phone_number_id);

-- 5. BUSINESS-SPECIFIC CUSTOMERS
CREATE TABLE IF NOT EXISTS customers (
    id VARCHAR(36) PRIMARY KEY,
    business_id VARCHAR(36) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    default_delivery_address TEXT,
    total_orders INTEGER DEFAULT 0 NOT NULL,
    total_spent DECIMAL(12, 2) DEFAULT 0.00 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
    CONSTRAINT uq_biz_customer_phone UNIQUE (business_id, phone)
);
CREATE INDEX IF NOT EXISTS idx_customers_biz_phone ON customers(business_id, phone);

-- 6. PRODUCT CATALOG & INVENTORY
CREATE TABLE IF NOT EXISTS product_categories (
    id VARCHAR(36) PRIMARY KEY,
    business_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
    CONSTRAINT uq_biz_category_slug UNIQUE (business_id, slug)
);

CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(36) PRIMARY KEY,
    business_id VARCHAR(36) NOT NULL,
    category_id VARCHAR(36),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sku VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    cost_price DECIMAL(10, 2),
    stock_quantity INTEGER DEFAULT 0 NOT NULL,
    low_stock_threshold INTEGER DEFAULT 5 NOT NULL,
    image_url TEXT,
    status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL, -- ACTIVE, INACTIVE, ARCHIVED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES product_categories(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_products_biz_status ON products(business_id, status);

-- 7. ORDERS & ORDER ITEMS
CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(36) PRIMARY KEY,
    business_id VARCHAR(36) NOT NULL,
    customer_id VARCHAR(36) NOT NULL,
    order_number VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL, -- PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED
    payment_status VARCHAR(20) DEFAULT 'UNPAID' NOT NULL, -- UNPAID, PARTIALLY_PAID, PAID, REFUNDED
    channel VARCHAR(20) DEFAULT 'WHATSAPP' NOT NULL,      -- WHATSAPP, WEB, MANUAL, API
    currency VARCHAR(3) DEFAULT 'GHS' NOT NULL,
    subtotal DECIMAL(10, 2) DEFAULT 0.00 NOT NULL,
    delivery_fee DECIMAL(10, 2) DEFAULT 0.00 NOT NULL,
    total_amount DECIMAL(10, 2) DEFAULT 0.00 NOT NULL,
    delivery_address TEXT,
    delivery_notes TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
    CONSTRAINT uq_biz_order_num UNIQUE (business_id, order_number)
);
CREATE INDEX IF NOT EXISTS idx_orders_biz_status ON orders(business_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_biz_customer ON orders(business_id, customer_id);

CREATE TABLE IF NOT EXISTS order_items (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36),
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);

-- 8. PAYMENT CONFIGURATIONS & TRANSACTIONS
CREATE TABLE IF NOT EXISTS business_payment_configs (
    id VARCHAR(36) PRIMARY KEY,
    business_id VARCHAR(36) NOT NULL UNIQUE,
    provider VARCHAR(50) DEFAULT 'PAYSTACK' NOT NULL,
    public_key VARCHAR(255),
    secret_key_encrypted TEXT,
    subaccount_code VARCHAR(100),
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    id VARCHAR(36) PRIMARY KEY,
    business_id VARCHAR(36) NOT NULL,
    order_id VARCHAR(36) NOT NULL,
    provider VARCHAR(50) DEFAULT 'PAYSTACK' NOT NULL,
    reference VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'GHS' NOT NULL,
    status VARCHAR(20) DEFAULT 'INITIALIZED' NOT NULL, -- INITIALIZED, SUCCESS, FAILED, REFUNDED
    payment_method VARCHAR(50),                        -- MOBILE_MONEY, CARD, BANK_TRANSFER, CASH
    payment_channel_details JSON,
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE RESTRICT,
    CONSTRAINT uq_biz_payment_ref UNIQUE (business_id, reference)
);
CREATE INDEX IF NOT EXISTS idx_payments_biz_order ON payments(business_id, order_id);
