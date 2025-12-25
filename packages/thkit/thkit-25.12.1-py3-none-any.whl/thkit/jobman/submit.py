from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from thkit.log import ColorLogger

from thkit.pkg import check_package

check_package("dpdispatcher", auto_install=False)

import asyncio
import threading
import time
from math import ceil
from pathlib import Path

from dpdispatcher import Machine, Resources, Submission, Task
from dpdispatcher.entrypoints.submission import handle_submission
from rich.progress import TaskProgressColumn, TextColumn

from thkit.jobman.helper import init_jobman_logger, log_machine_info
from thkit.markup import DynamicBarColumn, TextDecor, ThangBar, _index2color
from thkit.range import chunk_list


#####SECTION Dispatcher
def _prepare_submission(
    mdict: dict,
    work_dir: str,
    task_list: list[Task],
    forward_common_files: list[str] = [],
    backward_common_files: list[str] = [],
) -> Submission:
    """Function to simplify the preparation of the [Submission](https://docs.deepmodeling.com/projects/dpdispatcher/en/latest/api/dpdispatcher.html#dpdispatcher.Submission) object for dispatching jobs.

    Args:
        mdict (dict): a dictionary contains settings of the remote machine. The parameters described in [here](https://docs.deepmodeling.com/projects/dpdispatcher/en/latest/machine.html)
        work_dir (str): the base working directory on the local machine. All task directories are relative to this directory.
        task_list (list[Task]): a list of [Task](https://docs.deepmodeling.com/projects/dpdispatcher/en/latest/task.html) objects. Each task object contains the command to be executed on the remote machine, and the files to be copied to and from the remote machine. The dirs of each task must be relative to the `work_dir`.
        forward_common_files (list[str]): common files used for all tasks. These files are in the `work_dir`.
        backward_common_files (list[str]): common files to download from the remote machine when the jobs

    Notes:
        - When use `SSHContext`. if `remote path` not exist, the job will fail. See class `ConfigRemoteMachines`, its method will create the remote path before submitting jobs for `SSHContext`.
    """
    machine_dict = mdict["machine"]
    resources_dict = mdict["resources"]

    ### revise input path to absolute path and as_string
    abs_machine_dict = machine_dict.copy()
    abs_machine_dict["local_root"] = Path("./").resolve().as_posix()

    ### Set default values
    if "group_size" not in resources_dict:
        resources_dict["group_size"] = 1

    submission = Submission(
        machine=Machine.load_from_dict(abs_machine_dict),
        resources=Resources.load_from_dict(resources_dict),
        work_base=work_dir,
        task_list=task_list,
        forward_common_files=forward_common_files,
        backward_common_files=backward_common_files,
    )
    return submission


