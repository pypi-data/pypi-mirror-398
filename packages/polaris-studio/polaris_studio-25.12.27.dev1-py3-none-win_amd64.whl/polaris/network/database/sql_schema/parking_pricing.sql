-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ The parking pricing table lists the price for each time range
--@ for a specific parking rule at a given parking 

create TABLE IF NOT EXISTS Parking_Pricing (
    parking           INTEGER NOT NULL, --@ The parking facility identifier (Foreign key reference to the parking table)
    parking_rule      INTEGER NOT NULL,  --@ Parking rule type (Foreign key reference to the parking_rule table)
    entry_start       INTEGER NOT NULL,  --@ Start of the entry time range when the price is applicable for this parking rule (seconds)
    entry_end         INTEGER NOT NULL,  --@ End of the entry time range when the price is applicable for this parking rule (seconds)
    price             REAL    NOT NULL,  --@ Parking price for the current parking rule and time range ($)

    CONSTRAINT "parking_fk" FOREIGN KEY("parking") REFERENCES "Parking"("parking") DEFERRABLE INITIALLY DEFERRED
    CONSTRAINT "parking_rule_fk" FOREIGN KEY("parking_rule") REFERENCES "Parking_Rule"("parking_rule") DEFERRABLE INITIALLY DEFERRED
);
