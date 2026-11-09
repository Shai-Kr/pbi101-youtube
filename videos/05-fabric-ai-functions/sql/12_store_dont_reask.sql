-- Store the answers, don't ask twice: live (24.5 s) vs CTAS once vs reading the table (1.5 s)
-- Toastly demo (PBI101 video 05). Run one query at a time.

SELECT review_id, stars, review_text,
       AI_ANALYZE_SENTIMENT(review_text) AS sentiment,
       AI_CLASSIFY(review_text, 'build quality', 'performance', 'noise',
                   'cleaning', 'delivery', 'other') AS topic
FROM shop.product_reviews;

CREATE TABLE ai.review_enriched AS
SELECT review_id, product_id, stars, review_text,
       ISNULL(AI_ANALYZE_SENTIMENT(review_text), 'unknown') AS sentiment,
       ISNULL(AI_CLASSIFY(review_text, 'build quality', 'performance', 'noise',
                          'cleaning', 'delivery', 'other'), 'unknown') AS topic,
       CAST('v1' AS varchar(10)) AS prompt_version,
       CAST(SYSUTCDATETIME() AS datetime2(0)) AS processed_at
FROM shop.product_reviews;

SELECT review_id, stars, review_text, sentiment, topic, processed_at
FROM ai.review_enriched;
