-- Fact: her satır bir taksi yolculuğu. Ölçümler (measures) ve dimension'lara
-- foreign key'ler burada. Türetilmiş metrikler de bu katmanda hesaplanır.

with trips as (

    select * from {{ ref('stg_yellow_trips') }}

),

final as (

    select
        -- Surrogate key: doğal anahtar olmadığı için satır numarası üretiyoruz.
        -- (table olarak materyalize edildiği için deterministik ve benzersiz.)
        row_number() over (order by pickup_at, dropoff_at) as trip_id,

        vendor_id,
        pickup_at,
        dropoff_at,

        -- Türetilmiş metrik: yolculuk süresi (dakika)
        date_diff('second', pickup_at, dropoff_at) / 60.0 as trip_duration_minutes,

        passenger_count,
        trip_distance_miles,

        -- Türetilmiş metrik: ortalama hız (mil/saat). Sıfıra bölmeye karşı korumalı.
        case
            when date_diff('second', pickup_at, dropoff_at) > 0
            then trip_distance_miles / (date_diff('second', pickup_at, dropoff_at) / 3600.0)
        end as average_speed_mph,

        -- Dimension'lara foreign key'ler
        pickup_location_id,
        dropoff_location_id,

        payment_type_id,
        fare_amount,
        tip_amount,
        total_amount,

        -- Türetilmiş metrik: bahşiş oranı (ücrete göre)
        case
            when fare_amount > 0 then tip_amount / fare_amount
        end as tip_pct,

        source_month

    from trips

)

select * from final
