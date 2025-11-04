-- Create stored procedure for making reservations
-- Run this in MySQL Workbench after the main database is created

USE smart_parking_database_1;

-- Create reservations table if it doesn't exist
CREATE TABLE IF NOT EXISTS `reservations` (
  `reservation_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `lot_id` int NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `total_cost` decimal(10,2) NOT NULL,
  `status` enum('active','completed','cancelled') DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`reservation_id`),
  KEY `user_id` (`user_id`),
  KEY `lot_id` (`lot_id`),
  CONSTRAINT `reservations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `reservations_ibfk_2` FOREIGN KEY (`lot_id`) REFERENCES `parking_lots` (`lot_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Drop procedure if it exists
DROP PROCEDURE IF EXISTS `make_reservation1`;

-- Create the stored procedure
DELIMITER $$

CREATE PROCEDURE `make_reservation1`(
    IN p_user_id INT,
    IN p_lot_id INT,
    IN p_start_time DATETIME,
    IN p_end_time DATETIME,
    OUT p_total_cost DECIMAL(10,2)
)
BEGIN
    DECLARE v_hourly_rate DECIMAL(10,2);
    DECLARE v_hours DECIMAL(10,2);
    DECLARE v_available_spots INT;
    DECLARE v_total_spots INT;
    
    -- Check if lot exists and get details
    SELECT hourly_rate, available_spots, total_spots
    INTO v_hourly_rate, v_available_spots, v_total_spots
    FROM parking_lots
    WHERE lot_id = p_lot_id;
    
    -- Check if lot exists
    IF v_hourly_rate IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Parking lot not found';
    END IF;
    
    -- Check if lot is open
    IF (SELECT status FROM parking_lots WHERE lot_id = p_lot_id) != 'open' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Parking lot is closed';
    END IF;
    
    -- Check if spots are available
    IF v_available_spots <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No parking spots available';
    END IF;
    
    -- Validate time range
    IF p_end_time <= p_start_time THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'End time must be after start time';
    END IF;
    
    -- Calculate hours (round up to nearest hour)
    SET v_hours = CEIL(TIMESTAMPDIFF(MINUTE, p_start_time, p_end_time) / 60.0);
    
    -- Calculate total cost
    SET p_total_cost = v_hours * v_hourly_rate;
    
    -- Create reservation
    INSERT INTO reservations (user_id, lot_id, start_time, end_time, total_cost, status)
    VALUES (p_user_id, p_lot_id, p_start_time, p_end_time, p_total_cost, 'active');
    
    -- Update available spots (decrease by 1)
    UPDATE parking_lots
    SET available_spots = available_spots - 1
    WHERE lot_id = p_lot_id;
    
    -- Update parking spot status (set one spot as occupied)
    UPDATE parking_spots
    SET is_occupied = 1
    WHERE lot_id = p_lot_id 
    AND is_occupied = 0
    LIMIT 1;
    
END$$

DELIMITER ;

-- Verify procedure was created
SELECT 'Stored procedure make_reservation1 created successfully!' AS status;

