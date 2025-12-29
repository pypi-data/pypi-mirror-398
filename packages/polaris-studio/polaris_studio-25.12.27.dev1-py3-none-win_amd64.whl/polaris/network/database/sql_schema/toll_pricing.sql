-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ Toll pricing table provides the ability to set time-varying tolls on a given
--@ link/direction which are differentiated by time of day and vehicle class.
--@

CREATE TABLE IF NOT EXISTS Toll_Pricing(
    link            INTEGER NOT NULL,               --@ link identifier of the link that is to be tolled
    dir             INTEGER NOT NULL DEFAULT 0,     --@ direction of link (AB or BA, as 0 or 1) that is to be tolled
    start_time      INTEGER NOT NULL DEFAULT 0,     --@ Entry start time in seconds from when toll is active
    end_time        INTEGER NOT NULL DEFAULT 0,     --@ Entry end time in seconds after which toll specified is not active
    price           REAL    NOT NULL DEFAULT 0,     --@ Toll price paid by passenger vehicles
    md_price        REAL    NOT NULL DEFAULT 0,     --@ Toll price paid by medium duty vehicles (can be null, default value assumed as 1.5x price and can be customized in the scenario file)
    hd_price        REAL    NOT NULL DEFAULT 0,     --@ Toll price paid by heavy duty vehicles (can be null, default value assumed as 2x price and can be customized in the scenario file)

    CONSTRAINT "link_fk" FOREIGN KEY("link") REFERENCES "Link"("link") DEFERRABLE INITIALLY DEFERRED -- check
    CHECK("dir" >= 0),
    CHECK("dir" >= 0),
    CHECK("price" >= 0),
    CHECK(TYPEOF("dir") == 'integer')
);