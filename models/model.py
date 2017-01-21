#-*-coding:utf-8 -*-
#!/usr/bin/env python

import copy
import MySQLdb.constants
import MySQLdb.converters
import MySQLdb.cursors

import logging
import time
 

class Model():

    @property
    def db(self):
        return self.application.db

    def reconnect(self):
        
        self.close()
        self._db = MySQLdb.connect(**Model._db_settings)
        print self._db
    
    def commit(self):
        self._db.commit()
    
    def rollback(self):
        self._db.rollback()
        
    def cursor(self, cursorType = MySQLdb.cursors.DictCursor):
        self._ensure_connected()
        if cursorType == None:
            return self._db.cursor()
        
        return self._db.cursor(cursorType)
        
    
    def _ensure_connected(self):
        
        if self._db is None or (time.time() - self._last_use_sec > self.max_idle_sec):
            self.reconnect()
        
        self._last_use_sec = time.time()  
