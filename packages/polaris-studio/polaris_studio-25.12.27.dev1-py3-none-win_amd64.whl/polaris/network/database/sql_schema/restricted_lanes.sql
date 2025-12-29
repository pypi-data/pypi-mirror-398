-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
--@ The Restricted_Lanes table holds information on lanes on a link that are restricted to a certain use. 
--@ This is currently only used for AV-only lanes at the moment but could be used to model HOV or HOT lanes.
--@


CREATE TABLE IF NOT EXISTS Restricted_Lanes(
 link              INTEGER        NOT NULL,             --@ Link ID of the link to which these restricted lanes apply
 direction         INTEGER        NOT NULL,             --@ Direction of travel for which these lanes apply (0=AB, 1=BA)
 "use"             STRING         NOT NULL,             --@ Not in use at the moment but will be used to distinguish different types of lane restrictions in the future
 lanes             INTEGER        NOT NULL,             --@ Number of lanes that are reserved for the restricted use
 speed             REAL           NOT NULL,             --@ Speed (in m/s) for the restricted lanes
 capacity          REAL           NOT NULL DEFAULT 0,   --@ Capacity (in veh/hour) for the combined restricted lanes (ie not veh/lane/hour)

 CONSTRAINT "link_id_fk" FOREIGN KEY("link") REFERENCES "Link"("link") DEFERRABLE INITIALLY DEFERRED
 CHECK(direction IN (0, 1))
 CHECK(TYPEOF(lanes) == 'integer')
 CHECK(lanes>0)
 CHECK(speed>0)
);

create INDEX IF NOT EXISTS idx_polaris_restricted_lanes_link ON Restricted_Lanes (link);