-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
-- Comment line is the error message we will insert the error info in

-- Freight DB checks;

-- {} Airport(s) have X or Ys that differ from the geometry by more than 0.1 m
SELECT COUNT(*) from Airport where round(x-ST_X(geo),1)>0.1 or round(y-ST_Y(geo), 1)>0.1;

-- {} International_Port(s) have X or Ys that differ from the geometry by more than 0.1 m
SELECT COUNT(*) from International_Port where round(x-ST_X(geo),1)>0.1 or round(y-ST_Y(geo), 1)>0.1;

-- {} Railport(s) have X or Ys that differ from the geometry by more than 0.1 m
SELECT COUNT(*) from Railport where round(x-ST_X(geo),1)>0.1 or round(y-ST_Y(geo), 1)>0.1;