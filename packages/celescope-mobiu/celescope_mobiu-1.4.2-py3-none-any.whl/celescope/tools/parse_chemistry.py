import itertools
import os
import re
import sys
from collections import defaultdict

import pysam
from celescope.tools import utils
from celescope.chemistry_dict import chemistry_dict, chemistry_dir


def parse_pattern(pattern: str, allowed: str = "CLUNT") -> dict[str, list[slice]]:
    """Parse a pattern string into a dictionary of slices.

    >>> pattern_dict = parse_pattern("C8L16C8L16C8L1U12T18")
    >>> pattern_dict['C']
    [slice(0, 8, None), slice(24, 32, None), slice(48, 56, None)]
    >>> pattern_dict['L']
    [slice(8, 24, None), slice(32, 48, None), slice(56, 57, None)]
    """
    pattern_slices: dict[str, list[slice]] = {}
    p = re.compile(r"([A-Z])(\d+)")  # Compile the regex

    start = 0
    for char, length in p.findall(pattern):
        if char not in allowed:
            raise ValueError(f"Invalid character '{char}' in pattern: {pattern}")
        if char not in pattern_slices:
            pattern_slices[char] = []
        end = start + int(length)
        pattern_slices[char].append(slice(start, end))
        start = end
    return pattern_slices


def create_mismatch_seqs(seq: str, max_mismatch=1, allowed_bases="ACGTN") -> set[str]:
    """Create all sequences within a specified number of mismatches from the input sequence.

    >>> answer = set(["TCG", "AAG", "ACC", "ATG", "ACT", "ACN", "GCG", "ANG", "ACA", "ACG", "CCG", "AGG", "NCG"])
    >>> seq_set = create_mismatch_seqs("ACG")
    >>> seq_set == answer
    True
    """
    if max_mismatch < 0:
        raise ValueError("max_mismatch must be non-negative")
    if max_mismatch > len(seq):
        raise ValueError(
            f"max_mismatch ({max_mismatch}) cannot be greater than the sequence length ({len(seq)})"
        )

    result = set()
    for locs in itertools.combinations(range(len(seq)), max_mismatch):
        seq_locs = [
            list(allowed_bases) if i in locs else [base] for i, base in enumerate(seq)
        ]
        result.update("".join(p) for p in itertools.product(*seq_locs))
    return result


def create_mismatch_origin_dict(origin_seqs: list, n_mismatch=1) -> dict[str, str]:
    """Create a dictionary mapping sequences with mismatches to their original sequences(in whitelist).

    >>> origin_seqs = ["AACGTGAT", "AAACATCG"]
    >>> mismatch_dict = create_mismatch_origin_dict(origin_seqs)
    >>> mismatch_dict["AACGTGAA"] == "AACGTGAT"
    True
    """
    result = {}
    for origin_seq in origin_seqs:
        origin_seq = origin_seq.strip()
        if origin_seq == "":
            continue
        for mismatch_seq in create_mismatch_seqs(origin_seq, n_mismatch):
            result[mismatch_seq] = origin_seq
    return result


def create_mismatch_origin_dicts_from_whitelists(
    whitelists: list, n_mismatch: int = 1
) -> tuple[list, list]:
    """Returns origin whitelist list and mismatch dict list."""
    raw_list, mismatch_list = [], []
    for f in whitelists:
        barcodes = utils.one_col_to_list(f)
        raw_list.append(set(barcodes))
        barcode_mismatch_dict = create_mismatch_origin_dict(barcodes, n_mismatch)
        mismatch_list.append(barcode_mismatch_dict)

    return raw_list, mismatch_list


