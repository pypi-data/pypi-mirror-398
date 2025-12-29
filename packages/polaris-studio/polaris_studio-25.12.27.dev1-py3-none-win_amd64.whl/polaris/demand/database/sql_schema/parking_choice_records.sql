-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ A table for debugging the Parking choice model inputs.

CREATE TABLE Parking_Choice_Records (
    "id"                        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, --@ auto id for all parking choices available for this parking event
    "choice_id"                 INTEGER NOT NULL DEFAULT 0,  --@ Unique identifier of this parking choice id (to match with parking choice id in Parking Records)
    "person"                    INTEGER NOT NULL DEFAULT 0,  --@ The person driving the vehicle (to match with person id in Person table)
    "choice_event_time"         INTEGER NOT NULL DEFAULT 0,  --@ Time of the parking event
    "is_depart_pk"              INTEGER NOT NULL DEFAULT 0,  --@ Boolean flag - if the person departed for the activity in peak-hour?
    "act_dur_hr"                REAL             DEFAULT 0,  --@ Activity duration (hours)
    "female"                    INTEGER NOT NULL DEFAULT 0,  --@ Boolean flag - if the person is female?
    "hhsize"                    INTEGER NOT NULL DEFAULT 0,  --@ Household size of the person parking
    "ln_hhinc"                  REAL             DEFAULT 0,  --@ Natural logarithm of the household size
    "urgent"                    INTEGER NOT NULL DEFAULT 0,  --@ Boolean flag - if this activity is urgent?
    "age_above_60"              INTEGER NOT NULL DEFAULT 0,  --@ Boolean flag - if the person is above 60 years?
    "ln_dest_empdens"           REAL             DEFAULT 0,  --@ Natural logarithm of the activity zone employment density per acre
    "ln_dest_popdens"           REAL             DEFAULT 0,  --@ Natural logarithm of the activity zone population density per acre
    "destination"               INTEGER NOT NULL DEFAULT 0,  --@ Destination of the activity (to match with location id in Location table)
    "type"                      INTEGER NOT NULL DEFAULT 0,  --@ Type of parking !PARKING_CHOICE_TYPE!
    "distance_to_G"             REAL             DEFAULT 0,  --@ Distance from destination to the garage (kilometers)
    "parking_fee"               REAL             DEFAULT 0,  --@ Parking fee ($USD)
    "chosen"                    INTEGER NOT NULL DEFAULT 0,  --@ Boolean flag - if this specifc parking was chosen as an output of the choice model?
    "garage_id"                 INTEGER NOT NULL DEFAULT 0,  --@ Garage identifier (to match with parking id in Parking table)
    "reserved_or_not"           INTEGER NOT NULL DEFAULT 0,  --@ Boolean flag - if the parking was reserved or no?
    "num_garage_choices"        INTEGER NOT NULL DEFAULT 0,  --@ Number of garages with available capacity
    "garage_choices_existed"    INTEGER NOT NULL DEFAULT 0,  --@ Boolean flag - if there were any garages (even if full) nearby for the person to consider?
    "can_use_escooter"          INTEGER NOT NULL DEFAULT 0  --@ Boolean flag - if the person is willing to use an escooter ?
);