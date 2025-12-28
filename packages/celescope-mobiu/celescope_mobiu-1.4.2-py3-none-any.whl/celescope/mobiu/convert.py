"""
convert 5-prime and 3-prime to the same pattern.
"""

from multiprocessing import Process
from celescope.tools import utils, parse_chemistry
from celescope.tools.step import Step, s_common
import pysam


class Convert(Step):
    def __init__(self, args, display_title=None):
        Step.__init__(self, args, display_title=display_title)

        self.fq1_3p = args.fq1_3p.split(",")
        self.fq2_3p = args.fq2_3p.split(",")
        self.fq1_5p = args.fq1_5p.split(",")
        self.fq2_5p = args.fq2_5p.split(",")

        self.chemistry = parse_chemistry.get_chemistry(
            self.assay, self.args.chemistry, self.fq1_3p
        )
        chemistry_version = self.chemistry.split("-")[1]
        chemistry_5p, chemistry_3p = (
            f"mobiu_5p-{chemistry_version}",
            f"mobiu_3p-{chemistry_version}",
        )
        chemistry_dict = parse_chemistry.get_chemistry_dict()
        self.chemistry_dict_5p, self.chemistry_dict_3p = (
            chemistry_dict[chemistry_5p],
            chemistry_dict[chemistry_3p],
        )

    @utils.add_log
    def write_3p(self):
        p3_r1_file = f"{self.out_prefix}_3p_R1.fq.gz"
        p3_r2_file = f"{self.out_prefix}_3p_R2.fq.gz"
        fh_r1 = utils.generic_open(p3_r1_file, "wt", compresslevel=1)
        fh_r2 = utils.generic_open(p3_r2_file, "wt", compresslevel=1)
        runner = parse_chemistry.AutoMobiu(self.fq1_3p)
        for fn1, fn2 in zip(self.fq1_3p, self.fq2_3p):
            with pysam.FastxFile(fn1, persist=False) as fq1, pysam.FastxFile(
                fn2, persist=False
            ) as fq2:
                for entry1, entry2 in zip(fq1, fq2):
                    name1, seq1, qual1 = entry1.name, entry1.sequence, entry1.quality
                    name2, seq2, qual2 = entry2.name, entry2.sequence, entry2.quality
                    offset = runner.v2_offset(seq1)
                    if offset != -1:
                        seq1 = seq1[offset:]
                        qual1 = qual1[offset:]
                    bc_list, bc_quality_list, umi, umi_quality = (
                        parse_chemistry.get_raw_umi_bc_and_quality(
                            seq1, qual1, self.chemistry_dict_3p["pattern_dict"]
                        )
                    )
                    bc = "".join(bc_list)
                    bc_quality = "".join(bc_quality_list)
                    fh_r1.write(
                        utils.fastq_line(name1, bc + umi, bc_quality + umi_quality)
                    )
                    fh_r2.write(utils.fastq_line(name2, seq2, qual2))
        fh_r1.close()
        fh_r2.close()

    @utils.add_log
    def write_5p(self):
        P5_PREFIX = "5p:"
        p5_r1_file = f"{self.out_prefix}_5p_R1.fq.gz"
        p5_r2_file = f"{self.out_prefix}_5p_R2.fq.gz"
        fh_r1 = utils.generic_open(p5_r1_file, "wt", compresslevel=1)
        fh_r2 = utils.generic_open(p5_r2_file, "wt", compresslevel=1)

        for fn1 in self.fq1_5p:
            with pysam.FastxFile(fn1, persist=False) as fq1:
                for entry1 in fq1:
                    name1, seq1, qual1 = entry1.name, entry1.sequence, entry1.quality
                    bc_list, bc_quality_list, umi, umi_quality = (
                        parse_chemistry.get_raw_umi_bc_and_quality(
                            seq1,
                            qual1,
                            self.chemistry_dict_5p["pattern_dict"],
                            reverse_complement=True,
                        )
                    )
                    bc = "".join(bc_list)
                    bc_quality = "".join(bc_quality_list)
                    fh_r1.write(
                        utils.fastq_line(
                            P5_PREFIX + name1, bc + umi, bc_quality + umi_quality
                        )
                    )
        fh_r1.close()

        for fn2 in self.fq2_5p:
            with pysam.FastxFile(fn2, persist=False) as fq:
                for entry2 in fq:
                    name2, seq2, qual2 = entry2.name, entry2.sequence, entry2.quality
                    seq2 = utils.reverse_complement(seq2)
                    qual2 = qual2[::-1]
                    fh_r2.write(utils.fastq_line(P5_PREFIX + name2, seq2, qual2))
        fh_r2.close()

    @utils.add_log
    def run(self):
        p1 = Process(target=self.write_3p)
        p2 = Process(target=self.write_5p)
        p1.start()
        p2.start()
        p1.join()
        p2.join()


@utils.add_log
def convert(args):
    with Convert(args) as runner:
        runner.run()


def get_opts_convert(parser, sub_program=True):
    parser.add_argument(
        "--chemistry",
        default="auto",
        help="chemistry version",
    )
    if sub_program:
        parser.add_argument(
            "--fq1_3p",
            help="3 prime R1 fastq file. Multiple files are separated by comma.",
            required=True,
        )
        parser.add_argument(
            "--fq2_3p",
            help="3 prime R2 fastq file. Multiple files are separated by comma.",
            required=True,
        )
        parser.add_argument(
            "--fq1_5p",
            help="5 prime R1 fastq file. Multiple files are separated by comma.",
            required=True,
        )
        parser.add_argument(
            "--fq2_5p",
            help="5 prime R2 fastq file. Multiple files are separated by comma.",
            required=True,
        )
        parser = s_common(parser)

    return parser
