-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ The parking table lists all parking facilities available in the model. It
--@ includes dedicated parking structures, as well as parking lots attached to
--@ business, residences and other activity locations.

create TABLE IF NOT EXISTS Parking(
    parking      INTEGER NOT NULL PRIMARY KEY, --@ The parking facility identifier
    link         INTEGER NOT NULL,  --@ Foreign key reference to one link that is the closest spatially to the parking
    zone         INTEGER NOT NULL,  --@ The zone to which this parking facility belong
    offset       REAL,              --@ Auto-generated value of how far from the parking (perpendicular) the link is present (meters)
    setback      INTEGER,           --@ Auto-generated value of how far from node_a of the link this parking is present along the length of the link (meters)
    "type"         TEXT,              --@ The parking type: garage, lot, metered, street, etc.
    space        INTEGER NOT NULL,  --@ The capacity of this parking facility
    walk_link    INTEGER,           --@ Foreign key reference to the nearest walk link from the Transit_Walk table
    walk_offset  REAL,              --@ Same as offset above, but for the walk link (meters)
    walk_setback  REAL,              --@ Same as setback above, but for the walk link (meters)
    bike_link    BIGINT,           --@ Foreign key reference to the nearest bike link from the Transit_Bike table
    bike_offset  REAL,              --@ Same as offset above, but for the bike link (meters)
    bike_setback  REAL,              --@ Same as setback above, but for the bike link (meters)
    num_escooters    INTEGER  DEFAULT 0,           --@ Number of e-scooters available at this parking
    close_time      INTEGER DEFAULT 864000,        --@ Garage closing working time stamp, if 24/7 set as an arbitrarily (10 days default) large number (seconds)  

    CONSTRAINT "zone_fk" FOREIGN KEY("zone") REFERENCES "Zone"("zone") DEFERRABLE INITIALLY DEFERRED
);

select AddGeometryColumn( 'Parking', 'geo', SRID_PARAMETER, 'POINT', 'XY', 1);
select CreateSpatialIndex( 'Parking' , 'geo' );

create INDEX IF NOT EXISTS "idx_polaris_parking" ON "Parking" ("parking");
create INDEX IF NOT EXISTS "idx_polaris_parking_zone" ON "Parking" ("zone");