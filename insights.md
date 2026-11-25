# Day 3 Insights — Vendor Payments Analysis

1. **Late payments are frequent across vendors:** Multiple paid invoices settled 3 to 14 days past their due dates, with delays showing up across vendors such as Kaveri Office Supplies, Zenith Security Labs, Apex Cloud Systems, and Malnad Industrial Tools.
2. **Duplicate invoices exist in the payment log:** Partitioning by vendor and invoice number with `ROW_NUMBER()` surfaces duplicate records that need reconciliation before payout.
3. **Spend is concentrated in high-value and outlier invoices:** A small set of large/outlier invoices accounts for a disproportionate share of total spend compared to typical routine payments.
4. **Unpaid/overdue items require follow-up:** Invoices missing a `paid_date` (`Pending` or `Overdue`) represent open cash/follow-up items alongside completed payments.
5. **Index behavior depends on table size:** Adding an index on `vendor_name` prepares queries for scale, though on a 123-row dataset PostgreSQL can still prefer a sequential scan (`Seq Scan`) when reading the full table is cheaper.
