#-*-coding:utf-8 -*-
#!/usr/bin/env python

from model import Model
import hashlib
import MySQLdb
import torndb
import logging
import uuid
import time
import boto
import json
from boto.sqs.message import RawMessage

import imghdr
import cStringIO

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from time import  strftime, gmtime

class Image(Model):

    @staticmethod
    def set_post(db, description, safe_description, user_id):

        desc = torndb.MySQLdb.escape_string(description)
        safe_desc = torndb.MySQLdb.escape_string(safe_description)

        SQL = "INSERT INTO posts (title, url_safe_title, user_id) \
               VALUES ('{desc}', '{safe_title}',  {uid})".format(desc=desc, safe_title=safe_desc, uid=user_id)

        res = db.execute_lastrowid(SQL)

        hexval = hex(res).rstrip('L')

        SQL2 = "UPDATE posts set slug = '{slug}' where post_id = '{pid}'".format(slug=hexval, pid=res)

        print SQL2

        db.execute(SQL2)

        return res


    


    @staticmethod
    def get_post_items(db, post_id):

        post_id = torndb.MySQLdb.escape_string(str(post_id))

        SQL = "SELECT description from post_items where post_id='{post_id}'".format(post_id=post_id)

        #print SQL
        res = db.query(SQL)

        #print res
        return res


    @staticmethod
    def set_post_item(db, slug, title, url):

        post_id = torndb.MySQLdb.escape_string(str(slug))

        SQL = "INSERT INTO post_items (post_id, description, image_url) \
               VALUES ('{post_id}', '{title}', '{url}')".format(post_id=post_id, title=title, url=url)

        print SQL
        res = db.execute(SQL)
        return True



        #SQL = "SELECT description from post_items where post_id='{post_id}'".format(post_id=post_id)

        #print SQL
        #res = db.query(SQL)

        #print res
        #return res





    @staticmethod
    def get_post(db, hex_id):

        hex_id = torndb.MySQLdb.escape_string(hex_id)

        item_id = int(hex_id, 16)

        SQL = "select p.title, pi.description, pi.image_url from posts p \
               join post_items pi on (pi.post_id = p.post_id) \
               where p.post_id = {item_id};".format(item_id=item_id)

        print SQL
        res = db.query(SQL)

        print res
        return res






    @staticmethod
    def add_item_image(db, vid, vslug, vtitle, vurl):

        vslug = torndb.MySQLdb.escape_string(vslug)
        vtitle = torndb.MySQLdb.escape_string(vtitle)
        vurl = torndb.MySQLdb.escape_string(vurl)

        SQL = "INSERT INTO images (slug, user_id, image_url, title) \
               VALUES ('{slug}', {uid},  '{url}', '{title}')".format(slug=vslug, uid=vid, url=vurl, title=vtitle)

        print SQL
        res = db.execute(SQL)
        return True



    @staticmethod
    def check_unique_image(image_body):

        m = hashlib.md5()
        m.update(image_body)
        return m.hexdigest()[:8]



    @staticmethod
    def check_image_type(image_body):
        filetype = imghdr.what(cStringIO.StringIO(image_body))
        print filetype
        if filetype == 'jpg' or filetype == 'png' or filetype != 'gif':
            return filetype
        else:
            return False


    @staticmethod
    def generate_image_name(unique_file_name_component, filetype):
        return unique_file_name_component + '.' + filetype


    @staticmethod
    def string_to_readble_url_snippet(title):
        title = title.replace(" ","_")
        title = title.replace("-","_")
        acceptable_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'
        return "".join([ch for ch in title if ch in acceptable_chars])


    @staticmethod
    def generate_orignal_image_url(s3_bucket, filename):
        #return 'http://s3.amazonaws.com/{bucket}/{filename}'.format(bucket=s3_bucket, filename=filename)
        return 'http://{bucket}.s3-website-us-west-1.amazonaws.com/{filename}'.format(bucket=s3_bucket, filename=filename)



    @staticmethod
    def get_most_recent(db, dcount):

        dcount = torndb.MySQLdb.escape_string(str(dcount))

        SQL = "SELECT slug, title from images order by image_id desc limit {count}".format(count=dcount)
        res = db.query(SQL)
        return res



    @staticmethod
    def int_to_hex(num):
        return hex(num)



    @staticmethod
    def hex_to_int(num):
        return int(num, 16)