def check_seq_mismatch(seq_list, raw_list, mismatch_list):
    """
    Returns
        valid: True if seq in mismatch_list or mismatch_list is empty
        corrected: True if seq in mismatch_list but not in raw_list
        res: joined seq

    >>> seq_list = ['ATA', 'AAT', 'ATA']
    >>> correct_set_list = [{'AAA'},{'AAA'},{'AAA'}]
    >>> mismatch_dict_list = [create_mismatch_origin_dict(['AAA'])] * 3

    >>> check_seq_mismatch(seq_list, correct_set_list, mismatch_dict_list)
    (True, True, 'AAA_AAA_AAA')

    >>> seq_list = ['AAA', 'AAA', 'AAA']
    >>> check_seq_mismatch(seq_list, correct_set_list, mismatch_dict_list)
    (True, False, 'AAA_AAA_AAA')

    >>> seq_list = ['AAA', 'AAA', 'AAA']
    >>> raw_list, mismatch_list = [], []
    >>> check_seq_mismatch(seq_list, raw_list, mismatch_list)
    (True, False, 'AAA_AAA_AAA')
    """
    if not mismatch_list:
        return True, False, "_".join(seq_list)
    valid = True
    corrected = False
    res = []
    for index, seq in enumerate(seq_list):
        if seq not in raw_list[index]:
            if seq not in mismatch_list[index]:
                valid = False
                res.append("")
            else:
                corrected = True
                res.append(mismatch_list[index][seq])
        else:
            res.append(seq)

    return valid, corrected, "_".join(res)


def get_chemistry_dict():
    """
    Return:
    chemistry_dict. Key: chemistry name, value: chemistry dict
    """
    # add folder prefix
    for chemistry in chemistry_dict:
        cur = chemistry_dict[chemistry]
        bc = cur.get("bc", [])
        linker = cur.get("linker", [])
        if bc:
            cur["bc"] = [os.path.join(chemistry_dir, chemistry, x) for x in bc]
        if linker:
            cur["linker"] = [os.path.join(chemistry_dir, chemistry, x) for x in linker]
        cur["pattern_dict"] = parse_pattern(cur["pattern"])
    return chemistry_dict


def get_raw_umi_bc_and_quality(
    seq: str, quality: str, pattern_dict: dict, reverse_complement=False
) -> tuple[list, list, str, str]:
    """
    Returns:
        bc_list, umi, bc_quality_list, umi_qual
    """
    bc_list = [seq[x] for x in pattern_dict["C"]]
    bc_quality_list = [quality[x] for x in pattern_dict["C"]]
    umi = seq[pattern_dict["U"][0]]
    umi_qual = quality[pattern_dict["U"][0]]
    if reverse_complement:
        bc_list = [utils.reverse_complement(x) for x in bc_list[::-1]]
        bc_quality_list = bc_quality_list[::-1]
        umi = utils.reverse_complement(umi)
        umi_qual = umi_qual[::-1]
    return bc_list, bc_quality_list, umi, umi_qual


class Auto:
    """
    Auto detect singleron chemistrys from R1-read
    """

    def __init__(self, fq1_list, chemistry_dict, max_read=10000):
        """
        Returns:
            chemistry, chemistry_dict[chemistry]
        """
        self.fq1_list = fq1_list
        self.max_read = max_read
        self.chemistry_dict = chemistry_dict
        self.mismatch_dict = {}
        for chemistry in self.chemistry_dict:
            if "bc" in self.chemistry_dict[chemistry]:
                self.mismatch_dict[chemistry] = (
                    create_mismatch_origin_dicts_from_whitelists(
                        self.chemistry_dict[chemistry]["bc"], 1
                    )
                )

    def run(self):
        """
        Returns:
            chemistry, chemistry_dict[chemistry]
        """
        chemistry = self.get_chemistry()
        return chemistry, self.chemistry_dict[chemistry]

    def get_chemistry(self) -> str:
        """check chemistry in the fq1_list"""
        fq_chemistry = {}
        for fastq1 in self.fq1_list:
            chemistry = self.get_fq_chemistry(fastq1)
            fq_chemistry[fastq1] = chemistry
        if len(set(fq_chemistry.values())) != 1:
            sys.exit(
                f"Error: multiple chemistrys are not allowed for one sample: {self.fq1_list}! \n"
                + str(fq_chemistry)
            )
        chemistry = list(fq_chemistry.values())[0]
        return chemistry

    def is_chemistry(self, seq, chemistry):
        """check if seq matches the barcode of chemistry"""
        raw_list, mismatch_list = self.mismatch_dict[chemistry]
        bc_list = [seq[x] for x in self.chemistry_dict[chemistry]["pattern_dict"]["C"]]
        valid, _corrected, _res = check_seq_mismatch(bc_list, raw_list, mismatch_list)
        return valid

    def seq_chemistry(self, seq):
        """check if seq matches any chemistry in chemistry_dict"""
        for chemistry in self.chemistry_dict:
            if self.is_chemistry(seq, chemistry):
                return chemistry
        return None

    def get_fq_chemistry(self, fq1):
        chemistry_readcount = defaultdict(int)

        fq = pysam.FastxFile(fq1)
        n = 0
        for read in fq:
            seq = read.sequence
            n += 1
            chemistry = self.seq_chemistry(seq)
            if chemistry:
                chemistry_readcount[chemistry] += 1
            if n == self.max_read:
                break
        sorted_counts = sorted(
            chemistry_readcount.items(), key=lambda x: x[1], reverse=True
        )
        print(sorted_counts)

        chemistry, read_counts = sorted_counts[0]
        percent = float(read_counts) / n
        if percent < 0.1:
            print("Valid chemistry read counts percent < 0.1")
            raise Exception("Auto chemistry detection failed! ")
        elif percent < 0.5:
            print("Valid chemistry read counts percent < 0.5")
        print(f"{fq1}: {chemistry}")

        return chemistry


