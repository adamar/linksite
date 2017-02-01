

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



class ThanksHandler(BaseHandler):
    """
    /thanks
    """
    @tornado.web.authenticated
    def get(self):
        self.render("thanksforsignup.html", site_title=self.settings['site_title'])


class FourOhFourHandler(BaseHandler):
    """

    """
    def get(self):
        self.render("404.html", site_title=self.settings['site_title'])


class CreatePostHandler(BaseHandler):
    """
    currently unused
    """
    @tornado.web.authenticated
    def get(self):

        self.render("create_post.html", site_title=self.settings['site_title'])


    @tornado.web.authenticated
    def post(self):

        #print self.get_secure_cookie("user_id")
        user_id = int(tornado.escape.json_decode(self.get_secure_cookie("user_id")))
        self.post_title = self.request.arguments['title'][0]

        #print user_id
        #print self.post_title

        res = Image.set_post(self.db, self.post_title, user_id)

        if res:
            self.redirect("/createpostitems/"+str(res))
        else:
            print "Error"


class CreatePostItemsHandler(BaseHandler):
    """
    currently unused
    """
    @tornado.web.authenticated
    def get(self, slug):

        items = Image.get_post_items(self.db, slug)
        print items

        self.render("create_post_items.html", site_title=self.settings['site_title'], items=items)


    @tornado.web.authenticated
    def post(self, slug):

        #for key in self.request.files:
        #    print key

        for key in self.request.files['filebutton[]']:

            ## Capture the files details
            file_contents = key['body']
            content_type = key['content_type']
            file_name = key['filename']

            ## Check filetype matches whats allowed
            filetype = Image.check_image_type(file_contents)

            ## Upload the file in the form
            AWSServices.upload_to_s3(options.aws_key, options.aws_secret, options.s3_bucket, file_contents, file_name, content_type)

            ## Generate an S3 URL for the uploaded file
            image_url = generate_orignal_image_url(options.s3_bucket, file_name)


        ## Get the file description from the form
        description = self.request.arguments['description'][0]
        urlified_description = Image.string_to_readble_url_snippet(description)

        print description
        print urlified_description

        ## Insert the file details of the newly uploaded file
        ## into the database
        Image.set_post_item(self.db, slug, description, image_url)

        self.redirect("/createpostitems/"+"1")




class ImageUploadHandler(BaseHandler):
    """
    currently unused
    """
    @tornado.web.authenticated
    def get(self):

        #images = Image.get_item_images(self.db, slug)

        #err = self.get_argument("err", default=None, strip=False)  
        #if err:
        #    err = self.get_error(err)
        self.render("upload.html", site_title=self.settings['site_title'])


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
        print uid
        if uid:
            self.set_secure_cookie("user", tornado.escape.json_encode(self.username))
            self.set_secure_cookie("user_id", tornado.escape.json_encode(uid))
            self.redirect("/home")
            
        else:
            self.redirect("/login")


class LogoutHandler(BaseHandler):
    """
    /logout
    """
    def get(self):

        self.clear_cookie("user")
        self.clear_cookie("user_id")

        self.redirect("/")






class FaqHandler(BaseHandler):
    """
    /faq
    """
    def get(self):
        self.render("faq.html", site_title=self.settings['site_title'])



class SignupHandler(BaseHandler):
    """
    /signup
    """
    def get(self):
        self.render("signup.html", site_title=self.settings['site_title'])


class SignupFormHandler(BaseHandler):
    """
    /signup-form
    """
    def get(self):
        self.render("signup-form.html", site_title=self.settings['site_title'])

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
        
        #uname = self.get_secure_cookie("user")

        #enabled = User.check_users_ad_enabled(self.db, uname)

        #if enabled:
        self.render("home.html", site_title=self.settings['site_title'])
        #else:
        #    self.redirect("/notchecked")


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
            #(r'/recent', RecentHandler),
            (r'/', MainPageHandler),
            (r'/404', FourOhFourHandler),
            (r'/login', LoginHandler),
            (r'/logout', LogoutHandler),
            (r'/signup', SignupHandler),
            (r'/signup-form', SignupFormHandler),
            (r'/home', HomeHandler),
            #(r'/notchecked', AdNotEnabledHandler),
            (r'/thanks', ThanksHandler),
            (r'/faq', FaqHandler),
            (r'/createpost', CreatePostHandler),
            (r'/createpostitems/([^/]+)', CreatePostItemsHandler),
            #(r'/([^/]+)', PicHandler),
            (r'/([a-z0-9]+)(?:/[0-9a-zA-Z_-]+|/)?', PicHandler),
            ] 


        settings = dict(
            site_title=u"pic",
            cookie_secret="12oETzKXQAGaYdk9h2x9ff398g7np2XdTP1o/Vo=",
            login_url="/login",
            xsrf_cookies=False,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            debug=options.debug,
            default_handler_class=FourOhFourHandler,
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            )
        tornado.web.Application.__init__(self, handlers, **settings)


        if 'AWS_ACCESS_KEY_ID' in os.environ.keys():
            options.aws_key = os.environ['AWS_ACCESS_KEY_ID']

        if 'AWS_SECRET_ACCESS_KEY' in os.environ.keys():
            options.aws_secret = os.environ['AWS_SECRET_ACCESS_KEY']

        if 'S3_BUCKET' in os.environ.keys():
            options.s3_bucket = os.environ['S3_BUCKET']


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

