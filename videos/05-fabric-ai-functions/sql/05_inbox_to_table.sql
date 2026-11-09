-- 3. Inbox to table: AI_EXTRACT + OPENJSON, then money at risk per product type
-- Toastly demo (PBI101 video 05). Run one query at a time.

SELECT TOP 10 e.email_id, e.body, x.order_number, x.product, x.refund_amount, x.deadline
FROM shop.support_emails AS e
CROSS APPLY OPENJSON(AI_EXTRACT(e.body, 'order_number', 'product', 'refund_amount', 'deadline'))
WITH (order_number varchar(20), product varchar(100),
      refund_amount varchar(50), deadline varchar(50)) AS x
ORDER BY e.email_id;

WITH x AS (
    SELECT AI_CLASSIFY(e.body, 'toaster', 'air fryer', 'espresso machine', 'milk frother',
             'kettle', 'blender', 'rice cooker', 'slow cooker', 'food processor',
             'waffle maker', 'kitchen scale', 'ice cream maker') AS product,
           TRY_CAST(j.refund_amount_as_decimal_number AS decimal(10,2)) AS refund
    FROM shop.support_emails AS e
    CROSS APPLY OPENJSON(AI_EXTRACT(e.body, 'refund_amount_as_decimal_number'))
    WITH (refund_amount_as_decimal_number varchar(50)) AS j
)
SELECT product, COUNT(*) AS refund_emails, SUM(refund) AS money_at_risk
FROM x
WHERE refund > 0
GROUP BY product
ORDER BY money_at_risk DESC;
