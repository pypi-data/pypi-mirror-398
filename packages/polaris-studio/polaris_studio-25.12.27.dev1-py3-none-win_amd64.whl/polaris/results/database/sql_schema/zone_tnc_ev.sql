-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ Zone_TNC_EV table shows information of all electric TNC vehicles across the simulation day.
--@
--@

CREATE TABLE "Zone_TNC_EV" (
  "time" INTEGER NOT NULL DEFAULT 0, --@ Simulation time in seconds when EV-related metrics for vehicle is logged to database
  "tnc_id" INTEGER NOT NULL DEFAULT 0, --@ 1-based ID for TNC vehicle within a TNC operator
  "vehicle_id" INTEGER NOT NULL DEFAULT 0, --@ Vehicle ID consistent with Vehicle table in Demand
  "SoC" REAL NULL DEFAULT 0, --@ Percentage of energy contained in the battery
  "charging_trips" INTEGER NOT NULL DEFAULT 0, --@ Cumulative count of trips made to charging station
  "zone" INTEGER NOT NULL DEFAULT 0, --@ Zone ID of vehicle at the time when the record is created
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT) --@ Record identifier