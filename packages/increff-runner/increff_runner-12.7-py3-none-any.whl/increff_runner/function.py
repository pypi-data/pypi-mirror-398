import os
import shutil
import subprocess
import json
import configparser
import platform
from kubernetes import client
from kubernetes import config as kconfig

kubernetes_config_file_path = 'config'

from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
import azure.functions as func

from .commons.db_helper import get_table_values
from .commons.algo_block_downloader import *
from .commons.db_service import *
from .commons.callback_helper import *
from .commons.constants import *

from logging_increff.function import *

# TODO @jaynit: The client needs to initialize the params. #cr1_unni
python_config = configparser.ConfigParser()
python_config.read("config.ini")

scheduler = BackgroundScheduler()
scheduler.configure(timezone=utc)
scheduler.start()


def create_folder(name):
    if not os.path.exists(str(name)):
        os.makedirs(str(name))


def delete_folder(name, job_id):
    shutil.rmtree(str(name), ignore_errors=True)
    add_info_logs(job_id, f"Folder: {name} deleted successfully")


def read_json_file(file_path, job_id):
    add_info_logs(job_id, f"Reading JSON File: {file_path}")
    if os.path.exists(file_path):
        if os.path.getsize(file_path) == 0:
            # TODO @jaynit: Shouldn't this be a failure? #cr1_unni
            add_info_logs(job_id, f"File: {file_path} read successfully")
            add_info_logs(job_id,f"The data in file is None")
            return {}

        with open(file_path, "r") as json_file:
            data = json.load(json_file)
        add_info_logs(job_id, f"File: {file_path} read successfully")
        add_info_logs(job_id,f"The data in file is {data}")
        return data
    else:
        # TODO @jaynit: Shouldn't this be a failure? #cr1_unni
        add_info_logs(job_id, f"File: {file_path} read successfully")
        add_info_logs(job_id,f"The data in file is None")
        return {}


# TODO @jaynit not clear what is the unit of timeout value? seconds, ms, minutes?
# Make the variable name timeout_in_secs or similar #cr1_unni
def run_with_timeout(cmd, timeout, cwd=None):
    timeout = int(timeout)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    try:
        outs, errs = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        outs, errs = process.communicate()

        # TODO @jaynit: Remove commented out parts if not required #cr1_unni
        # Handle the timeout scenario here
        # handle_timeout(job, output_path)
        return subprocess.CompletedProcess(
            args=cmd, returncode=400, stdout=outs, stderr="Script execution timed out"
        )

    return subprocess.CompletedProcess(
        args=cmd, returncode=process.returncode, stdout=outs, stderr=errs
    )


