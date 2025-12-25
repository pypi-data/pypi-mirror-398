#!/usr/bin/env python3

"""Module containing the GOdMDRun class and the command line interface."""

import shutil
from pathlib import Path, PurePath
from typing import Optional

from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools.file_utils import launchlogger

from biobb_godmd.godmd.common import check_input_path, check_output_path


class GOdMDRun(BiobbObject):
    """
    | biobb_godmd GOdMDRun
    | Wrapper of the `GOdMD tool <http://mmb.irbbarcelona.org/GOdMD/>`_ module.
    | Computes conformational transition trajectories for proteins using GOdMD tool.

    Args:
        input_pdb_orig_path (str): Input PDB file to be used as origin in the conformational transition. File type: input. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/data/godmd/1ake_A.pdb>`_. Accepted formats: pdb (edam:format_1476).
        input_pdb_target_path (str): Input PDB file to be used as target in the conformational transition. File type: input. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/data/godmd/4ake_A.pdb>`_. Accepted formats: pdb (edam:format_1476).
        input_aln_orig_path (str): Input GOdMD alignment file corresponding to the origin structure of the conformational transition. File type: input. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/data/godmd/1ake_A.aln>`_. Accepted formats: aln (edam:format_2330), txt (edam:format_2330).
        input_aln_target_path (str): Input GOdMD alignment file corresponding to the target structure of the conformational transition. File type: input. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/data/godmd/4ake_A.aln>`_. Accepted formats: aln (edam:format_2330), txt (edam:format_2330).
        input_config_path (str) (Optional): Input GOdMD configuration file. File type: input. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/data/godmd/params.in>`_. Accepted formats: in (edam:format_2330), txt (edam:format_2330).
        output_log_path (str): Output log file. File type: output. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/reference/godmd/godmd.log>`_. Accepted formats: log (edam:format_2330), out (edam:format_2330), txt (edam:format_2330), o (edam:format_2330).
        output_ene_path (str): Output energy file. File type: output. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/reference/godmd/godmd_ene.out>`_. Accepted formats: log (edam:format_2330), out (edam:format_2330), txt (edam:format_2330), o (edam:format_2330).
        output_trj_path (str): Output trajectory file. File type: output. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/reference/godmd/godmd_trj.mdcrd>`_. Accepted formats: trj (edam:format_3878), crd (edam:format_3878), mdcrd (edam:format_3878), x (edam:format_3878).
        output_pdb_path (str): Output structure file. File type: output. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/reference/godmd/godmd_pdb.pdb>`_. Accepted formats: pdb (edam:format_1476).
        properties (dict - Python dictionary object containing the tool parameters, not input/output files):
            * **godmdin** (*dict*) - ({}) GOdMD options specification.
            * **binary_path** (*str*) - ("discrete") Binary path.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.
            * **sandbox_path** (*str*) - ("./") [WF property] Parent path to the sandbox directory.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_godmd.godmd.godmd_run import godmd_run
            prop = {
                'remove_tmp': True
            }
            godmd_run(   input_pdb_orig_path='/path/to/pdb_orig.pdb',
                         input_pdb_target_path='/path/to/pdb_target.pdb',
                         input_aln_orig_path='/path/to/aln_orig.aln',
                         input_aln_target_path='/path/to/aln_target.aln',
                         output_log_path='/path/to/godmd_log.log',
                         output_ene_path='/path/to/godmd_ene.txt',
                         output_trj_path='/path/to/godmd_trj.mdcrd',
                         output_pdb_path='/path/to/godmd_pdb.pdb',
                         properties=prop)

    Info:
        * wrapped_software:
            * name: GOdMD
            * version: >=1.0
            * license: Apache-2.0
        * ontology:
            * name: EDAM
            * schema: http://edamontology.org/EDAM.owl

    """

    def __init__(
        self,
        input_pdb_orig_path: str,
        input_pdb_target_path: str,
        input_aln_orig_path: str,
        input_aln_target_path: str,
        input_config_path: Optional[str],
        output_log_path: str,
        output_ene_path: str,
        output_trj_path: str,
        output_pdb_path: str,
        properties: Optional[dict] = None,
        **kwargs,
    ) -> None:
        properties = properties or {}

        # Call parent class constructor
        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        # Input/Output files
        self.io_dict = {
            "in": {
                "input_pdb_orig_path": input_pdb_orig_path,
                "input_pdb_target_path": input_pdb_target_path,
                "input_aln_orig_path": input_aln_orig_path,
                "input_aln_target_path": input_aln_target_path,
                "input_config_path": input_config_path,
            },
            "out": {
                "output_log_path": output_log_path,
                "output_ene_path": output_ene_path,
                "output_trj_path": output_trj_path,
                "output_pdb_path": output_pdb_path,
            },
        }

        # Properties specific for BB
        self.properties = properties
        self.godmdin = {k: str(v) for k, v in properties.get("godmdin", dict()).items()}
        self.binary_path = properties.get("binary_path", "discrete")

        # Check the properties
        self.check_properties(properties)
        # self.check_arguments()

    def check_data_params(self, out_log, out_err):
        """Checks input/output paths correctness"""

        # Check input(s)
        self.io_dict["in"]["input_pdb_orig_path"] = check_input_path(
            self.io_dict["in"]["input_pdb_orig_path"],
            "input_pdb_orig_path",
            False,
            out_log,
            self.__class__.__name__,
        )
        self.io_dict["in"]["input_pdb_target_path"] = check_input_path(
            self.io_dict["in"]["input_pdb_target_path"],
            "input_pdb_target_path",
            False,
            out_log,
            self.__class__.__name__,
        )
        self.io_dict["in"]["input_aln_orig_path"] = check_input_path(
            self.io_dict["in"]["input_aln_orig_path"],
            "input_aln_orig_path",
            False,
            out_log,
            self.__class__.__name__,
        )
        self.io_dict["in"]["input_aln_target_path"] = check_input_path(
            self.io_dict["in"]["input_aln_target_path"],
            "input_aln_target_path",
            False,
            out_log,
            self.__class__.__name__,
        )
        self.io_dict["in"]["input_config_path"] = check_input_path(
            self.io_dict["in"]["input_config_path"],
            "input_config_path",
            True,
            out_log,
            self.__class__.__name__,
        )

        # Check output(s)
        self.io_dict["out"]["output_log_path"] = check_output_path(
            self.io_dict["out"]["output_log_path"],
            "output_log_path",
            False,
            out_log,
            self.__class__.__name__,
        )
        self.io_dict["out"]["output_ene_path"] = check_output_path(
            self.io_dict["out"]["output_ene_path"],
            "output_ene_path",
            False,
            out_log,
            self.__class__.__name__,
        )
        self.io_dict["out"]["output_trj_path"] = check_output_path(
            self.io_dict["out"]["output_trj_path"],
            "output_trj_path",
            False,
            out_log,
            self.__class__.__name__,
        )
        self.io_dict["out"]["output_pdb_path"] = check_output_path(
            self.io_dict["out"]["output_pdb_path"],
            "output_pdb_path",
            False,
            out_log,
            self.__class__.__name__,
        )

    def create_godmdin(self, path: Optional[str] = None) -> str:
        """Creates a GOdMD configuration file (godmdin) using the properties file settings"""
        godmdin_list = []

        self.output_godmdin_path = path

        if self.io_dict["in"]["input_config_path"]:
            # GOdMD input parameters read from an input godmdin file
            with open(self.io_dict["in"]["input_config_path"]) as input_params:
                for line in input_params:
                    if "=" in line:
                        godmdin_list.append(line.upper())
        else:
            # Pre-configured simulation type parameters
            godmdin_list.append("  TSNAP = 500 ! BioBB GOdMD default params \n")
            godmdin_list.append("  TEMP = 300 ! BioBB GOdMD default params \n")
            godmdin_list.append("  SEED = 2525 ! BioBB GOdMD default params \n")
            godmdin_list.append("  ENER_EVO_SIZE = 20 ! BioBB GOdMD default params \n")
            godmdin_list.append("  NBLOC = 10000 ! BioBB GOdMD default params \n")
            godmdin_list.append(
                "  ERRORACCEPTABLE = 1.5 ! BioBB GOdMD default params \n"
            )

        # Adding the rest of parameters in the config file to the mdin file
        # if the parameter has already been added replace the value
        parameter_keys = [parameter.split("=")[0].strip() for parameter in godmdin_list]
        for k, v in self.godmdin.items():
            config_parameter_key = str(k).strip().upper()
            if config_parameter_key in parameter_keys:
                godmdin_list[parameter_keys.index(config_parameter_key)] = (
                    "\t" + config_parameter_key + " = " + str(v) + " ! BioBB property \n"
                )
            else:
                godmdin_list.append(
                    "\t" + config_parameter_key + " = " + str(v) + " ! BioBB property \n"
                )

        # Writing MD configuration file (mdin)
        with open(str(self.output_godmdin_path), "w") as godmdin:
            # GOdMDIN parameters added by the biobb_godmd module
            godmdin.write(
                "!This godmdin file has been created by the biobb_godmd module from the BioBB library \n\n"
            )

            godmdin.write("&INPUT\n")

            # MD config parameters
            for line in godmdin_list:
                godmdin.write(line)

            godmdin.write("&END\n")

        return str(self.output_godmdin_path)

    @launchlogger
    def launch(self):
        """Launches the execution of the GOdMDRun module."""

        # check input/output paths and parameters
        self.check_data_params(self.out_log, self.err_log)

        # Setup Biobb
        if self.check_restart():
            return 0
        self.stage_files()

        # Creating GOdMD input file
        self.output_godmdin_path = self.create_godmdin(
            path=str(Path(self.stage_io_dict["unique_dir"]).joinpath("godmd.in"))
        )

        # Command line
        # discrete -i $fileName.in -pdbin $pdbch1 -pdbtarg $pdbch2 -ener $fileName.ene -trj $fileName.crd -p1 $alignFile1 -p2 $alignFile2 -o $fileName.log >& $fileName.out
        self.cmd = [
            "cd",
            self.stage_io_dict["unique_dir"],
            ";",
            self.binary_path,
            "-i",
            "godmd.in",
            "-pdbin",
            PurePath(self.stage_io_dict["in"]["input_pdb_orig_path"]).name,
            "-pdbtarg",
            PurePath(self.stage_io_dict["in"]["input_pdb_target_path"]).name,
            "-p1",
            PurePath(self.stage_io_dict["in"]["input_aln_orig_path"]).name,
            "-p2",
            PurePath(self.stage_io_dict["in"]["input_aln_target_path"]).name,
            "-o",
            PurePath(self.stage_io_dict["out"]["output_log_path"]).name,
            "-ener",
            PurePath(self.stage_io_dict["out"]["output_ene_path"]).name,
            "-trj",
            PurePath(self.stage_io_dict["out"]["output_trj_path"]).name,
        ]

        # Run Biobb block
        self.run_biobb()

        # Copy outputs from temporary folder to output path
        shutil.copy2(
            str(Path(self.stage_io_dict["unique_dir"]).joinpath("reference.pdb")),
            PurePath(self.io_dict["out"]["output_pdb_path"]),
        )

        # Copy files to host
        self.copy_to_host()

        # Remove temporary folder(s)
        self.remove_tmp_files()

        self.check_arguments(output_files_created=True, raise_exception=False)

        return self.return_code


def godmd_run(
    input_pdb_orig_path: str,
    input_pdb_target_path: str,
    input_aln_orig_path: str,
    input_aln_target_path: str,
    output_log_path: str,
    output_ene_path: str,
    output_trj_path: str,
    output_pdb_path: str,
    input_config_path: Optional[str] = None,
    properties: Optional[dict] = None,
    **kwargs,
) -> int:
    """Create :class:`GOdMDRun <godmd.godmd_run.GOdMDRun>`godmd.godmd_run.GOdMDRun class and
    execute :meth:`launch() <godmd.godmd_run.GOdMDRun.launch>` method"""
    return GOdMDRun(**dict(locals())).launch()


godmd_run.__doc__ = GOdMDRun.__doc__
main = GOdMDRun.get_main(godmd_run, "Computing conformational transition trajectories for proteins using GOdMD tool.")

if __name__ == "__main__":
    main()
