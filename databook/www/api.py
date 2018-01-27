import logging

from flask import Blueprint
from flask_login import login_required, current_user
from flask import request
from flask import jsonify
from flask import url_for
from databook.www.errors import InvalidUsage
from databook.www import search
from databook.www.neo4j_services import Neo4JService
from databook.utils.logging_mixin import LoggingMixin


logger = LoggingMixin().log
api_blueprint = Blueprint('apiv1', __name__)


def get_person_data(res):
    data = []
    for hit in res['hits']['hits']:
        d = {}
        d['_id'] = hit['_id']
        d['link'] = url_for('person.showPerson', person_id=d['_id'])
        for k, v in hit['_source'].items():
            d[k] = v
        data.append(d)    
    return data


def get_tableau_data(res):
    data = []
    for hit in res['hits']['hits']:
        d = {}
        d['_id'] = hit['_id']
        d['link'] = url_for('chart.showChart', chart_id=d['_id'])
        for k, v in hit['_source'].items():
            d[k] = v
        data.append(d)    
    return data


def get_group_data(res):
    data = []
    for hit in res['hits']['hits']:
        d = {}
        d['_id'] = hit['_id']
        d['link'] = url_for('group.showGroup', group_id=d['_id'])
        for k, v in hit['_source'].items():
            d[k] = v
        data.append(d)    
    return data


def get_table_data(res):
    data = []
    for hit in res['hits']['hits']:
        d = {}
        d['_id'] = hit['_id']
        d['link'] = url_for('table.showTable', table_id=d['_id'])
        for k, v in hit['_source'].items():
            d[k] = v
        data.append(d)    
    return data


@api_blueprint.route('/search', methods=['POST'])
@login_required
def searchTerm():
    searchterm = request.json['searchTerm']
    nodetype = request.json['nodeType']

    logger.info("Called search with '{0}'".format(searchterm))

    res = None
    if nodetype == "any":
        res = search.search_elastic(searchterm)
    if nodetype == "person":
        res = search.search_elastic(searchterm, doc_type="Person")
    if nodetype == "group":
        res = search.search_elastic(searchterm, doc_type="Group")
    if nodetype == "tableau":
        res = search.search_elastic(searchterm, doc_type="Tableau")
    if nodetype == "table":
        res = search.search_elastic(searchterm, doc_type="Table")

    data = None
    if len(res) > 0:
        if nodetype == "person":
            data = get_person_data(res)
        if nodetype == "group":
            data = get_group_data(res)
        if nodetype == "tableau":
            data = get_tableau_data(res)
        if nodetype == "table":
            data = get_table_data(res)

    logger.info("Found {0} results".format(len(data)))

    return jsonify(data)


@api_blueprint.route('/favorite_table', methods=['POST'])
@login_required
def favoriteTable():
    favorite = request.json['favorite']
    table_uuid = request.json['table_uuid']

    logger.info("Favouriting table {0} for {1}".format(table_uuid, current_user.get_id()))

    svc = Neo4JService()
    if favorite:
        svc.query("MATCH (table:Entity:Database:Table {uuid: {uuid}}), (person:Entity:Org:Person {id: {login}}) "
            "MERGE (person)-[r:LIKES]->(table)", {"uuid": table_uuid, "login": current_user.get_id()})
    else:
        svc.query("MATCH (person:Entity:Org:Person {id: {login}})-[r:LIKES]->(table:Entity:Database:Table {uuid: {uuid}}) "
            "DELETE r", {"uuid": table_uuid, "login": current_user.get_id()})

    return jsonify({})


@api_blueprint.route('/favorite_chart', methods=['POST'])
@login_required
def favoriteChart():
    favorite = request.json['favorite']
    chart_uuid = request.json['chart_uuid']

    logger.info("Favouriting chart {0} for {1}".format(chart_uuid, current_user.get_id()))

    svc = Neo4JService()
    if favorite:
        svc.query("MATCH (table:Entity:Tableau:Chart {uuid: {uuid}}), (person:Entity:Org:Person {id: {login}}) "
            "MERGE (person)-[r:LIKES]->(table)", {"uuid": chart_uuid, "login": current_user.get_id()})
    else:
        svc.query("MATCH (person:Entity:Org:Person {id: {login}})-[r:LIKES]->(table:Entity:Tableau:Chart {uuid: {uuid}}) "
            "DELETE r", {"uuid": chart_uuid, "login": current_user.get_id()})

    return jsonify({})


