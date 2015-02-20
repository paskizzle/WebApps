import webapp2
import logging
import re
import jinja2
import os
import datetime
import time
import random
import string
import cgi
import hashlib
from google.appengine.ext import db
from datetime import timedelta
from datetime import datetime
import urllib2
from xml.dom import minidom
import json
from google.appengine.api import memcache
global update
update = True

def age_str(age):
   s = 'queried %s seconds ago'
   age = int(age)
   if age == 1:
      s = s.replace('seconds', 'second')
   return s % age
def mc_set(k,v):
    t = datetime.utcnow()
    tup = (v,t)
    memcache.set(k,tup)
    return None
def mc_get(k):
    if memcache.get(k):
        temp = memcache.get(k)[1]
        now = datetime.utcnow()
        dif = now - temp
        age = dif.total_seconds()
        tup = (memcache.get(k)[0],age)
    else:
        tup = (None, 0)
    return tup

def top_posts():
  global update
  if update == True:
    posts = db.GqlQuery("SELECT * FROM Blogpost "
                    "ORDER BY created DESC "
                    "Limit 10" )
    posts = list(posts)
    mc_set("topposts",posts)
    logging.info("db hit")
    update = False
    return mc_get("topposts")
  else:
    logging.info("cache hit")
    update = False
    return mc_get("topposts")
def get_coords(s):
    p = urllib2.urlopen(s)
    x = minidom.parseString(p.read())
    k = x.getElementsByTagName("ipLocation")
    if k:
        brick = k[0].childNodes[1].childNodes[1].childNodes[1].childNodes[0].nodeValue
        brickt = brick.split(",")
        newcoords = brickt[1] + ',' + brickt[0]
        return db.GeoPt(newcoords)
    else:
        return None

## see http://jinja.pocoo.org/docs/api/#autoescaping
def guess_autoescape(template_name):
    if template_name is None or '.' not in template_name:
        return False
    ext = template_name.rsplit('.', 1)[1]
    return ext in ('html', 'htm', 'xml')
def make_salt():
    salt = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(25)])
    return salt
def hash_str(s):
    s = str(s)
    s = hashlib.md5(s)
    return s.hexdigest()
def make_secure_val(name,pw,salt = None):
    if salt:
        s = name + pw + salt
        logging.info(s)
        fs = hash_str(name + pw + salt) + "|" + salt
        return fs
    else:
        salt = make_salt()
        s = name + pw + salt
        fs = hash_str(s) + "|" + salt
        return fs
def make_secure_val1(s):
    string = str(s) + '|' + hash_str(s)
    return string
def valid_pw(name,pw,h):
    temp = h.split('|')
    hs = temp[0]
    salt = temp[1]
    if make_secure_val(name,pw,salt) == h:
        return True
    else:
        return False
def check_secure_val(h):
    if h:
        temp = h.split('|')
        s = temp[0]
        if make_secure_val1(s) == h:
            return s
    else:
        return None
JINJA_ENVIRONMENT = jinja2.Environment(
    autoescape=guess_autoescape,     ## see http://jinja.pocoo.org/docs/api/#autoescaping
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

class MyHandler(webapp2.RequestHandler):
    def write(self, *items):    
        self.response.write(" : ".join(items))

    def render_str(self, template, **params):
        tplt = JINJA_ENVIRONMENT.get_template('templates/'+template)
        return tplt.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)

class Blogpost(db.Model):
    subject = db.StringProperty()
    content = db.TextProperty()
    created = db.DateTimeProperty(auto_now_add = True)
    coords  = db.GeoPtProperty()
    def as_dict(self):
      time_fmt = '%c'
      d = {'subject' : self.subject,
           'content' : self.content,
           'created' : self.created.strftime(time_fmt)}
      return d
class MainPage(MyHandler):
    def get(self):
        logging.info("********** MainPage GET **********")
        self.redirect('/blog')
