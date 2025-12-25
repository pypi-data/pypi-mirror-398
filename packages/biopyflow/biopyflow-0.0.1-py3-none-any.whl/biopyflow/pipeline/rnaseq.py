from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_BINDS = [
    "/farmshare/user_data/khoang99",
    "/farmshare/home/classes/bios/270",
    f"{PROJECT_ROOT}",
]

from biopyflow.core.channel import Channel
from biopyflow.core.config import Config, Resource
from biopyflow.core.flow import Flow
from biopyflow.core.step import Step

class FASTQC(Step):
    INPUTS = {"fastq_pair": [None, None], "sample_name": None}
    OUTPUTS = {"fastqc_html": "{outdir}/{sample_name}/*.html"}
    RESOURCE = Resource(cpu=4, mem=8, time=1)
    CONFIG = Config(
        image="/farmshare/user_data/khoang99/bios270/envs/bioinformatics_latest.sif",
        runtime="singularity",
        executor="slurm",
        binds=list(DEFAULT_BINDS),
    )
    PARAMS = {"outdir": "fastqc_out"}

    def script(self) -> str:
        r1, r2 = self.inputs()["fastq_pair"]
        sample = self.inputs()["sample_name"]
        outdir = os.path.join(self.params["outdir"], sample)
        os.makedirs(outdir, exist_ok=True)
        cmd = f"fastqc {r1} {r2} -o {outdir}"
        print(f"Running FASTQC: {sample} {cmd}")
        # dummy command to test if the step is running with the correct inputs and outputs
        os.makedirs(outdir, exist_ok=True)
        # create a dummy output file with correct extension
        with open(os.path.join(outdir, f"{sample}_1_fastqc.html"), "w") as f:
            f.write("dummy output file")
        with open(os.path.join(outdir, f"{sample}_2_fastqc.html"), "w") as f:
            f.write("dummy output file")
        return "sleep 10"
        # return cmd


class TRIM_GALORE(Step):
    INPUTS = {"fastq_pair": [None, None], "sample_name": None}
    OUTPUTS = {"trimmed_pair": ["{outdir}/{sample_name}/*1.fq", "{outdir}/{sample_name}/*2.fq"]}
    RESOURCE = Resource(cpu=4, mem=16, time=2)
    CONFIG = Config(
        image="/farmshare/user_data/khoang99/bios270/envs/bioinformatics_latest.sif",
        runtime="singularity",
        executor="slurm",
        binds=list(DEFAULT_BINDS),
    )
    PARAMS = {"outdir": "trimmed", "quality": 20, "length": 20}

    def script(self) -> str:
        r1, r2 = self.inputs()["fastq_pair"]
        sample = self.inputs()["sample_name"]
        outdir = os.path.join(self.params["outdir"], sample)
        os.makedirs(outdir, exist_ok=True)
        cmd = f"trim_galore --paired {r1} {r2} --output_dir {outdir} --quality {self.params['quality']} --length {self.params['length']}"
        print(f"Running TRIM_GALORE: {sample} {cmd}")
        # dummy command to test if the step is running with the correct inputs and outputs
        os.makedirs(outdir, exist_ok=True)
        # create a dummy output file with correct extension
        with open(os.path.join(outdir, f"{sample}_1_val_1.fq"), "w") as f:
            f.write("dummy output file")
        with open(os.path.join(outdir, f"{sample}_2_val_2.fq"), "w") as f:
            f.write("dummy output file")
        return "sleep 10"
        # return cmd


class SALMON_QUANT(Step):
    INPUTS = {"trimmed_pair": [None, None], "index": None, "sample_name": None}
    OUTPUTS = {"quant_dir": "{outdir}/{sample_name}"}
    RESOURCE = Resource(cpu=8, mem=32, time=4)
    CONFIG = Config(
        image="/farmshare/user_data/khoang99/bios270/envs/bioinformatics_latest.sif",
        runtime="singularity",
        executor="slurm",
        binds=list(DEFAULT_BINDS),
    )
    PARAMS = {"outdir": "salmon"}

    def script(self) -> str:
        (r1, r2) = self.inputs()["trimmed_pair"]
        index = self.inputs()["index"]
        sample = self.inputs()["sample_name"]
        outdir = os.path.join(self.params["outdir"], sample)
        os.makedirs(outdir, exist_ok=True)

        self.outputs()["quant_dir"].val = outdir
        print(f"Running SALMON_QUANT: {sample} {index} {outdir} {r1} {r2}")
        os.makedirs(outdir, exist_ok=True)
        # create a dummy output file with correct extension
        with open(os.path.join(outdir, f"{sample}.sf"), "w") as f:
            f.write("dummy output file")
        # dummy command to test if the step is running
        return "sleep 10"
        # return f"salmon quant -i {index} -l A -1 {r1} -2 {r2} -o {outdir} --validateMappings"


class RNASeqFlow(Flow):
    def __init__(self, samplesheet_path: str, salmon_index: str):
        super().__init__()

        samples = self.parse_samplesheet(samplesheet_path)

        fastq_pairs = list(zip(samples["read1"].tolist(), samples["read2"].tolist()))
        sample_names = samples["sample"].tolist()

        self.raw_reads = Channel("raw_reads", val=fastq_pairs)
        self.sample_names = Channel("sample_names", val=sample_names)
        self.salmon_index = Channel("salmon_index", val=salmon_index)

        self.fastqc = FASTQC()
        self.trim = TRIM_GALORE()
        self.salmon = SALMON_QUANT()

        self.fastqc(fastq_pair=self.raw_reads, sample_name=self.sample_names)
        self.trim(fastq_pair=self.raw_reads, sample_name=self.sample_names)
        self.salmon(
            trimmed_pair=self.trim.outputs()["trimmed_pair"],
            index=self.salmon_index,
            sample_name=self.sample_names,
        )

        self.finalize()

    def parse_samplesheet(self, samplesheet_path: str) -> pd.DataFrame:
        df = pd.read_csv(samplesheet_path)
        return df

if __name__ == "__main__":
    flow = RNASeqFlow(
        samplesheet_path="test_data/samplesheet.csv",
        salmon_index="/farmshare/home/classes/bios/270/data/indexes/ecoli_transcripts_index",
    )
    flow.run(max_workers=4)