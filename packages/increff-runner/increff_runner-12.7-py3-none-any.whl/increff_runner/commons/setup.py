import logging
import os


def create_folder(path):
    if not os.path.exists(str(path)):
        os.makedirs(str(path))


def setup_logger(env, job_id):
    create_folder(f"/tmp/logs")
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s.%(msecs)03d %(levelname)s %(pathname)s:%(lineno)s [env="
        + env
        + "] %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
        force=True,
        handlers=[
            logging.FileHandler(f"/tmp/logs/{job_id}.log"),
            logging.StreamHandler(),
        ],
    )
    logging.getLogger("azure").setLevel(logging.WARNING)


def add_info_logs(job_id, msg):
    logging.info(f"[job_id={job_id}] [{msg}]")
