-- Only send new rows to the AI (and the NOT EXISTS trap)
-- Toastly demo (PBI101 video 05). Run one query at a time.

INSERT INTO shop.product_reviews
    (review_id, product_id, review_date, country, language, stars, review_text)
VALUES
(261, 5,  '2026-11-08', 'US', 'en', 5, 'Leaking again. Third time I''m writing this. Five stars so you actually read it.'),
(262, 11, '2026-11-08', 'IT', 'it', 5, 'Riso perfetto anche stasera. Il miglior acquisto dell''anno!'),
(263, 3,  '2026-11-08', 'CA', 'en', 2, 'Coating is peeling AGAIN on the replacement basket. Unreal.');

DECLARE @last int = (SELECT MAX(review_id) FROM ai.review_enriched);

INSERT INTO ai.review_enriched
SELECT review_id, product_id, stars, review_text,
       ISNULL(AI_ANALYZE_SENTIMENT(review_text), 'unknown'),
       ISNULL(AI_CLASSIFY(review_text, 'build quality', 'performance', 'noise',
                          'cleaning', 'delivery', 'other'), 'unknown'),
       'v1', CAST(SYSUTCDATETIME() AS datetime2(0))
FROM shop.product_reviews
WHERE review_id > @last;   -- only the rows the AI hasn't seen

SELECT review_id, stars, review_text, sentiment, topic, processed_at
FROM ai.review_enriched
WHERE review_id > 260;

-- THE TRAP (measured 2026-11-08): this looks incremental, but the AI functions run BEFORE the anti-join,
-- so all 263 rows went to the AI for 3 new ones (and 260 with zero new rows). Check it in 14_what_did_i_send.sql.
-- INSERT INTO ai.review_enriched
-- SELECT r.review_id, ..., AI_ANALYZE_SENTIMENT(r.review_text), ...
-- FROM shop.product_reviews AS r
-- WHERE NOT EXISTS (SELECT 1 FROM ai.review_enriched AS e WHERE e.review_id = r.review_id);
--
-- Also works (only the new rows go to the AI): stage the new rows first, without AI, then run the AI on the stage:
-- SELECT r.* INTO #new FROM shop.product_reviews AS r
-- WHERE NOT EXISTS (SELECT 1 FROM ai.review_enriched AS e WHERE e.review_id = r.review_id);
-- INSERT INTO ai.review_enriched SELECT ..., AI_ANALYZE_SENTIMENT(review_text), ... FROM #new;

