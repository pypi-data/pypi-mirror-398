import os
import sys
import math
from itertools import chain
import argparse
import parmed
from io import StringIO

import logging

logger = logging.getLogger('pdb4ambermini_log')
logger.setLevel(logging.DEBUG)

string_types = str

from .residue import (
    RESPROT, RESPROTE, RESNA, 
    AMBER_SUPPORTED_RESNAMES,
    HEAVY_ATOM_DICT, )

__version__ = '0.1.2'

class AmberPDBFixer(object):
    ''' Base class for handling pdb4ambermini tasks (derived from pdb4amber)

    Parameters
    ----------
    parm : str or parmed.Structure or None, default None
    '''

    def __init__(self, parm=None):
        # TODO: make a copy?
        # Why not now? parm[:] will not correctly assign TER residue
        # self.parm = parm[:]
        if isinstance(parm, string_types):
            self.parm = parmed.load_file(parm)
        elif parm is None:
            self.parm = parmed.Structure()
        else:
            self.parm = parm

    def mutate(self, mask_list):
        # TODO : same syntax as pdbfixer (openmm)?
        '''

        Parameters
        ----------
        mask_list: List[Tuple[int, str]]
            [(1, 'ARG'),]

        '''
        idxs = []
        for (idx, resname) in mask_list:
            self.parm.residues[idx].name = resname
            idxs.append(str(idx + 1))
        excluded_mask = ':' + ','.join(idxs) + '&!@C,CA,N,O'
        self.parm.strip(excluded_mask)
        return self

    def assign_histidine(self):
        ''' Assign correct name for Histidine based on the atom name

        Returns
        -------
        parm : updated `parm`
        '''

        for residue in self.parm.residues:
            if residue.name == 'HIS':
                atom_name_set = sorted(
                    set(atom.name for atom in residue.atoms
                        if atom.atomic_number == 1))
                if set(['HD1', 'HE2']).issubset(atom_name_set):
                    residue.name = 'HIP'
                elif 'HD1' in atom_name_set:
                    residue.name = 'HID'
                elif 'HE2' in atom_name_set:
                    residue.name = 'HIE'
        return self

    def strip(self, mask):
        self.parm.strip(mask)
        return self

    def find_missing_heavy_atoms(self, heavy_atom_dict=HEAVY_ATOM_DICT):
        residue_collection = []
        for residue in self.parm.residues:
            if residue.name in heavy_atom_dict:
                n_heavy_atoms = len(
                    set(atom.name for atom in residue.atoms
                        if atom.atomic_number != 1))
                n_missing = heavy_atom_dict[residue.name] - n_heavy_atoms
                if n_missing > 0:
                    residue_collection.append([residue, n_missing])
        return residue_collection

    def constph(self):
        """ Update AS4, GL4, HIP for constph.

        Returns
        -------
        parm : updated `parm`
        """
        for residue in self.parm.residues:
            if residue.name == 'ASP':
                residue.name = 'AS4'
            elif residue.name == 'GLU':
                residue.name = 'GL4'
            elif residue.name == 'HIS':
                residue.name = 'HIP'
            else:
                pass
        return self

    def find_gaps(self):
        # report original resnum?
        CA_atoms = []
        C_atoms = []
        N_atoms = []
        O3_atoms = []
        O5_atoms = []
        gaplist = []
        parm = self.parm

        # First, for protein chains:
        for i, atom in enumerate(parm.atoms):
            if atom.name == 'CA' and atom.residue.name in RESPROTE:
                CA_atoms.append(i)
            if atom.name == 'C' and atom.residue.name in RESPROTE:
                C_atoms.append(i)
            if atom.name == 'N' and atom.residue.name in RESPROTE:
                N_atoms.append(i)

        nca = len(CA_atoms)
        ngaps = 0

        for i in range(nca - 1):
            is_ter = parm.atoms[CA_atoms[i]].residue.ter
            if is_ter:
                continue
            # Changed here to look at the C-N peptide bond distance:
            C_atom = parm.atoms[C_atoms[i]]
            N_atom = parm.atoms[N_atoms[i + 1]]

            dx = float(C_atom.xx) - float(N_atom.xx)
            dy = float(C_atom.xy) - float(N_atom.xy)
            dz = float(C_atom.xz) - float(N_atom.xz)
            gap = math.sqrt(dx * dx + dy * dy + dz * dz)

            if gap > 2.0:
                gaprecord = (gap, C_atom.residue.name, C_atom.residue.idx,
                             N_atom.residue.name, N_atom.residue.idx)
                gaplist.append(gaprecord)
                ngaps += 1

        # Repeat for nucleic acid chains:
        for i, atom in enumerate(parm.atoms):
            if atom.name == "O3'" and atom.residue.name in RESNA:
                O3_atoms.append(i)
            if atom.name == "O5'" and atom.residue.name in RESNA:
                O5_atoms.append(i)

        np = len(O5_atoms)

        for i in range(np - 1):
            is_ter = parm.atoms[O5_atoms[i]].residue.ter
            if is_ter:
                continue
            O3_atom = parm.atoms[O3_atoms[i]]
            O5_atom = parm.atoms[O5_atoms[i + 1]]

            dx = float(O3_atom.xx) - float(O5_atom.xx)
            dy = float(O3_atom.xy) - float(O5_atom.xy)
            dz = float(O3_atom.xz) - float(O5_atom.xz)
            gap = math.sqrt(dx * dx + dy * dy + dz * dz)

            if gap > 3.0:
                gaprecord = (gap, O3_atom.residue.name, O3_atom.residue.idx,
                             O5_atom.residue.name, O5_atom.residue.idx)
                gaplist.append(gaprecord)
                ngaps += 1

        if ngaps > 0:
            logger.info("\n---------- Gaps (Renumbered Residues!)")
            cformat = "gap of %lf A between %s %d and %s %d"
            for _, (d, resname0, resid0, resname1,
                    resid1) in enumerate(gaplist):
                # convert to 1-based
                logger.info(cformat % (d, resname0, resid0 + 1, resname1,
                                       resid1 + 1))
        return gaplist

    def find_disulfide(self):
        """ return set of cys-cys pairs

        Returns
        -------
        cys_cys_set : Set[List[int, int]]
        """
        residues = [
            res for res in self.parm.residues if res.name in ['CYS', 'CYX']
        ]

        cys_cys_resid_set = set()
        cys_cys_atomidx_set = set()
        for residue in residues:
            for atom in residue.atoms:
                if 'SG' in atom.name:
                    for partner in atom.bond_partners:
                        if (partner.residue.name.startswith('CY') and
                                partner.name.startswith('SG')):
                            # use tuple for hashing
                            cys_cys_resid_set.add(
                                tuple(
                                    sorted((atom.residue.idx,
                                            partner.residue.idx))))
                            cys_cys_atomidx_set.add(
                                tuple(sorted((atom.idx, partner.idx))))
        return sorted(cys_cys_resid_set), sorted(cys_cys_atomidx_set)

    def rename_cys_to_cyx(self, cys_cys_set):
        """ Rename CYS to CYX of having S-S bond.

        Parameters
        ----------
        cys_cys_set : Set[List[int, int]]
        """
        for index in chain.from_iterable(cys_cys_set):
            residue = self.parm.residues[index]
            residue.name = 'CYX'

    def find_non_standard_resnames(self):
        ns_names = set()
        for residue in self.parm.residues:
            if len(residue.name) > 3:
                rname = residue.name[:3]
            else:
                rname = residue.name
            if rname.strip() not in AMBER_SUPPORTED_RESNAMES:
                ns_names.add(rname)
        return ns_names

    def visualize(self):
        return self.parm.visualize()

    def write_pdb(self, filename):
        '''

        Parameters
        ----------
        filename : str or file object
        '''
        self.parm.write_pdb(filename)

    def _write_renum(self, basename):
        ''' write original and renumbered residue index
        '''

        with open(basename + '_renum.txt', 'w') as fh:
            for residue in self.parm.residues:
                fh.write("%3s %1s %5s    %3s %5s\n" %
                   (residue.name, residue.chain, residue.number, residue.name,
                    residue.idx + 1))

    def _write_pdb_to_stringio(self,
                               cys_cys_atomidx_set=None,
                               disulfide_conect=True,
                               noter=False,
                               seqres_lines=None,
                               **kwargs):
        stringio_file = StringIO()
        stringio_file_out = StringIO()
        self.parm.write_pdb(stringio_file, **kwargs)
        stringio_file.seek(0)
        lines = stringio_file.readlines()

        if seqres_lines:
            lines = [line for line in lines if not line.startswith("SEQRES")]
            lines = seqres_lines + lines

        # TODO: update ParmEd?
        if disulfide_conect:
            conect_record = [
                'CONECT%5d%5d\n' % (idx0 + 1, idx1 + 1)
                for (idx0, idx1) in cys_cys_atomidx_set
            ]
            conect_str = ''.join(conect_record)
            lines[-1] = conect_str + 'END\n'

        if noter:
            lines = [line for line in lines if not line.startswith("TER")]

        stringio_file_out.writelines(lines)
        stringio_file_out.seek(0)
        return stringio_file_out

    def remove_water(self):
        ''' Remove waters and return new `parm` with only waters
        '''
        # TODO : add AMBER water names (TP3, ...)
        water_mask = ':' + ','.join(parmed.residue.WATER_NAMES)
        self.parm.strip(water_mask)
        return self

    def _summary(self):
        sumdict = dict(has_altlocs=False)

        alt_residues = set()
        chains = set()
        for residue in self.parm.residues:
            chains.add(residue.chain)
            for atom in residue.atoms:
                if atom.other_locations:
                    alt_residues.add(residue)

        # chain
        logger.info('\n----------Chains')
        logger.info('The following (original) chains have been found:')
        for chain_name in sorted(chains):
            logger.info(chain_name)

        # altlocs
        logger.info('\n---------- Alternate Locations (Original Residues!))')
        logger.info('\nThe following residues had alternate locations:')
        if alt_residues:
            sumdict['has_altlocs'] = True
            for residue in sorted(alt_residues):
                logger.info('{}_{}'.format(residue.name, residue.number))
        else:
            logger.info('None')
        return sumdict


