-- -----------------------------------------------------
-- Table `dollar`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `dollar` (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   code TEXT NOT NULL,
   codein TEXT NOT NULL,
   name TEXT NOT NULL,
   high DECIMAL(10, 4) NOT NULL,
   low DECIMAL(10, 4) NOT NULL,
   varBid DECIMAL(10, 4) NOT NULL,
   pctChange DECIMAL(10, 4) NOT NULL,
   bid DECIMAL(10, 4) NOT NULL,
   ask DECIMAL(10, 4) NOT NULL,
   date_hour DATETIME NOT NULL
);