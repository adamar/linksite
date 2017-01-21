#!/usr/bin/python

import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.gen
#import tornado.options
from tornado.options import define, options
import torndb

import os
import json
import time
import sys
import hashlib
import random

from urlparse import urlparse

from models.images import Image
from models.awsservices import AWSServices
from models.users import User

define("mysql_host", default="127.0.0.1:3306", help="database host")
define("mysql_database", default="current", help="database name")
define("mysql_user", default="root", help="database user")
define("mysql_password", default="password", help="database password")
define("s3_bucket", default="", help="s3 bucket for file")
define("aws_key", default="AKIA", help="Aws key")
define("aws_secret", default="Sdfm", help="Aws secret")
define("port", default=8080, help="Tornado Port")
define("debug", default="False", help="Debug")






class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def write_error(self, status_code, **kwargs):
        #if options.debug == "False":
        self.redirect("/404")    

    def get_current_user(self):
        return self.get_secure_cookie("user")


class PicHandler(BaseHandler):
    """
    main image page /{something}
    """
    def get(self, slug):
        row = Image.get_image_and_adblock(self.db, slug)[0]
        image = row['image_url']
        adblock = row['adblock']
        verified = row['enabled']
        title = row['title']

        use_secondary_ad = False
        if verified == 1: # Check Adblock is accepted
            if random.randint(0,1) == 1:
                use_secondary_ad = True

        if image < 1:
            self.redirect("/404")

        self.render("image.html", site_title=self.settings['site_title'],  title=title, image=image, ad=adblock, use_secondary_ad=use_secondary_ad)


class MainPageHandler(BaseHandler):
    """
    /
    """
    def get(self):
        self.render("index.html", site_title=self.settings['site_title'])


class AdNotEnabledHandler(BaseHandler):
    """
    /notchecked
    """
    def get(self):
        self.render("notchecked.html", site_title=self.settings['site_title'])


class ThanksHandler(BaseHandler):
    """
    /thanks
    """
    def get(self):
        self.render("thanksforsignup.html", site_title=self.settings['site_title'])



class RecentHandler(BaseHandler):
    """
    /recent
    """
    @tornado.web.authenticated
    def get(self):
        count = 10
        imglist = Image.get_most_recent(self.db, count)
        self.render("recent.html", imglist=imglist, site_title=self.settings['site_title'])



class FourOhFourHandler(BaseHandler):
    """
    /404
    """
    def get(self):
        self.render("404.html", site_title=self.settings['site_title'])


class CreatePostHandler(BaseHandler):
    """
    currently unused
    """
    def get(self):

        self.render("create_post.html", site_title=self.settings['site_title'])

    def post(self):

        self.post_title = self.request.arguments['title'][0]

        Post.create_post(self.post_title)




class CreatePostItemsHandler(BaseHandler):
    """
    currently unused
    """
    def get(self, slug):

        self.render("create_post_items.html", site_title=self.settings['site_title'])





class ImageUploadHandler(BaseHandler):
    """
    currently unused
    """
    def get(self):

        #images = Image.get_item_images(self.db, slug)

        #err = self.get_argument("err", default=None, strip=False)  
        #if err:
        #    err = self.get_error(err)
        self.render("upload.html", site_title=self.settings['site_title'])

    def post(self):
        for key in self.request.files['userfile[]']:

            file_contents = key['body']

            content_type = key['content_type']

            filetype = Image.check_image_type(file_contents)

            if not filetype:
                try:
                    print key['filename']
                    filetype = key['filename'].split('.')[-1:][0]
                    print "from filename", filetype
                except:
                    self.redirect("/no-filetype-detected")

            # Hash image
            unique_file_name_component = Image.check_unique_image(file_contents)

            # Generate a filename
            print "file will be named", unique_file_name_component, filetype
            file_name = Image.generate_image_name(unique_file_name_component, filetype)

            # Generate a URL 
            URL = Image.generate_orignal_image_url(options.s3_bucket, file_name)

            # Upload to S3
            AWSServices.upload_to_s3(options.aws_key, options.aws_secret, options.s3_bucket, file_contents, file_name, content_type)

            self.title = self.request.arguments['title'][0]
            self.description = self.request.arguments['description'][0]
            
            print URL
            
            Image.add_item_image(self.db, unique_file_name_component, self.title, self.description, URL)

            self.new_title = Image.readble_url(self.title)

            
        self.redirect("/"+unique_file_name_component+"/"+self.new_title)




