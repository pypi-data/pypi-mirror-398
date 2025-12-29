-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ Table records the average wait times observed for a shared mobility request to be picked up.
--@ Values are stored across all operators operating in the simulated region and by hour in day and origin zone.
--@

CREATE TABLE "ZoneWaitTimes" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, --@ Record identifier
  "start" INTEGER NOT NULL DEFAULT 0, --@ Simulation time in seconds when data aggregation STARTS
  "avg_wait_minutes" REAL NULL DEFAULT 0, --@ Average wait time for a request to be picked up in minutes
  "trips" INTEGER NOT NULL DEFAULT 0, --@ Number of trip requests that contributed to calculating the average
  "requests" INTEGER NOT NULL DEFAULT 0, --@ Unused. Will be removed.
  "end" INTEGER NOT NULL DEFAULT 0, --@ Simulation time in seconds for when data aggregation ENDS
  "mode" INTEGER NOT NULL DEFAULT 0, --@ Mode of travel for which average wait time is stored. !Vehicle_Type_Keys!
  "zone" INTEGER NOT NULL DEFAULT 0) --@ 0-based zone ID (or 0 through n-1 zones) to store average wait time