-- How to prompt: a vague prompt vs a spec prompt on the same 8 emails
-- Toastly demo (PBI101 video 05). Run one query at a time.

SELECT TOP 8 email_id, body,
       AI_GENERATE_RESPONSE('What is this email about?', body) AS answer
FROM shop.support_emails
ORDER BY email_id;

SELECT TOP 8 email_id, AI_GENERATE_RESPONSE(
  'Task: label the main issue of this customer email.
   Allowed issues: refund, shipping, defect, question, billing, other.
   Urgent = true only if the customer gives a deadline or threatens a chargeback.
   Return only JSON, nothing else: {"issue": "...", "urgent": true or false}
   Context: Toastly sells small kitchen appliances online.', body) AS answer
INTO #answers
FROM shop.support_emails
ORDER BY email_id;

SELECT email_id, answer,
       JSON_VALUE(answer, '$.issue')  AS issue,
       JSON_VALUE(answer, '$.urgent') AS urgent
FROM #answers;
