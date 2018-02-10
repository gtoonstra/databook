from flask import Flask, render_template
from flask_admin import Admin, base
from flask_wtf.csrf import CSRFProtect
from six.moves.urllib.parse import urlparse
from werkzeug.wsgi import DispatcherMiddleware
import flask_login
from databook.www import views
import logging
from databook.www.errors import InvalidUsage
from databook.utils.logging_mixin import LoggingMixin
from databook import configuration as conf


csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.secret_key = 'super secret key'

    csrf.init_app(app)

    with app.app_context():
        admin = Admin(
            app, name='DataBook',
            static_url_path='/',
            index_view=views.Databook(endpoint='', url='/', name="Databook"),
            template_mode='bootstrap3',
        )
        av = admin.add_view
        av(views.Login(name='Login', category='Admin'))
        av(views.Person(name='Persons', category='Entities'))
        av(views.Group(name='Groups', category='Entities'))
        av(views.Table(name='Tables', category='Entities'))
        #av(views.Chart(name='Charts', category='Entities'))

    login_manager = flask_login.LoginManager()

    @login_manager.user_loader
    def load_user(user_id):
        return views.DefaultUser(user_id)

    login_manager.login_view = "login.login"
    login_manager.init_app(app)

    from databook.www import api
    csrf.exempt(api.api_blueprint)
    app.register_blueprint(api.api_blueprint)

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    return app


app = None

def root_app(env, resp):
    resp(b'404 Not Found', [(b'Content-Type', b'text/plain')])
    return [b'Apache Airflow is not at this location']


def cached_app(config=None, testing=False):
    global app
    if not app:
        base_url = urlparse(conf.get('webserver', 'base_url'))[2]
        if not base_url or base_url == '/':
            base_url = ""

        app = create_app()
        app = DispatcherMiddleware(root_app, {base_url: app})
    return app


if __name__ == "__main__":
    app = cached_app()
    app.run()
