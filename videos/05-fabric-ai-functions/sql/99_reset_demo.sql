-- Reset the demo to the start of the video (keeps shop.products / reviews / emails as loaded).
DELETE FROM shop.product_reviews WHERE review_id > 260;   -- the 3 "new" reviews from 13_only_new_rows.sql
DROP TABLE IF EXISTS ai.review_enriched;