@api_blueprint.route('/favorite_group', methods=['POST'])
@login_required
def favoriteGroup():
    favorite = request.json['favorite']
    group_uuid = request.json['group_uuid']

    logger.info("Favouriting group {0} for {1}".format(group_uuid, current_user.get_id()))

    svc = Neo4JService()
    if favorite:
        svc.query("MATCH (group:Entity:Org:Group {uuid: {uuid}}), (person:Entity:Org:Person {id: {login}}) "
            "MERGE (person)-[r:LIKES]->(group)", {"uuid": group_uuid, "login": current_user.get_id()})
    else:
        svc.query("MATCH (person:Entity:Org:Person {id: {login}})-[r:LIKES]->(table:Entity:Org:Group {uuid: {uuid}}) "
            "DELETE r", {"uuid": group_uuid, "login": current_user.get_id()})

    return jsonify({})

@api_blueprint.route('/create_group', methods=['POST'])
@login_required
def createGroup():
    group_name = request.json['groupTitle']

    logger.info("Trying to create group {0}".format(group_name))

    svc = Neo4JService()
    groupList = svc.query("MATCH (g:Entity:Org:Group {name: {name}}) "
        "RETURN g", {"name": group_name})
    if len(groupList) > 0:
        res = jsonify({"error": "group already exists"})
        res.status_code = 400
        return res

    groupList = svc.query("MERGE (g:Entity:Org:Group {name: {name}}) "
        "WITH g "
        "MATCH (person:Entity:Org:Person {id: {login}}) "
        "MERGE (person)-[r:ASSOCIATED]->(g) "
        "RETURN g", {"name": group_name, "login": current_user.get_id()})

    groupList = svc.query("MATCH (g:Entity:Org:Group {name: {name}}) "
        "RETURN g", {"name": group_name})
    if len(groupList) > 0:
        group = groupList[0]['g'].properties

    url = url_for('group.showGroup', group_id=group['uuid'])

    return jsonify({"url": url})

@api_blueprint.route('/leave_group', methods=['POST'])
@login_required
def leaveGroup():
    group_uuid = request.json['uuid']

    logger.info("Trying to leave group {0}".format(group_uuid))

    svc = Neo4JService()
    groupList = svc.query("MATCH (g:Entity:Org:Group {uuid: {uuid}}) "
        "RETURN g", {"uuid": group_uuid})
    if len(groupList) == 0:
        res = jsonify({"error": "group does not exist"})
        res.status_code = 400
        return res
    else:
        group = groupList[0]['g'].properties

    groupList = svc.query("MATCH (g:Entity:Org:Group {uuid: {uuid}}) "
        "MATCH (person:Entity:Org:Person {id: {login}}) "
        "MATCH (person)-[r:ASSOCIATED]->(g) "
        "DELETE r", {"uuid": group_uuid, "login": current_user.get_id()})

    url = url_for('group.showGroup', group_id=group['uuid'])

    return jsonify({"url": url})

@api_blueprint.route('/join_group', methods=['POST'])
@login_required
def joinGroup():
    group_uuid = request.json['uuid']

    logger.info("Trying to join group {0}".format(group_uuid))

    svc = Neo4JService()
    groupList = svc.query("MATCH (g:Entity:Org:Group {uuid: {uuid}}) "
        "RETURN g", {"uuid": group_uuid})
    if len(groupList) == 0:
        res = jsonify({"error": "group does not exist"})
        res.status_code = 400
        return res
    else:
        group = groupList[0]['g'].properties

    groupList = svc.query("MATCH (g:Entity:Org:Group {uuid: {uuid}}) "
        "MATCH (person:Entity:Org:Person {id: {login}}) "
        "MERGE (person)-[r:ASSOCIATED]->(g) "
        "RETURN g", {"uuid": group_uuid, "login": current_user.get_id()})

    url = url_for('group.showGroup', group_id=group['uuid'])

    return jsonify({"url": url})