LINKER1 = "ATCCAGCTGCTTGAGATC"


class AutoMobiu(Auto):
    def __init__(self, fq1_list, max_read=10000):
        super().__init__(fq1_list, get_chemistry_dict(), max_read)
        self.linker1_mismatch = create_mismatch_seqs(LINKER1, max_mismatch=2)

    def seq_chemistry(self, seq):
        """
        Returns: chemistry or None
        """
        if self.v2_offset(seq) != -1:
            return "mobiu-2"
        for chemistry in ["mobiu_3p-1"]:
            if self.is_chemistry(seq, chemistry):
                return chemistry.replace("_3p", "")

    def v2_offset(self, seq):
        """
        return -1 if not v2

        >>> seq = "ATCCAGCTGCTTGAGATC" + "AACGGACCT" + "ACGATG" + "TTGGTGACC" + "CATAGT" + "TTCGGTCAA" + "CATATCAATGGG" + "TTTTTTTTTT"
        >>> runner = AutoMobiu([], "fake_sample")
        >>> runner.v4_offset(seq)
        0

        >>> seq = "AA" + "ATCCAGCTGCTTGAGATC" + "AACGGACCT" + "ACGATG" + "TTGGTGACC" + "CATAGT" + "TTCGGTCAA" + "CATATCAATGGG" + "TTTTTTTTTT"
        >>> runner = AutoMobiu([], "fake_sample")
        >>> runner.v4_offset(seq)
        2

        >>> seq = "AA" + "TATATATCCAGCTGCTTGAGATC" + "AACGGACCT" + "ACGATG" + "TTGGTGACC" + "CATAGT" + "TTCGGTCAA" + "CATATCAATGGG" + "TTTTTTTTTT"
        >>> runner = AutoMobiu([], "fake_sample")
        >>> runner.v4_offset(seq)
        -1
        """
        max_offset_len = 3 + 1  # allow for extra 1 bases
        for offset in range(max_offset_len + 1):
            linker1_seq = seq[offset : offset + len(LINKER1)]
            if linker1_seq in self.linker1_mismatch:
                return offset
        return -1


@utils.add_log
def get_pattern_dict_and_bc(
    chemistry, pattern: str = "", whitelist: str = ""
) -> tuple[dict, list]:
    if chemistry != "customized":
        chemistry_dict = get_chemistry_dict()
        pattern_dict = chemistry_dict[chemistry]["pattern_dict"]
        bc = chemistry_dict[chemistry]["bc"]
    else:
        pattern_dict = parse_pattern(pattern)
        bc = whitelist.split(" ")
    return pattern_dict, bc


def get_chemistry(assay, args_chemistry, fq1_list):
    if args_chemistry == "auto":
        runner = AutoMobiu(fq1_list)
        return runner.get_chemistry()
    else:
        return args_chemistry
