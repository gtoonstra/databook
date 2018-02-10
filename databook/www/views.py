from flask_admin import BaseView, expose, AdminIndexView
from flask_login import login_required, login_user, logout_user, current_user
from flask import url_for, redirect, request, flash
from databook.www.neo4j_services import Neo4JService
from databook.www.utils import discover_type
from databook import configuration as conf
from ldap3 import Server, Connection, ALL, LEVEL, SUBTREE, BASE
from future.utils import native
from databook.utils.logging_mixin import LoggingMixin


log = LoggingMixin().log


def get_ldap_connection(dn=None, password=None):
    tls_configuration = None
    use_ssl = False
    try:
        cacert = conf.get("ldap", "cacert")
        tls_configuration = Tls(validate=ssl.CERT_REQUIRED, ca_certs_file=cacert)
        use_ssl = True
    except:
        pass

    server = Server(conf.get("ldap", "uri"), use_ssl, tls_configuration)
    conn = Connection(server, native(dn), native(password))

    if not conn.bind():
        log.error("Cannot bind to ldap server: %s ", conn.last_error)
        raise Exception("Cannot bind to ldap server")

    return conn


class DefaultUser(object):
    def __init__(self, userid):
        self.userid = userid

    def is_active(self):
        '''Required by flask_login'''
        return True

    def is_authenticated(self):
        '''Required by flask_login'''
        return True

    def is_anonymous(self):
        '''Required by flask_login'''
        return False

    def get_id(self):
        return self.userid

    @staticmethod
    def try_login(username, password):
        conn = get_ldap_connection(conf.get("ldap", "bind_user"),
                                   conf.get("ldap", "bind_password"))

        search_filter = "(&({0})({1}={2}))".format(
            conf.get("ldap", "user_filter"),
            conf.get("ldap", "user_name_attr"),
            username
        )

        search_scopes = {
            "LEVEL": LEVEL,
            "SUBTREE": SUBTREE,
            "BASE": BASE
        }

        search_scope = LEVEL
        if conf.has_option("ldap", "search_scope"):
            search_scope = SUBTREE if conf.get("ldap", "search_scope") == "SUBTREE" else LEVEL

        # todo: BASE or ONELEVEL?

        res = conn.search(native(conf.get("ldap", "basedn")),
                          native(search_filter),
                          search_scope=native(search_scope))

        # todo: use list or result?
        if not res:
            log.info("Cannot find user %s", username)
            raise Exception("Invalid username or password")

        entry = conn.response[0]

        conn.unbind()

        if 'dn' not in entry:
            # The search filter for the user did not return any values, so an
            # invalid user was used for credentials.
            raise Exception("Invalid username or password")

        try:
            conn = get_ldap_connection(entry['dn'], password)
        except KeyError as e:
            log.error("""
            Unable to parse LDAP structure. If you're using Active Directory and not specifying an OU, you must set search_scope=SUBTREE in airflow.cfg.
            %s
            """ % traceback.format_exc())
            raise Exception("Could not parse LDAP structure. Try setting search_scope in airflow.cfg, or check logs")

        if not conn:
            log.info("Password incorrect for user %s", username)
            raise Exception("Invalid username or password")

        return DefaultUser(username)


class Databook(AdminIndexView):

    def is_visible(self):
        return True

    @expose('/', methods=['GET', 'POST'])
    @login_required
    def index(self):
        return self.render('search.html')

    @expose('/logout')
    def logout(self):
        logout_user()
        flash('You have been logged out.')
        return redirect(url_for('admin.index'))


