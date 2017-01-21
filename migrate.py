

import torndb
import os
from tornado.options import define, options
from urlparse import urlparse


define("mysql_host", default="127.0.0.1:3306", help="database host")
define("mysql_database", default="current", help="database name")
define("mysql_user", default="root", help="database user")
define("mysql_password", default="password", help="database password")



def migrate():

    if 'CLEARDB_DATABASE_URL' in os.environ.keys():
        parsed = urlparse(os.environ['CLEARDB_DATABASE_URL'])
        options.mysql_host = parsed.hostname
        options.mysql_database = parsed.path.strip("/")
        options.mysql_user = parsed.username
        options.mysql_password = parsed.password


    db = torndb.Connection(host=options.mysql_host, database=options.mysql_database,
                                    user=options.mysql_user, password=options.mysql_password)



    USERS = """
    
CREATE TABLE `images` (
  `image_id` INT NOT NULL AUTO_INCREMENT,
  `slug` VARCHAR(10),
  `image_url` VARCHAR(255),
  `title` VARCHAR(255),
  `description` TEXT,
  `timestamp` DATETIME,
  PRIMARY KEY  (`image_id`)
);  
"""

    db.execute(USERS)



migrate()


