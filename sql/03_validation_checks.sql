-- =====================================================================
-- فحوصات جودة البيانات (Data quality checks) بعد كل تشغيل شهري
-- كل فحص المفروض يرجع فاضي (أو الرقم المتوقع)
-- =====================================================================
USE muwasil_db;
GO

-- 1) عدد السائقين الكلي (للمقارنة بعدد صفوف الشيت)
SELECT COUNT(*) AS total_drivers FROM drivers;

-- 2) سائقين مكرّرين بعد توحيد المسافات (المفروض فاضي)
SELECT LTRIM(RTRIM(REPLACE(REPLACE(name, '  ', ' '), '  ', ' '))) AS clean_name,
       COUNT(*) AS how_many
FROM drivers
GROUP BY LTRIM(RTRIM(REPLACE(REPLACE(name, '  ', ' '), '  ', ' ')))
HAVING COUNT(*) > 1;

-- 3) سائقين بدون فرع (المفروض فاضي - branch_id إلزامي)
SELECT driver_id, name FROM drivers WHERE branch_id IS NULL;

-- 4) رحلات على مسارات غير موجودة في route_rates (المفروض فاضي)
SELECT rs.id, rs.route_id
FROM route_stats rs
LEFT JOIN route_rates rr ON rr.route_id = rs.route_id
WHERE rr.route_id IS NULL;

-- 5) الشهور المحمّلة في كل جدول (للتأكد إن الشهر الصح اتحمّل)
SELECT 'route_stats' AS source, year, month, COUNT(*) AS rows_n
FROM route_stats GROUP BY year, month
UNION ALL
SELECT 'diesel', year, month, COUNT(*) FROM driver_monthly_diesel GROUP BY year, month
UNION ALL
SELECT 'adjustments', year, month, COUNT(*) FROM driver_adjustments GROUP BY year, month
ORDER BY source, year, month;

-- 6) سائقين بدون صف ديزل في شهر معيّن (غيّر الشهر والسنة)
DECLARE @month INT = 9, @year INT = 2026;
SELECT d.driver_id, d.name
FROM drivers d
LEFT JOIN driver_monthly_diesel ds
    ON ds.driver_id = d.driver_id AND ds.month = @month AND ds.year = @year
WHERE ds.driver_id IS NULL;
GO