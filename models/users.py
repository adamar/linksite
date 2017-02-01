
#-*-coding:utf-8 -*-
#!/usr/bin/env python

from model import Model
import hashlib
import MySQLdb
import logging
import torndb

from time import  strftime, gmtime

class User(Model):

    def check_password(self, submitted_password):
        return self._data["encrypted_password"] == self._secure_hash("%s--%s" %(self._data["password_salt"], submitted_password ))
    

    @staticmethod
    def add_user(db, username, password, email):
        passhash = hashlib.sha1(password).hexdigest()


        SQL = "INSERT INTO users \
                          (username, password, \
                          user_email) \
                          VALUES ('%s', '%s', '%s')" % (username, passhash, email)



        res = db.execute_lastrowid(SQL)

        print SQL, " and result: ", res


        if res:
            return True
        else:
            return False


    @staticmethod
    def check_user(db, username, password):

        # hasing not implemented yet
        passhash = hashlib.sha1(password).hexdigest()


        SQL = "SELECT user_id, username \
               from users where username = '{username}' \
               and password = '{password}' limit 1".format(username=username, password=passhash)

        res = db.query(SQL)
        print SQL, "  Results: ", res

        if res:
            return True, res[0]
        else:
            print "user not found, result: ", res
            return False, {}


    @staticmethod
    def check_users_ad_enabled(db, username):

        SQL = "SELECT enabled from users \
               where username = {username}".format(username=username)

        res = db.query(SQL)
        
        print res[0]['enabled']
 
        if res[0]['enabled'] == 1:
            return True
        else:
            return False