class Newpost(MyHandler):
    def get(self):
        logging.info("*****newpost******")

        cookcheck = self.request.cookies.get("user_id")
        
        if cookcheck:
            temp = cookcheck.split('|')
            userid = int(temp[0])
            logging.info(userid)
        if check_secure_val(cookcheck):
            user = users.get_by_id(userid).username
            self.render("newpost.html", username = user)
        else:
            self.redirect("/blog/")

    def post(self):
        global update
        subject = self.request.get('subject')
        content = self.request.get('content')
        error = "please enter both subject and content!"
        urltemp = "http://api.hostip.info/?ip="
        ip = self.request.remote_addr
        ip = str(ip)
        urltemp1 = urltemp + ip
        p = Blogpost()
        if get_coords(urltemp1):
            p.coords = get_coords(urltemp1)
            logging.info(get_coords(urltemp1))
            p.put()
        else:
            ip1 = self.request.get("ip")
            urltemp2 = urltemp + ip1
            logging.info(get_coords(urltemp2))
            p.coords = get_coords(urltemp2)
            p.put()
        if not (content and subject):
            self.render("newpost.html", ph_subject = subject, ph_content = content, ph_error = error)
        if (content and subject):
            p.subject = subject
            p.content = content
            p.put()
            time.sleep(0.5)
            id = p.key().id()
            update = True
            self.redirect("/blog/"+str(id))
class BlogFront(MyHandler):
    def get(self):
        make_salt()
        cookcheck = self.request.cookies.get("user_id")
        logging.info("***************************" + str(cookcheck) + "*************************")
        if cookcheck and check_secure_val(cookcheck):
            temp = cookcheck.split('|')
            userid = int(temp[0])
            user = users.get_by_id(userid).username
            self.render_blog(username = user)
            logging.info("dicks*********************************************************")
        else:
            self.render_blog()
            logging.info("dicks22222*********************************************************")
    def render_blog(self, subject = "", content = "", username = ""):
        template = JINJA_ENVIRONMENT.get_template('templates/post.html')
        posts = top_posts()[0]
        params = {'post':"", "posts":posts}
        logging.info(posts)
        if self.request.url.endswith('.json'):

            self.render_json([post.as_dict() for post in posts])
        else:
            self.render("post.html", posts = posts, username = username, age = age_str(top_posts()[1]))
class Posthandler(MyHandler):
    def get(self, post_id):
        id = int(post_id)
        logging.info(id)
        cookcheck = self.request.cookies.get("user_id")
        temp = cookcheck.split('|')
        if cookcheck:
            userid = int(temp[0])
        logging.info(userid)
        if check_secure_val(cookcheck):
            user = users.get_by_id(userid).username
            self.render_post(username = user, id = id)
        else:
            self.redirect("/blog/")
    def render_post(self, id, subject = "", content = "", username = ""):
        id = int(id)
        if memcache.get(str(id)):
            logging.info("cache hit")
            posts = mc_get(str(id))[0]
        else:
            logging.info("db hit")
            p = {Blogpost.get_by_id(id)}
            mc_set(str(id), p)
            posts = mc_get(str(id))[0]
        params = {'post':"", "posts":posts, "age": age_str(mc_get(str(id))[1])}
        logging.info(posts)
        if self.request.url.endswith('.json'):
            self.render_json([post.as_dict() for post in posts])
            self.write(str(posts)+"write method")
        else:
            self.render("post.html", posts = posts, username = username, age = age_str(mc_get(str(id))[1]))
class users(db.Model):
    username = db.StringProperty()
    secureval = db.StringProperty()
    email = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add = True)

