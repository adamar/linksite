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
    def generate_image_name(unique_file_name_component, filetype):
        return unique_file_name_component + '.' + filetype


    @staticmethod
    def readble_url(title):
        title = title.replace(" ","_")
        title = title.replace("-","_")
        acceptable_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'
        return "".join([ch for ch in title if ch in acceptable_chars])


    @staticmethod
    def generate_orignal_image_url(s3_bucket, filename):
        return 'http://s3.amazonaws.com/{bucket}/{filename}'.format(bucket=s3_bucket, filename=filename)

    @staticmethod
    def upload_to_s3(image, filename, content_type):
        conn = S3Connection('','')
        bucket = conn.create_bucket('buket_name')
        k = Key(bucket)
        k.key = filename
        k.set_metadata("Content-Type", content_type)
        k.set_contents_from_string(image)
        k.set_acl('public-read')
        return

    @staticmethod
    def get_most_recent(db, dcount):

        dcount = torndb.MySQLdb.escape_string(str(dcount))

        SQL = "SELECT slug, title from images order by image_id desc limit {count}".format(count=dcount)
        res = db.query(SQL)
        return res


    @staticmethod
    def get_image(db, item_id):

        item_id = torndb.MySQLdb.escape_string(str(item_id))

        SQL = "SELECT image_url, title, description from images where slug='{item_id}'".format(item_id=item_id)

        print SQL
        res = db.query(SQL)

        print res
        return res


    @staticmethod
    def get_image_and_adblock(db, item_id):

        item_id = torndb.MySQLdb.escape_string(str(item_id))

        SQL = "select i.image_url, i.title, u.adblock, u.enabled from images i join users \
               u on (i.user_id = u.user_id) where i.slug = '{item_id}'".format(item_id=item_id)

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





