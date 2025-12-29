-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ The parking occupancy table lists the occupancy of the parking 
--@ during each time interval

create TABLE IF NOT EXISTS "Parking_Occupancy" (
    "parking_id"        INTEGER NOT NULL,  --@ The parking facility identifier
    "start"             INTEGER NOT NULL,  --@ Start of the time interval when the occupancy is calculated (seconds)
    "end"               INTEGER NOT NULL,  --@ End of the time interval when the occupancy is calculated (seconds)
    "occupancy"         REAL    NOT NULL   --@ Parking occupancy percentage compared to the parking capacity
);
