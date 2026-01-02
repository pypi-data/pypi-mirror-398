import os
import pandas as pd
from deeplc.feat_extractor import FeatExtractor
from deeplc import DeepLC
  
def predict_from_DeepLC(peptides: pd.DataFrame, unimod_path: str, model_path: str, calibration: pd.DataFrame = None) -> list:
    """
    Make predictions based on a given peptide DataFrame and an optional
    calibration DataFrame using DeepLC.
    Args:
        peptides: pandas DataFrame with peptides contains columns need for predictions 
                  i-e ["seq", "modifications", "tr"] : DeepLC columns
        calibration: pandas DataFrame with calibration peptide hits (optional)
    """

    #extract all modifications 
    if os.path.isfile(unimod_path):
         features = FeatExtractor(unimod_path)
    else:
        print("Error!!! modification file not found at", unimod_path)
    
    dlc = DeepLC(
        path_model=[
            model_path+"_1fd8363d9af9dcad3be7553c39396960.hdf5",
            model_path+"_8c22d89667368f2f02ad996469ba157e.hdf5",
            model_path+"_cb975cfdd4105f97efa0b3afffe075cc.hdf5"
        ],
        f_extractor = features,
        pygam_calibration=True
        )

    if calibration is None:
        peptides["rt_pred"] = dlc.make_preds(seq_df=peptides, calibrate=False)
    else:
        dlc.calibrate_preds(seq_df=calibration)
        peptides["rt_pred"] = dlc.make_preds(seq_df=peptides) 
        

    return peptides  

def calculate_RTfeatures(feature_df: pd.DataFrame):

    """
    Calculate retention time features for rescoring (used in MS2PIP rescore)
    https://github.com/compomics/ms2rescore/blob/master/ms2rescore/plotting.py (for details)
    Args:
        feature_df: A Dataframe contains rt essential + prediction column 
        write_file: bool, to write RT feature file in out folder
    Returns:
        final_feature_df: A Dataframe contains rt essential + prediction column + RT features
    """ 
    
    # Absolute difference between observed and predicted'
    feature_df["observed_retention_time"] = feature_df["tr"]
    feature_df["predicted_retention_time"] = feature_df["rt_pred"]
    
    feature_df["rt_diff"] = (feature_df["observed_retention_time"] - feature_df["predicted_retention_time"]).abs()

    # Minimum RT difference for a peptidoform
    min_rt_diff = feature_df[
        [
            "sequence",
            "modifications",
            "observed_retention_time",
            "predicted_retention_time",
            "rt_diff",
        ]
    ].copy()
    
    
    min_rt_diff = (
        min_rt_diff.sort_values("rt_diff", ascending=True)
        .drop_duplicates(subset=["sequence", "modifications"], keep="first")
        .rename(
            columns={
                "rt_diff": "rt_diff_best",
                "observed_retention_time": "observed_retention_time_best",
                "predicted_retention_time": "predicted_retention_time_best",
            }
        )
    )

    # Merging minimum RT difference features to full set
    feature_df = feature_df.merge(
        min_rt_diff, on=["sequence", "modifications"], how="left"
    )
            
    RT_feature_columns = [
        "spec_id",
        "rank",
        "sequence",
        "modifications",
        "observed_retention_time",
        "predicted_retention_time",
        "rt_diff",
        "rt_diff_best",
        "observed_retention_time_best",
        "predicted_retention_time_best",
    ]
    
    final_feature_df = feature_df[RT_feature_columns]
    
    return final_feature_df
    
