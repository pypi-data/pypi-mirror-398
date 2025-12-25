from logging_increff.function import *
from .mse_helper import create_events_for_next_blocks, mark_dependant_as_failed
from .constants import *
import requests
import json
from .db_service import update_job
from .db_helper import get_interim_tasks
from .graphdb_helper import *
import time
from .slack_util import slack_notify_failed

def send_success_callback(url, output, error_data, job):
    if error_data != {}:
        send_failure_callback(url, "Script Failed", output, error_data, job)
        return
    output["caas_job_id"] = job["id"]
    add_info_logs(job["id"], "Hitting Success Callback")
    body = {
        "StatusCode": "200",
        "Output": {"output_data": output, "error_data": error_data},
    }
    add_info_logs(job["id"], f"Success message -> {str(body)}")
    job["callback_status"] = "200"
    update_job(job)
    response = requests.post(url, json=body)
    add_info_logs(job["id"], f"Ignoring success callback response for [{response.status_code}] -> {response.text}")


def send_success_webhook(url, master_url, output, error_data, job):
    if error_data != {}:
        if('is_warning' not in error_data or ('is_warning' in error_data and error_data['is_warning'] == 0)):
            send_failure_webhook(master_url, job["data"]["task_id"], error_data, job)
            return
    
    output["caas_job_id"] = job["id"]
    add_info_logs(job["id"], "Hitting Success WebHook Callback")
    create_events_for_next_blocks(url, master_url, output, error_data, job)


def send_failure_callback(url, error, output_data, error_data, job):
    add_info_logs(job["id"], "Hitting Failure Callback")
    output_data["caas_job_id"] = job["id"]
    body = {
        "Output": {"output_data": output_data, "error_data": error_data},
        "Error": {"ErrorCode": "400", "Message": str(error)},
        "StatusCode": "400",
    }
    add_info_logs(job["id"], f" failure message -> {str(body)}")
    job["callback_status"] = 400
    update_job(job)
    response = requests.post(url, json=body)
    add_info_logs(job["id"], f"Ignoring failure callback response for [{response.status_code}] -> {response.text}")


def send_failure_webhook(url, task_id, error, job):
    node = get_task_node(job["data"]["algo_name"],task_id,job["data"]["level"])
    add_error_logs(job["id"], "Hitting Failure WebHook Callback with error -> "+str(error)) 
    data = {"taskId": task_id, "subtaskName":  node['parent_task']}
    body = {"reason":json.dumps(error),"status": "FAILED"}
    if(error=={}):
        body['reason']=json.dumps({"reason":"Script Failed","reason_details":"Script Failed"})
    headers = {
        "Content-Type": "application/json",
        "authUsername":"caas-user@increff.com",
        "authPassword":"caasuser@123",
        "authdomainname": job["data"]['script_info']['domain'],
        "Conection":"keep-alive"
    }
    add_info_logs(job["id"], f" failure message -> {str(data)}")
    job["webhook_status"] = 400
    update_job(job)

    change_status_of_task_node(job["data"]["algo_name"], job["data"]["task_id"], job["data"]["level"], FAILED)
    mark_dependant_as_failed(task_id,job["data"]["webHookUri"])

    timings = [0,60,300]
    flag = False
    for secs in timings:
        time.sleep(secs)
        add_info_logs(job['id'],f"Retrying on {url} after {secs} seconds")
        response = requests.put(url, params=data,headers=headers,data=json.dumps(body))
        if(response.status_code==200):
            flag = True
            break
        add_info_logs(job["id"], f"Failure Webhook Response -> {response.text}")
    if not flag:
        add_error_logs(task_id,"Failed to hit the callback URI after 3 retries")
        slack_notify_failed(job["id"],"Failed to hit the callback URI after 3 retries")
