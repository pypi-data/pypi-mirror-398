-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md

CREATE INDEX IF NOT EXISTS a.idx_freight_trips ON trip (tour);

DROP TABLE IF EXISTS freight_trips;
CREATE TABLE freight_trips AS
SELECT t.* 
FROM   a.trip t
WHERE  t.tour > 0;

CREATE INDEX IF NOT EXISTS idx_freight_trips ON freight_trips (tour, origin, destination);

-- Create table combining trip and delivery
DROP TABLE IF EXISTS trip_delivery;
CREATE TABLE trip_delivery AS
SELECT t.trip_id,
       t.path,
       t.mode,
       t.type,
       t.purpose,
       t.tour,
       t.start,
       t.end,
       t.origin,
       t.destination,
       t.routed_travel_time,
       t.travel_distance,
       d.leg AS tour_leg,
       d.volume
FROM freight_trips t
INNER JOIN delivery d ON t.tour = d.tour AND t.origin = d.origin_location AND t.destination = d.destination_location;


-- Add Shipment IDs
DROP TABLE IF EXISTS trip_shipment_delivery;
CREATE TABLE trip_shipment_delivery AS
SELECT    td.*, sd.shipment AS shipment, sd.shipment_leg AS shipment_leg 
FROM      trip_delivery td
LEFT JOIN shipment_delivery sd ON td.tour = sd.tour AND td.tour_leg = sd.tour_leg;

-- Finalize freight trip table
DROP TABLE IF EXISTS freight_trip;
CREATE TABLE freight_trip AS
SELECT td.*, ship.trade_pair, freight_mode_fn, ship.shipment_size
FROM      trip_shipment_delivery td
LEFT JOIN shipment ship ON td.shipment = ship.shipment;

-- 
DROP TABLE IF EXISTS freight_mode_trade_type;
CREATE TABLE freight_mode_trade_type AS
SELECT mode, freight_mode, trade_type_fn, count(*)*scaling_factor as trips, sum(travel_distance)/1609.3/1000000*scaling_factor as M_VMT, sum(end-start)/3600/1000000*scaling_factor as M_VHT
FROM (SELECT *, tf.trade_type
      FROM freight_trip ft
      LEFT JOIN Trade_Flow tf ON ft.trade_pair = tf.trade_pair WHERE shipment is not null)
GROUP BY 1,2,3;

-- Drop all temporary tables
DROP TABLE freight_trips;
DROP TABLE trip_delivery;
DROP TABLE trip_shipment_delivery;