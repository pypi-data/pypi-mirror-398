-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ Table contains a list of generated electric vehicle charging stations
--@ Records in this table are only generated when using the heuristic in-simulation siting algorithm

CREATE TABLE "Generated_EVCS" (
  "ID" INTEGER NOT NULL PRIMARY KEY, --@ Unique identifier of generated/existing electric vehicle charging station
  "Latitude" REAL NULL DEFAULT 0, --@ Not used
  "Longitude" REAL NULL DEFAULT 0, --@ Not used
  "num_plugs_L1" INTEGER NOT NULL DEFAULT 0, --@ Number of Level 1 plugs at charging station with a power rating of about 1000 W
  "num_plugs_L2" INTEGER NOT NULL DEFAULT 0, --@ Number of Level 2 plugs at charging station with a power rating of about 7000 w
  "num_plugs_DCFC" INTEGER NOT NULL DEFAULT 0, --@ Number of Direct Current Fast Charging (DCFC) plugs at charging station with a power rating of about 50,000 W
  "location" INTEGER NOT NULL DEFAULT 0, --@ Location ID from Location table in Supply on where the new charging stations
  "zone" INTEGER NOT NULL DEFAULT 0) --@ Zone ID from Zone table in Supply on which zone contains the new charging station