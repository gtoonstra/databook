from flask import Flask, render_template
from flask_admin import Admin, base
from flask_wtf.csrf import CSRFProtect
import flask_login
from databook.www import views
import logging
from errors import InvalidUsage


FORMAT = '%(asctime)-15s - %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)


csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.secret_key = 'super secret key'

    csrf.init_app(app)

    with app.app_context():
        admin = Admin(
            app, name='DataPortal',
            static_url_path='/',
            index_view=views.DataPortal(endpoint='', url='/', name="DataPortal"),
            template_mode='bootstrap3',
        )
        av = admin.add_view
        av(views.Person(name='Persons', category='Entities'))
        av(views.Table(name='Tables', category='Entities'))
        av(views.Chart(name='Charts', category='Entities'))
        av(views.Group(name='Groups', category='Entities'))

    login_manager = flask_login.LoginManager()

    @login_manager.user_loader
    def load_user(user_id):
        return views.DefaultUser(user_id)

    login_manager.login_view = "admin.login"
    login_manager.init_app(app)

    import api
    csrf.exempt(api.api_blueprint)
    app.register_blueprint(api.api_blueprint)

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    app.run()


app = None


def cached_app(config=None, testing=False):
    global app
    if not app:
        base_url = urlparse(configuration.get('webserver', 'base_url'))[2]
        if not base_url or base_url == '/':
            base_url = ""

        app = create_app(config, testing)
        app = DispatcherMiddleware(root_app, {base_url: app})
    return app
