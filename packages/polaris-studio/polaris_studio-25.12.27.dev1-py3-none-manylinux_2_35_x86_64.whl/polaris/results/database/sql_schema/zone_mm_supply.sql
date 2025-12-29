-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ The Zone_MM_Supply table records the number of escooter available by zone and time of the day.
--@ 
--@

CREATE TABLE "Zone_MM_Supply" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, --@ The unique identifier of escooter availability by zone and time of day
  "zone" INTEGER NOT NULL DEFAULT 0, --@ 0-based identifier (for zones 0 through n-1)
  "hour" INTEGER NOT NULL DEFAULT 0, --@ Integer representing starting hour of the day, the duration of which information is logged
  "escooter_availability" INTEGER NOT NULL DEFAULT 0, --@ Number of escooters available in the zone within the simulation (scaling needs to be considered if using for analysis)
  "avg_walk_access_minutes" REAL NULL DEFAULT 0 --@ Average walking time to access an escooter in minutes
  )