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

-- View: Revenue summary by parking lot (exclude cancelled bookings)
CREATE OR REPLACE VIEW v_lot_revenue_summary AS
SELECT 
    p.lot_id,
    p.lot_name,
    p.location,
    COUNT(CASE WHEN r.reservation_id IS NOT NULL AND r.status != 'cancelled' THEN r.reservation_id END) as total_bookings,
    COALESCE(SUM(CASE WHEN r.status != 'cancelled' THEN r.total_cost ELSE 0 END), 0) as total_revenue,
    COALESCE(AVG(CASE WHEN r.status != 'cancelled' THEN r.total_cost END), 0) as avg_booking_cost,
    COALESCE(MAX(CASE WHEN r.status != 'cancelled' THEN r.total_cost END), 0) as max_booking_cost,
    COALESCE(MIN(CASE WHEN r.status != 'cancelled' THEN r.total_cost END), 0) as min_booking_cost
FROM parking_lots p
LEFT JOIN reservations r ON p.lot_id = r.lot_id
GROUP BY p.lot_id, p.lot_name, p.location;

SELECT 'All advanced database features created successfully!' AS status;

