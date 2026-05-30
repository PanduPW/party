CREATE DATABASE IF NOT EXISTS railway_system ;
USE railway_system;

CREATE TABLE IF NOT EXISTS Train (
    train_id INT AUTO_INCREMENT PRIMARY KEY,
    train_name VARCHAR(255) NOT NULL,
    total_seats INT NOT NULL,
    train_type VARCHAR(100) NOT NULL,
    ticket_price DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS Station (
    station_id INT AUTO_INCREMENT PRIMARY KEY,
    station_name VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    state_name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS Route (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    departure_station_id INT NOT NULL,
    arrival_station_id INT NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    train_id INT DEFAULT NULL,
    FOREIGN KEY (departure_station_id) REFERENCES Station (station_id) ON DELETE CASCADE,
    FOREIGN KEY (arrival_station_id) REFERENCES Station (station_id) ON DELETE CASCADE,
    FOREIGN KEY (train_id) REFERENCES Train (train_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Passenger (
    passenger_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_no VARCHAR(50) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS Purchase (
    purchase_id INT AUTO_INCREMENT PRIMARY KEY,
    passenger_id INT NOT NULL,
    route_id INT NOT NULL,
    seat_no VARCHAR(50) NOT NULL,
    purchase_date_status DATE NOT NULL DEFAULT (CURRENT_DATE),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    FOREIGN KEY (passenger_id) REFERENCES Passenger (passenger_id) ON DELETE CASCADE,
    FOREIGN KEY (route_id) REFERENCES Route (route_id) ON DELETE CASCADE,
    CHECK (status IN ('pending', 'paid', 'canceled'))
);

