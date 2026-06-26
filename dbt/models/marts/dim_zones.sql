-- Dimension: taksi bölgeleri. Her bölge için tanımlayıcı özellikler.
-- fct_trips bu tabloya location_id üzerinden bağlanır (yıldız şeması).

with zones as (

    select * from {{ ref('stg_taxi_zones') }}

)

select
    location_id,        -- birincil anahtar (fct_trips buraya FK ile bağlanır)
    borough,
    zone_name,
    service_zone

from zones
