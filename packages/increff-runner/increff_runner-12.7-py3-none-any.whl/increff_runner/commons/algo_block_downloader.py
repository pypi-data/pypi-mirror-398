import os
from github import Github
from azure.storage.filedatalake import DataLakeServiceClient
from azure.storage.blob import BlobServiceClient
from .constants import *
from logging_increff.function import *


def download_folder_from_github(
    username, repository, branch, folder_path, output_path, token, job_id
):
    try:
        g = Github(token)
        repo = g.get_repo(f"{username}/{repository}")
        contents = repo.get_contents(folder_path, ref=branch)
        output_folder = os.path.join(output_path + "/", os.path.basename(folder_path))
        os.makedirs(output_folder, exist_ok=True)

        download_contents(contents, output_folder, repo, branch, job_id)
        return SUCCESS
    except Exception as e:
        return e


def download_contents(contents, current_path, repo, branch, job_id):
    for content in contents:
        if content.type == "dir":
            new_path = os.path.join(current_path, content.name)
            os.makedirs(new_path, exist_ok=True)

            sub_contents = repo.get_contents(content.path, ref=branch)
            download_contents(sub_contents, new_path, repo, branch)
        else:
            file_content = repo.get_contents(content.path, ref=branch)
            with open(os.path.join(current_path, content.name), "wb") as f:
                add_info_logs(
                    job_id,
                    f"Downloaded {str(os.path.join(current_path, content.name))} successfully",
                )
                f.write(file_content.decoded_content)


def download_folder_from_datalake(
    account_name,
    file_system_name,
    storage_account_key,
    folder_path,
    local_output_path,
    job_id,
):
    try:
        service_client = DataLakeServiceClient(
            account_url=f"https://{account_name}.dfs.core.windows.net",
            credential=storage_account_key,
        )

        file_system_client = service_client.get_file_system_client(file_system_name)
        paths = file_system_client.get_paths(folder_path)
        for path in paths:
            pathss = local_output_path + "/"
            folders = path.name.split("/")[:-1]
            for folder in folders:
                pathss += folder
                if not os.path.exists(pathss):
                    os.makedirs(pathss)
                pathss += "/"
            if "." in path.name:
                file_client = file_system_client.get_file_client(path.name)
                download = file_client.download_file()
                downloaded_bytes = download.readall()
                with open(local_output_path + "/" + path.name, "wb") as local_file:
                    add_info_logs(
                        job_id,
                        f"Downloaded {local_output_path}/{path.name} successfully",
                    )
                    local_file.write(downloaded_bytes)
        return SUCCESS
    except Exception as e:
        return e


def download_folder_from_blob_storage(
    account_name, container_name, storage_account_key, local_output_path, job_id
):
    try:
        blob_service_client = BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=storage_account_key,
        )
        container_client = blob_service_client.get_container_client(container_name)

        # List all blobs in the container
        blob_list = container_client.walk_blobs()

        # Download each blob and maintain folder structure
        for blob in blob_list:
            blob_path = blob.name
            local_path = os.path.join(local_output_path, blob_path)

            # Create local directories if they don't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Download blob to a local file
            with open(local_path, "wb") as local_file:
                blob_data = container_client.download_blob(blob.name)
                local_file.write(blob_data.readall())
            add_info_logs(
                job_id, f"Blob {blob_path} downloaded to {local_path} successfully."
            )
        return SUCCESS

    except Exception as e:
        return str(e)
