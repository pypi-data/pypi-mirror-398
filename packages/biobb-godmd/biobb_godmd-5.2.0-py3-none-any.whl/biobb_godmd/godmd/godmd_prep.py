#!/usr/bin/env python3

"""Module containing the GOdMDPrep class and the command line interface."""
from typing import Optional
from pathlib import Path
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools import file_utils as fu
from biobb_common.tools.file_utils import launchlogger
from biobb_godmd.godmd.common import check_input_path, check_output_path


class GOdMDPrep(BiobbObject):
    """
    | biobb_godmd GOdMDPrep
    | Helper bb to prepare inputs for the `GOdMD tool <http://mmb.irbbarcelona.org/GOdMD/>`_ module.
    | Prepares input files for the GOdMD tool.

    Args:
        input_pdb_orig_path (str): Input PDB file to be used as origin in the conformational transition. File type: input. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/data/godmd/1ake_A.pdb>`_. Accepted formats: pdb (edam:format_1476).
        input_pdb_target_path (str): Input PDB file to be used as target in the conformational transition. File type: input. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/data/godmd/4ake_A.pdb>`_. Accepted formats: pdb (edam:format_1476).
        output_aln_orig_path (str): Output GOdMD alignment file corresponding to the origin structure of the conformational transition. File type: output. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/data/godmd/1ake_A.aln>`_. Accepted formats: aln (edam:format_2330), txt (edam:format_2330).
        output_aln_target_path (str): Output GOdMD alignment file corresponding to the target structure of the conformational transition. File type: output. `Sample file <https://github.com/bioexcel/biobb_godmd/raw/main/biobb_godmd/test/data/godmd/4ake_A.aln>`_. Accepted formats: aln (edam:format_2330), txt (edam:format_2330).
        properties (dict - Python dictionary object containing the tool parameters, not input/output files):
            * **gapopen** (*float*) - (12.0) Standard gap penalty: score taken away when a gap is created.
            * **gapextend** (*float*) - (2.0) Penalty added to the standard gap penalty for each base or residue in the gap.
            * **datafile** (*str*) - ("EPAM250") Scoring matrix file used when comparing sequences.
            * **binary_path** (*str*) - ("water") Binary path.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.
            * **sandbox_path** (*str*) - ("./") [WF property] Parent path to the sandbox directory.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_godmd.godmd.godmd_prep import godmd_prep
            prop = {
                'gapopen': 10.0,
                'gapextend': 2.0
            }
            godmd_prep( input_pdb_orig_path='/path/to/input_orig.pdb',
                        input_pdb_target_path='/path/to/input_target.pdb',
                        output_aln_orig_path='/path/to/orig.aln',
                        output_aln_target_path='/path/to/target.aln',
                        properties=prop)

    Info:
        * wrapped_software:
            * name: In house
            * license: Apache-2.0
        * ontology:
            * name: EDAM
            * schema: http://edamontology.org/EDAM.owl

    """

    def __init__(self, input_pdb_orig_path: str, input_pdb_target_path: str,
                 output_aln_orig_path: str, output_aln_target_path: str,
                 properties: Optional[dict] = None, **kwargs) -> None:

        properties = properties or {}

        # Call parent class constructor
        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        self.AA_TRANSLATOR = {'GLY': 'G',
                              'ALA': 'A',
                              'VAL': 'V',
                              'LEU': 'L',
                              'ILE': 'I',
                              'MET': 'M',
                              'PHE': 'F',
                              'TRP': 'W',
                              'PRO': 'P',
                              'SER': 'S',
                              'THR': 'T',
                              'CYS': 'C',
                              'CYX': 'C',
                              'CYM': 'C',
                              'TYR': 'Y',
                              'TYM': 'Y',
                              'ASN': 'N',
                              'GLN': 'Q',
                              'ASP': 'D',
                              'ASH': 'D',
                              'GLU': 'E',
                              'GLH': 'E',
                              'LYS': 'K',
                              'LYN': 'K',
                              'ARG': 'R',
                              'ARN': 'R',
                              'HIS': 'H',
                              'HIE': 'H',
                              'HID': 'H',
                              'HIP': 'H'}

        # Input/Output files
        self.io_dict = {
            'in': {'input_pdb_orig_path': input_pdb_orig_path,
                   'input_pdb_target_path': input_pdb_target_path},
            'out': {'output_aln_orig_path': output_aln_orig_path,
                    'output_aln_target_path': output_aln_target_path}
        }

        # Properties specific for BB
        self.properties = properties
        self.gapopen = properties.get('gapopen', 12.0)
        self.gapextend = properties.get('gapextend', 2.0)
        self.datafile = properties.get('datafile', "EPAM250")
        self.binary_path = properties.get('binary_path', "water")

        # Check the properties
        self.check_properties(properties)
        self.check_arguments()

    def check_data_params(self, out_log, out_err):
        """ Checks input/output paths correctness """

        # Check input(s)
        self.io_dict["in"]["input_pdb_orig_path"] = check_input_path(self.io_dict["in"]["input_pdb_orig_path"], "input_pdb_orig_path", False, out_log, self.__class__.__name__)
        self.io_dict["in"]["input_pdb_target_path"] = check_input_path(self.io_dict["in"]["input_pdb_target_path"], "input_pdb_target_path", False, out_log, self.__class__.__name__)

        # Check output(s)
        self.io_dict["out"]["output_aln_orig_path"] = check_output_path(self.io_dict["out"]["output_aln_orig_path"], "output_aln_orig_path", False, out_log, self.__class__.__name__)
        self.io_dict["out"]["output_aln_target_path"] = check_output_path(self.io_dict["out"]["output_aln_target_path"], "output_aln_target_path", False, out_log, self.__class__.__name__)

    def extract_sequence(self, pdb):
        '''
        Parses a PDB file to retrieve the sequence of a certain chain.
        '''
        seq = ''
        resids = []
        with open(pdb) as file:
            for line in file:
                line = line.rstrip('\n')
                record = line[:6].replace(" ", "")
                if record != 'ATOM':
                    continue
                atomname = line[12:16]
                atomname = atomname.replace(" ", "")
                if atomname != 'CA':
                    continue
                alternate = line[16]
                if alternate != ' ':
                    if alternate != 'A':
                        continue  # if alt loc, only A-labeled residues
                resname = line[17:20].replace(" ", "")
                if resname not in self.AA_TRANSLATOR:
                    continue
                resnum = line[22:26].replace(" ", "")
                icode = line[26:27]
                seq += self.AA_TRANSLATOR[resname]
                resids += [(' ', int(resnum), icode)]  # BioPython's standard PDB atom id (' ',resid,insertioncode) (e.g. (' ',40,'B'))

        return seq, resids

    def retrieve_alignment(self, waterFile, resids1, resids2):
        '''
        Gets the FASTA sequence of two PDB structures and a list of their residues in Biopython residue format.
        Opens a file containing a local sequence alignment (Water program of EMBOSS package) between those two PDB structures.
        Returns the sequence identity and the pairs of residues of the alignment.
        '''
        # Parsing Water alignment file
        is_alignment = 0
        is_qseq = 0
        is_sseq = 0
        qseq = ""
        sseq = ""
        ident = ""
        next_seq = 0
        qstart = ""
        sstart = ""
        with open(waterFile) as file:
            for line in file:
                line = line.rstrip("\n")
                if is_alignment == 0:
                    if not line.startswith(">>#1"):
                        continue
                    else:
                        is_alignment = 1
                else:
                    if line.startswith("; sw_ident:"):
                        ident = line[12:]
                    elif line.startswith("; al_start:"):
                        if next_seq == 0:
                            qstart = line[12:]
                        else:
                            sstart = line[12:]
                    elif line.startswith("; al_display_start:"):
                        if next_seq == 0:
                            is_qseq = 1
                        else:
                            is_sseq = 1
                    else:
                        if is_qseq == 1:
                            if not line.startswith(">"):
                                qseq = qseq + line
                            else:
                                is_qseq = 0
                                next_seq = 1
                        if is_sseq == 1:
                            if line != "":
                                sseq = sseq + line
                            else:
                                is_sseq = 0

        # Get the Sequence Identity of the alignment
        seq_id = float(ident)

        # Get the residues of the alignment.
        # -2 is applied because in the first iteration of next loop all values will always be increased by 1 (local alignment)
        # and we also need to convert the number into a python index to retrieve the proper token in the list
        resid_pairs = []
        idx1 = int(qstart)-2
        idx2 = int(sstart)-2
        for i in range(len(qseq)):  # it could be also len(sseq)
            if qseq[i] != '-':
                idx1 += 1
            if sseq[i] != '-':
                idx2 += 1
            if qseq[i] == '-' or sseq[i] == '-':
                continue
            resid_pairs += [(resids1[idx1], resids2[idx2])]
        # Check contents of the residues of the alignment
        if len(resid_pairs) == 0:  # Alignment file was empty or there was no possible matching residues between the PDBs
            fu.log('Alignment file was empty or there was no possible matching residues between the PDBs' % self.stage_io_dict["unique_dir"], self.out_log)
            return False, False
        else:
            return seq_id, resid_pairs

    @launchlogger
    def launch(self):
        """Launches the execution of the GOdMDPrep module."""

        # check input/output paths and parameters
        self.check_data_params(self.out_log, self.err_log)

        # Setup Biobb
        if self.check_restart():
            return 0
        self.stage_files()

        # Starting the work...
        # Parsing the input PDB files
        pdb1 = self.io_dict["in"]["input_pdb_orig_path"]
        pdb2 = self.io_dict["in"]["input_pdb_target_path"]

        # Generate sequence of first PDB
        seq1, resids1 = self.extract_sequence(pdb1)

        # Generate sequence of second PDB
        seq2, resids2 = self.extract_sequence(pdb2)

        if len(seq1) < 50:
            fu.log('WARNING: Short sequence (ORIGIN)' % self.stage_io_dict["unique_dir"], self.out_log)
        if len(seq2) < 50:
            fu.log('WARNING: Short sequence (TARGET)' % self.stage_io_dict["unique_dir"], self.out_log)

        # Produce FASTA files
        name1 = "fasta1.fa"
        name2 = "fasta2.fa"
        fasta1Filename = str(Path(self.stage_io_dict["unique_dir"]).joinpath(name1))
        fasta1File = open(fasta1Filename, "w")
        fasta1File.write(">"+pdb1+"\n"+seq1)
        fasta1File.close()
        fasta2Filename = str(Path(self.stage_io_dict["unique_dir"]).joinpath(name2))
        fasta2File = open(fasta2Filename, "w")
        fasta2File.write(">"+pdb2+"\n"+seq2)
        fasta2File.close()

        waterFilename = str(Path(self.stage_io_dict["unique_dir"]).joinpath("water_align.out"))

        # water -auto -outfile=water_align.out -asequence=1ake.chains.nolig.pdb.fa
        # -bsequence=4ake.chains.pdb.fa -gapopen=12 -gapextend=2
        # -datafile=EPAM250 -aformat=markx10

        # Command line
        self.cmd = [self.binary_path,
                    '-auto',
                    '-outfile', waterFilename,
                    '-asequence', fasta1Filename,
                    '-bsequence', fasta2Filename,
                    '-gapopen', str(self.gapopen),
                    '-gapextend', str(self.gapextend),
                    '-datafile', self.datafile,
                    '-aformat', "markx10"
                    ]

        # Run Biobb block
        self.run_biobb()

        # Starting post-alignment process: generating .aln files

        # Retrieve sequence identity of the pair, based on local sequence alignment
        # previously computed, and generate the pairs of residues from both structres
        # to drive the superimposition
        seq_id, resid_pairs = self.retrieve_alignment(waterFilename, resids1, resids2)

        aln1Filename = self.io_dict["out"]["output_aln_orig_path"]
        aln1File = open(aln1Filename, 'w')
        for pair in resid_pairs:
            aln1File.write("%s%s\n" % (pair[0][1], pair[0][2].replace(" ", "")))
        aln1File.close()

        aln2Filename = self.io_dict["out"]["output_aln_target_path"]
        aln2File = open(aln2Filename, 'w')
        for pair in resid_pairs:
            aln2File.write("%s%s\n" % (pair[1][1], pair[1][2].replace(" ", "")))
        aln2File.close()

        # Copy files to host
        self.copy_to_host()

        # Remove temporary folder(s)
        self.remove_tmp_files()

        self.check_arguments(output_files_created=True, raise_exception=False)

        return self.return_code


def godmd_prep(input_pdb_orig_path: str, input_pdb_target_path: str,
               output_aln_orig_path: str, output_aln_target_path: str,
               properties: Optional[dict] = None, **kwargs) -> int:
    """Create :class:`GOdMDPrep <godmd.godmd_prep.GOdMDPrep>`godmd.godmd_prep.GOdMDPrep class and
    execute :meth:`launch() <godmd.godmd_prep.GOdMDPrep.launch>` method"""
    return GOdMDPrep(**dict(locals())).launch()


godmd_prep.__doc__ = GOdMDPrep.__doc__
main = GOdMDPrep.get_main(godmd_prep, "Prepares input files for the GOdMD tool.")

if __name__ == '__main__':
    main()
