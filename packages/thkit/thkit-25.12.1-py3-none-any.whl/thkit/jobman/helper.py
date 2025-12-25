from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from thkit.log import ColorLogger

import logging
import time
import warnings
from pathlib import Path

from thkit import THKIT_ROOT
from thkit.config import Config
from thkit.log import create_logger, write_to_logfile
from thkit.markup import TextDecor, _index2color


#####ANCHOR Helper functions for dispatcher package
def change_logfile_dispatcher(newlogfile: str):
    """Change the logfile of dpdispatcher."""
    from dpdispatcher.dlog import dlog

    try:
        for hl in dlog.handlers[:]:  # Remove all old handlers
            hl.close()
            dlog.removeHandler(hl)

        fh = logging.FileHandler(newlogfile)
        # fmt = logging.Formatter(
        #     "%(asctime)s | %(name)s-%(levelname)s: %(message)s", "%Y%b%d %H:%M:%S"
        # )
        fmt = logging.Formatter(
            "%(asctime)s | dispatch-%(levelname)s: %(message)s", "%Y%b%d %H:%M:%S"
        )
        fh.setFormatter(fmt)
        dlog.addHandler(fh)
        ### Remove the old log file if it exists
        if Path("./dpdispatcher.log").is_file():
            Path("./dpdispatcher.log").unlink()
    except Exception as e:
        warnings.warn(f"Error during change logfile_path {e}. Use the original path.")
    return


def init_jobman_logger(logfile: str | None = None) -> ColorLogger:
    """Initialize the default logger under `log/` if not provided."""
    if logfile is None:
        logfile = f"log/{time.strftime('%y%m%d_%H%M%S')}_jobman.log"  # "%y%b%d" "%Y%m%d"
    logger = create_logger("jobman", level="INFO", logfile=logfile)
    change_logfile_dispatcher(logfile)
    return logger


#####ANCHOR helper functions
def log_machine_info(num_jobs: int, mdict: dict, machine_index: int, logger: logging.Logger):
    """Log remote machine information."""
    color = _index2color(machine_index)
    remote_host = mdict["machine"]["remote_profile"]["hostname"]
    remote_path = mdict["machine"]["remote_root"]
    submit_size = mdict.get("submit_size", 1)
    ### Header
    margin = 2 * " "
    h = ["Index", "Jobs", "Slot", "Hostname", "Remote_path"]
    hh = ["-" * len(x) for x in h]
    w = [5, 6, 4, 14, None]
    header1 = f"{h[0]:{w[0]}} {h[1]:^{w[1]}} {h[2]:^{w[2]}} {h[3]:{w[3]}} {h[4]}"
    header2 = f"{hh[0]:{w[0]}} {hh[1]:^{w[1]}} {hh[2]:^{w[2]}} {hh[3]:{w[3]}} {hh[4]}"
    header = f"{margin}{header1}\n{margin}{header2}"
    ### Text
    text = f"{margin}{machine_index:^{w[0]}} {num_jobs:^{w[1]}} {submit_size:^{w[2]}} {remote_host:{w[3]}} {remote_path}"
    if machine_index == 0:
        print(f"{header}\n{TextDecor(text).mkcolor(color)}")
        write_to_logfile(logger, f"{header}\n{text}\n")
    else:
        print(TextDecor(text).mkcolor(color))
        write_to_logfile(logger, f"{text}\n")
    return


class ConfigRemoteMachines(Config):
    """Class for remote machine configuration files.

    Args:
        machines_file (str): path to the YAML file contains multiple machines configs.
    """

    def __init__(self, machines_file: str):
        super().__init__()
        self.machines_file: str = machines_file
        self.multi_mdicts = self.loadconfig(machines_file)  # multiple machine dicts
        self.validate_machine_config()
        return

    def validate_machine_config(self, schema_file: str | None = None):
        """Validate multiple machines configs."""
        if schema_file is None:
            schema_file = f"{THKIT_ROOT}/jobman/schema/schema_machine.yml"
        schemas = self.loadconfig(schema_file)  # mutiple schemas
        multi_mdicts = self.multi_mdicts
        for k, mdict in multi_mdicts.items():
            self.validate(config_dict={k: mdict}, schema_dict={k: schemas["tha"]})

        ### validate each type of machine config
        # for k, v in config.items():
        #     if k.startswith("md"):
        #         Config.validate(config_dict={k: v}, schema_dict={k: schema["tha"]})
        #     elif k.startswith("train"):
        #         Config.validate(config_dict={k: v}, schema_dict={k: schema["train"]})
        #     elif k.startswith("dft"):
        #         Config.validate(config_dict={k: v}, schema_dict={k: schema["dft"]})
        return

    def select_machines(self, mdict_prefix: str = "") -> list[dict]:
        """Select machine dicts based on the prefix.

        To specify multiple remote machines for the same purpose, the top-level keys in the `machines_file` should start with the same prefix. Example:
            - `train_1`, `train_2`,... for training jobs
            - `lammps_1`, `lammps_2`,... for lammps jobs
            - `gpaw_1`, `gpaw_2`,... for gpaw jobs

        Args:
            mdict_prefix (str): the prefix to select remote machines for the same purpose. Example: 'dft_', 'md_', 'train_'.

        Returns:
            list[dict]: list of machine dicts
        """
        mdict_list = [v for k, v in self.multi_mdicts.items() if k.startswith(mdict_prefix)]
        if len(mdict_list) < 1:
            warnings.warn(
                f"No machine configs found with prefix '{mdict_prefix}' in file {self.machines_file}"
            )
        return mdict_list

    def check_connection(self, mdict_prefix: str = ""):
        """Check whether the connections to all remote machines are valid.

        Args:
            mdict_prefix (str): Only check the remote machines with this prefix.
        """
        from dpdispatcher import Machine

        def _connect_one_machine(mdict: dict) -> dict | None:
            ### Revise temporary fields for connection test
            mdict["local_root"] = "./"  # tmp local root for connection test
            if mdict["context_type"] == "SSH":
                mdict["remote_profile"]["execute_command"] = f"mkdir -p {mdict['remote_root']}"

            try:
                _ = Machine.load_from_dict(mdict)
            except Exception as e:
                return {"hostname": mdict["remote_profile"]["hostname"], "error": str(e)}
            return None

        ### check all machines
        mdict_list = self.select_machines(mdict_prefix)
        err_machines = [
            _connect_one_machine(mdict["machine"])
            for mdict in mdict_list
            if _connect_one_machine(mdict["machine"]) is not None
        ]
        if len(err_machines) > 0:
            raise RuntimeError(f"Failed to connect to remote machines: {err_machines}")
        return

    def check_resource_settings(self, mdict_prefix: str = ""):
        """Check whether the resource settings in all remote machines are valid."""
        # write a function to test machine's resource settings (after test connnection is ok)
        # Give up: Checking resource settings will take long time if the queue in remote machine is busy.
        return