# TODO @jaynit This function is too long, try breaking into smaller functions and invoke them. #cr1_unni
def trigger_script(job, algo_block, run_cmd, output_path):
    add_info_logs(job["id"], "Starting the Algo Run")
    run_cmd = run_cmd.split(" ")
    if "timeout" not in algo_block or algo_block["timeout"] == "-1":
        script_status = subprocess.run(
            run_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=output_path
        )
    else:
        script_status = run_with_timeout(run_cmd, algo_block["timeout"], cwd=output_path)
    if script_status.returncode == 0:
        add_info_logs(job["id"], f"Script run successfull for the job {job['id']}")
        change_job_to_success_state(job)

        # Hitting the callback URL if present in the job
        if "callBackUri" in job["data"] and job["data"]["callBackUri"] != "":
            send_success_callback(
                job["data"]["callBackUri"],
                read_json_file(output_path + "/" + SCRIPT_OUTPUT_DATA, job["id"]),
                read_json_file(output_path + "/" + SCRIPT_ERROR_DATA, job["id"]),
                job,
            )

        # Mark completion of current algo block, and start next jobs
        if "webHookUri" in job["data"] and job["data"]["webHookUri"] != "":
            send_success_webhook(
                job["data"]["webHookUri"],
                job["data"]["masterUri"],
                read_json_file(output_path + "/" + SCRIPT_OUTPUT_DATA, job["id"]),
                read_json_file(output_path + "/" + SCRIPT_ERROR_DATA, job["id"]),
                job,
            )

    else:
        add_info_logs(job["id"], f"Script run failed for the job {job['id']}")
        add_error_logs(job["id"],f"Script failed with error {script_status.stderr}")
        error_message = script_status.stderr.decode('utf-8') if isinstance(script_status.stderr, bytes) else str(script_status.stderr)        # check if error is present in error list of algo block
        if 'error_list_to_retry' in algo_block and algo_block['error_list_to_retry']:
            for error in algo_block['error_list_to_retry']:
                if error in error_message:
                    # delete the pod so that it can be retried
                    pod_name = platform.node()
                    kconfig.load_kube_config(kubernetes_config_file_path)
                    try:
                        # 60 seconds for graceful shutdown
                        client.CoreV1Api().delete_namespaced_pod(pod_name, "default",grace_period_seconds=60  )
                        add_info_logs(job["id"], f"Pod {pod_name} deleted successfully")
                        job['reason'] = f"Pod deletion successful due to {error}"
                        persist_value(JOBS_TABLE, job["id"], job)
                        return
                    except Exception as e:
                        add_error_logs(job["id"], f"Failed to delete pod {pod_name}: {str(e)}")
                        job['reason'] = f"Pod deletion failed for {error} due to {str(e)}"
                        persist_value(JOBS_TABLE, job["id"], job)
        change_job_to_failure_state(job, script_status.stderr)
        if "callBackUri" in job["data"] and job["data"]["callBackUri"] != "":
            send_failure_callback(
                job["data"]["callBackUri"],
                script_status.stderr,
                read_json_file(output_path + "/" + SCRIPT_OUTPUT_DATA, job["id"]),
                read_json_file(output_path + "/" + SCRIPT_ERROR_DATA, job["id"]),
                job,
            )

        if "masterUri" in job["data"] and job["data"]["masterUri"] != "":
            send_failure_webhook(
                job["data"]["masterUri"],
                job["data"]["task_id"],
                read_json_file(output_path + "/" + SCRIPT_ERROR_DATA, job["id"]),
                job,
            )
    delete_folder(output_path, job["id"])


def parametrize_configs(file_path, params):
    with open(file_path, "r") as local_file:
        file_content = local_file.read()
        local_file.close()

    for param in params:
        file_content.replace("${" + param + "}", params[param])

    with open(file_path, "w") as local_file:
        local_file.write(file_content)
        local_file.close

