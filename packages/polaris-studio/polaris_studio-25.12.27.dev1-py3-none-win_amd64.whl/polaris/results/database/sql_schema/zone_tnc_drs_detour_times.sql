-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ Table is currently unused
--@ Zone_TNC_DRS_Detour_Times stores the average detour experienced when using shared mobility services and pooling the ride when traveling
--@ aggregated by a combination of origin zone, destination zone, the time period of travel, and mode.

CREATE TABLE "Zone_TNC_DRS_Detour_Times" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "start" INTEGER NOT NULL DEFAULT 0,
  "avg_detour_minutes" REAL NULL DEFAULT 0,
  "end" INTEGER NOT NULL DEFAULT 0,
  "mode" INTEGER NOT NULL DEFAULT 0,
  "o_zone" INTEGER NOT NULL DEFAULT 0,
  "d_zone" INTEGER NOT NULL DEFAULT 0)