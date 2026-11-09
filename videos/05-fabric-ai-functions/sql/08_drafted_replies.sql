-- 6. Drafted replies for the negative emails (a human approves before anything is sent)
-- Toastly demo (PBI101 video 05). Run one query at a time.

SELECT TOP 5 e.email_id, e.body,
       AI_GENERATE_RESPONSE(
         'You write replies for Toastly customer support. Max 60 words. Calm, warm tone. Mention the order number if there is one. Never promise a refund, a replacement or a date. Sign off as: Toastly Support.',
         e.body) AS draft_reply
FROM shop.support_emails AS e
WHERE AI_ANALYZE_SENTIMENT(e.body) = 'negative'
ORDER BY e.email_id;
