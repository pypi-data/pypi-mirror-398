-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ Traveler_Logsum generates logsum values from evaluating different choice models during simulation.
--@ When choice model queries are repeated in simulation, logsum values are aggregated and reported here.
--@
--@ Not currently advised to use information from this table.

CREATE TABLE "Traveler_Logsum" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, --@ Record identifier
  "person" INTEGER NOT NULL DEFAULT 0, --@ Person ID consistent with Person table in demand whose logsums are reported
  "household" INTEGER NOT NULL DEFAULT 0, --@ Household ID consistent to Household table in demand to which person belongs
  "origin_zone" INTEGER NOT NULL DEFAULT 0, --@ 0-based zone ID (for zones 0 through n-1) to store logsums by zone where choice model was queried
  "mc_logsum" REAL NULL DEFAULT 0, --@ Aggregating mode choice related logsum 
  "dc_logsum" REAL NULL DEFAULT 0) --@ Aggregating destination choice related logsum