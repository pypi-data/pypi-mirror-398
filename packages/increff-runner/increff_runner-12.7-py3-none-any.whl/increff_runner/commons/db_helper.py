import pymongo
import configparser
from .event_helper import *
from logging_increff.function import *
from .graphdb_helper import *
config = configparser.ConfigParser()
config.read("config.ini")


def change_id_to_mongo_id(data):
    data["_id"] = data["id"]
    del data["id"]
    return data


def change_mongo_id_to_id(data):
    data["id"] = data["_id"]
    del data["_id"]
    return data


def persist_value(table, key, value):
    connection_string = config["db"][
        "connection_string"
    ]  # Primary or secondary access key
    client = pymongo.MongoClient(connection_string)
    client_table = client["caas"][table]
    value = change_id_to_mongo_id(value)
    client_table.replace_one({"_id": key}, value, upsert=True)
    value = change_mongo_id_to_id(value)
    client.close()


def get_table_values(table, key):
    connection_string = config["db"][
        "connection_string"
    ]  # Primary or secondary access key
    client = pymongo.MongoClient(connection_string)
    client_table = client["caas"][table]
    data = client_table.find_one({"_id": key})
    data = change_mongo_id_to_id(data)
    client.close()
    return data


def delete_table_values(table, key):
    connection_string = config["db"][
        "connection_string"
    ]  # Primary or secondary access key
    client = pymongo.MongoClient(connection_string)
    client_table = client["caas"][table]
    client_table.delete_one({"_id": key})
    client.close()


def get_all_values_from_interim_jobs(table):
    connection_string = config["db"][
        "connection_string"
    ]  # Primary or secondary access key
    client = pymongo.MongoClient(connection_string)
    client_table = client["caas"][table]
    data = client_table.find({})
    all_ids = []
    for job in data:
        all_ids.append(job["_id"])
    client.close()
    return all_ids


def get_levels_for_block(table, task_id, algo_name):
    connection_string = config["db"][
        "connection_string"
    ]  # Primary or secondary access key
    client = pymongo.MongoClient(connection_string)
    client_table = client["caas"][table]
    data = client_table.find(
        {"$and": [{"task_id": task_id}, {"algo_block": algo_name}]}
    )
    all_levels = []
    for i in data:
        all_levels.append(i["level"])
    client.close()
    return all_levels


def get_interim_tasks(table, task_id, algo_name, level):
    connection_string = config["db"][
        "connection_string"
    ]  # Primary or secondary access key
    client = pymongo.MongoClient(connection_string)
    client_table = client["caas"][table]
    data = client_table.find_one(
        {"$and": [{"task_id": task_id}, {"algo_block": algo_name}, {"level": level}]}
    )
    data = change_mongo_id_to_id(data)
    client.close()
    return data


def check_status_of_algo_block(table, task_id, algo_name):
    connection_string = config["db"][
        "connection_string"
    ]  # Primary or secondary access key
    client = pymongo.MongoClient(connection_string)
    client_table = client["caas"][table]
    data = client_table.find(
        {"$and": [{"task_id": task_id}, {"algo_block": algo_name}]}
    )
    for i in data:
        if i["last_block"] == 0:
            return False
        if "status" in i:
            if i["status"] == "FAILED":
                return False
        else:
            return False
    client.close()
    return True


def mark_dependant_as_failed(task_id,url):
    nodes = mark_all_dependants_as_failed(task_id)
    for node in nodes:
        if "caas_job" in  node and node['status']==NEW:
            stop_caas_job(url,node["caas_job"])