#####ANCHOR Synchronous submission
def submit_job_chunk(
    mdict: dict,
    work_dir: str,
    task_list: list[Task],
    forward_common_files: list[str] = [],
    backward_common_files: list[str] = [],
    machine_index: int = 0,
    logger: ColorLogger | None = None,
):
    """Function to submit a jobs to the remote machine.

    Includes:
    - Prepare the task list
    - Make the submission of jobs to remote machines
    - Wait for the jobs to finish and download the results to the local machine

    Args:
        mdict (dict): a dictionary contain settings of the remote machine. The parameters described in the [remote machine schema](https://thangckt.github.io/thkit_doc/schema_doc/config_remote_machine/). This dictionary defines the login information, resources, execution command, etc. on the remote machine.
        work_dir (str): the base working directory on the local machine. All task directories are relative to this directory.
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
    logger = logger or init_jobman_logger()

    logger.info(f"Distribute {len(task_list)} jobs to remote machine")
    num_tasks = len(task_list)
    submit_size = mdict.get("submit_size", 1)
    log_machine_info(num_tasks, mdict, machine_index, logger)

    ### Prepare progress bars
    thangbar = _define_progress_bar()
    bar1 = thangbar.add_task(
        description=(
            TextDecor(f"{_strtime_now()}").mkcolor("bright_black")
            + TextDecor(f" Machine {machine_index}").mkcolor(color)
        ),
        total=num_tasks,
        eta_text="running...",  # add custom field
        task_color=color,  # add custom field
        # complete_color=color,  # add custom field
        finished_color=color,  # add custom field
    )
    thangbar.start()

    ### Submit task_list by chunks with progress bar
    oldtime = time.time()
    num_chunks = ceil(num_tasks / submit_size)
    chunks = chunk_list(task_list, submit_size)
    for idx, task_list_current_chunk in enumerate(chunks):
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
            thangbar.hide_bar()  # hide all bars to avoid mess up
            logger.error(f"Machine {machine_index} error: \n\t{e}", color=color)
            thangbar.show_bar()  # show all bars back

        ## Update time info
        eta_text = thangbar.compute_eta(
            num_iters=num_chunks,
            iter_index=idx,
            old_time=oldtime,
            new_time=time.time(),
        )
        oldtime = time.time()

        ## Update progress bar
        thangbar.update(
            bar1,
            advance=len(task_list_current_chunk),
            description=(
                TextDecor(f"{_strtime_now()}").mkcolor("bright_black")
                + TextDecor(f" Machine {machine_index}").mkcolor(color)
            ),
            eta_text=eta_text,  # update custom field
        )
        thangbar.refresh()

    ### Finish message
    thangbar.hide_bar()
    logger.info(f"Machine {machine_index} finished all jobs !", color=color)
    thangbar.show_bar()

    thangbar.stop()
    return


#####ANCHOR Asynchronous submission
_machine_locks: dict[int, asyncio.Lock] = {}  # Dictionary to store per-machine locks
_machine_locks_guard = threading.Lock()  # protects the dict itself


def _get_machine_lock(machine_index: int) -> asyncio.Lock:
    """Get or create an asyncio.Lock for the specified machine index.

    Notes:
        - The threading.Lock ensures only one coroutine/thread can mutate _machine_locks at a time.
        - `dict.setdefault(key, default)` returns the existing value if the key exists, otherwise sets it to `default` and returns it.
    """
    with _machine_locks_guard:
        return _machine_locks.setdefault(machine_index, asyncio.Lock())


async def _run_submission_wrapper(submission, check_interval=30, machine_index=0):
    """Ensure only one instance of 'submission.run_submission' runs at a time.
    - If use one global lock for all machines, it will prevent concurrent execution of submissions on different machines. Therefore, each machine must has its own lock, so different machines can process jobs in parallel.

    Returns:
        None if successful, or the exception object if an error occurred.
    """
    lock = _get_machine_lock(machine_index)  # Get per-machine lock
    async with lock:  # Prevents concurrent execution
        try:
            await asyncio.to_thread(submission.run_submission, check_interval=check_interval)
        except Exception as e:
            await asyncio.to_thread(
                handle_submission,
                submission_hash=submission.get_hash(),
                download_finished_task=True,
            )
            return e  # return the error if occurred
    return None


sync_dict = {}  # global dict to store dynamic variables for async functions
global_lock = asyncio.Lock()


async def async_submit_job_chunk(
    mdict: dict,
    work_dir: str,
    task_list: list[Task],
    forward_common_files: list[str] = [],
    backward_common_files: list[str] = [],
    machine_index: int = 0,
    logger: ColorLogger | None = None,
):
    """Convert `submit_job_chunk()` into an async function.

    The approach in this function is only need to wait for the completion of the entire `for` loop (without worrying about the specifics of each operation inside the loop)

    Note:
        - An async function normally contain a `await ...` statement to be awaited (yield control to event loop)
        - If the 'event loop is blocked' by a asynchronous function (it will not yield control to event loop), the async function will wait for the completion of the synchronous function. So, the async function will not be executed asynchronously. Try to use `await asyncio.to_thread()` to run the synchronous function in a separate thread, so that the event loop is not blocked.
        - This version use `rich` instead of `tqdm` for better handle progess bars (see retired codes). Multiple `tqdm` bars work well if there are not errors during job submission. However, if the jobs raise errors, the `tqdm` bars will be messed up.
        - `rich`'s remaining time does not work well with multiple progress bars. So, I implemented a customized time remaining column.
    """
    global sync_dict
    color = _index2color(machine_index)
    logger = logger or init_jobman_logger()

    num_tasks = len(task_list)
    submit_size = mdict.get("submit_size", 1)
    log_machine_info(num_tasks, mdict, machine_index, logger)

    ### Prepare progress bars
    if "thangbar" not in sync_dict:
        sync_dict["thangbar"] = _define_progress_bar()
    thangbar = sync_dict["thangbar"]
    sync_dict[f"pbar_{machine_index}"] = thangbar.add_task(
        description=(
            TextDecor(f"{_strtime_now()}").mkcolor("bright_black")
            + TextDecor(f" Machine {machine_index}").mkcolor(color)
        ),
        total=num_tasks,
        ## add custom fields
        eta_text="running...",
        task_color=color,
        # complete_color=color,
        finished_color=color,
    )
    ## First show all pbars
    async with global_lock:
        sync_dict["count_machine"] = sync_dict.get("count_machine", 0) + 1
        if sync_dict["count_machine"] >= sync_dict["num_run_machines"]:
            thangbar.start()

    ### Submit task_list by chunks with progress bar
    sync_dict[f"oldtime_{machine_index}"] = time.time()
    num_chunks = ceil(num_tasks / submit_size)
    chunks = chunk_list(task_list, submit_size)
    for idx, task_list_current_chunk in enumerate(chunks):
        submission = _prepare_submission(
            mdict=mdict,
            work_dir=work_dir,
            task_list=task_list_current_chunk,
            forward_common_files=forward_common_files,
            backward_common_files=backward_common_files,
        )
        e = await _run_submission_wrapper(submission, 30, machine_index)
        ## Handle error message
        if e is not None:
            thangbar.hide_bar()  # hide all bars to avoid mess up
            logger.error(f"Machine {machine_index} error: \n\t{e}", color=color)
            thangbar.show_bar()  # show all bars back

        ## Update time info
        eta_text = thangbar.compute_eta(
            num_iters=num_chunks,
            iter_index=idx,
            old_time=sync_dict[f"oldtime_{machine_index}"],
            new_time=time.time(),
        )
        sync_dict[f"oldtime_{machine_index}"] = time.time()
        sync_dict[f"width_{machine_index}"] = len(eta_text.replace("[ETA", "").strip())
        async with global_lock:
            sync_dict["old_width"] = max(
                (sync_dict.get(f"width_{i}", 0) for i in range(sync_dict["num_run_machines"])),
            )

        ## Update progress bar
        thangbar.update(
            sync_dict[f"pbar_{machine_index}"],
            advance=len(task_list_current_chunk),
            description=(
                TextDecor(f"{_strtime_now()}").mkcolor("bright_black")
                + TextDecor(f" Machine {machine_index}").mkcolor(color)
            ),
            visible=True,
            eta_text=eta_text,  # update custom field
        )
        thangbar.align_etatext(width=sync_dict["old_width"])
        thangbar.refresh()

    ### Finish message
    thangbar.hide_bar()
    logger.info(f"Machine {machine_index} finished all jobs !", color=color)
    thangbar.show_bar()

    ### Close all pbars after all async tasks are done
    async with global_lock:
        sync_dict["count_finish"] = sync_dict.get("count_finish", 0) + 1
        if sync_dict["count_finish"] >= sync_dict["num_run_machines"]:
            thangbar.stop()
    return


def _strtime_now() -> str:
    return time.strftime("%b%d %H:%M")


def _define_progress_bar() -> ThangBar:
    progressbar = ThangBar(
        TextColumn("[progress.description]{task.description}"),
        # TextColumn("[progress.description][{task.fields[task_color]}]{task.description}"),
        DynamicBarColumn(bar_width=20),
        TaskProgressColumn(text_format="[{task.fields[task_color]}]{task.percentage:>3.0f}%"),
        TextColumn("[{task.fields[task_color]}]{task.completed}/{task.total}"),
        TextColumn("[{task.fields[task_color]}]{task.fields[eta_text]}"),
        auto_refresh=False,
    )
    return progressbar


#####!SECTION


#####SECTION Support functions used for `alff` package
def _alff_prepare_task_list(
    command_list: list[str],
    task_dirs: list[str],
    forward_files: list[str],
    backward_files: list[str],
    outlog: str,
    errlog: str,
    # delay_fail_report: bool = True,
) -> list[Task]:
    """Prepare the task list for `alff` package.

    The feature of jobs in `alff` package is that they have the same: command_list, forward_files, backward_files. So, this function prepares the list of Task object for `alff` package. For general usage, should prepare the task list manually.

    Args:
        command_list (list[str]): the list of commands to be executed on the remote machine.
        task_dirs (list[str]): the list of directories for each task. They must be relative to the `work_dir` in function `_prepare_submission`
        forward_files (list[str]): the list of files to be copied to the remote machine. These files must existed in each `task_dir`.
        backward_files (list[str]): the list of files to be copied back from the remote machine.
        outlog (str): the name of the output log file.
        errlog (str): the name of the error log file.
        # delay_fail_report (bool): whether to delay the failure report until all tasks are done. This is useful when there are many tasks, and we want to wait all tasks finished instead of "the controller interupts if one task fail".

    Returns:
        list[Task]: a list of Task objects.
    """
    command = " &&\n".join(command_list)
    # if delay_fail_report:
    #     command = f"({command}) || :"  # this treat fail jobs as finished jobs -> should not be used.

    ### Define the task_list
    task_list: list = [None] * len(task_dirs)
    for i, path in enumerate(task_dirs):
        task_list[i] = Task(
            command=command,
            task_work_path=path,
            forward_files=forward_files,
            backward_files=backward_files,
            outlog=outlog,
            errlog=errlog,
        )
    return task_list


def _divide_workload(mdict_list: list[dict]) -> list[float]:
    """Revise workload ratio among multiple machines based on their work load ratio."""
    ### parse workloads
    workloads = [mdict.get("work_load_ratio", 0) for mdict in mdict_list]
    assert sum(workloads) <= 1.0, "The sum of work_load_ratio in all machines must be <= 1.0"

    zero_count = workloads.count(0)
    if zero_count > 0:
        share_value = (1 - sum(workloads)) / zero_count
        workloads = [x if x > 0 else share_value for x in workloads]
    return workloads


def _divide_task_dirs(mdict_list: list[dict], task_dirs: list[str]) -> list[list[str]]:
    """Distribute task_dirs among multiple machines based on their work load ratio."""
    workloads = _divide_workload(mdict_list)

    ### distribute number of jobs
    total_jobs = len(task_dirs)
    numjobs = [ceil(total_jobs * x) for x in workloads]
    exceed = sum(numjobs) - total_jobs
    if exceed > 0:
        numjobs[-1] -= exceed

    ### distribute task_dirs
    distributed_task_dirs = []
    idx = 0
    for num in numjobs:
        distributed_task_dirs.append(task_dirs[idx : idx + num])
        idx += num
    return distributed_task_dirs


#####ANCHOR Submit to multiple machines
### New function to compatible with new update in alff
async def alff_submit_job_multi_remotes(  # noqa: D417
    mdict_list: list[dict],
    commandlist_list: list[list[str]],
    work_dir: str,
    task_dirs: list[str],
    forward_files: list[str],
    backward_files: list[str],
    forward_common_files: list[str] = [],
    backward_common_files: list[str] = [],
    logger: ColorLogger | None = None,
):
    """Submit jobs to multiple machines asynchronously.

    Args:
        mdict_list (list[dict]): list of multiple `mdicts`. Each `mdict` contains parameters of one remote machine, which parameters as in the [remote machine schema](https://thangckt.github.io/thkit_doc/schema_doc/config_remote_machine/).
        commandlist_list (list[list[str]]): list of command_lists, each list for each remote machine. Need to prepare outside.
    """
    global sync_dict
    logger = logger or init_jobman_logger()

    logger.info(f"Distribute {len(task_dirs)} jobs across {len(mdict_list)} remote machines")
    distributed_task_dirs = _divide_task_dirs(mdict_list, task_dirs)
    num_run_machines = sum([1 for dirs in distributed_task_dirs if len(dirs) > 0])
    sync_dict["num_run_machines"] = num_run_machines
    sync_dict["num_chunks"] = len(distributed_task_dirs)

    background_runs = []
    for i, mdict in enumerate(mdict_list):
        current_task_dirs = distributed_task_dirs[i]
        current_command_list = commandlist_list[i]

        ### Prepare task_list
        task_list = _alff_prepare_task_list(
            command_list=current_command_list,
            task_dirs=current_task_dirs,
            forward_files=forward_files,
            backward_files=backward_files,
            outlog="run_out.log",
            errlog="run_err.log",
        )

        ### Submit jobs
        if len(current_task_dirs) > 0:
            async_task = async_submit_job_chunk(
                mdict=mdict,
                work_dir=work_dir,
                task_list=task_list,
                forward_common_files=forward_common_files,
                backward_common_files=backward_common_files,
                machine_index=i,
                logger=logger,
            )
            background_runs.append(async_task)
            # logger.debug(f"Assigned coroutine to Machine {i}: {async_task}")
    await asyncio.gather(*background_runs)
    sync_dict.clear()  # clean up global dict
    return


#####!SECTION


#####ANCHOR help functions
