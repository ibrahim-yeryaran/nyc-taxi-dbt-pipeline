-- Fact: each row is one taxi trip. Measures and foreign keys to dimensions
-- live here. Derived metrics are also computed in this layer.

with trips as (

    select * from {{ ref('stg_yellow_trips') }}

),

final as (

    select
        -- Surrogate key: no natural key exists, so we generate a row number.
        -- (Deterministic and unique because it's materialized as a table.)
        row_number() over (order by pickup_at, dropoff_at) as trip_id,

        vendor_id,
        pickup_at,
        dropoff_at,

        -- Derived metric: trip duration (minutes)
        date_diff('second', pickup_at, dropoff_at) / 60.0 as trip_duration_minutes,

        passenger_count,
        trip_distance_miles,

        -- Derived metric: average speed (mph). Guarded against divide-by-zero.
        case
            when date_diff('second', pickup_at, dropoff_at) > 0
            then trip_distance_miles / (date_diff('second', pickup_at, dropoff_at) / 3600.0)
        end as average_speed_mph,

        -- Foreign keys to dimensions
        pickup_location_id,
        dropoff_location_id,

        payment_type_id,
        fare_amount,
        tip_amount,
        total_amount,

        -- Derived metric: tip ratio (relative to fare)
        case
            when fare_amount > 0 then tip_amount / fare_amount
        end as tip_pct,

        source_month

    from trips

)

select * from final
