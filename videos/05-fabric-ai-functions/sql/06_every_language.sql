-- 4. Every language: translate, then sentiment by country across 5 languages
-- Toastly demo (PBI101 video 05). Run one query at a time.

SELECT TOP 10 country, language, review_text,
       AI_TRANSLATE(review_text, 'en') AS review_en
FROM shop.product_reviews
WHERE language <> 'en'
ORDER BY review_id;

WITH s AS (
    SELECT country, AI_ANALYZE_SENTIMENT(review_text) AS sentiment
    FROM shop.product_reviews
)
SELECT country, COUNT(*) AS reviews,
       SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS negative,
       CAST(100.0 * SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) / COUNT(*) AS decimal(5,1)) AS pct_negative
FROM s
GROUP BY country
ORDER BY pct_negative DESC;
