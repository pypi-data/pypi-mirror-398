-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ Zone_FMLM_Success stores the number of successful first-mile-last-mile (FMLM) trips to and from transit,
--@ by hour of day separately aggregated by origin and destination.

CREATE TABLE "Zone_FMLM_Success" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, --@ Record identifier
  "start" INTEGER NOT NULL DEFAULT 0, --@ Simulation time in seconds when information aggregation starts
  "end" INTEGER NOT NULL DEFAULT 0, --@ Simulation time in seconds when information aggregation ends
  "zone" INTEGER NOT NULL DEFAULT 0, --@ 0-based zone ID (for zones 0 through n-1)
  "o_success_prop" REAL NULL DEFAULT 0, --@ Proportion of trips that successfully executed a FMLM trip with zone being an origin
  "d_success_prop" REAL NULL DEFAULT 0, --@ Proportion of trips that successfully executed a FMLM trip with zone being a destination
  "o_attempts" INTEGER NOT NULL DEFAULT 0, --@ Total number of trips from demand model for which a router query was attempted with zone being an origin
  "d_attempts" INTEGER NOT NULL DEFAULT 0) --@ Total number of trips from demand model for which a router query was attempted with zone being a destination