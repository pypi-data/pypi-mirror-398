import pandas as pd
from pyopenms import *
from pkg_resources import get_distribution

from .plotting import plot_weights_perc, comparison_PSMs, plot_FDR_plot
from .FDR_calculation import FDR_filtering_perc, run_percolator, FDR_unique_PSMs
from .Data_parser import peptide_ids_to_dataframe, read_pin_file, read_fasta, annotate_features
from .entrapment import entrapment_calculations
from .RT_features import predict_from_DeepLC, calculate_RTfeatures
from .ms2pip_features import Take_MS2PIP_features, Take_MS2PIP_rescore_features

import os
import warnings

# Ignore all UserWarnings
warnings.filterwarnings("ignore", category=UserWarning)
# Suppress TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def run_pipeline(_id=None, _calibration=None, _unimod=None, _feat_config=None, _feat_out=True,
    _model_path=None, _ms2pip=None, _ms2pip_path=None,
    _ms2pip_rescore=None, _ms2pip_rescore_path=None,
    _rt_model=None, _entrap=None, _actual_db=None, _out=None, _peprec_path=None, _mgf_path=None,
    _perc_exec=None, _perc_adapter=None, _plot_results=False
):
    """
    explicit function arguments when called as Python API.
    """

    #print(
    #f"""
    #Configuration:
    #_id: {_id}
    #_calibration: {_calibration}
    #_unimod: {_unimod}
    #_feat_config: {_feat_config}
    #_feat_out: {_feat_out}
    #_model_path: {_model_path}
    #_ms2pip: {_ms2pip}
    #_ms2pip_path: {_ms2pip_path}
    #_ms2pip_rescore: {_ms2pip_rescore}
    #_ms2pip_rescore_path: {_ms2pip_rescore_path}
    #_rt_model: {_rt_model}
    #_entrap: {_entrap}
    #_actual_db: {_actual_db}
    #_out: {_out}
    #_peprec_path: {_peprec_path}
    #_mgf_path: {_mgf_path},
    #_perc_exec: {_perc_exec}, 
    #_perc_adapter: {_perc_adapter}
    #_plot_results: {_plot_results}
    #    """
    #)

    print("==> idXML Loading")
    protein_ids = []
    peptide_ids = []
    IdXMLFile().load(_id, protein_ids, peptide_ids)

    # -----------------------------
    # RT FEATURES
    # -----------------------------
    RT_predictions_feat_df = None

    if _rt_model is not None:
        print("==> RT columns extracting")

        RT_id_cols = peptide_ids_to_dataframe(peptide_ids)

        if _rt_model == "DeepLC":
            calibration_data = pd.read_csv(_calibration)

            print("==> Taking from DeepLC model")
            RT_predictions = predict_from_DeepLC(RT_id_cols, unimod_path=_unimod, model_path=_model_path, calibration=calibration_data)
            RT_predictions_feat_df = calculate_RTfeatures(RT_predictions)

            print("==> Successfully extracted RT_features:", RT_predictions_feat_df.shape)
            RT_features_path = f"{_out}/RT_features.csv"
            RT_predictions_feat_df.to_csv(RT_features_path)

    if RT_predictions_feat_df is None:
        print("Warning: RT predictions not extracted. Use -rt_model DeepLC")

    # -----------------------------
    # MS2PIP INTENSITY FEATURES
    # -----------------------------
    MS2PIP_feat_df = None

    if _ms2pip:
        if _ms2pip_path is not None:
            MS2PIP_feat_df = pd.read_csv(_ms2pip_path)
        else:
            MS2PIP_path = Take_MS2PIP_features(id_file=_id, peprec_file=_peprec_path, mgf_file=_mgf_path, out_dir=_out, feat_config_path=_feat_config)
            MS2PIP_feat_df = pd.read_csv(MS2PIP_path)

        print("Successfully extracted MS2PIP_Features:", MS2PIP_feat_df.shape)

    else:
        print("Warning: MS2PIP intensity features disabled.")

    # -----------------------------
    # MS2RESCORE FEATURES
    # -----------------------------
    MS2PIP_rescore_feat_df = None

    if _ms2pip_rescore:
        if _ms2pip_rescore_path is not None:
            MS2PIP_rescore_feat_df = read_pin_file(_ms2pip_rescore_path)
        else:
            MS2PIP_rescore_feat_df = Take_MS2PIP_rescore_features(id_file=_id, peprec_file=_peprec_path, mgf_file=_mgf_path, out_dir=_out)

        print("Successfully extracted MS2PIP_rescore Features:",
              MS2PIP_rescore_feat_df.shape)

    else:
        print("Warning: MS2PIP_rescore features disabled.")

    # -----------------------------
    # ANNOTATE FEATURES & STORE NEW idXML
    # -----------------------------
    print("==> Annotating features in idXML file")

    prot_ids, pep_ids, extra_feat_names = annotate_features(
        _feat_config, _feat_out, _out, 
        protein_ids, peptide_ids,
        RT_predictions_feat_df,
        MS2PIP_feat_df,
        MS2PIP_rescore_feat_df
    )

    if _rt_model and _ms2pip:
        out_file = _id.split("/")[-1]
        Feat_idXML_out_path = f"{_out}/RT_Int_feat_{out_file}"
    
    elif _rt_model and _ms2pip == False:
        out_file = _id.split("/")[-1]
        Feat_idXML_out_path = f"{_out}/RT_feat_{out_file}"

    elif _ms2pip and _rt_model == None:
        out_file = _id.split("/")[-1]
        Feat_idXML_out_path = f"{_out}/Int_feat_{out_file}"
    
    else:
        out_file = _id.split("/")[-1]
        Feat_idXML_out_path = f"{_out}/updated_feat_{out_file}"

    IdXMLFile().store(Feat_idXML_out_path, prot_ids, pep_ids)
    print("==> Annotated idXML stored at:", Feat_idXML_out_path)

    # -----------------------------
    # PERCOLATOR
    # -----------------------------
    if _plot_results:
        print("==> Percolator and FDR without extra features")
        perc_result_file = run_percolator(_id, _perc_exec, _perc_adapter, _out)
        FDR_perc_file = FDR_filtering_perc(perc_result_file + '.idXML')

    print("==> Percolator and FDR with extra features")
    Feat_perc_result_file = run_percolator(
        Feat_idXML_out_path, _perc_exec, _perc_adapter, _out
    )

    if _plot_results:
        plot_weights_perc(Feat_perc_result_file + '.weights', extra_feat_names)

    print("==> FDR calculation with extra features")
    Feat_FDR_perc_file = FDR_filtering_perc(Feat_perc_result_file + '.idXML')

    # -----------------------------
    # ENTRAPMENT OR COMPARISON
    # -----------------------------
    if not _entrap:
        if _plot_results:
            print("==> Generating PseudoROC plots")
            comparison_PSMs(
                Feat_perc_result_file + '_0.0100_XLs.idXML',
                perc_result_file + '_0.0100_XLs.idXML'
            )

            XL_all = perc_result_file + '_1.0000_XLs.idXML'
            XL_feat_all = Feat_perc_result_file + '_1.0000_XLs.idXML'

            plot_FDR_plot(XL_all, XL_feat_all)

    else:
        actual = read_fasta(_actual_db)
        unq = FDR_unique_PSMs(perc_result_file + '.idXML')
        unq_feat = FDR_unique_PSMs(Feat_perc_result_file + '.idXML')
        entrapment_calculations(unq, unq_feat, actual)
        