global epass
global everify
global euser
global eemail
eemail = ""
euser = ""
everify = ""
epass = ""
USER_RE = re.compile(r"^[a-z,A-Z,0-9,_,-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"[\w._%-]+@[\w.-]+\.[a-zA-Z]{2,4}")
def escape_html(s):
    return cgi.escape(s, quote = True)
def valid_user(username):
    match = db.GqlQuery("SELECT * FROM users WHERE username IN ('%s')"%username).get()
    if match:
        x = False
    else:
        x = True
    if USER_RE.match(username) and x:
        return True
def valid_password(password1, password2):
    if password1 == password2:
        logging.info("***PASWORDS MATCH***")
        if PASSWORD_RE.match(password1) and PASSWORD_RE.match(password2):
            logging.info("**********passowords legit**********")
            return True
        else:
            logging.info("*************passwords not legit**********")
            return False
    else:
        return 3
        logging.info("****************PASWORDS do not match**********")
def valid_email(email):
    if EMAIL_RE.match(email):
        return True
    elif len(email) == 0:
        logging.info("*******no email***********")
        return True
    else:
        return False
class SignupHandler(MyHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        global epass
        global everify
        global euser
        global eemail
        eemail = ""
        euser = ""
        everify = ""
        epass = ""
        self.write_form("","","","","","")

    def post(self):
        global epass
        global everify
        global euser
        global eemail
        eemail = ""
        euser = ""
        everify = ""
        epass = ""
        user = self.request.get("username")
        email = self.request.get("email")
        password = escape_html(self.request.get("password"))
        verify = escape_html(self.request.get("verify"))
        v_valid_user = valid_user(escape_html(self.request.get("username")))
        v_valid_password = valid_password(password, verify)
        v_valid_email = valid_email(escape_html(self.request.get("email")))
        if not (v_valid_user and v_valid_password and v_valid_email) or (v_valid_user and v_valid_password == 3 and v_valid_email):
            if v_valid_user == None:
                if db.GqlQuery("SELECT * FROM users WHERE username IN ('%s')"%user).get():
                    euser = "This username has been taken"
                else:
                    euser = "Please enter a valid Username (a-z,A-Z,0-9,_,-) length (3-20)"
                    logging.info(v_valid_user)
                    logging.info(euser)

            else:
                euser = ""
                logging.info(v_valid_user)
            if not v_valid_password:
                logging.info(v_valid_password)
                epass = "Please enter a valid Passsword (3-20)"
            else:
                if v_valid_password == 3:
                    everify = "Please make sure passwords match"
            if v_valid_email == False:
                eemail = "Please enter a valid email or leave blank"
            else:
                eemail = ""
            self.write_form(euser, epass, everify, eemail,user,email)
        else:
            u = users()
            u.username = user
            logging.info(make_secure_val(user,password))
            u.secureval = make_secure_val(user,password)
            u.email = email
            u.put()
            time.sleep(.2)
            self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/; max-age = 36000' % make_secure_val1(u.key().id()))
            self.redirect("/blog/welcome")
    def write_form(self, erroruser="", errorpassword="", errorverify="", erroremail="",user="",email=""):
        global euser
        global epass
        global everify
        global eemail
        logging.info("ERROR 2 "+ euser)
        template_values = {"erroruser": euser,
                           "errorpassword": epass,
                           "errorverify": everify,
                           "erroremail": eemail,
                           "username": user,
                           "email": email}
        template = JINJA_ENVIRONMENT.get_template('templates/form.html')
        self.response.write(template.render(template_values))  
class SuccessHandler(MyHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/welcome.html')
        cookcheck = self.request.cookies.get("user_id")
        if cookcheck:
            temp = cookcheck.split('|')
            userid = int(temp[0])
            logging.info(userid)
        if check_secure_val(cookcheck):
            user = users.get_by_id(userid).username
            self.render("welcome.html", user = user, username = user)
        else:
            self.redirect("/blog/")
class Login(MyHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/login.html')
        self.response.write(template.render())
    def post(self):
        user = escape_html(self.request.get("username"))
        password = escape_html(self.request.get("password"))
        error = "Invalid Login"
        match1 = db.GqlQuery("SELECT * FROM users WHERE username IN ('%s')"%user).get()
        if match1:
            id1 = match1.key().id()
        if match1 and valid_pw(user,password, match1.secureval):
            self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/; max-age = 36000' % make_secure_val1(id1))
            self.redirect("/blog/welcome")
        else:
            self.render("login.html",error = error)
class Logout(MyHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        self.redirect("/blog")
class MapHandler(MyHandler):
    def get(self):
        cookcheck = self.request.cookies.get("user_id")
        if cookcheck:
            temp = cookcheck.split('|')
            userid = int(temp[0])
            logging.info(userid)
        if check_secure_val(cookcheck):
            user = users.get_by_id(userid).username
            mapurl1 = "http://maps.googleapis.com/maps/api/staticmap?size=800x600&sensor=false"
            posts = db.GqlQuery("SELECT * FROM Blogpost")
            for x in posts:
                if x.coords:
                    y = x.coords
                    logging.info(y)
                    mapurl1 = mapurl1 + "&markers=" + str(y.lat) + "," + str(y.lon)
            self.render("map.html", username = user, mapurl = mapurl1)
        else:
            self.redirect("/blog/")
class Flushhandler(MyHandler):
    def get(self):
        global update
        memcache.flush_all()
        update = True
        self.redirect("/blog")

application = webapp2.WSGIApplication([
    (r'/', MainPage),
    (r'/blog/?', BlogFront),
    (r'/blog/newpost/?', Newpost),
    (r'/blog/(\d+)', Posthandler),
    (r'/blog/signup/?', SignupHandler),
    (r'/blog/welcome/?', SuccessHandler),
    (r'/blog/login/?', Login),
    (r'/blog/logout/?', Logout),
    (r'/blog/map/?', MapHandler),
    (r'/blog/?(?:\.json)?', BlogFront),
    (r'/blog/(\d+)(?:\.json)?', Posthandler),
    (r'/flush/?', Flushhandler)
], debug=True)