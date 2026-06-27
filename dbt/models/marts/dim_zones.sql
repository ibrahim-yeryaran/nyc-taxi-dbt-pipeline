-- Dimension: taxi zones. Descriptive attributes for each zone.
-- fct_trips joins to this table via location_id (star schema).

with zones as (

    select * from {{ ref('stg_taxi_zones') }}

)

select
    location_id,        -- primary key (fct_trips links here via FK)
    borough,
    zone_name,
    service_zone

from zones
