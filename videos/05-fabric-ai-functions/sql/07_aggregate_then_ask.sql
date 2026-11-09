-- 5. Aggregate first, ask once: one AI call per product (16 instead of 260)
-- Toastly demo (PBI101 video 05). Run one query at a time.

WITH g AS (
    SELECT p.product_name, COUNT(*) AS reviews,
           STRING_AGG(CAST(r.review_text AS varchar(max)), ' | ') AS all_reviews
    FROM shop.product_reviews AS r
    JOIN shop.products AS p ON p.product_id = r.product_id
    GROUP BY p.product_name
)
SELECT product_name, reviews,
       AI_GENERATE_RESPONSE(
         'Below are all customer reviews of one product, in several languages. Reply in English, one line, max 15 words, exactly this format: Love: <top thing> | Hate: <top complaint>',
         all_reviews) AS cheat_sheet
FROM g
ORDER BY reviews DESC;
