DROP TABLE IF EXISTS vendor_payments;

CREATE TABLE vendor_payments (
    payment_id INTEGER PRIMARY KEY,
    vendor_id VARCHAR(20) NOT NULL,
    vendor_name VARCHAR(120) NOT NULL,
    category VARCHAR(60) NOT NULL,
    invoice_number VARCHAR(40) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    paid_date DATE,
    amount NUMERIC(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL
);
