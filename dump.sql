--
-- Файл сгенерирован с помощью SQLiteStudio v3.3.3 в Вт июн 28 00:25:57 2022
--
-- Использованная кодировка текста: UTF-8
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Таблица: Version
CREATE TABLE "Version" (
	"Id"	INTEGER,
	"Ip"	TEXT,
	"Ids_version"	TEXT,
	"Time_license"	INTEGER,
	"Name_base"	TEXT,
	PRIMARY KEY("Id" AUTOINCREMENT)
);

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
