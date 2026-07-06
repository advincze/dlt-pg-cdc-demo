CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  customer_name TEXT NOT NULL,
  amount NUMERIC(10,2) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE PUBLICATION my_pub FOR TABLE orders;
