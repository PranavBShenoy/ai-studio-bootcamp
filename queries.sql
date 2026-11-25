-- 1. Top vendors by total spend
SELECT vendor_id, vendor_name, SUM(amount) AS total_spend
FROM vendor_payments
GROUP BY vendor_id, vendor_name
ORDER BY total_spend DESC
LIMIT 10;

-- 2. Duplicate invoice numbers paid more than once (using ROW_NUMBER window function)
WITH ranked_invoices AS (
    SELECT
        payment_id,
        vendor_id,
        vendor_name,
        invoice_number,
        paid_date,
        amount,
        ROW_NUMBER() OVER (
            PARTITION BY vendor_id, invoice_number
            ORDER BY paid_date NULLS LAST, payment_id
        ) AS row_num
    FROM vendor_payments
)
SELECT payment_id, vendor_id, vendor_name, invoice_number, paid_date, amount
FROM ranked_invoices
WHERE row_num > 1;

-- 3. Monthly payment totals
SELECT
    DATE_TRUNC('month', invoice_date)::DATE AS month_start,
    COUNT(*) AS invoice_count,
    SUM(amount) AS total_amount
FROM vendor_payments
GROUP BY DATE_TRUNC('month', invoice_date)
ORDER BY month_start;

-- 4. Late payments (paid after due date)
SELECT
    payment_id,
    vendor_name,
    invoice_number,
    due_date,
    paid_date,
    (paid_date - due_date) AS days_late,
    amount
FROM vendor_payments
WHERE paid_date IS NOT NULL AND paid_date > due_date
ORDER BY days_late DESC;

-- 5. Vendors with more than 1 late payment (using HAVING)
SELECT
    vendor_id,
    vendor_name,
    COUNT(*) AS late_payments,
    SUM(amount) AS late_amount
FROM vendor_payments
WHERE paid_date IS NOT NULL AND paid_date > due_date
GROUP BY vendor_id, vendor_name
HAVING COUNT(*) > 1
ORDER BY late_payments DESC;

-- 6. Breakdown by payment status
SELECT
    status,
    COUNT(*) AS tx_count,
    SUM(amount) AS total_amount
FROM vendor_payments
GROUP BY status
ORDER BY total_amount DESC;

-- 7. Average invoice amount by category
SELECT
    category,
    COUNT(*) AS invoice_count,
    ROUND(AVG(amount), 2) AS avg_amount
FROM vendor_payments
GROUP BY category
ORDER BY avg_amount DESC;

-- 8. High-value outlier invoices (more than 2x overall average)
SELECT
    payment_id,
    vendor_name,
    invoice_number,
    amount,
    status
FROM vendor_payments
WHERE amount > (SELECT 2 * AVG(amount) FROM vendor_payments)
ORDER BY amount DESC;

-- 9. Month-over-month spend change (using LAG)
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', invoice_date)::DATE AS month_start,
        SUM(amount) AS total_spend
    FROM vendor_payments
    GROUP BY DATE_TRUNC('month', invoice_date)
)
SELECT
    month_start,
    total_spend,
    LAG(total_spend) OVER (ORDER BY month_start) AS prev_month_spend,
    total_spend - LAG(total_spend) OVER (ORDER BY month_start) AS mom_diff
FROM monthly
ORDER BY month_start;

-- 10. Largest single invoice per vendor (using ROW_NUMBER)
WITH vendor_ranked AS (
    SELECT
        vendor_id,
        vendor_name,
        invoice_number,
        amount,
        ROW_NUMBER() OVER (PARTITION BY vendor_id ORDER BY amount DESC) AS rn
    FROM vendor_payments
)
SELECT vendor_id, vendor_name, invoice_number, amount
FROM vendor_ranked
WHERE rn = 1
ORDER BY amount DESC;
