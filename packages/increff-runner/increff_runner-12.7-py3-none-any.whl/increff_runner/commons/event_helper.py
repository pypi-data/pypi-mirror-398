import json
import requests
from logging_increff.function import *

def create_caas_job(url, data):
    data["subject"] = "mse-runner"
    response = requests.post(url, data=json.dumps(data))
    return response

def stop_caas_job(url,job_id):
    data = {
        'subject':'stop-mse-runner',
        'job_id':job_id,
        'app_name':'mse'
    }
    add_info_logs(job_id, f"Stopping the job with job_id {job_id}")
    response = requests.post(url, data=json.dumps(data))