def run(
        arg_pdbout,
        arg_pdbin,
        arg_nohyd=False,
        arg_dry=False,
        arg_prot=False,
        arg_amber_compatible_residues=False,
        arg_strip_atom_mask=None,
        arg_mutate_string=None,
        arg_constph=False,
        arg_mostpop=False,
        arg_model=0,
        arg_elbow=False,
        arg_logfile='pdb4ambermini.log',
        arg_keep_altlocs=False,
        arg_conect=True,
        arg_noter=False,
        arg_keep_seqres=False, ):

    # always reset handlers to avoid duplication if run method is called more
    # than once
    logger.handlers = []
    if isinstance(arg_logfile, string_types):
        logfile_handler = logging.FileHandler(arg_logfile)
    elif hasattr(arg_logfile, 'write'):
        logfile_handler = logging.StreamHandler(arg_logfile)
    else:
        raise ValueError(
            "wrong arg_logfile: must be either string or file object")

    logger.addHandler(logfile_handler)
    name = arg_pdbin if not hasattr(arg_pdbin,
                                    '__name__') else arg_pdbin.__name__
    logger.info("\n==================================================")
    logger.info("Summary of pdb4ambermini for: %s" % name)
    logger.info("===================================================")

    if arg_pdbin == arg_pdbout:
        raise RuntimeError(
            "The input and output file names cannot be the same!\n")

    base_filename, extension = os.path.splitext(arg_pdbout)
    if arg_pdbin == 'stdin':
        pdbin = StringIO(sys.stdin.read())
    else:
        pdbin = arg_pdbin

    seqres_lines = None
    pdb_for_parmed = pdbin
    if arg_keep_seqres and not isinstance(pdbin, parmed.Structure):
        if hasattr(pdbin, 'read'):
            pdb_text = pdbin.read()
            seqres_lines = [
                line for line in pdb_text.splitlines(True)
                if line.startswith("SEQRES")
            ]
            pdb_for_parmed = StringIO(pdb_text)
        else:
            with open(pdbin, 'r') as fh:
                pdb_text = fh.read()
            seqres_lines = [
                line for line in pdb_text.splitlines(True)
                if line.startswith("SEQRES")
            ]
            pdb_for_parmed = StringIO(pdb_text)

    if isinstance(pdb_for_parmed, parmed.Structure):
        parm = pdb_for_parmed
    elif hasattr(pdb_for_parmed, 'read'):
        # StringIO (e.g: read from pipe)
        # need to use read_PDB
        parm = parmed.read_PDB(pdb_for_parmed)
    else:
        parm = parmed.read_PDB(pdb_for_parmed)

    pdbfixer = AmberPDBFixer(parm)

    pdbfixer._write_renum(base_filename)

    sumdict = pdbfixer._summary()

    # remove hydrogens if option -y is used:==============================
    if arg_nohyd:
        pdbfixer.parm.strip('@/H')

    # find non-standard Amber residues:===================================
    #   TODO: why does the following call discard the return array of
    #         non-standard residue names?
    ns_names = pdbfixer.find_non_standard_resnames()
    logger.info("-----------Non-standard-resnames")
    logger.info(", ".join(ns_names))

    ns_mask = ':' + ','.join(ns_names)
    ns_mask_filename = base_filename + '_nonprot.pdb'
    if ns_mask != ':':
        pdbfixer.parm[ns_mask].save(ns_mask_filename, overwrite=True)
    else:
        with open(ns_mask_filename, 'w') as fh:
            fh.write("")

    # if arg_elbow:
    #     ns_names = find_non_standard_resnames_elbow(parm)

    # keep only protein:==================================================
    if arg_prot:
        pdbfixer.parm.strip('!:' + ','.join(RESPROT))
    if arg_amber_compatible_residues:
        pdbfixer.parm.strip('!:' + ','.join(AMBER_SUPPORTED_RESNAMES))

    # strip atoms with given mask    =====================================
    if arg_strip_atom_mask is not None:
        pdbfixer.parm.strip(arg_strip_atom_mask)

    # remove water if -d option used:=====================================
    if arg_dry:
        water_mask = ':' + ','.join(parmed.residue.WATER_NAMES)
        water_parm = pdbfixer.parm[water_mask]
        pdbfixer.remove_water()
        water_parm.save('{}_water.pdb'.format(base_filename), overwrite=True)
    # find histidines that might have to be changed:=====================
    if arg_constph:
        pdbfixer.constph()
    else:
        pdbfixer.assign_histidine()

    # find possible S-S in the final protein:=============================
    sslist, cys_cys_atomidx_set = pdbfixer.find_disulfide()
    pdbfixer.rename_cys_to_cyx(sslist)
    with open(base_filename + '_sslink', 'w') as fh:
        for (idx0, idx1) in sslist:
            fh.write('{} {}\n'.format(idx0 + 1, idx1 + 1))

    # find possible gaps:==================================================
    gaplist = pdbfixer.find_gaps()

    mask_str_list = []
    if arg_mutate_string is not None:
        # e.g: arg_mutate_str = "3-ALA,4-GLU"
        for mask_str in arg_mutate_string.replace(';', ',').split(','):
            index, resname = mask_str.split('-')
            mask_str_list.append([int(index.strip()) - 1, resname.strip()])
        pdbfixer.mutate(mask_str_list)

    # count heavy atoms:==================================================
    missing_atom_residues = pdbfixer.find_missing_heavy_atoms()
    logger.info("\n---------- Missing heavy atom(s)\n")
    if missing_atom_residues:
        for (residue, n_missing) in missing_atom_residues:
            logger.warn('{}_{} misses {} heavy atom(s)'.format(
                residue.name, residue.idx + 1, n_missing))
    else:
        logger.info('None')

    # =====================================================================
    # make final output to new PDB file
    # =====================================================================
    if arg_model >= 0:
        final_coordinates = pdbfixer.parm.get_coordinates()[arg_model]
        write_kwargs = dict(coordinates=final_coordinates)
    else:
        # keep all models
        write_kwargs = dict()
    write_kwargs['increase_tercount'] = False # so CONECT record can work properly
    if not arg_keep_altlocs:
        if sumdict['has_altlocs']:
            logger.info('The alternate coordinates have been discarded.')
            if arg_mostpop:
                logger.info(
                    'Only the highest occupancy for each atom was kept.')
                write_kwargs = dict(altlocs='occupancy')
            else:
                logger.info(
                    'Only the first occurrence for each atom was kept.')
                write_kwargs = dict(altlocs='first')
        # remove altlocs label
        for atom in pdbfixer.parm.atoms:
            atom.altloc = ''
            for oatom in atom.other_locations.values():
                oatom.altloc = ''
    if arg_pdbout in ['stdout', 'stderr'] or arg_pdbout.endswith('.pdb'):
        output = pdbfixer._write_pdb_to_stringio(
            cys_cys_atomidx_set=cys_cys_atomidx_set,
            disulfide_conect=arg_conect,
            noter=arg_noter,
            seqres_lines=seqres_lines,
            **write_kwargs)
        output.seek(0)
        if arg_pdbout in ['stdout', 'stderr']:
            pdb_out_filename = 'stdout.pdb'
            print(output.read())
        else:
            pdb_out_filename = arg_pdbout
            with open(arg_pdbout, 'w') as fh:
                fh.write(output.read())
    else:
        # mol2 does not accept altloc keyword
        pdb_out_filename = arg_pdbout
        pdbfixer.parm.save(pdb_out_filename, overwrite=True)

    return ns_names, gaplist, sslist


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        nargs='?',
        help="PDB input file (default: stdin)", )
    parser.add_argument(
        "-i",
        "--in",
        metavar="FILE",
        dest="pdbin",
        help="PDB input file (default: stdin)",
        default='stdin')
    parser.add_argument(
        "-o",
        "--out",
        metavar="FILE",
        dest="pdbout",
        help="PDB output file (default: stdout)",
        default='stdout')
    parser.add_argument(
        "-y",
        "--nohyd",
        action="store_true",
        dest="nohyd",
        help="remove all hydrogen atoms (default: no)")
    parser.add_argument(
        "-d",
        "--dry",
        action="store_true",
        dest="dry",
        help="remove all water molecules (default: no)")
    parser.add_argument(
        "-s",
        "--strip",
        dest="strip_atom_mask",
        default=None,
        help="Strip given atom mask, (default: no)")
    parser.add_argument(
        "-m",
        "--mutate",
        dest="mutation_string",
        default=None,
        help="Mutate residue")
    parser.add_argument(
        "-p",
        "--prot",
        action="store_true",
        dest="prot",
        help="keep only protein residues (default: no)")
    parser.add_argument(
        "-a",
        "--amber-compatible-residues",
        action="store_true",
        dest="amber_compatible_residues",
        help="keep only Amber-compatible residues (default: no)")
    parser.add_argument(
        "--constantph",
        action="store_true",
        dest="constantph",
        help="rename GLU,ASP,HIS for constant pH simulation")
    parser.add_argument(
        "--most-populous",
        action="store_true",
        dest="mostpop",
        help="keep most populous alt. conf. (default is to keep 'A')")
    parser.add_argument(
        "--keep-altlocs",
        action="store_true",
        dest="keep_altlocs",
        help="Keep alternative conformations")
    parser.add_argument(
        "--pdbid",
        action="store_true",
        dest="pdbid",
        help="fetch structure with given pdbid, "
        "should combined with -i option.\n"
        "Subjected to change")
    parser.add_argument(
        "--model",
        type=int,
        dest="model",
        default=1,
        help=
        "Model to use from a multi-model pdb file (integer).  (default: use 1st model). "
        "Use a negative number to keep all models")
    parser.add_argument(
        "-l",
        "--logfile",
        metavar="FILE",
        dest="logfile",
        help="log filename",
        default='stderr')
    parser.add_argument(
        "-v", "--version", action="store_true", dest="version", help="version")
    parser.add_argument(
        "--no-conect",
        action='store_true',
        dest="no_conect",
        help="do Not write S-S CONECT records")
    parser.add_argument(
        "--noter",
        action='store_true',
        dest="noter",
        help="do Not write TER records")
    parser.add_argument(
        "--keep-seqres",
        action='store_true',
        dest="keep_seqres",
        help="Keep SEQRES records from the input PDB and place them at the top of the output PDB")
    opt = parser.parse_args(argv)

    # pdbin : {str, file object, parmed.Structure}
    if opt.version:
        print(__version__)
    if opt.input is not None:
        pdbin = opt.input
    else:
        pdbin = opt.pdbin

    if opt.pdbid:
        pdbin = parmed.download_PDB(pdbin)

    if opt.pdbin == 'stdin' and opt.input is None:
        if os.isatty(sys.stdin.fileno()):
            parser.print_help()
            sys.exit(0)
    if opt.logfile == 'stderr':
        logfile = sys.stderr
    elif opt.logfile == 'stdout':
        logfile = sys.stdout
    else:
        logfile = opt.logfile

    run(
        arg_pdbout=opt.pdbout,
        arg_pdbin=pdbin,
        arg_nohyd=opt.nohyd,
        arg_dry=opt.dry,
        arg_strip_atom_mask=opt.strip_atom_mask,
        arg_mutate_string=opt.mutation_string,
        arg_prot=opt.prot,
        arg_amber_compatible_residues=opt.amber_compatible_residues,
        arg_constph=opt.constantph,
        arg_mostpop=opt.mostpop,
        arg_model=opt.model - 1,
        arg_keep_altlocs=opt.keep_altlocs,
        arg_logfile=logfile,
        arg_conect=not opt.no_conect,
        arg_noter=opt.noter,
        arg_keep_seqres=opt.keep_seqres)


if __name__ == '__main__':
    main()
