-- What did I really send? Query Insights
-- Toastly demo (PBI101 video 05). Run one query at a time.

SELECT TOP 8 h.start_time, s.function_name, s.rows_total,
       LEFT(h.command, 60) AS query
FROM queryinsights.external_api_call_stats AS s
JOIN queryinsights.exec_requests_history AS h
  ON h.distributed_statement_id = s.distributed_statement_id
ORDER BY h.start_time DESC;
