-- Database schema for MIR ML Challenge
-- Creates all tables needed for CSV data loading

-- Population lookup table
CREATE TABLE IF NOT EXISTS population (
    code VARCHAR(20) PRIMARY KEY,
    population TEXT NOT NULL
);

-- Region lookup table
CREATE TABLE IF NOT EXISTS region (
    code VARCHAR(20) PRIMARY KEY,
    region VARCHAR(100) NOT NULL,
    description TEXT
);

-- Travel mode lookup table
CREATE TABLE IF NOT EXISTS travel_mode (
    code VARCHAR(20) PRIMARY KEY,
    mode VARCHAR(100) NOT NULL,
    description TEXT
);

-- Travel motives lookup table
CREATE TABLE IF NOT EXISTS travel_motives (
    code VARCHAR(20) PRIMARY KEY,
    motive VARCHAR(200) NOT NULL,
    description TEXT
);

-- Urbanization level lookup table
CREATE TABLE IF NOT EXISTS urbanization_level (
    id INTEGER,
    provinces VARCHAR(100),
    level_urbanization VARCHAR(50),
    area VARCHAR(100)
);

-- Main trips fact table
CREATE TABLE IF NOT EXISTS trips (
    id SERIAL PRIMARY KEY,
    "TravelMotives" VARCHAR(20),
    "Population" VARCHAR(20),
    "TravelModes" VARCHAR(20),
    "RegionCharacteristics" VARCHAR(20),
    "Periods" VARCHAR(20),
    "Trip in a year" NUMERIC,
    "Km travelled in a year" NUMERIC,
    "Hours travelled in a year" NUMERIC,
    "UserId" INTEGER
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_trips_travel_motives ON trips("TravelMotives");
CREATE INDEX IF NOT EXISTS idx_trips_population ON trips("Population");
CREATE INDEX IF NOT EXISTS idx_trips_travel_modes ON trips("TravelModes");
CREATE INDEX IF NOT EXISTS idx_trips_region ON trips("RegionCharacteristics");
CREATE INDEX IF NOT EXISTS idx_trips_periods ON trips("Periods");
CREATE INDEX IF NOT EXISTS idx_trips_user_id ON trips("UserId");