
INSERT INTO station (station_name, city, state_name) VALUES
    ('Central Station','Singapore','Central'),
    ('Woodlands Station','Woodlands','North'),
    ('Jurong East','Jurong','West'),
    ('Tampines Hub','Tampines','East');


INSERT INTO train (train_name, total_seats, train_type, ticket_price) VALUES
    ('Express 101','200','Express',25.00),
    ('Regional 202','350','Regional',15.00),
    ('Night Owl','150','Night',35.00);

INSERT INTO route (departure_station_id, arrival_station_id, departure_time, arrival_time, train_id) VALUES
    (1,2,'08:00','08:45',1),
    (2,3,'09:00','09:30',2),
    (1,4,'10:00','10:50',3)
;
