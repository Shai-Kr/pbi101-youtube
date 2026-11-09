-- 7. PII scrub: a helper, not a compliance guarantee
-- Toastly demo (PBI101 video 05). Run one query at a time.

SELECT TOP 5 email_id, body,
       AI_GENERATE_RESPONSE(
         'Rewrite this text exactly as it is, but replace every person name, email address and phone number with [REDACTED]. Change nothing else.',
         body) AS safe_body
FROM shop.support_emails
ORDER BY email_id;
