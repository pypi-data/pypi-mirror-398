PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE aisle (
    id INTEGER PRIMARY KEY,
    length_feet REAL,
    refrigerated INTEGER,
    has_endcaps INTEGER
);
INSERT INTO aisle VALUES(1,50.0,0,1);
INSERT INTO aisle VALUES(2,45.0,1,1);
INSERT INTO aisle VALUES(3,50.0,0,0);
INSERT INTO aisle VALUES(4,55.0,1,1);
INSERT INTO aisle VALUES(5,50.0,0,1);
INSERT INTO aisle VALUES(6,60.0,1,0);
INSERT INTO aisle VALUES(7,45.0,0,1);
INSERT INTO aisle VALUES(8,50.0,0,0);
CREATE TABLE product (
    id INTEGER PRIMARY KEY,
    name TEXT,
    brand TEXT,
    weight TEXT,
    size TEXT,
    aisle_id INTEGER,
    FOREIGN KEY (aisle_id) REFERENCES aisle(id)
);
INSERT INTO product VALUES(1,'Milk','Organic Valley','1 gal','Large',2);
INSERT INTO product VALUES(2,'Bread','Wonder','20 oz','Medium',1);
INSERT INTO product VALUES(3,'Cheese','Kraft','16 oz','Medium',2);
INSERT INTO product VALUES(4,'Chips','Lays','10 oz','Small',3);
INSERT INTO product VALUES(5,'Cookies','Oreo','14 oz','Medium',3);
INSERT INTO product VALUES(6,'Yogurt','Chobani','32 oz','Large',2);
INSERT INTO product VALUES(7,'Butter','Land O Lakes','16 oz','Medium',2);
INSERT INTO product VALUES(8,'Eggs','Organic Valley','12 ct','Medium',2);
INSERT INTO product VALUES(9,'Sour Cream','Daisy','16 oz','Medium',2);
INSERT INTO product VALUES(10,'Cream Cheese','Philadelphia','8 oz','Small',2);
INSERT INTO product VALUES(11,'Ice Cream','Ben & Jerrys','16 oz','Medium',4);
INSERT INTO product VALUES(12,'Frozen Pizza','DiGiorno','28 oz','Large',4);
INSERT INTO product VALUES(13,'Frozen Vegetables','Birds Eye','16 oz','Medium',4);
INSERT INTO product VALUES(14,'Frozen Waffles','Eggo','12 oz','Medium',4);
INSERT INTO product VALUES(15,'Ice Cream Bars','Klondike','6 ct','Medium',4);
INSERT INTO product VALUES(16,'Pretzels','Snyders','16 oz','Medium',3);
INSERT INTO product VALUES(17,'Crackers','Ritz','13 oz','Medium',3);
INSERT INTO product VALUES(18,'Popcorn','Orville Redenbacher','6 ct','Medium',3);
INSERT INTO product VALUES(19,'Granola Bars','Nature Valley','12 ct','Medium',3);
INSERT INTO product VALUES(20,'Trail Mix','Kirkland','28 oz','Large',3);
INSERT INTO product VALUES(21,'Bagels','Thomas','20 oz','Medium',1);
INSERT INTO product VALUES(22,'Muffins','Hostess','16 oz','Medium',1);
INSERT INTO product VALUES(23,'Donuts','Krispy Kreme','12 ct','Medium',1);
INSERT INTO product VALUES(24,'English Muffins','Thomas','13 oz','Medium',1);
INSERT INTO product VALUES(25,'Soup','Campbells','10.75 oz','Small',5);
INSERT INTO product VALUES(26,'Beans','Bush''s','15 oz','Small',5);
INSERT INTO product VALUES(27,'Tomatoes','Hunt''s','14.5 oz','Small',5);
INSERT INTO product VALUES(28,'Tuna','StarKist','5 oz','Small',5);
INSERT INTO product VALUES(29,'Corn','Del Monte','15.25 oz','Small',5);
INSERT INTO product VALUES(30,'Ground Beef','Angus','1 lb','Medium',6);
INSERT INTO product VALUES(31,'Chicken Breast','Tyson','2 lb','Large',6);
INSERT INTO product VALUES(32,'Bacon','Oscar Mayer','16 oz','Medium',6);
INSERT INTO product VALUES(33,'Ham','Boars Head','1 lb','Medium',6);
INSERT INTO product VALUES(34,'Turkey','Butterball','1 lb','Medium',6);
INSERT INTO product VALUES(35,'Orange Juice','Tropicana','52 oz','Large',7);
INSERT INTO product VALUES(36,'Soda','Coca Cola','2 L','Large',7);
INSERT INTO product VALUES(37,'Water','Aquafina','24 pk','Large',7);
INSERT INTO product VALUES(38,'Coffee','Folgers','30.5 oz','Large',7);
INSERT INTO product VALUES(39,'Tea','Lipton','100 ct','Medium',7);
INSERT INTO product VALUES(40,'Cereal','Cheerios','18 oz','Medium',8);
INSERT INTO product VALUES(41,'Oatmeal','Quaker','42 oz','Large',8);
INSERT INTO product VALUES(42,'Pancake Mix','Aunt Jemima','32 oz','Large',8);
INSERT INTO product VALUES(43,'Syrup','Mrs. Butterworth','24 oz','Medium',8);
INSERT INTO product VALUES(44,'Pop Tarts','Kelloggs','8 ct','Medium',8);
CREATE TABLE cost (
    id INTEGER PRIMARY KEY,
    product_id INTEGER,
    price REAL,
    date TEXT,
    price_model INTEGER DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES product(id)
);
INSERT INTO cost (id, product_id, price, date) VALUES(1,1,4.990000000000000213,'2025-01-01');
INSERT INTO cost (id, product_id, price, date) VALUES(2,2,2.990000000000000213,'2025-01-01');
INSERT INTO cost (id, product_id, price, date) VALUES(3,3,5.990000000000000213,'2025-01-01');
INSERT INTO cost (id, product_id, price, date) VALUES(4,4,3.490000000000000213,'2025-01-01');
INSERT INTO cost (id, product_id, price, date) VALUES(5,5,4.290000000000000035,'2025-01-01');
INSERT INTO cost (id, product_id, price, date) VALUES(6,1,3.990000000000000213,'2024-01-01');
INSERT INTO cost (id, product_id, price, date) VALUES(7,1,4.290000000000000035,'2024-06-01');
INSERT INTO cost (id, product_id, price, date) VALUES(8,1,4.490000000000000213,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(9,2,2.490000000000000213,'2024-01-01');
INSERT INTO cost (id, product_id, price, date) VALUES(10,2,2.790000000000000035,'2024-06-01');
INSERT INTO cost (id, product_id, price, date) VALUES(11,2,2.990000000000000213,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(12,3,4.990000000000000213,'2024-01-01');
INSERT INTO cost (id, product_id, price, date) VALUES(13,3,5.490000000000000213,'2024-06-01');
INSERT INTO cost (id, product_id, price, date) VALUES(14,6,4.990000000000000213,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(15,7,3.490000000000000213,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(16,8,3.990000000000000213,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(17,11,5.990000000000000213,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(18,12,7.990000000000000213,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(19,16,3.290000000000000035,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(20,20,12.99000000000000021,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(21,25,1.290000000000000035,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(22,30,5.990000000000000213,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(23,31,8.990000000000000213,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(24,35,4.490000000000000213,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(25,36,2.290000000000000035,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(26,40,4.990000000000000213,'2024-12-01');
INSERT INTO cost (id, product_id, price, date) VALUES(27,41,5.490000000000000213,'2024-12-01');
COMMIT;
