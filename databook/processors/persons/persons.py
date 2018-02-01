import logging
import configuration
import github
import slack

from future.utils import native
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES
from lib.hierarchy import Person, Group, Organization


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# # set a connection without encryption: uri = ldap://<your.ldap.server>:<port>
# uri = ldaps://<your.ldap.server>:<port>
# user_filter = objectClass=*
# # in case of Active Directory you would use: user_name_attr = sAMAccountName
# user_name_attr = uid
# superuser_filter = memberOf=CN=airflow-super-users,OU=Groups,OU=RWC,OU=US,OU=NORAM,DC=example,DC=com
# data_profiler_filter = memberOf=CN=airflow-data-profilers,OU=Groups,OU=RWC,OU=US,OU=NORAM,DC=example,DC=com
# bind_user = cn=Manager,dc=example,dc=com
# bind_password = insecure
# basedn = dc=example,dc=com
# cacert = /etc/ca/ldap_ca.crt
# # Set search_scope to one of them:  BASE, LEVEL , SUBTREE
# # Set search_scope to SUBTREE if using Active Directory, and not specifying an Organizational Unit
# search_scope = LEVEL

def get_ldap_connection(dn=None, password=None):
    server = Server(configuration.LDAP_URI, get_info=ALL)
    conn = Connection(server, native(dn), native(password))

    if not conn.bind():
        logger.error("Cannot bind to ldap server: %s ", conn.last_error)
        raise Exception("Cannot bind to ldap server")

    return conn


def query_users(org):
    searchParameters = { 'search_base': 'dc=demo1,dc=freeipa,dc=org',
                         'search_filter': '(objectClass=person)',
                         'attributes': [ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, 'mail', 'displayName', 'manager'] }

    logger.info("Connecting to LDAP to get users")
    conn = get_ldap_connection(configuration.LDAP_USER, configuration.LDAP_PASS)
    conn.search(**searchParameters)

    for entry in conn.entries:
        l = entry['memberOf'].value
        if l:
            for member in l:
                if not ',cn=groups,' in member:
                    print("Removing {0}".format(member))
                    l.remove(member)
        else:
            l = []

        person = Person(dn=entry.entry_dn, 
                        cn=entry['cn'], 
                        role=entry['sn'],
                        login=entry['uid'], 
                        mail=entry['mail'], 
                        manager=entry['manager'],
                        displayName=entry['displayName'], 
                        memberOf=entry['memberOf'])
        org.add_person(person)


def query_groups(org):
    searchParameters = { 'search_base': 'dc=demo1,dc=freeipa,dc=org',
                         'search_filter': '(objectClass=posixgroup)',
                         'attributes': ['displayName', 'cn', 'description'] }

    logger.info("Connecting to LDAP to get groups")
    conn = get_ldap_connection(configuration.LDAP_USER, configuration.LDAP_PASS)
    conn.search(**searchParameters)

    for entry in conn.entries:
        group = Group(dn=entry.entry_dn,
                      cn=entry['cn'],
                      displayName=entry['displayName'],
                      description=entry['description'])
        org.add_group(group)


def main():
    org = Organization()
    query_groups(org)
    query_users(org)

    for person in org.iter_persons():
        # Look up github profile if there is one
        github.add_github_details(person)
        # slack lookup
        slack.add_slack_details(person)

    f = open('persons.csv', 'w')
    f.write('login,email,name,role,slack,github,location\n')

    for person in org.iter_persons():
        f.write('{p.login},{p.mail},{p.displayName},{p.role},{p.slack},{p.github},{p.location}\n'.format(p=person))
    f.flush()
    f.close()

    f = open('person_groups.csv', 'w')
    f.write('login,relation,group,description\n')

    for person in org.iter_persons():
        for group in person.iter_groups():
            f.write('{p.login},ASSOCIATED,{g.cn},{g.description}\n'.format(p=person, g=group))
    f.flush()
    f.close()    


if __name__ == "__main__":
    main()
