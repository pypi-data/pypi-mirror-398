from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # only for type hints, not actual import at runtime
    import asyncio
    import datetime
    import re
    import time
    from math import ceil

    from dpdispatcher import Task
    from dpdispatcher.entrypoints.submission import handle_submission
    from tqdm import tqdm

    from thkit.jobman.helper import (
        _info_current_dispatch,
        init_jobman_logger,
        remote_info,
    )
    from thkit.jobman.submit import _prepare_submission, _run_submission_wrapper
    from thkit.markup import _index2color, text_color
    from thkit.range import chunk_list

#####SECTION Retired codes for reference only


#####ANCHOR Synchronous submission
def submit_job_chunk(
    mdict: dict,
    work_dir: str,
    task_list: list[Task],
    forward_common_files: list[str] = [],
    backward_common_files: list[str] = [],
    machine_index: int = 0,
    logger: object = None,
):
    """Function to submit a jobs to the remote machine. The function will:

    - Prepare the task list
    - Make the submission of jobs to remote machines
    - Wait for the jobs to finish and download the results to the local machine

    Args:
        mdict (dict): a dictionary contain settings of the remote machine. The parameters described in the [remote machine schema](https://thangckt.github.io/thkit_doc/schema_doc/config_remote_machine/). This dictionary defines the login information, resources, execution command, etc. on the remote machine.
        task_list (list[Task]): a list of [Task](https://docs.deepmodeling.com/projects/dpdispatcher/en/latest/task.html) objects. Each task object contains the command to be executed on the remote machine, and the files to be copied to and from the remote machine. The dirs of each task must be relative to the `work_dir`.
        forward_common_files (list[str]): common files used for all tasks. These files are i n the `work_dir`.
        backward_common_files (list[str]): common files to download from the remote machine when the jobs are finished.
        machine_index (int): index of the machine in the list of machines.
        logger (object): the logger object to be used for logging.

    Note:
        - Split the `task_list` into chunks to control the number of jobs submitted at once.
        - Should not use the `Local` contexts, it will interference the current shell environment which leads to the unexpected behavior on local machine. Instead, use another account to connect local machine with `SSH` context.
    """
    color = _index2color(machine_index)
    logger = logger if logger is not None else init_jobman_logger()

    num_tasks = len(task_list)
    machine_dict = mdict["machine"]
    text = text_color(
        f"Assigned {num_tasks} jobs to Machine {machine_index} \n{remote_info(machine_dict)}",
        color=color,
    )
    logger.info(text)

    ### Submit task_list by chunks
    submit_size = mdict.get("submit_size", 1)
    chunks = chunk_list(task_list, submit_size)
    old_time = None
    for chunk_index, task_list_current_chunk in enumerate(chunks):
        num_tasks_current_chunk = len(task_list_current_chunk)
        new_time = time.time()
        text = _info_current_dispatch(
            num_tasks,
            num_tasks_current_chunk,
            submit_size,
            chunk_index,
            old_time,
            new_time,
        )
        logger.info(text)
        submission = _prepare_submission(
            mdict=mdict,
            work_dir=work_dir,
            task_list=task_list_current_chunk,
            forward_common_files=forward_common_files,
            backward_common_files=backward_common_files,
        )
        try:
            submission.run_submission()
        except Exception as e:
            handle_submission(submission_hash=submission.get_hash(), download_finished_task=True)
            err_text = f"Machine {machine_index} has error job: \n\t{e}"
            logger.error(text_color(err_text, color=color))
        old_time = new_time
    return


#####ANCHOR Asynchronous submission
runvar = {}  # global dict to store dynamic variables for async functions
global_lock = asyncio.Lock()


async def async_submit_job_chunk(
    mdict: dict,
    work_dir: str,
    task_list: list[Task],
    forward_common_files: list[str] = [],
    backward_common_files: list[str] = [],
    machine_index: int = 0,
    logger: object = None,
):
    """Convert `submit_job_chunk()` into an async function but only need to wait for the completion of the entire `for` loop (without worrying about the specifics of each operation inside the loop)

    Note:
        - An async function normally contain a `await ...` statement to be awaited (yield control to event loop)
        - If the 'event loop is blocked' by a asynchronous function (it will not yield control to event loop), the async function will wait for the completion of the synchronous function. So, the async function will not be executed asynchronously. Try to use `await asyncio.to_thread()` to run the synchronous function in a separate thread, so that the event loop is not blocked.
    """
    color = _index2color(machine_index)
    logger = logger if logger is not None else init_jobman_logger()

    num_tasks = len(task_list)
    machine_dict = mdict["machine"]
    text = text_color(
        f"Assigned {num_tasks} jobs to Machine {machine_index} \n{remote_info(machine_dict)}",
        color=color,
    )
    logger.info(text)

    ### Submit task_list by chunks
    submit_size = mdict.get("submit_size", 1)
    chunks = chunk_list(task_list, submit_size)
    timer = {f"oldtime_{machine_index}": None}  # dynamic var_name
    for chunk_index, task_list_current_chunk in enumerate(chunks):
        num_tasks_current_chunk = len(task_list_current_chunk)
        timer[f"newtime_{machine_index}"] = time.time()
        text = _info_current_dispatch(
            num_tasks,
            num_tasks_current_chunk,
            submit_size,
            chunk_index,
            timer[f"oldtime_{machine_index}"],
            timer[f"newtime_{machine_index}"],
            machine_index,
        )
        logger.info(text)
        submission = _prepare_submission(
            mdict=mdict,
            work_dir=work_dir,
            task_list=task_list_current_chunk,
            forward_common_files=forward_common_files,
            backward_common_files=backward_common_files,
        )
        # await asyncio.to_thread(submission.run_submission, check_interval=30)  # this is old, may cause (10054) error
        await _run_submission_wrapper(submission, logger, 30, machine_index)
        timer[f"oldtime_{machine_index}"] = timer[f"newtime_{machine_index}"]
    logger.info(text_color(f"Machine {machine_index} finished all jobs.", color=color))
    return


