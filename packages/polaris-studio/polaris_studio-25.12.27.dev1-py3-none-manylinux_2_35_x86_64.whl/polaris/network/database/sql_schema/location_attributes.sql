-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ The Location_Attributes table holds numerical location attributes
--@ like enrolments or employment.
--@
--@ This table is connected to location.
--@
--@ Required by all models.

create TABLE IF NOT EXISTS Location_Attributes(
    location         INTEGER NOT NULL PRIMARY KEY,    --@ Foreign key reference to the location this entry refers to
    enrolments       REAL             DEFAULT 0,      --@ Number of enrolments. Used in school location choice.

   CONSTRAINT "location_fk" FOREIGN KEY("location") REFERENCES "location"("location") DEFERRABLE INITIALLY DEFERRED
);

create INDEX IF NOT EXISTS "idx_polaris_Location_Attributes_location" ON "Location_Attributes" ("location");

