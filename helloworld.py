import cgi
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

import logging
import os
from google.appengine.ext.webapp import template


specializations = set(['Neurology,', 'General', 'Psychology', 'Dental']);

class Doctor(db.Model):
    name              = db.StringProperty('Name' )
    specialization    = db.StringProperty('Specialization', 
        default='General', required=True, choices=specializations)
    sits_from = db.StringProperty('From')
    sits_upto = db.StringProperty('Up to')
    address = db.StringProperty('Address')
    rating = db.RatingProperty()
    

class DoctorsListings(webapp.RequestHandler):

    def get(self):
        
        doctors = db.GqlQuery("SELECT * FROM Doctor ORDER BY rating DESC LIMIT 10");
        
        template_values = {'doctors': doctors, 'specializations' : specializations}
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        
        self.response.out.write(template.render(path, template_values))
	
		
class RegisterDoctor(webapp.RequestHandler):
	def post(self):
	   
		_name = self.request.get('name')
		_spec = self.request.get('specialization')
		_frm = self.request.get('sits_from')
		_to = self.request.get('sits_upto')
		_address = self.request.get('address')
		
		doctor = Doctor()
		
		doctor.name = _name
		doctor.specialization = _spec
		doctor.sits_from = _frm
		doctor.sits_upto = _to
		doctor.address = _address
		 
		doctor.put()
		
		self.redirect('/')
    


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
