-- 1. Stars vs words: sentiment next to the star rating, then the hidden unhappy customers
-- Toastly demo (PBI101 video 05). Run one query at a time.

SELECT TOP 20 r.review_id, p.product_name, r.stars, r.review_text,
       AI_ANALYZE_SENTIMENT(r.review_text) AS sentiment
FROM shop.product_reviews AS r
JOIN shop.products AS p ON p.product_id = r.product_id
ORDER BY r.review_id;

SELECT p.product_name, r.stars, r.review_text, s.sentiment
FROM shop.product_reviews AS r
JOIN shop.products AS p ON p.product_id = r.product_id
CROSS APPLY (SELECT AI_ANALYZE_SENTIMENT(r.review_text) AS sentiment) AS s
WHERE r.stars = 5
  AND s.sentiment = 'negative';
