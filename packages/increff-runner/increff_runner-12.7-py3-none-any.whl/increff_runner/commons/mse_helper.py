from .db_helper import *
from .constants import *
from logging_increff.function import *
import copy
from .db_service import *
from .event_helper import *
from .db_helper import *
from .graphdb_helper import *
from .slack_util import slack_notify_failed
import time

def create_next_dag(algo_name, next_blocks, dag):
    extra_blocks = [block for block in next_blocks if block != algo_name]
    for block in extra_blocks:
        del dag[block]
    return dag


def create_algo_block_runner_data(
    client,
    task_id,
    algo_name,
    level,
    block_identifier,
    app,
    app_id,
    masterUri,
    script_info,
    webHookUri,
):
    return {
        "client":client,
        "task_id": task_id,
        "algo_name": algo_name,
        "level": level,
        "block_identifier": block_identifier,
        "app_name": app,
        "app_id": app_id,
        "masterUri": masterUri,
        "script_info": script_info,
        "webHookUri": webHookUri,
    }


def create_events_for_next_blocks(url, master_url, output, error_data, job):
    change_status_of_task_node(job["data"]["algo_name"], job["data"]["task_id"], job["data"]["level"], "SUCCESS")

    node = get_task_node(job["data"]["algo_name"],job["data"]["task_id"],job["data"]["level"])
    if(str(node['last_block'])=="1"):
        status = check_last_block_status(job["data"]["task_id"], job["data"]["algo_name"])
        if status:
            add_info_logs(job["id"], "All levels for the block are completed")
            send_subtask_success_callback(
                master_url, job["data"]["task_id"], node['parent_task'],job["data"]['script_info']['domain'],error_data,job["id"]
            )

    next_nodes = get_next_task_nodes(job["data"]["algo_name"], job["data"]["task_id"], job["data"]["level"])
    for next_node in next_nodes:
        change_edge_between_task_nodes(node,next_node)
        data = create_algo_block_runner_data(
            job["data"]["client"],
            job["data"]["task_id"],
            next_node['name'],
            next_node['level'],
            job["data"]["block_identifier"],
            job["data"]["app_name"],
            job["data"]["app_id"],
            job["data"]["masterUri"],
            job["data"]["script_info"],
            job["data"]["webHookUri"],
        )
        add_info_logs(job["id"], f"Success message -> {str(data)}")
        job["webhook_status"] = "200"
        update_job(job)
        response = create_caas_job(url, data)
        if not response.ok:
            slack_notify_failed(job["id"],f"Failed to hit create job url for node {next_node['name']} and level {next_node['level']}")
            add_error_logs(job["id"], f"Failed to create job url for node {next_node['name']} and level {next_node['level']} due to status_code: {response.status_code}, text: {response.text}")
            if "reason" not in job:
                job["reason"] = ""
            job["reason"] += f"Failed to create job url for node {next_node['name']} and level {next_node['level']} due to status_code: {response.status_code}, text: {response.text}"
            persist_value(JOBS_TABLE, job["id"], job)


def send_subtask_success_callback(url, task_id, algo_name,domain,error_data,job_id):
    if url == "":
        return
    body = {
        "reason":json.dumps(error_data),
        "status": "SUCCESS",
    }

    if 'is_warning' in error_data and error_data['is_warning'] == 1:
        body['status'] = "WARNING"
        data = {"taskId": task_id, "subtaskName": algo_name}
    else:
        body['reason'] = json.dumps({"reason":"SUCCESS","reason_details":"SUCCESS"})
        data = {"taskId": task_id, "subtaskName": algo_name}
    
    headers = {
        "Content-Type": "application/json",
        "authUsername":"caas-user@increff.com",
        "authPassword":"caasuser@123",
        "authdomainname": domain,
        "Conection":"keep-alive"
    }
    add_info_logs(job_id, f"Hitting Success Callback on {url} with data {data} ")
    timmings = [0,60,300]
    flag = False
    for secs in timmings:
        time.sleep(secs)
        add_info_logs(job_id,f"Retrying after {secs} seconds")
        response = requests.put(url, headers=headers,params=data,data=json.dumps(body))
        if response.status_code==200:
            flag = True
            break
        add_error_logs(job_id,f"Retry Failed after {secs} seconds with response {response.text}")
    if not flag:
        slack_notify_failed(job_id,"Failed to hit the callback URI after 3 retries")
        add_error_logs(job_id,"Failed to hit the callback URI after 3 retries")
        
