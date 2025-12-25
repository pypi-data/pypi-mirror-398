from neo4j import GraphDatabase
import configparser
from .constants import *

config = configparser.ConfigParser()
config.read('config.ini')

def create_algo_nodes(nodes,client,parallel_flag=0,count=1):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    for node in nodes:
        properties = f'{{name: $name, client: $client, parallel_flag: $parallel_flag, count: $count, last_block: 1, parent_task: $parent_task}}'
        parameters = {'name': node, 'client': client, 'parallel_flag': parallel_flag, 'count': count, 'parent_task': node}
        query = session.run(f"merge (n:node{properties}) return n", parameters).data()
    return query

def connect_algo_nodes(node1,node2,client):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    property1 = f'{{name: $name1, client: $client}}'
    property2 = f'{{name: $name2, client: $client}}'
    parameters = {'name1': node1, 'name2': node2, 'client': client}
    query = session.run(f"match (n1:node{property1}), (n2:node{property2}) merge (n1)-[:next]->(n2)", parameters).data()
    return query

def get_algo_node(node,client):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    property = f'{{name: $name, client: $client}}'
    parameters = {'name': node, 'client': client}
    query = session.run(f"match (n:node{property}) return n", parameters).data()
    return query[0]['n']

def get_next_algo_nodes(node,client):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    property = f'{{name: $name, client: $client}}'
    parameters = {'name': node, 'client': client}
    query = session.run(f"match (n:node{property})-[r:next]->(m) return m", parameters).data()
    next_nodes = []
    for node in query:
        next_nodes.append(node['m'])
    return next_nodes

def create_task_nodes(nodes,task_id,level,parent_task,last_block,block_identifier):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    for node in nodes:
        properties = f'{{name: $name, task_id: $task_id, level: $level, parent_task: $parent_task, last_block: $last_block, block_identifier: $block_identifier}}'
        parameters = {'name': node, 'task_id': task_id, 'level': str(level), 'parent_task': parent_task, 'last_block': last_block, 'block_identifier': block_identifier}
        query = session.run(f"merge(n:node{properties}) return n", parameters).data()

    return query

def connect_task_nodes(task_id,node1,node2,level1,level2):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    property1 = f'{{name: $name1, task_id: $task_id, level: $level1}}'
    property2 = f'{{name: $name2, task_id: $task_id, level: $level2}}'
    parameters = {'name1': node1, 'name2': node2, 'task_id': task_id, 'level1': str(level1), 'level2': str(level2)}
    query = session.run(f"match (n1:node{property1}), (n2:node{property2}) merge (n1)-[:new]->(n2)", parameters).data()
    return query

def get_next_task_nodes(node,task_id,level):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    property = f'{{name: $name, task_id: $task_id, level: $level}}'
    parameters = {'name': node, 'task_id': task_id, 'level': str(level)}
    query = session.run(f"match (n:node{property})-[r:new]->(m) return m", parameters).data()
    next_nodes = []
    for node in query:
        next_nodes.append(node['m'])
    return next_nodes

def get_task_node(node,task_id,level):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    property = f'{{name: $name, task_id: $task_id, level: $level}}'
    parameters = {'name': node, 'task_id': task_id, 'level': str(level)}
    query = session.run(f"match (n:node{property}) return n", parameters).data()
    return query[0]['n']

def get_no_of_parent_tasks(node,task_id,level):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    property = f'{{name: $name, task_id: $task_id, level: $level}}'
    parameters = {'name': node, 'task_id': task_id, 'level': str(level)}
    query = session.run(f"match (n:node{property})<-[r]-(m) return count(r) as count", parameters).data()
    return query[0]['count']

def get_no_of_completed_parent_tasks(node,task_id,level):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    property = f'{{name: $name, task_id: $task_id, level: $level}}'
    parameters = {'name': node, 'task_id': task_id, 'level': str(level)}
    query = session.run(f"match (n:node{property})<-[r:completed]-(m) return count(r) as count", parameters).data()
    return query[0]['count']

def add_caas_job_to_task_node(node,task_id,level,caas_job_id):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    property = f'{{name: $name, task_id: $task_id, level: $level}}'
    parameters = {'name': node, 'task_id': task_id, 'level': str(level)}
    query = session.run(f"match (n:node{property}) set n.caas_job = '{caas_job_id}' return n", parameters).data()
    return query

def change_status_of_task_node(node,task_id,level,status):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    property = f'{{name: $name, task_id: $task_id, level: $level}}'
    parameters = {'name': node, 'task_id': task_id, 'level': str(level)}
    query = session.run(f"match (n:node{property}) set n.status = '{status}' return n", parameters).data()
    return query

def check_last_block_status(task_id,node):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')
    
    property = f'{{task_id: $task_id, name: $name}}'
    parameters = {'task_id': task_id, 'name': node}
    query = session.run(f"match (n:node{property}) return count(*) as count", parameters).data()
    total = query[0]['count']
    completed = session.run(f"match (n:node{property}) where n.status = 'SUCCESS' return count(*) as count", parameters).data()[0]['count']
    if total == completed:
        return True
    return False

def change_edge_between_task_nodes(node1,node2):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    property1 = f'{{last_block: $last_block_1, level: $level_1, caas_job: $caas_job_1, name: $name_1, parent_task: $parent_task_1, task_id: $task_id_1, status: $status_1, block_identifier: $block_identifier_1}}'
    property2 = f'{{last_block: $last_block_2, level: $level_2, name: $name_2, parent_task: $parent_task_2, task_id: $task_id_2, status: $status_2, block_identifier: $block_identifier_2}}'
    parameters = {'last_block_1': node1["last_block"], 'level_1': str(node1["level"]), 'caas_job_1': node1["caas_job"], 'name_1': node1["name"], 'parent_task_1': node1["parent_task"], 'task_id_1': node1["task_id"], 'status_1': node1["status"], 'block_identifier_1': node1["block_identifier"], 'last_block_2': node2["last_block"], 'level_2': str(node2["level"]), 'name_2': node2["name"], 'parent_task_2': node2["parent_task"], 'task_id_2': node2["task_id"], 'status_2': node2["status"], 'block_identifier_2': node2["block_identifier"]} 
    query = session.run(f" match (n1:node{property1})-[old:`new`]->(n2:node{property2}) delete old", parameters).data() 
    query = session.run(f" match (n1:node{property1}), (n2:node{property2}) merge (n1)-[:`success`]->(n2)", parameters).data()
   
def mark_all_dependants_as_failed(task_id):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    property = f'{{task_id: $task_id}}'
    parameters = {'task_id': task_id}
    query = session.run(f"match(n:node{property}) where n.status<>'{SUCCESS}' and n.status<>'{FAILED}' set n.status='STOPED' return n", parameters).data()
    nodes = []
    for node in query:
        nodes.append(node['n'])
    return nodes

def get_all_running_tasks_for_id(task_id):
    driver = GraphDatabase.driver(config['graphdb']['connection_string'], auth=(config['graphdb']['username'], config['graphdb']['password']))
    session = driver.session(database='neo4j')

    query = session.run(f"match(n:node) where n.task_id = '{task_id}' and exists(n.caas_job) and n.status<>'{SUCCESS}' return n").data()
    caas_ids = []
    for node in query:
        caas_ids.append(node['n']['caas_job'])

    return caas_ids