class LoginHandler(BaseHandler):
    """
    /login
    """
    def get(self):
        self.render("login.html", site_title=self.settings['site_title'])

    def post(self):
        self.username = self.request.arguments['username'][0]
        self.password = self.request.arguments['password'][0]

        uid = User.check_user(self.db, self.username, self.password)
        if uid:
            self.set_secure_cookie("user", tornado.escape.json_encode(self.username))
            self.set_secure_cookie("user_id", tornado.escape.json_encode(uid))
            self.redirect("/home")
            
        else:
            self.redirect("/login")


class SignupHandler(BaseHandler):
    """
    /signup
    """
    def get(self):
        self.render("signup.html", site_title=self.settings['site_title'])

    def post(self):
        self.username = self.request.arguments['username'][0]
        self.password = self.request.arguments['password'][0]
        self.email = self.request.arguments['email'][0]

        User.add_user(self.db, self.username, self.password, self.email)
        self.redirect("/thanks")



class HomeHandler(BaseHandler):
    """
    /home
    """
    @tornado.web.authenticated
    def get(self):
        
        uname = self.get_secure_cookie("user")

        enabled = User.check_users_ad_enabled(self.db, uname)

        if enabled:
            self.render("auth_upload.html", site_title=self.settings['site_title'])
        else:
            self.redirect("/notchecked")


    @tornado.web.authenticated
    def post(self):
        for key in self.request.files['userfile[]']:

            file_contents = key['body']

            content_type = key['content_type']

            filetype = Image.check_image_type(file_contents)

            if not filetype:
                try:
                    print key['filename']
                    filetype = key['filename'].split('.')[-1:][0]
                    print "from filename", filetype
                except:
                    self.redirect("/no-filetype-detected")

            # Hash image
            unique_file_name_component = Image.check_unique_image(file_contents)

            # Generate a filename
            print "file will be named", unique_file_name_component, filetype
            file_name = Image.generate_image_name(unique_file_name_component, filetype)

            # Generate a URL 
            URL = Image.generate_orignal_image_url(options.s3_bucket, file_name)

            # Upload to S3
            AWSServices.upload_to_s3(options.aws_key, options.aws_secret, options.s3_bucket, file_contents, file_name, content_type)

            self.title = self.request.arguments['title'][0]

            
            user_id = int(tornado.escape.json_decode(self.get_secure_cookie("user_id")))
            print "userid", user_id

            Image.add_item_image(self.db, user_id, unique_file_name_component, self.title, URL)

            self.new_title = Image.readble_url(self.title)


        self.redirect("/"+unique_file_name_component+"/"+self.new_title)


    #def post(self):



class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            #(r'/upload', ImageUploadHandler), 
            (r'/recent', RecentHandler),
            (r'/', MainPageHandler),
            (r'/404', FourOhFourHandler),
            (r'/login', LoginHandler),
            (r'/signup', SignupHandler),
            (r'/home', HomeHandler),
            (r'/notchecked', AdNotEnabledHandler),
            (r'/thanks', ThanksHandler),
            (r'/createpost', CreatePostHandler),
            (r'/createpostitems/([^/]+)', CreatePostItemsHandler),
            #(r'/([^/]+)', PicHandler),
            (r'/([a-z0-9]+)(?:/[0-9a-zA-Z_-]+|/)?', PicHandler),
            ] 


        settings = dict(
            site_title=u"pic",
            cookie_secret="12oETzKXQAGaYdk9h2x9ff398g7np2XdTP1o/Vo=",
            login_url="/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            debug=options.debug,
            default_handler_class=FourOhFourHandler,
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            )
        tornado.web.Application.__init__(self, handlers, **settings)


        if 'CLEARDB_DATABASE_URL' in os.environ.keys():
            parsed = urlparse(os.environ['CLEARDB_DATABASE_URL'])
            options.mysql_host = parsed.hostname
            options.mysql_database = parsed.path.strip("/")
            options.mysql_user = parsed.username
            options.mysql_password = parsed.password


        self.db = torndb.Connection(host=options.mysql_host, database=options.mysql_database,
                                    user=options.mysql_user, password=options.mysql_password)


if __name__ == '__main__':
    tornado.options.parse_command_line()
    #tornado.options.parse_config_file(options.config_file)
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

