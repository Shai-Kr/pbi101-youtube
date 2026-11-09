-- Video 05: Fabric Warehouse AI functions. Toastly demo tables (synthetic data).
-- Run in a Fabric Warehouse (any name). Each CREATE SCHEMA must run as its own batch.
-- Fabric Warehouse tables use varchar (UTF-8), not nvarchar, and smallint instead of tinyint.

CREATE SCHEMA shop;   -- raw data
GO
CREATE SCHEMA ai;     -- stored AI results
GO

CREATE TABLE shop.products
(
    product_id   int           NOT NULL,
    product_name varchar(100)  NOT NULL,
    category     varchar(50)   NOT NULL,
    price        decimal(10,2) NOT NULL
);

CREATE TABLE shop.product_reviews
(
    review_id   int            NOT NULL,
    product_id  int            NOT NULL,
    review_date date           NOT NULL,
    country     char(2)        NOT NULL,
    language    char(2)        NOT NULL,
    stars       smallint       NOT NULL,
    review_text varchar(2000)  NOT NULL
);

CREATE TABLE shop.support_emails
(
    email_id       int           NOT NULL,
    received_at    datetime2(0)  NOT NULL,
    customer_name  varchar(100)  NOT NULL,
    customer_email varchar(200)  NOT NULL,
    subject        varchar(200)  NOT NULL,
    body           varchar(4000) NOT NULL
);
