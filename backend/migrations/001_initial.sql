CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE listings (
  id            SERIAL PRIMARY KEY,
  source        VARCHAR(20)    NOT NULL,
  source_id     VARCHAR(100)   NOT NULL,
  url           TEXT           NOT NULL,
  title         TEXT,
  price         BIGINT,
  unit_price    INTEGER,
  area_ping     NUMERIC(8,2),
  rooms         SMALLINT,
  floor         SMALLINT,
  total_floors  SMALLINT,
  building_age  SMALLINT,
  district      VARCHAR(20),
  address       TEXT,
  lat           NUMERIC(10,7),
  lng           NUMERIC(10,7),
  photos        TEXT[]         DEFAULT '{}',
  is_active     BOOLEAN        DEFAULT true,
  scraped_at    TIMESTAMPTZ    DEFAULT NOW(),
  updated_at    TIMESTAMPTZ    DEFAULT NOW(),
  UNIQUE(source, source_id)
);

CREATE INDEX listings_geo ON listings
  USING GIST (ST_SetSRID(ST_MakePoint(lng::float8, lat::float8), 4326))
  WHERE lat IS NOT NULL AND lng IS NOT NULL;
CREATE INDEX listings_district ON listings (district);
CREATE INDEX listings_active   ON listings (is_active, scraped_at DESC);

CREATE TABLE price_records (
  id               SERIAL PRIMARY KEY,
  address          TEXT,
  district         VARCHAR(20),
  price            BIGINT,
  unit_price       INTEGER,
  area_ping        NUMERIC(8,2),
  building_type    VARCHAR(20),
  transaction_date DATE NOT NULL,
  lat              NUMERIC(10,7),
  lng              NUMERIC(10,7),
  imported_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX price_records_geo ON price_records
  USING GIST (ST_SetSRID(ST_MakePoint(lng::float8, lat::float8), 4326))
  WHERE lat IS NOT NULL AND lng IS NOT NULL;
CREATE INDEX price_records_date ON price_records (transaction_date DESC);
CREATE INDEX listings_district_active ON listings (district, is_active);
CREATE INDEX price_records_district_date ON price_records (district, transaction_date DESC);

CREATE TABLE scraper_status (
  id              SERIAL PRIMARY KEY,
  platform        VARCHAR(20) UNIQUE NOT NULL,
  status          VARCHAR(20)  DEFAULT 'ok',
  last_success    TIMESTAMPTZ,
  last_failure    TIMESTAMPTZ,
  failure_count   INTEGER      DEFAULT 0,
  error_log       TEXT,
  screenshot_path TEXT
);

INSERT INTO scraper_status (platform) VALUES
  ('591'), ('sinyi'), ('yungching'), ('rakuya'), ('etwarm');
