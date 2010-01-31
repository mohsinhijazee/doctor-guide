import cgi
import logging
import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db


from google.appengine.ext.webapp import template
from google.appengine.ext.db import djangoforms


specializations = set(['Neurology,', 'General', 'Psychology', 'Dental']);
hours = ["%02d" % h for h in range(1,13)]
mins = ["%02d" % h for h in range(0,60)]

#TODO: Doctor deletion
#TODO: What should be the default values for time boxes?
#TODO: Calculating the time difference
#      Time difference should be stored as float with following procedure
# time_to_store = hour + min/60
# if pm:
#   time_to_store += 12


def time_as_number(t):
    temp = t.split(':')
    
    h = float(temp[0])
    
    if h == 12 and temp[2].lower() == 'am':
        h = 0
        
    if h < 12 and temp[2].lower() == 'pm':
        h += 12
        
    h = h + float(temp[1])/60.0

    return h


def time_as_string(num):
    h = int(num)
    m = round((num - int(num)) * 60.0)
    
    ampm = 'AM'
    
    if h >= 12:
      h -= 12
      ampm = 'PM'
      
    return "%02d:%02d:%s" % (h,m,ampm)
    
    
#FIXME: Timings must be datetime.datetime
class Doctor(db.Model):
    name              = db.StringProperty('Name', required=True)
    specialization    = db.StringProperty('Specialization',
                         default='General', required=True, 
                         choices=specializations)
    sits_from         = db.FloatProperty('From')
    sits_upto         = db.FloatProperty('Up to')
    address           = db.PostalAddressProperty('Address')
    fee               = db.IntegerProperty('Fee')
    phone             = db.PhoneNumberProperty('Phone')
    email             = db.EmailProperty('Email')
    rating            = db.RatingProperty('Rating')
    
    def sits_from_string(self, time_as_str=None):
        if time_as_str is None:
           return time_as_string(self.sits_from)
        else:
           self.sits_from = time_as_number(time_as_str)
           
    def sits_upto_string(self, time_as_str=None):
        if time_as_str is None:
           return time_as_string(self.sits_upto)
        else:
           self.sits_upto = time_as_number(time_as_str)
    
    
    

# This is just temporary as we will not be generating the form
# own our own.
class DoctorForm(djangoforms.ModelForm):
    class Meta:
        model   = Doctor
        exclude = ['rating']
    

#TODO: The form should have a client side validation.
class DoctorsListings(webapp.RequestHandler):

    def get(self):
        
        doctors = db.GqlQuery("SELECT * FROM Doctor ORDER BY rating DESC LIMIT 10");
        
        template_values = {'doctors': doctors, 
                           'specializations' : specializations,
                           'hours': hours,
                           'mins': mins
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        
        self.response.out.write(template.render(path, template_values))
        #self.response.out.write(DoctorForm())
	
		
#TODO: This should do validation and should put all the errors in a dictionary
# that would be forwarded to the main page where it would be visible on the 
# form with relvant error messges.
class RegisterDoctor(webapp.RequestHandler):
    def post(self):
        
        doctor= Doctor(name=self.request.get('name'),  specialization=self.request.get('specialization'))
        
        from_time = "%s:%s:%s" % (self.request.get('sits_from_hour'),
                                  self.request.get('sits_from_min'),
                                  self.request.get('sits_from_ampm'))
                                  
        upto_time = "%s:%s:%s" % (self.request.get('sits_upto_hour'),
                                  self.request.get('sits_upto_min'),
                                  self.request.get('sits_upto_ampm'))

        doctor.sits_from = float(time_as_number(from_time))
        doctor.sits_upto = float(time_as_number(upto_time))
        doctor.address = db.PostalAddress(self.request.get('address'))
        doctor.fee = int(self.request.get('fee'))
        doctor.phone = db.PhoneNumber(self.request.get('phone'))
        doctor.email = db.Email(self.request.get('email'))
        
        doctor.put()
        
        self.redirect('/')
        
        
    


#FIXME: Remove this stuff.
class MainPage(webapp.RequestHandler):
    def get(self):
		  
        self.response.out.write("""<html><head><title>Guest book</title></head><body>""")
        
        greetings = db.GqlQuery("SELECT * FROM Greeting ORDER BY date DESC LIMIT 10")
        
        for greeting in greetings:
            if greeting.author:
                self.response.out.write('<b>%s</b> wrote:' % greeting.author.nickname())
            else:
                 self.response.out.write('An unknown person wrote')
            self.response.out.write("<blockquote>%s</blockquote>" % cgi.escape(greeting.content))

            
        
        # Write the page footer.
        self.response.out.write("""
          <form action="/sign" method="post">
            <div><textarea name="content" rows="3" cols="60"></textarea></div>
            <div><input type="submit" value="Sign Guestbook"></div>
          </form>
          </body>
        </html>
        """)


class GuestBook(webapp.RequestHandler):

    def post(self):
        greeting = Greeting()
        
        if users.get_current_user():
            greeting.author = users.get_current_user()
            
        greeting.content = self.request.get('content')
        greeting.put()
        self.redirect('/')

application = webapp.WSGIApplication([
('/', DoctorsListings),
('/newdoctor', RegisterDoctor),
('/sign', GuestBook)], debug=True)

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    run_wsgi_app(application)
  

if __name__ == "__main__":
    main()
