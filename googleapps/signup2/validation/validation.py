import webapp2
import cgi
form = """<form method="post">
  What is your birthday?
  <br>
  <label> Month <input type="text" name="month" value="%(month)s"> </label>
  <label> Day   <input type="text" name="day"   value="%(day)s">   </label>
  <label> Year  <input type="text" name="year"  value="%(year)s">  </label>
  <br>
  <div style="color: red">%(error)s</div>
  <input type="submit">
</form>"""
def escape_html(s):
            return cgi.escape(s, quote = True)
class Mainpage(webapp2.RequestHandler):

    def get(self):
            self.response.headers["Content-Type"]="text/html"
            self.write_form("","","","")
    def post(self):
            day = self.request.get("day")
            month = self.request.get("month")
            year = self.request.get("year")
            user_day   = self.valid_day(escape_html(self.request.get('day')))
            user_month = self.valid_month(escape_html(self.request.get('month')))
            user_year  = self.valid_year(escape_html(self.request.get('year')))

            if not (user_month and user_day and user_year):
              if user_month != True:
                emonth = "Please Enter a Valid Month"
              else:
                emonth = self.request.get('month')
              if user_year != True:
                eyear = "Please Enter a Valid Year"
              else:
                eyear = self.request.get('year')
              if user_day != True:
                eday = "Please Enter a Valid Day"
              else:
                eday = self.request.get('day')
              self.write_form("Error",month,eday,eyear) #change this for better error response
            else:
                self.redirect("/success")
    def write_form(self, error="", month="", day="", year=""):
            month = escape_html(month)
            day =escape_html(day)
            year =escape_html(year)
            self.response.write(form % {"error":error, "month":month, "day":day, "year":year})
    def valid_day(self, day):
            try:
              day = int(day)
              if (day <= 31 and day >= 0):
                return True
              else:
                return False
            except:
              return False
    def valid_month(self, month):
            months = ("jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec")
            month = month.lower()
            try:
              month = str(month)
              if (len(month) == 3 and month in months):
                return True
              else:
                return False
            except:
              return False
    def valid_year(self, year):
            try:
              year = int(year)
              if (year >= 1900 and year <= 2014):
                return True
              else:
                return False
            except:
              return False
class SuccessHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("Thanks! That's a totally valid day!!!")
application = webapp2.WSGIApplication([
    ('/', Mainpage),
    ('/success', SuccessHandler),  
], debug=True)