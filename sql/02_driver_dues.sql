-- =====================================================================
-- المستحقات الشهرية للسائقين (Monthly driver dues)
-- المستحق = قيمة الرحلات - الديزل + (الإضافات - الخصومات)
-- غيّر @month و @year لكل شهر
-- =====================================================================
USE muwasil_db;
GO

DECLARE @month INT = 9;
DECLARE @year  INT = 2026;

SELECT
    d.driver_id,
    d.name,
    b.branch_name,
    ISNULL(SUM(rs.trips_count), 0)                       AS total_trips,
    ISNULL(SUM(rs.trips_count * rr.price_per_trip), 0)   AS trips_value,
    ISNULL(ds.diesel_cost, 0)                            AS diesel_cost,
    ISNULL(adj.total_adjustments, 0)                     AS adjustments,
    ISNULL(SUM(rs.trips_count * rr.price_per_trip), 0)
        - ISNULL(ds.diesel_cost, 0)
        + ISNULL(adj.total_adjustments, 0)               AS due
FROM drivers d
JOIN branches b
    ON d.branch_id = b.branch_id
-- شروط الشهر في ON (مش WHERE) عشان السائق من غير رحلات يفضل ظاهر
LEFT JOIN route_stats rs
    ON d.driver_id = rs.driver_id AND rs.month = @month AND rs.year = @year
LEFT JOIN route_rates rr
    ON rr.route_id = rs.route_id
LEFT JOIN driver_monthly_diesel ds
    ON d.driver_id = ds.driver_id AND ds.month = @month AND ds.year = @year
-- تجميع الخصومات والإضافات لكل سائق أولاً، عشان ما تتضاعفش صفوف الرحلات
-- (amount بالسالب للخصم وبالموجب للإضافة)
LEFT JOIN (
    SELECT driver_id, SUM(amount) AS total_adjustments
    FROM driver_adjustments
    WHERE month = @month AND year = @year
    GROUP BY driver_id
) adj
    ON adj.driver_id = d.driver_id
GROUP BY b.branch_name, d.name, d.driver_id, ds.diesel_cost, adj.total_adjustments
ORDER BY b.branch_name, d.name;
GO