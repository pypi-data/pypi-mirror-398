# -*- coding: UTF-8 -*-

import sciv

if __name__ == '__main__':

    # The save path for process files and result files.
    save_path = "/path/result/data"
    # The save path for PoissonVI training model.
    poisson_vi_save_path = "/path/result/data/poisson_vi"
    cache_path = "/path/result/cache_path"
    log_path = "/path/result/log"

    # Path containing three files
    sc_atac_base_path = "/path/data/meta"
    # A folder for storing trait or disease files
    variant_base_path = "/path/data/variant"

    # set log information
    sciv.ul.is_form_log_file = True
    sciv.ul.log_file_path = log_path

    # set cache path
    sciv.ul.project_cache_path = cache_path

    # read variant information
    variants, trait_info = sciv.fl.read_variants(base_path=variant_base_path)

    # scATAC-seq data
    sc_atac = sciv.fl.read_sc_atac(resource=sc_atac_base_path)

    # run
    trs = sciv.ml.core(
        adata=sc_atac,
        variants=variants,
        trait_info=trait_info,
        model_dir=poisson_vi_save_path,
        save_path=save_path,
        is_file_exist_loading=True
    )

    print(trs)
