# -*- coding: UTF-8 -*-

import os
from typing import Optional, Literal, List

import pandas as pd
from pandas import DataFrame

from .. import util as ul
from ..util import chrtype

__name__: str = "preprocessing_gencode"

_Feature = Optional[Literal['UTR', 'transcript', 'exon', 'Selenocysteine', 'CDS', 'start_codon', 'gene', 'stop_codon']]


def get_gene_anno(
    feature: _Feature = None,
    gtf_file: Optional[str] = None,
    filter_chromatin: bool = True,
    columns: Optional[List[str]] = None,
) -> DataFrame:

    from gtfparse import read_gtf

    cache_path: str = os.path.join(ul.project_cache_path, "gencode")
    ul.file_method(__name__).makedirs(cache_path)

    _gtf_file_: str

    if gtf_file is not None:
        if not gtf_file.endswith("gtf") and not gtf_file.endswith("gtf.gz"):
            raise ValueError("GTF files must end with .gtf or .gtf.gz.")
        else:
            _gtf_file_ = gtf_file
    else:
        filename = os.path.join(ul.project_cache_path, "gencode.annotation.gtf.gz")
        ul.log(__name__).info(f"Downloading GTF file: {filename}")

        if not os.path.exists(filename):
            ul.file_method(__name__).download_file(
                url="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_46/gencode.v46.annotation.gtf.gz",
                filename=os.path.join(ul.project_cache_path, "gencode.annotation.gtf.gz")
            )

        _gtf_file_ = filename
        del filename

    del gtf_file

    ul.log(__name__).info("Read GTF file")
    gtf = read_gtf(_gtf_file_)
    data = pd.DataFrame(data=gtf, columns=gtf.columns)

    if feature is not None:
        data = data[data["feature"] == feature]

    if filter_chromatin:
        chr_list: list = list(chrtype.categories)
        data = data[data["seqname"].isin(chr_list)]

    _columns_: list[str] = ['seqname', 'source', 'feature', 'start', 'end', 'strand', 'gene_id', 'gene_type', 'gene_name']

    if columns is not None:
        _columns_ = columns

    data = data[_columns_]

    return data
