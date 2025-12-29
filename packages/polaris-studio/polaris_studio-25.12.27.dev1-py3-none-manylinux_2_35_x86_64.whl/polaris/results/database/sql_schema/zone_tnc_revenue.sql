-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ Zone_TNC_Revenue contains information of the aggregated revenue earned by shared mobility operators in each zone at every hour of the day.
--@ The surge factor imposed by travel from a particular origin zone is also logged for each hour in the day in the same record.
--@

CREATE TABLE "Zone_TNC_Revenue" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, --@ Record identifier
  "zone" INTEGER NOT NULL DEFAULT 0, --@ 0-ordered zone ID (for 0 through n-1 zones) 
  "hour" INTEGER NOT NULL DEFAULT 0, --@ Integer value (starting at 0) representing the starting hour of day for which the information is logged
  "surge_factor" REAL NULL DEFAULT 0, --@ Surge factor observed for zone
  "revenue" REAL NULL DEFAULT 0) --@ Revenue earned by all shared mobility operators for the specific hour in the specific zone