# TODO @jaynit This function is too long, try breaking into smaller functions and invoke them. #cr1_unni
def add_script(job, algo_block, output_path, job_id, background_flag):
    global scheduler
    change_job_to_processing_state(job)
    if algo_block["repo_type"] == "github":
        add_info_logs(job_id, "Downloading the files from github")
        status = download_folder_from_github(
            algo_block["repo_creds"]["username"],
            algo_block["repo_creds"]["repository"],
            algo_block["repo_creds"]["branch"],
            algo_block["repo_creds"]["folder_path"],
            output_path,
            algo_block["repo_creds"]["access_token"],
            job_id,
        )
        output_path = os.path.join(output_path, algo_block["repo_creds"]["folder_path"])
    elif algo_block["repo_type"] == "data_lake":
        add_info_logs(job_id, "Downloading the files from DataLake")
        status = download_folder_from_datalake(
            algo_block["repo_creds"]["account_name"],
            algo_block["repo_creds"]["file_system_name"],
            algo_block["repo_creds"]["storage_account_key"],
            algo_block["repo_creds"]["folder_path"],
            output_path,
            job_id,
        )
        output_path = os.path.join(output_path, algo_block["repo_creds"]["folder_path"])
    elif algo_block["repo_type"] == "blob_storage":
        add_info_logs(job_id, "Downloading the files from BlobStorage")
        status = download_folder_from_blob_storage(
            algo_block["repo_creds"]["account_name"],
            algo_block["repo_creds"]["file_system_name"],
            algo_block["repo_creds"]["storage_account_key"],
            output_path,
            job_id,
        )
    else:
        status = FAILED

    command = ""
    if "run_cmd" not in job["data"]["script_info"]:
        command = algo_block["run_cmd"]
    else:
        command = job['data']['script_info']["run_cmd"]
        
    run_command = (
        str(command)
        .replace("${" + "root_dir" + "}", output_path)
        .replace("${" + "job_id" + "}", job_id)
    )
    add_info_logs(job_id, f"run command for the script is {run_command}")

    if status != SUCCESS:
        add_info_logs(job_id, "Failed to download the files from the repo")
        change_job_to_failure_state(job, str(status))
        if "callBackUri" in job["data"] and job["data"]["callBackUri"] != "":
            send_failure_callback(
                job["data"]["callBackUri"],
                status,
                read_json_file(output_path + "/" + SCRIPT_OUTPUT_DATA, job["id"]),
                read_json_file(output_path + "/" + SCRIPT_ERROR_DATA, job["id"]),
                job,
            )

        if "masterUri" in job["data"] and job["data"]["masterUri"] != "":
            send_failure_webhook(
                job["data"]["masterUri"],
                job["data"]["task_id"],
                read_json_file(output_path + "/" + SCRIPT_ERROR_DATA, job["id"]),
                job,
            )

        delete_folder(output_path, job_id)
        return

    if "config_path" in job["data"]["script_info"]:
        config_path = job["data"]["script_info"]["config_path"]
        if config_path not in [None, ""]:
            add_info_logs(job_id, f"Substituting Config File {config_path}")
            config_path = config_path.replace("${" + "root_dir" + "}", output_path)
            parametrize_configs(
                config_path, job["data"]["script_info"]["config_params"]
            )

    if "run_cmd_params" in job["data"]["script_info"]:
        with open(output_path + "/" + SCRIPT_INPUT_DATA, "w") as json_file:
            add_info_logs(job_id, f"created {output_path}/{SCRIPT_INPUT_DATA} file")
            json_file.write(json.dumps(job["data"]["script_info"]["run_cmd_params"]))

    if background_flag:
        scheduler.add_job(
            trigger_script, args=[job, algo_block, run_command, output_path]
        )
    else:
        trigger_script(job, algo_block, run_command, output_path)


def increff_runner(job_id, background_flag=False):
    setup_logger(python_config["env"]["env"], job_id)
    add_info_logs(job_id, f"received a task to run")

    folder_name = "/tmp/mount/caas_" + job_id

    create_folder(folder_name)
    job = get_table_values(JOBS_TABLE, job_id)

    #check if node name or start time is already present in the job
    if "node_name" in job or job['start_time']:
        status = "Node is already assigned to this job before"
        # delete the pod so that it can be retried
        pod_name = platform.node()
        kconfig.load_kube_config(kubernetes_config_file_path)
        try:
            # 60 seconds for graceful shutdown
            client.CoreV1Api().delete_namespaced_pod(pod_name, "default",grace_period_seconds=60)
            add_info_logs(job["id"], f"Pod {pod_name} deleted successfully")
            job['reason'] = f"Pod deletion successful due to {status}"
            persist_value(JOBS_TABLE, job["id"], job)
        except Exception as e:
            add_error_logs(job["id"], f"Failed to delete pod {pod_name}: {str(e)}")
            job['reason'] = f"Pod deletion failed for {status} due to {str(e)}"
            persist_value(JOBS_TABLE, job["id"], job)

        return func.HttpResponse(json.dumps({"msg": status}))
    
    algo_block = get_table_values(
        ALGO_BLOCK_TABLE,
        str(job["data"]["app_id"]) + "." + job["data"]["block_identifier"],
    )

    try:
        pod_name = platform.node()
        kconfig.load_kube_config(kubernetes_config_file_path)
        node_name = client.CoreV1Api().read_namespaced_pod(pod_name, "default").spec.node_name
        job['node_name'] = node_name
        persist_value(JOBS_TABLE, job_id, job)
    except Exception as e:
        add_error_logs(job_id,f"Failed in writing VM name with error {e}")
        
    add_script(job, algo_block, folder_name, job_id, background_flag)

    return func.HttpResponse(json.dumps({"msg": "Run Trigger Successful!"}))
