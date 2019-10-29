import mysql.connector

config = {
       'user': 'dlytle',
       'password': 'dlytle',
       'host': 'astropci.lowell.edu',
       'database': 'temperature',
       'raise_on_warnings': True
         }

cnx = mysql.connector.connect(**config)

my_database = cnx.cursor()

# my_database.execute("CREATE DATABASE temperature")

my_database.execute(
    "CREATE TABLE `temps` ("
    "  `t_id` int NOT NULL,"
    "  `t` float NOT NULL,"
    "  `date` date NOT NULL,"
    "  `time` time NOT NULL,"
    "  `location` varchar(16) NOT NULL,"
    "  `sensor` varchar(16) NOT NULL,"
    "  `computer` varchar(16) NOT NULL,"
    "  `user` varchar(16) NOT NULL,"
    "  PRIMARY KEY (`t_id`)"
    ") ENGINE=InnoDB"
)

cnx.close()