async def async_submit_job_chunk_tqdm(
    mdict: dict,
    work_dir: str,
    task_list: list[Task],
    forward_common_files: list[str] = [],
    backward_common_files: list[str] = [],
    machine_index: int = 0,
    logger: object = None,
):
    """Revised version of `async_submit_job_chunk()` with `tqdm` progress bar."""
    global runvar
    color = _index2color(machine_index)
    logger = logger if logger is not None else init_jobman_logger()

    num_tasks = len(task_list)
    machine_dict = mdict["machine"]
    submit_size = mdict.get("submit_size", 1)

    text = text_color(
        f"Assigned {num_tasks} jobs (submit size {submit_size}) to Machine {machine_index} \n{remote_info(machine_dict)}",
        color=color,
    )
    logger.info(text)

    ### Prepare progress bars
    if f"pbar_{machine_index}" not in runvar:
        runvar[f"pbar_{machine_index}"] = tqdm(
            total=num_tasks,
            colour=color,
            desc=text_color(f"{time.strftime('%b%d %H:%M')} Machine {machine_index}", color=color),
            bar_format="{desc} {bar} {percentage:.0f}% {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            ncols=75,
            delay=1,
        )
    ## First fresh all pbars
    async with global_lock:
        runvar["count_machine"] = runvar.get("count_machine", 0) + 1
        if runvar["count_machine"] == runvar["num_machine"]:
            pbars = [v for k, v in runvar.items() if re.match(r"^pbar_\d+$", k)]
            for pbar in pbars:
                pbar.refresh()

    ### Submit task_list by chunks with tqdm progress bar
    pbar = runvar[f"pbar_{machine_index}"]
    chunks = chunk_list(task_list, submit_size)
    for task_list_current_chunk in chunks:
        submission = _prepare_submission(
            mdict=mdict,
            work_dir=work_dir,
            task_list=task_list_current_chunk,
            forward_common_files=forward_common_files,
            backward_common_files=backward_common_files,
        )
        await _run_submission_wrapper(submission, logger, 30, machine_index)
        ## Update progress bar
        desc_str = text_color(f"{time.strftime('%b%d %H:%M')} Machine {machine_index}", color=color)
        pbar.set_description(desc_str)  # update time in desc
        pbar.update(len(task_list_current_chunk))

    ### Close all pbars after all async tasks are done
    async with global_lock:
        runvar["count_finish"] = runvar.get("count_finish", 0) + 1
        if runvar["count_finish"] == runvar["num_machine"]:
            pbars = [v for k, v in runvar.items() if re.match(r"^pbar_\d+$", k)]
            for pbar in pbars:
                pbar.close()
    return


#####ANCHOR Helper function
def _info_current_dispatch(
    num_tasks: int,
    num_tasks_current_chunk: int,
    submit_size,
    chunk_index,  # start from 0
    old_time=None,
    new_time=None,
    machine_index=0,
) -> str:
    """Return the information of the current chunk of tasks."""
    num_chunks = ceil(num_tasks / submit_size)
    remaining_tasks = num_tasks - chunk_index * submit_size
    text = f"Machine {machine_index} is handling {num_tasks_current_chunk}/{remaining_tasks} jobs [chunk {chunk_index + 1}/{num_chunks}]."
    ### estimate time remaining
    if old_time is not None and new_time is not None:
        duration = new_time - old_time
        time_remain = duration * (num_chunks - chunk_index)
        delta_str = str(datetime.timedelta(seconds=time_remain)).split(".", 2)[0]
        text += f" ETC {delta_str}"
    text = text_color(text, color=_index2color(machine_index))  # make color
    return text


def remote_info(machine_dict) -> str:
    """Return the remote machine information.
    Args:
        mdict (dict): the machine dictionary
    """
    remote_path = machine_dict["remote_root"]
    hostname = machine_dict["remote_profile"]["hostname"]
    info_text = f"{' ' * 12}Remote host: {hostname}\n"
    info_text += f"{' ' * 12}Remote path: {remote_path}"
    return info_text


#####!SECTION
