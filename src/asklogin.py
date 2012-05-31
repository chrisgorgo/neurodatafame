import os

import webapp2

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.db import djangoforms

import jinja2

from resolve_doi import getPaperProperties


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

def clone_entity(e, **extra_args):
  """Clones an entity, adding or overriding constructor attributes.

  The cloned entity will have exactly the same property values as the original
  entity, except where overridden. By default it will have no parent entity or
  key name, unless supplied.

  Args:
    e: The entity to clone
    extra_args: Keyword arguments to override from the cloned entity and pass
      to the constructor.
  Returns:
    A cloned, possibly modified, copy of entity e.
  """
  klass = e.__class__
  props = dict((k, v.__get__(e, klass)) for k, v in klass.properties().iteritems())
  props.update(extra_args)
  return klass(**props)


class Paper(db.Model):
    doi = db.StringProperty(required=True)
    title = db.StringProperty()
    authors = db.StringProperty()
    publish_date = db.DateProperty()
    url = db.LinkProperty()
    dataset = db.StringProperty(required=True)
    dataset_url = db.StringProperty(required=True)
    n_subjects = db.IntegerProperty(required=True)
    potential_cost = db.IntegerProperty()
    added_by = db.UserProperty()
    add_date = db.DateProperty(auto_now_add=True)


class PaperForm(djangoforms.ModelForm):
    class Meta:
        model = Paper
        exclude = ['url', 'title', 'authors', 'publish_date', 'added_by']


class MainPage(webapp2.RequestHandler):
    def get(self):
        papers_query = Paper.all()

        papers = papers_query.fetch(None)
        total_cost = 0
        for paper in papers:
            total_cost += paper.potential_cost

        template_values = {
            'papers': papers,
            'total_cost': total_cost
        }

        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))


class AddPaper(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()
        if not user:
            template = jinja_environment.get_template('add_paper_login.html')
            self.response.out.write(template.render({'login_url' : users.create_login_url("/add_paper")}))
        else:
            template = jinja_environment.get_template('add_paper.html')
            key_name = self.request.get_all("key_name")
            if key_name:
                data = dict((k, v.__get__(Paper.get_by_key_name(key_name)[0], Paper)) for k, v in Paper.properties().iteritems())
                self.response.out.write(template.render({'form' : PaperForm(
                                                                            data=data
                                                                            ),
                                                         'edit_menu' : True}))
            else:
                self.response.out.write(template.render({'form' : PaperForm()}))

    def post(self):
        user = users.get_current_user()
        if not user:
            template = jinja_environment.get_template('add_paper_login.html')
            self.response.out.write(template.render({'login_url' : users.create_login_url("/add_paper")}))
        else:
            data = PaperForm(data=self.request.POST)
            if 'delete' in self.request.POST:
                entity = data.save(commit=False)
                Paper.get_by_key_name(entity.doi).delete()
                self.redirect('/')
            elif data.is_valid():
                entity = data.save(commit=False)
                entity = clone_entity(entity, key_name = entity.doi)
                entity.added_by = user
                entity.title, entity.authors, entity.url, entity.publish_date = getPaperProperties(entity.doi)
                if not entity.potential_cost:
                    entity.potential_cost = entity.n_subjects * 400
                # Save the data, and redirect to the view page
                entity.put()
                self.redirect('/')
            else:
                template = jinja_environment.get_template('add_paper.html')
                self.response.out.write(template.render(form=data))

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/add_paper', AddPaper)],
                              debug=True)