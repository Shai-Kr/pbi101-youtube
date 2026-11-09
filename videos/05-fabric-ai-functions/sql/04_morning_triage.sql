-- 2. Morning triage: classify the inbox into your team labels, then GROUP BY
-- Toastly demo (PBI101 video 05). Run one query at a time.

WITH t AS (
    SELECT AI_CLASSIFY(subject + ' ' + body,
             'refunds', 'shipping', 'product quality',
             'product help', 'billing', 'other') AS team
    FROM shop.support_emails
)
SELECT team, COUNT(*) AS emails
FROM t
GROUP BY team
ORDER BY emails DESC;
