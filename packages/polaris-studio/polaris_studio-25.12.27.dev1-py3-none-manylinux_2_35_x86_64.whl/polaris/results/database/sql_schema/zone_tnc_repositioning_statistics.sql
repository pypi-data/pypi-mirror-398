-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ Table stores information related to zone-level outcomes after the 'joint_evcr' TNC strategy is solved.
--@ This is a strategy-specific table and is only generated when using the 'joint_evcr' strategy in the TNC fleet model file.
--@

CREATE TABLE "Zone_TNC_Repositioning_Statistics" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, --@ Record identifier
  "time" INTEGER NOT NULL DEFAULT 0, --@ Simulation time in seconds when the output of the solver is condensed and logged
  "zone" INTEGER NOT NULL DEFAULT 0, --@ 0-based zone ID (for zones 0 through n-1)
  "idle_veh" INTEGER NOT NULL DEFAULT 0, --@ Number of idle vehicles in the zone before optimization
  "avg_soc_idle" REAL NULL DEFAULT 0, --@ Average state of charge of all idle vehicles in zone
  "avail_plugs" INTEGER NOT NULL DEFAULT 0, --@ Total unused plugs at charging stations in the zone
  "out_repositioning_trips" INTEGER NOT NULL DEFAULT 0, --@ Number of vehicles repositioned to leave the zone after optimization
  "in_repositioning_trips" INTEGER NOT NULL DEFAULT 0, --@ Number of vehicles repositioned to arrive at the zone after optimization
  "out_charging_trips" INTEGER NOT NULL DEFAULT 0, --@ Number of vehicles sent to charge outside of the zone
  "in_charging_trips" INTEGER NOT NULL DEFAULT 0, --@ Number of vehicles that are asked to come to the zone to charge
  "slack" INTEGER NOT NULL DEFAULT 0) --@ Slack value of requirement unment at the zone from solving the optimization problem