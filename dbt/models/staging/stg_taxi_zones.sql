-- Staging: cleans/standardizes the zone lookup table.

with source as (

    select * from {{ source('raw', 'taxi_zones') }}

)

select
    cast(LocationID as integer) as location_id,
    Borough                     as borough,
    Zone                        as zone_name,
    service_zone

from source
