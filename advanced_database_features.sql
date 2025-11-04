-- Advanced Database Features for Smart Parking System
-- Run this in MySQL Workbench after the main database is created
-- This adds: Triggers, Functions, CTEs, and Views

USE smart_parking_database_1;

-- ============================================
-- 1. USER-DEFINED FUNCTIONS
-- ============================================

-- Function to calculate parking cost
DROP FUNCTION IF EXISTS calculate_parking_cost;
DELIMITER $$
CREATE FUNCTION calculate_parking_cost(
    p_lot_id INT,
    p_start_time DATETIME,
    p_end_time DATETIME
) RETURNS DECIMAL(10,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_hourly_rate DECIMAL(10,2);
    DECLARE v_hours DECIMAL(10,2);
    DECLARE v_total_cost DECIMAL(10,2);
    
    SELECT hourly_rate INTO v_hourly_rate
    FROM parking_lots
    WHERE lot_id = p_lot_id;
    
    IF v_hourly_rate IS NULL THEN
        RETURN 0;
    END IF;
    
    SET v_hours = CEIL(TIMESTAMPDIFF(MINUTE, p_start_time, p_end_time) / 60.0);
    SET v_total_cost = v_hours * v_hourly_rate;
    
    RETURN v_total_cost;
END$$
DELIMITER ;

-- Function to check if parking lot has available spots
DROP FUNCTION IF EXISTS check_available_spots;
DELIMITER $$
CREATE FUNCTION check_available_spots(p_lot_id INT) RETURNS INT
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_available INT;
    
    SELECT available_spots INTO v_available
    FROM parking_lots
    WHERE lot_id = p_lot_id;
    
    RETURN IFNULL(v_available, 0);
END$$
DELIMITER ;

-- Function to get parking lot status
DROP FUNCTION IF EXISTS get_lot_status;
DELIMITER $$
CREATE FUNCTION get_lot_status(p_lot_id INT) RETURNS VARCHAR(20)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_available INT;
    
    SELECT status, available_spots INTO v_status, v_available
    FROM parking_lots
    WHERE lot_id = p_lot_id;
    
    IF v_status = 'closed' THEN
        RETURN 'closed';
    ELSEIF v_available <= 0 THEN
        RETURN 'full';
    ELSE
        RETURN 'available';
    END IF;
END$$
DELIMITER ;

-- ============================================
-- 2. TRIGGERS
-- ============================================

-- Trigger: Auto-update available_spots when a reservation is created
DROP TRIGGER IF EXISTS after_reservation_insert;
DELIMITER $$
CREATE TRIGGER after_reservation_insert
AFTER INSERT ON reservations
FOR EACH ROW
BEGIN
    -- Decrease available spots
    UPDATE parking_lots
    SET available_spots = available_spots - 1
    WHERE lot_id = NEW.lot_id;
    
    -- Mark one parking spot as occupied
    UPDATE parking_spots
    SET is_occupied = 1
    WHERE lot_id = NEW.lot_id 
    AND is_occupied = 0
    LIMIT 1;
END$$
DELIMITER ;

-- Trigger: Auto-update available_spots when a reservation is deleted/cancelled
DROP TRIGGER IF EXISTS after_reservation_delete;
DELIMITER $$
CREATE TRIGGER after_reservation_delete
AFTER DELETE ON reservations
FOR EACH ROW
BEGIN
    -- Increase available spots only if reservation was active
    IF OLD.status = 'active' THEN
        UPDATE parking_lots
        SET available_spots = available_spots + 1
        WHERE lot_id = OLD.lot_id;
        
        -- Free up one parking spot
        UPDATE parking_spots
        SET is_occupied = 0
        WHERE lot_id = OLD.lot_id 
        AND is_occupied = 1
        LIMIT 1;
    END IF;
END$$
DELIMITER ;

-- Trigger: Auto-update when reservation status changes
DROP TRIGGER IF EXISTS after_reservation_update;
DELIMITER $$
CREATE TRIGGER after_reservation_update
AFTER UPDATE ON reservations
FOR EACH ROW
BEGIN
    -- If status changed from active to completed/cancelled
    IF OLD.status = 'active' AND NEW.status != 'active' THEN
        UPDATE parking_lots
        SET available_spots = available_spots + 1
        WHERE lot_id = NEW.lot_id;
        
        -- Free up parking spot
        UPDATE parking_spots
        SET is_occupied = 0
        WHERE lot_id = NEW.lot_id 
        AND is_occupied = 1
        LIMIT 1;
    END IF;
END$$
DELIMITER ;

-- Trigger: Audit log for parking lot changes (create audit table first)
CREATE TABLE IF NOT EXISTS parking_lot_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    lot_id INT NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_value VARCHAR(255),
    new_value VARCHAR(255),
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TRIGGER IF EXISTS parking_lot_audit_trigger;
DELIMITER $$
CREATE TRIGGER parking_lot_audit_trigger
AFTER UPDATE ON parking_lots
FOR EACH ROW
BEGIN
    IF OLD.hourly_rate != NEW.hourly_rate THEN
        INSERT INTO parking_lot_audit (lot_id, action, old_value, new_value)
        VALUES (NEW.lot_id, 'rate_change', OLD.hourly_rate, NEW.hourly_rate);
    END IF;
    
    IF OLD.status != NEW.status THEN
        INSERT INTO parking_lot_audit (lot_id, action, old_value, new_value)
        VALUES (NEW.lot_id, 'status_change', OLD.status, NEW.status);
    END IF;
END$$
DELIMITER ;

-- ============================================
-- 3. VIEWS
-- ============================================

-- View: Parking lot availability summary
CREATE OR REPLACE VIEW v_parking_lot_summary AS
SELECT 
    lot_id,
    lot_name,
    location,
    total_spots,
    available_spots,
    (total_spots - available_spots) as occupied_spots,
    ROUND((available_spots / total_spots * 100), 2) as availability_percent,
    hourly_rate,
    status,
    CASE 
        WHEN available_spots = 0 THEN 'FULL'
        WHEN available_spots <= 5 THEN 'LOW'
        ELSE 'AVAILABLE'
    END as availability_status
FROM parking_lots;

-- View: User booking history with details
CREATE OR REPLACE VIEW v_user_bookings AS
SELECT 
    r.reservation_id,
    r.user_id,
    u.name as user_name,
    u.email,
    r.lot_id,
    p.lot_name,
    p.location,
    r.start_time,
    r.end_time,
    TIMESTAMPDIFF(HOUR, r.start_time, r.end_time) as duration_hours,
    r.total_cost,
    r.status,
    r.created_at
FROM reservations r
JOIN users u ON r.user_id = u.user_id
JOIN parking_lots p ON r.lot_id = p.lot_id;

-- View: Revenue summary by parking lot
CREATE OR REPLACE VIEW v_lot_revenue_summary AS
SELECT 
    p.lot_id,
    p.lot_name,
    p.location,
    COUNT(r.reservation_id) as total_bookings,
    SUM(r.total_cost) as total_revenue,
    AVG(r.total_cost) as avg_booking_cost,
    MAX(r.total_cost) as max_booking_cost,
    MIN(r.total_cost) as min_booking_cost
FROM parking_lots p
LEFT JOIN reservations r ON p.lot_id = r.lot_id
GROUP BY p.lot_id, p.lot_name, p.location;

-- ============================================
-- 4. COMMON TABLE EXPRESSIONS (CTEs) - Example Queries
-- ============================================

-- Note: CTEs are used in SELECT queries, not stored as database objects
-- Here are example queries you can use in your backend code:

/*
-- Example CTE Query 1: Find parking lots with decreasing availability trend
WITH availability_trend AS (
    SELECT 
        lot_id,
        lot_name,
        available_spots,
        LAG(available_spots) OVER (PARTITION BY lot_id ORDER BY lot_id) as previous_spots
    FROM parking_lots
)
SELECT 
    lot_id,
    lot_name,
    available_spots,
    previous_spots,
    (available_spots - previous_spots) as change
FROM availability_trend
WHERE (available_spots - previous_spots) < 0;
*/

/*
-- Example CTE Query 2: Monthly revenue breakdown with running totals
WITH monthly_revenue AS (
    SELECT 
        DATE_FORMAT(created_at, '%Y-%m') as month,
        SUM(total_cost) as revenue
    FROM reservations
    GROUP BY DATE_FORMAT(created_at, '%Y-%m')
),
running_total AS (
    SELECT 
        month,
        revenue,
        SUM(revenue) OVER (ORDER BY month) as running_total
    FROM monthly_revenue
)
SELECT * FROM running_total ORDER BY month;
*/

/*
-- Example CTE Query 3: Find top users by spending
WITH user_spending AS (
    SELECT 
        user_id,
        SUM(total_cost) as total_spent,
        COUNT(*) as booking_count
    FROM reservations
    GROUP BY user_id
),
ranked_users AS (
    SELECT 
        u.user_id,
        u.name,
        u.email,
        us.total_spent,
        us.booking_count,
        RANK() OVER (ORDER BY us.total_spent DESC) as spending_rank
    FROM users u
    JOIN user_spending us ON u.user_id = us.user_id
)
SELECT * FROM ranked_users WHERE spending_rank <= 10;
*/

-- ============================================
-- 5. HELPER QUERIES TO USE CTEs
-- ============================================

-- Query: Parking lots with recursive availability check (using CTE)
-- This shows how to use CTE for complex analytics

-- Example: Daily booking trends (this query can be used in admin dashboard)
-- Use this in your backend/routes/admin.py

/*
WITH daily_stats AS (
    SELECT 
        DATE(created_at) as booking_date,
        COUNT(*) as bookings_count,
        SUM(total_cost) as daily_revenue,
        AVG(total_cost) as avg_booking_value
    FROM reservations
    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY DATE(created_at)
)
SELECT 
    booking_date,
    bookings_count,
    daily_revenue,
    avg_booking_value,
    SUM(daily_revenue) OVER (ORDER BY booking_date) as cumulative_revenue
FROM daily_stats
ORDER BY booking_date DESC;
*/

-- ============================================
-- 6. TESTING THE FEATURES
-- ============================================

-- Test Function: Calculate parking cost
-- SELECT calculate_parking_cost(1, '2024-01-01 10:00:00', '2024-01-01 14:00:00') as total_cost;

-- Test Function: Check available spots
-- SELECT check_available_spots(1) as available_spots;

-- Test Function: Get lot status
-- SELECT get_lot_status(1) as status;

-- Test View: Parking lot summary
-- SELECT * FROM v_parking_lot_summary WHERE lot_id = 1;

-- Test View: User bookings
-- SELECT * FROM v_user_bookings WHERE user_id = 1;

-- Test View: Revenue summary
-- SELECT * FROM v_lot_revenue_summary ORDER BY total_revenue DESC;

SELECT 'All advanced database features created successfully!' AS status;