'''def main():

    print("-----Configuation-----")
    for attr, value in vars(args).items():
        print(f"{attr}: {value}")

    if args.ms2pip and args.ms2pip_rescore : 
        print("Error! please select ms2rescore features or ms2pip intensity features or combine features like e-g RT+intensities or RT+ms2rescore")
    
    else :
        if args.ms2pip and args.ms2pip_path is None:
            ms2pip_curr_version = get_distribution("ms2pip").version
            ms2pip_desire_version = "3.11.0"
            print("ms2pip version: ", ms2pip_curr_version)
            if ms2pip_curr_version != ms2pip_desire_version :
                print("Error! ms2pip version ", ms2pip_desire_version , "required ", "For help, about dependencies see requirements.txt")
                print("Try pip install ms2pip==3.11.0")
            else: 
                run_pipeline()
        
        elif args.ms2pip_rescore and args.ms2pip_rescore_path is None:
            try:
                ms2pip_curr_version = get_distribution("ms2pip").version
                ms2rescore_curr_version = get_distribution("ms2rescore").version
                ms2pip_desire_version = "4.0.0.dev1"
                print("ms2pip version: ", ms2pip_curr_version)
                print("ms2rescore version: ", ms2rescore_curr_version)
                if int(ms2pip_curr_version[0]) != int(4):
                    print("Error! ms2pip desire version 4.0.0.dev1, .., 4.0.0.dev5")
                    print("For help, about dependencies see requirements.txt")
                elif int(ms2rescore_curr_version[0]) < int(3):
                    print("Error! ms2rescore desire version 3.0.b4")
                    print("For help, about dependencies see requirements.txt")
                else:
                    run_pipeline()
            
            except Exception as e:
                print("An error occurred:", e)
                print("For help, about dependencies see requirements.txt")
              
        else:
            run_pipeline()

            
    '''