class Login(BaseView):

    def is_visible(self):
        return True

    @expose('/')
    def index(self):
        return self.render('error.html')

    @expose('/login', methods=['GET', 'POST'])
    def login(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']        

            user = DefaultUser.try_login(username, password)
            login_user(user)
            next_url = request.args.get('next')
            return redirect(next_url or url_for("admin.index"))
        return self.render('login.html')


class Person(BaseView):

    def is_visible(self):
        return True

    @expose('/')
    @login_required
    def index(self):
        return self.render('error.html')

    @expose('/me')
    @login_required
    def me(self):
        svc = Neo4JService()

        person_uuid = None
        personList = svc.query(
            "MATCH (a:Entity:Org:Person) WHERE a.id = {login} "
            "RETURN a.uuid as uuid", {"login": current_user.get_id()})
        if len(personList) > 0:
            person_uuid = personList[0]['uuid']

        return self.showPerson(person_uuid)        

    @expose('/<string:person_id>')
    @login_required
    def showPerson(self, person_id):
        svc = Neo4JService()
        person = {'name': 'Untitled'}
        personList = svc.query(
            "MATCH (a:Entity:Org:Person) WHERE a.uuid = {uuid} "
            "RETURN a", {"uuid": person_id})
        if len(personList) > 0:
            person = personList[0]['a'].properties
            person['link'] = url_for('person.showPerson', person_id=person['uuid'])

        groups = []
        groupList = svc.query("MATCH (p:Entity:Org:Person {uuid: {uuid}})-[s:ASSOCIATED]->(g:Entity:Org:Group) "
            "RETURN g", {"uuid": person_id})
        for record in groupList:
            d = record['g'].properties
            d['link'] = url_for('group.showGroup', group_id=d['uuid'])
            groups.append(d)

        favorites = []
        favoritesList = svc.query("MATCH (p:Entity:Org:Person {uuid: {uuid}})-[s:LIKES]->(c) "
            "RETURN c, labels(c) as l", {"uuid": person_id})
        for record in favoritesList:
            d = record['c'].properties
            d['type'] = discover_type(record['l'])
            if d['type'] == 'Database:Table':
                d['link'] = url_for('table.showTable', table_id=d['uuid'])
            elif d['type'] == 'Tableau:Chart':
                d['link'] = url_for('chart.showChart', chart_id=d['uuid'])
            elif d['type'] == 'Org:Group':
                d['link'] = url_for('group.showGroup', group_id=d['uuid'])
            favorites.append(d)
        
        return self.render('person.html',
            person=person, 
            groups=groups,
            favorites=favorites)
""" DISABLE
        created = []
        createList = svc.query("MATCH (p:Entity:Org:Person {uuid: {uuid}})-[s:CREATED]->(c)<-[r:CONSUMED]-() "
            "RETURN c, labels(c) as l, COUNT(r) as count "
            "ORDER BY COUNT(r) DESC "
            "LIMIT 20", {"uuid": person_id})
        for record in createList:
            d = record['c'].properties
            d['type'] = discover_type(record['l'])
            d['count'] = record['count']
            if d['type'] == 'Database:Table':
                d['link'] = url_for('table.showTable', table_id=d['uuid'])
            elif d['type'] == 'Tableau:Chart':
                d['link'] = url_for('chart.showChart', chart_id=d['uuid'])
            created.append(d)

        consumed = []
        consumptionList = svc.query("MATCH (p:Entity:Org:Person {uuid: {uuid}})-[s:CONSUMED]->(c) "
            "RETURN c, labels(c) as l", {"uuid": person_id})
        for record in consumptionList:
            d = record['c'].properties
            d['type'] = discover_type(record['l'])
            if d['type'] == 'Database:Table':
                d['link'] = url_for('table.showTable', table_id=d['uuid'])
            elif d['type'] == 'Tableau:Chart':
                d['link'] = url_for('chart.showChart', chart_id=d['uuid'])
            consumed.append(d)
"""



class Group(BaseView):

    def is_visible(self):
        return False

    @expose('/')
    @login_required
    def index(self):
        return self.render('error.html')

    @expose('/<string:group_id>')
    @login_required
    def showGroup(self, group_id):
        svc = Neo4JService()
        group = {'name': 'Untitled'}

        person_uuid = None
        personList = svc.query(
            "MATCH (a:Entity:Org:Person) WHERE a.id = {login} "
            "RETURN a.uuid as uuid", {"login": current_user.get_id()})
        if len(personList) > 0:
            person_uuid = personList[0]['uuid']

        groupList = svc.query(
            "MATCH (a:Entity:Org:Group) WHERE a.uuid = {uuid} "
            "RETURN a", {"uuid": group_id})
        if len(groupList) > 0:
            group = groupList[0]['a'].properties
        else:
            group['uuid'] = '-1'

        groupList = svc.query(
            "MATCH (a:Entity:Org:Group {uuid: {uuid}})<-[s:LIKES]-(p:Entity:Org:Person {uuid: {person_uuid}}) "
            "RETURN COUNT(s) as count", {"uuid": group_id, "person_uuid": person_uuid})
        if len(groupList) > 0:
            if groupList[0]['count'] > 0:
                group['liked'] = 1
            else:
                group['liked'] = 0

        members = []
        memberList = svc.query("MATCH (a:Entity:Org:Group {uuid: {uuid}})<-[s:ASSOCIATED]-(p:Entity:Org:Person) "
            "RETURN p", {"uuid": group_id})
        for record in memberList:
            d = record['p'].properties
            d['link'] = url_for('person.showPerson', person_id=d['uuid'])
            members.append(d)

        isMember = False
        for member in members:
            if member['id'] == current_user.get_id():
                isMember = True

        return self.render('group.html', 
            group=group,
            members=members,
            isMember=isMember)

""" DISABLE 
        charts = []
        chartList = svc.query("MATCH (a:Entity:Org:Group {uuid: {uuid}})<-[s:ASSOCIATED]-(p:Entity:Org:Person)"
            "-[b:CREATED]->(c:Entity:Tableau:Chart)<-[r:CONSUMED]-() "
            "RETURN c, COUNT(r) as count "
            "ORDER BY COUNT(r) DESC "
            "LIMIT 10", {"uuid": group_id})
        for record in chartList:
            d = record['c'].properties
            d['link'] = url_for('chart.showChart', chart_id=d['uuid'])
            charts.append(d)

        tables = []
        tableList = svc.query("MATCH (a:Entity:Org:Group {uuid: {uuid}})<-[s:ASSOCIATED]-(p:Entity:Org:Person)"
            "-[b:CREATED]->(t:Entity:Database:Table)<-[r:CONSUMED]-() "
            "RETURN t, COUNT(r) as count "
            "ORDER BY COUNT(r) DESC "
            "LIMIT 10", {"uuid": group_id})
        for record in tableList:
            d = record['t'].properties
            d['link'] = url_for('table.showTable', table_id=d['uuid'])
            tables.append(d)

"""

""" DISABLE 
class Table(BaseView):

    def is_visible(self):
        return True

    @expose('/')
    @login_required
    def index(self):
        return self.render('error.html')

    @expose('/<string:table_id>')
    @login_required
    def showTable(self, table_id):
        svc = Neo4JService()
        table = {'name': 'Untitled'}

        person_uuid = None
        personList = svc.query(
            "MATCH (a:Entity:Org:Person) WHERE a.id = {login} "
            "RETURN a.uuid as uuid", {"login": current_user.get_id()})
        if len(personList) > 0:
            person_uuid = personList[0]['uuid']

        tableList = svc.query(
            "MATCH (a:Entity:Database:Table {uuid: {uuid}}) "
            "RETURN a", {"uuid": table_id})
        if len(tableList) > 0:
            table = tableList[0]['a'].properties

        tableList = svc.query(
            "MATCH (a:Entity:Database:Table {uuid: {uuid}})<-[s:LIKES]-(p:Entity:Org:Person {uuid: {person_uuid}}) "
            "RETURN COUNT(s) as count", {"uuid": table_id, "person_uuid": person_uuid})
        if len(tableList) > 0:
            if tableList[0]['count'] > 0:
                table['liked'] = 1
            else:
                table['liked'] = 0

        upstream = []
        upstreamList = svc.query("MATCH (a:Entity:Database:Table {uuid: {uuid}})-[s:CONSUMED *1..3]->(t:Entity:Database:Table) "
            "RETURN t", {"uuid": table_id})
        for record in upstreamList:
            d = record['t'].properties
            d['link'] = url_for('table.showTable', table_id=d['uuid'])
            upstream.append(d)

        downstream = []
        downstreamList = svc.query("MATCH (a:Entity:Database:Table {uuid: {uuid}})<-[s:CONSUMED *1..3]-(t:Entity:Database:Table) "
            "RETURN t", {"uuid": table_id})
        for record in downstreamList:
            d = record['t'].properties
            d['link'] = url_for('table.showTable', table_id=d['uuid'])
            downstream.append(d)

        charts = []
        chartList = svc.query("MATCH (a:Entity:Database:Table {uuid: {uuid}})<-[s:CONSUMED]-(c:Entity:Tableau:Chart) "
            "RETURN c", {"uuid": table_id})
        for record in chartList:
            d = record['c'].properties
            d['link'] = url_for('chart.showChart', chart_id=d['uuid'])
            charts.append(d)

        creators = []
        creatorList = svc.query("MATCH (a:Entity:Database:Table {uuid: {uuid}})<-[s:CREATED]-(p:Entity:Org:Person) "
            "RETURN p", {"uuid": table_id})
        for record in creatorList:
            d = record['p'].properties
            d['link'] = url_for('person.showPerson', person_id=d['uuid'])
            creators.append(d)

        consumers = []
        consumerList = svc.query("MATCH (t:Entity:Database:Table {uuid: {uuid}})<-[a:CONSUMED]-()"
            "<-[b:CONSUMED]-(p:Entity:Org:Person) "
            "RETURN p, COUNT(b) as count "
            "ORDER BY COUNT(b) DESC "
            "LIMIT 10", {"uuid": table_id})
        for record in consumerList:
            d = record['p'].properties
            d['link'] = url_for('person.showPerson', person_id=d['uuid'])
            consumers.append(d)

        consumerGroups = []
        consumerGroupList = svc.query("MATCH (t:Entity:Database:Table {uuid: {uuid}})<-[a:CONSUMED]-()"
            "<-[b:CONSUMED]-(p:Entity:Org:Person)-[r:ASSOCIATED]->(g:Entity:Org:Group) "
            "RETURN g, COUNT(r) as count "
            "ORDER BY COUNT(r) DESC "
            "LIMIT 10", {"uuid": table_id})
        for record in consumerGroupList:
            d = record['g'].properties
            d['link'] = url_for('group.showGroup', group_id=d['uuid'])
            consumerGroups.append(d)

        consumptionCount = None
        consumptionList = svc.query("MATCH (t:Entity:Database:Table {uuid: {uuid}})<-[a:CONSUMED]-()"
            "<-[b:CONSUMED]-(p:Entity:Org:Person) "
            "RETURN COUNT(b) as count ", {"uuid": table_id})
        for record in consumptionList:
            consumptionCount = record['count']

        return self.render('table.html', 
            table=table,
            upstream=upstream,
            downstream=downstream,
            charts=charts,
            creators=creators,
            consumers=consumers,
            consumerGroups=consumerGroups,
            consumptionCount=consumptionCount)


class Chart(BaseView):

    def is_visible(self):
        return False

    @expose('/')
    @login_required
    def index(self):
        return self.render('error.html')

    @expose('/<string:chart_id>')
    @login_required
    def showChart(self, chart_id):
        svc = Neo4JService()
        chart = {'name': 'Untitled'}

        person_uuid = None
        personList = svc.query(
            "MATCH (a:Entity:Org:Person) WHERE a.id = {login} "
            "RETURN a.uuid as uuid", {"login": current_user.get_id()})
        if len(personList) > 0:
            person_uuid = personList[0]['uuid']

        chartList = svc.query(
            "MATCH (a:Entity:Tableau:Chart) WHERE a.uuid = {uuid} "
            "RETURN a", {"uuid": chart_id})
        if len(chartList) > 0:
            chart = chartList[0]['a'].properties

        chartList = svc.query(
            "MATCH (a:Entity:Tableau:Chart {uuid: {uuid}})<-[s:LIKES]-(p:Entity:Org:Person {uuid: {person_uuid}}) "
            "RETURN COUNT(s) as count", {"uuid": chart_id, "person_uuid": person_uuid})
        if len(chartList) > 0:
            if chartList[0]['count'] > 0:
                chart['liked'] = 1
            else:
                chart['liked'] = 0

        creators = []
        creatorList = svc.query("MATCH (a:Entity:Tableau:Chart {uuid: {uuid}})<-[s:CREATED]-(p:Entity:Org:Person) "
            "RETURN p", {"uuid": chart_id})
        for record in creatorList:
            d = record['p'].properties
            d['link'] = url_for('person.showPerson', person_id=d['uuid'])
            creators.append(d)

        consumers = []
        consumerList = svc.query("MATCH (a:Entity:Tableau:Chart {uuid: {uuid}})<-[r:CONSUMED]-(p:Entity:Org:Person) "
            "RETURN p, COUNT(r) as count "
            "ORDER BY COUNT(r) DESC "
            "LIMIT 10", {"uuid": chart_id})
        for record in consumerList:
            d = record['p'].properties
            d['link'] = url_for('person.showPerson', person_id=d['uuid'])
            consumers.append(d)

        tables = []
        tablesList = svc.query("MATCH (a:Entity:Tableau:Chart {uuid: {uuid}})-[s:CONSUMED]->(t:Entity:Database:Table) "
            "RETURN t", {"uuid": chart_id})
        for record in tablesList:
            d = record['t'].properties
            d['link'] = url_for('table.showTable', table_id=d['uuid'])
            tables.append(d)

        workbook = None
        workbookList = svc.query("MATCH (a:Entity:Tableau:Chart {uuid: {uuid}})-[s:ASSOCIATED]->(w:Entity:Tableau:Workbook) "
            "RETURN w", {"uuid": chart_id})
        for record in workbookList:
            d = record['w'].properties
            workbook = d

        return self.render('chart.html', 
            chart=chart,
            creators=creators,
            consumers=consumers,
            tables=tables,
            workbook=workbook)
"""

