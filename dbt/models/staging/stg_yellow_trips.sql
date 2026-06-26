-- Staging: ham yolculuk verisini temizler ve standartlaştırır.
--  * kolon isimlerini okunabilir snake_case'e çevirir
--  * tipleri netleştirir
--  * bariz hatalı satırları eler (negatif tutar/mesafe, ters tarih)

with source as (

    select * from {{ source('raw', 'yellow_trips') }}

),

cleaned as (

    select
        cast(VendorID as integer)            as vendor_id,
        tpep_pickup_datetime                 as pickup_at,
        tpep_dropoff_datetime                as dropoff_at,
        cast(passenger_count as integer)     as passenger_count,
        trip_distance                        as trip_distance_miles,
        cast(PULocationID as integer)        as pickup_location_id,
        cast(DOLocationID as integer)        as dropoff_location_id,
        cast(payment_type as integer)        as payment_type_id,
        fare_amount,
        tip_amount,
        total_amount,
        source_month

    from source

    -- Temel veri kalitesi filtreleri
    where tpep_pickup_datetime < tpep_dropoff_datetime
      and trip_distance >= 0
      and total_amount >= 0

)

select * from cleaned
