#!/usr/bin/env python3

"""Module containing the Pdbsplitseg class and the command line interface."""

import glob
import os
import zipfile
from pathlib import Path
from typing import Optional
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools import file_utils as fu
from biobb_common.tools.file_utils import launchlogger


class Pdbsplitseg(BiobbObject):
    """
    | biobb_pdb_tools Pdbsplitseg
    | Splits a PDB file into several, each containing one segment.
    | This tool splits a PDB file into several, each containing one segment. It can be used to split a PDB file into several, each containing one segment.

    Args:
        input_file_path (str): Input PDB file. File type: input. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_pdb_tools/master/biobb_pdb_tools/test/data/pdb_tools/input_pdb_splitseg.pdb>`_. Accepted formats: pdb (edam:format_1476).
        output_file_path (str): ZIP file containing all PDB files splited by protein segment. File type: output. `Sample file <https://github.com/bioexcel/biobb_pdb_tools/blob/master/biobb_pdb_tools/test/reference/pdb_tools/ref_pdb_splitseg.zip>`_. Accepted formats: zip (edam:format_3987).
        properties (dic):
            * **binary_path** (*str*) - ("pdb_splitseg") Path to the pdb_splitseg executable binary.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_pdb_tools.pdb_tools.biobb_pdb_splitseg import biobb_pdb_splitseg

            biobb_pdb_splitseg(input_file_path='/path/to/input.pdb',
                    output_file_path='/path/to/output.pdb')

    Info:
        * wrapped_software:
            * name: pdb_tools
            * version: >=2.5.0
            * license: Apache-2.0
        * ontology:
            * name: EDAM
            * schema: http://edamontology.org/EDAM.owl

    """

    def __init__(
        self, input_file_path, output_file_path, properties=None, **kwargs
    ) -> None:
        properties = properties or {}

        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        self.io_dict = {
            "in": {"input_file_path": input_file_path},
            "out": {"output_file_path": output_file_path},
        }

        self.binary_path = properties.get("binary_path", "pdb_splitseg")
        self.properties = properties
        self.check_init(properties)

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`Pdbsplitseg <biobb_pdb_tools.pdb_tools.pdb_splitseg>` object."""

        if self.check_restart():
            return 0
        self.stage_files()

        self.cmd = [
            "cd",
            self.stage_io_dict.get("unique_dir", ""),
            ";",
            self.binary_path,
            self.stage_io_dict["in"]["input_file_path"],
        ]

        fu.log(" ".join(self.cmd), self.out_log, self.global_log)
        fu.log(
            "Creating command line with instructions and required arguments",
            self.out_log,
            self.global_log,
        )
        self.run_biobb()

        stem = Path(self.stage_io_dict["in"]["input_file_path"]).stem
        pdb_files = glob.glob(
            os.path.join(self.stage_io_dict.get(
                "unique_dir", ""), stem + "_*.pdb")
        )

        if len(pdb_files) > 1:
            output_zip_path = os.path.join(
                self.stage_io_dict.get("unique_dir", ""),
                self.stage_io_dict["out"]["output_file_path"],
            )
            fu.log(
                "Saving %d pdb segment files in a zip" % len(pdb_files),
                self.out_log,
                self.global_log,
            )
            with zipfile.ZipFile(output_zip_path, "w") as zipf:
                for pdb_file in pdb_files:
                    zipf.write(pdb_file, os.path.basename(pdb_file))
        else:
            fu.log(
                "The given input file has no segments. Saving the input file into a zip.",
                self.out_log,
                self.global_log,
            )
            output_zip_path = os.path.join(
                self.stage_io_dict.get("unique_dir", ""),
                self.stage_io_dict["out"]["output_file_path"],
            )
            with zipfile.ZipFile(output_zip_path, "w") as zipf:
                zipf.write(
                    self.stage_io_dict["in"]["input_file_path"],
                    os.path.basename(
                        self.stage_io_dict["in"]["input_file_path"]),
                )
            pass

        self.copy_to_host()
        self.remove_tmp_files()
        self.check_arguments(output_files_created=True, raise_exception=False)

        return self.return_code


def biobb_pdb_splitseg(
    input_file_path: str,
    output_file_path: str,
    properties: Optional[dict] = None,
    **kwargs,
) -> int:
    """Create :class:`Pdbsplitseg <biobb_pdb_tools.pdb_tools.pdb_splitseg>` class and
    execute the :meth:`launch() <biobb_pdb_tools.pdb_tools.pdb_splitseg.launch>` method."""

    return Pdbsplitseg(**dict(locals())).launch()


biobb_pdb_splitseg.__doc__ = Pdbsplitseg.__doc__
main = Pdbsplitseg.get_main(biobb_pdb_splitseg, "Splits a PDB file into several, each containing one segment.")

if __name__ == "__main__":
    main()
