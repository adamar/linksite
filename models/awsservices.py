#-*-coding:utf-8 -*-
#!/usr/bin/env python

from model import Model
import hashlib
import MySQLdb
import logging
import uuid
import time
import boto
import json
from boto.sqs.message import RawMessage

from boto.s3.connection import S3Connection
from boto.s3.key import Key


import mimetypes
from email import encoders
from email.utils import COMMASPACE
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from boto.ses import SESConnection

from time import  strftime, gmtime

class AWSServices(Model):

    @staticmethod
    def upload_to_s3(key, secret, bucket, image, filename, content_type):
        conn = S3Connection(key, secret)
        #bucket = conn.create_bucket(bucket)
        bucket = conn.get_bucket(bucket)
        k = Key(bucket)
        k.key = filename
        k.set_metadata("Content-Type", content_type)
        k.set_contents_from_string(image)
        k.set_acl('public-read')
        return






