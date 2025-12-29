-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ An output table for the simulated parking events.
--@ For each parking event, it records the vehicle, driver, 
--@ parking location, parking start and end time and the parking cost 


CREATE TABLE Parking_Records (
    "id"                INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, --@ Unique identifier of this Parking event
    "Parking_ID"        INTEGER NOT NULL DEFAULT -1, --@ The parking facility at which this event occurred (to match with parking id in Parking table)
    "Location_ID"       INTEGER NOT NULL DEFAULT -1, --@ Optional, the location where this event occurred; only used where no nearby parking facility is available (foreign key to Location table)
    "Link_ID"           INTEGER NOT NULL DEFAULT 0,  --@ The link from which the parking event occurred (to match with link id in Link table)
    "vehicle"           INTEGER NOT NULL DEFAULT 0,  --@ The vehicle being parked (to match with vehicle id in Vehicle table)
    "person"            INTEGER NOT NULL DEFAULT 0,  --@ The person driving the vehicle (to match with person id in Person table)
    "Time_In"           INTEGER NOT NULL DEFAULT 0,  --@ Time stamp when the vehicle started parking (units: seconds)
    "Time_Out"          INTEGER NOT NULL DEFAULT 0,  --@ Time stamp when the vehicle exited parking (units: seconds)
    "Is_TNC_Vehicle"    INTEGER NOT NULL DEFAULT 0,  --@ Boolean flag - is this a TNC vehicle?
    "Cost"              REAL             DEFAULT 0,  --@ The vehicle's parking cost ($USD)
    "Choice_ID"         INTEGER NOT NULL DEFAULT 0,  --@ The parking choice identifier
    "Escooter_Borrowed" INTEGER NOT NULL DEFAULT 0   --@ Boolean flag - is there an escooter borrowed by the user after parking?
);
