-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ TNC_Statistics contains all the aggregated outputs of the shared mobility simulation.
--@ Results are stored for each vehicle across all the operators simulated
--@

CREATE TABLE "TNC_Statistics" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, --@ Record id for a unique row
  "tnc_operator" TEXT NOT NULL DEFAULT '', --@ Text description of the operator name, such as Operator_1
  "tnc_id" INTEGER NOT NULL DEFAULT 0, --@ 1-ordered ID of TNC vehicles within a specific operator
  "vehicle_id" INTEGER NOT NULL DEFAULT 0, --@ Vehicle ID corresponding to the Vehicle table in Demand and is typically used in all Demand-related tables
  "human_driver" INTEGER NOT NULL DEFAULT 0, --@ Boolean to denote whether this vehicle was driven by a human driver or was controlled in an automated fashion by the operator
  "driver_reloc_type" INTEGER NOT NULL DEFAULT 0, --@ Driver relocation type uses an enum to define the different behaviors experienced by TNC drivers while waiting for a request. !TNC_Driver_Type!
  "start" INTEGER NOT NULL DEFAULT 0, --@ Simulation time in seconds when TNC vehicle begins operations
  "end" INTEGER NOT NULL DEFAULT 0, --@ Simulation time in seconds when TNC vehicle ends operations
  "tot_pickups" INTEGER NOT NULL DEFAULT 0, --@ Total number of pickups successfully completed by vehicle in the simulation
  "tot_dropoffs" INTEGER NOT NULL DEFAULT 0, --@ Total number of dropoffs successfully completed by vehicle in the simulation
  "num_same_OD_trips" INTEGER NOT NULL DEFAULT 0, --@ Integer value recording if there were trips starting and ending from the same location/link
  "enroute_switches" INTEGER NOT NULL DEFAULT 0, --@ Total number of reroute/detours requested of the vehicle while serving all trips
  "charging_trips" INTEGER NOT NULL DEFAULT 0, --@ Total number of trips to an electric vehicle charging station made by vehicle
  "maintenance_trips" INTEGER NOT NULL DEFAULT 0, --@ Total number of trips for maintenance made by vehicle
  "cleaning_trips" INTEGER NOT NULL DEFAULT 0, --@ Total number of trips for cleaning only made by vehicle
  "parking_trips" INTEGER NOT NULL DEFAULT 0, --@ Total number of trips for parking made by vehicle
  "revenue" REAL NULL DEFAULT 0, --@ Total revenue earned by vehicle in serving requests while in operation
  "target_income" REAL NULL DEFAULT 0, --@ If human driver, an estimate of target income desired to be earned by driver while in operation
  "initial_loc" INTEGER NOT NULL DEFAULT 0, --@ Location ID consistent with the Location table of where the vehicle began operations from in the simulation period
  "final_loc" INTEGER NOT NULL DEFAULT 0, --@ Location ID consistent with the Location table of where the vehicle ended operations at in the simulation period
  "trip_requests" INTEGER NOT NULL DEFAULT 0, --@ Total number of requests passed along to the vehicle after several conditions are evaluated (such as proximity and detour if shared)
  "trip_rejections" INTEGER NOT NULL DEFAULT 0, --@ If human driver, total number of requests rejected by driver. Always lesser than or equal to trip_requests.
  "driver_rating" REAL NOT NULL DEFAULT 0, --@ Driver rating set from a distribution and tracked to repeat across iterations.
  "service_type" INTEGER NOT NULL DEFAULT 0, --@ Integer from an enum list representing the type of service offered by the vehicle. @@ TNC_Service_Types @@
  "num_seats" INTEGER NOT NULL DEFAULT 0) --@ Number of seats offered by the vehicle, especially useful for pooling but also when requests need a minimum number of available seats.