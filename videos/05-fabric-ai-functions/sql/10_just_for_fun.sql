-- Just for fun: the doorstop review as a haiku
-- Toastly demo (PBI101 video 05). Run one query at a time.

SELECT review_text,
       AI_GENERATE_RESPONSE('Turn this product review into a haiku. Just the haiku.', review_text) AS haiku
FROM shop.product_reviews
WHERE review_id = 4;
