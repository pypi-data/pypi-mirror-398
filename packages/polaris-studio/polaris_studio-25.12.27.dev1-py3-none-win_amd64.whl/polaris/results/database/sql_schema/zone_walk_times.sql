-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ Zone_Walk_Times aggregates the average walk time experienced when using a shared mobility service (TNCs)
--@ The information in this table is relevant especially when a strategy actively requires requests to shift origins and destinations.
--@ If not all travel using the TNC mode is considered door-to-door.

CREATE TABLE "Zone_Walk_Times" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, --@ Record identifier
  "start" INTEGER NOT NULL DEFAULT 0, --@ Simulation time in seconds when data aggregation STARTS
  "walk_time_minutes" REAL NULL DEFAULT 0, --@ Average walk time experienced by requests in the zone at the specific hour
  "trips" INTEGER NOT NULL DEFAULT 0, --@ Number of trips used to aggregate the information
  "end" INTEGER NOT NULL DEFAULT 0, --@ Simulation time in seconds when data aggregation ENDS
  "zone" INTEGER NOT NULL DEFAULT 0) --@ 0-based zone ID (for zones 0 through n-1) for recording zone-specific information