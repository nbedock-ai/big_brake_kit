-- database/init.sql

DROP TABLE IF EXISTS rotors;
DROP TABLE IF EXISTS pads;
DROP TABLE IF EXISTS vehicles;

-- ------------------------------------------------------------
--  Rotors
-- ------------------------------------------------------------

CREATE TABLE rotors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    outer_diameter_mm REAL NOT NULL,
    nominal_thickness_mm REAL NOT NULL,
    hat_height_mm REAL NOT NULL,
    overall_height_mm REAL NOT NULL,
    center_bore_mm REAL NOT NULL,
    bolt_circle_mm REAL NOT NULL,
    bolt_hole_count INTEGER NOT NULL,
    ventilation_type TEXT NOT NULL,
    directionality TEXT NOT NULL,
    offset_mm REAL,

    rotor_weight_kg REAL,
    mounting_type TEXT,
    oem_part_number TEXT,
    pad_swept_area_mm2 REAL,

    brand TEXT NOT NULL,
    catalog_ref TEXT NOT NULL
);

-- ------------------------------------------------------------
--  Pads
-- ------------------------------------------------------------

CREATE TABLE pads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    shape_id TEXT NOT NULL,
    length_mm REAL NOT NULL,
    height_mm REAL NOT_NULL,
    thickness_mm REAL NOT_NULL,

    swept_area_mm2 REAL,
    backing_plate_type TEXT,

    brand TEXT NOT NULL,
    catalog_ref TEXT NOT NULL
);

-- ------------------------------------------------------------
--  Vehicles
-- ------------------------------------------------------------

CREATE TABLE vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    make TEXT NOT NULL,
    model TEXT NOT NULL,
    generation TEXT,
    year_from INTEGER NOT NULL,
    year_to INTEGER,

    hub_bolt_circle_mm REAL NOT NULL,
    hub_bolt_hole_count INTEGER NOT NULL,
    hub_center_bore_mm REAL NOT NULL,

    knuckle_bolt_spacing_mm REAL,
    knuckle_bolt_orientation_deg REAL,

    max_rotor_diameter_mm REAL,
    wheel_inner_barrel_clearance_mm REAL,
    rotor_thickness_min_mm REAL,
    rotor_thickness_max_mm REAL
);
