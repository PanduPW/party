INSERT INTO Users (user_id, email, password_hash, role) VALUES
(1, 'superadmin@gmail.com', 'scrypt:32768:8:1$lpLbKXVDwXCIiLey$8508a4145ed105e8737d7a2db0723378da852df642273bb7e55ec8215b063a63ad205452d31e0d702c1e3af88d5f244f5faa186ea6ce9632c01c2ba2f44147ff', 'superadmin'),
(2, 'admin@gmail.com', 'scrypt:32768:8:1$lpLbKXVDwXCIiLey$8508a4145ed105e8737d7a2db0723378da852df642273bb7e55ec8215b063a63ad205452d31e0d702c1e3af88d5f244f5faa186ea6ce9632c01c2ba2f44147ff', 'admin'),
(3, 'user@gmail.com', 'scrypt:32768:8:1$lpLbKXVDwXCIiLey$8508a4145ed105e8737d7a2db0723378da852df642273bb7e55ec8215b063a63ad205452d31e0d702c1e3af88d5f244f5faa186ea6ce9632c01c2ba2f44147ff', 'user'),
(4, 'user2@gmail.com', 'scrypt:32768:8:1$lpLbKXVDwXCIiLey$8508a4145ed105e8737d7a2db0723378da852df642273bb7e55ec8215b063a63ad205452d31e0d702c1e3af88d5f244f5faa186ea6ce9632c01c2ba2f44147ff', 'user');

INSERT INTO Station (station_id, station_name, city) VALUES
(1, 'Jakarta Kota', 'Jakarta Barat'),
(2, 'Manggarai', 'Jakarta Selatan'),
(3, 'Tanah Abang', 'Jakarta Pusat'),
(4, 'Bogor', 'Bogor'),
(5, 'Bekasi', 'Bekasi'),
(6, 'Cikarang', 'Bekasi');

INSERT INTO Train (train_id, train_name, train_type, total_seats) VALUES
(1, 'Express', 'local', 200),
(2, 'Ekonomi', 'express', 100),
(3, 'Bisnis', 'intercity', 50),
(4, 'Regional', 'regional', 150);

INSERT INTO Route (route_id, train_id, departure_station_id, arrival_station_id, departure_time, arrival_time, ticket_price) VALUES
(1, 1, 4, 1, '06:00:00', '07:15:00', 6000.00),
(2, 1, 4, 2, '06:30:00', '07:45:00', 6000.00),
(3, 3, 4, 1, '17:15:00', '18:30:00', 6000.00),
(4, 2, 6, 2, '06:10:00', '07:05:00', 5000.00),
(5, 2, 6, 4, '18:00:00', '18:55:00', 5000.00),
(6, 2, 3, 2, '08:00:00', '08:15:00', 3000.00);

INSERT INTO Passenger (passenger_id, user_id, first_name, last_name, phone_no) VALUES
(1, 3, 'Bambang', 'Pamungkas', '081234567890'),
(2, 4, 'Siti', 'Aminah', '089987654321');

INSERT INTO Ticket (ticket_id, passenger_id, route_id, purchase_date, status) VALUES
(1, 1, 1, '2026-06-05 05:45:12', 'pending'),
(2, 1, 3, '2026-06-07 09:00:00', 'paid'),
(3, 2, 4, '2026-06-07 10:15:30', 'pending'),
(4, 2, 6, '2026-06-04 07:50:00', 'canceled');
