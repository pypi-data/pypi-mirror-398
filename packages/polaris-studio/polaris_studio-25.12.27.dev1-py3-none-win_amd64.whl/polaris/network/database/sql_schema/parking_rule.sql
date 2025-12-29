-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ The parking rule table lists the parking rules for each parking,
--@ the prioirty of applying this rule (if multiple rules exist), and
--@ the maximum duration for the application of that rule

create TABLE IF NOT EXISTS Parking_Rule (
    parking_rule      INTEGER NOT NULL PRIMARY KEY, --@ The parking rule identifier
    parking           INTEGER NOT NULL, --@ The parking facility identifier (Foreign key reference to the parking table)
    rule_type         INTEGER NOT NULL,  --@ Parking rule type !Parking_Rule_Type!
    rule_priority     INTEGER NOT NULL,  --@ Priority for applying this parking rule
    min_cost          REAL DEFAULT 0,  --@ Minimum cost associated with this parking rule ($)
    min_duration      REAL DEFAULT 0,  --@ Minimum duration of stay of vehicles under this parking rule (seconds)
    max_duration      REAL DEFAULT 86400,  --@ Maximum duration of stay of vehicles under this parking rule (seconds)

    CONSTRAINT "parking_fk" FOREIGN KEY("parking") REFERENCES "Parking"("parking") DEFERRABLE INITIALLY DEFERRED
);
