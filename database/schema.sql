CREATE DATABASE IF NOT EXISTS railway_system;
USE railway_system;

CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('superadmin', 'admin', 'user') NOT NULL DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS Station (
    station_id INT AUTO_INCREMENT PRIMARY KEY,
    station_name VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS Train (
    train_id INT AUTO_INCREMENT PRIMARY KEY,
    train_name VARCHAR(255) NOT NULL,
    train_type ENUM('local', 'express','intercity','regional') NOT NULL,
    total_seats INT NOT NULL
);

CREATE TABLE IF NOT EXISTS Route (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    train_id INT NOT NULL,
    departure_station_id INT NOT NULL,
    arrival_station_id INT NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    ticket_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (departure_station_id) REFERENCES Station (station_id) ON DELETE CASCADE,
    FOREIGN KEY (arrival_station_id) REFERENCES Station (station_id) ON DELETE CASCADE,
    FOREIGN KEY (train_id) REFERENCES Train (train_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Passenger (
    passenger_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    phone_no VARCHAR(50) DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS Ticket (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    passenger_id INT NOT NULL,
    route_id INT NOT NULL,
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'paid', 'canceled') NOT NULL DEFAULT 'pending',
    FOREIGN KEY (passenger_id) REFERENCES Passenger (passenger_id) ON DELETE CASCADE,
    FOREIGN KEY (route_id) REFERENCES Route (route_id) ON DELETE CASCADE
);
