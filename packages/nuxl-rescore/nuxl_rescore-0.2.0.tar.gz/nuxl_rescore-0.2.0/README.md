# NuXL_rescore

This repository created for percolator base rescoring investigations of protein-nucleic acid crosslinking protocols
with the addition of retention time prediction features from fine-tuned deepLC models and predictions of MS2PIP base peak intensity features.<br />
Siraj, A., Bouwmeester, R., Declercq, A., Welp, L., Chernev, A., Wulf, A., ... & Sachsenberg, T. (2024). Intensity and retention time prediction improves the rescoring of protein‐nucleic acid cross‐links. Proteomics, 24(8), 2300144.
[https://doi.org/10.1002/pmic.202300144](https://doi.org/10.1002/pmic.202300144)


---

- [Usage](#usage)
- [Feature configurations](#Feature-configuration) 
- [Output](#Output)
- [Fine tunning and feature extraction](#Fine-tunning-and-feature-extraction)
- [Run example script](#Run-example-script)

---

## Usage

### Command line interface

```
usage: nuxl_rescore run [-h] [-id id] [-rt_model rt_model] [-calibration calibration] [-model_path model_path]
                        [-unimod unimod] [-out out] [-ms2pip] [-ms2pip_rescore] [-perc_exec perc_exec]
                        [-perc_adapter perc_adapter] [-feat_out] [-ms2pip_path MS2PIP_PATH]
                        [-ms2pip_rescore_path MS2PIP_RESCORE_PATH] [-mgf MGF] [-peprec PEPREC] [-feat_config feat_config]
                        [-entrap] [-actual_db actual_db] [-plot_results]

options:
  -h, --help            show this help message and exit
  -id id                Input file (idXML format) …
  -rt_model rt_model    if None no RT feature consider
  -calibration calibration DeepLC calibration data path (.csv)
  -model_path model_path  model path with name like full_hc_Train_RNA_All
  -unimod unimod  unimod/NuXL modification example /unimod/unimod_to_formula.csv
  -out out output folder path
  -ms2pip               Extract ms2pip features {bool}
  -ms2pip_rescore       Extract ms2pip_rescore features {bool}
  -perc_exec perc_exec  percolater executable path (Full path)
  -perc_adapter perc_adapter
                        percolater Adapter path (Full path)
  -feat_out             Write all extra feature output file at Out-folder (.csv)
  -ms2pip_path ms2pip_path
                        MS2PIP features file path (.csv file)
  -ms2pip_rescore_path ms2pip_rescore_path
                        MS2PIP rescore features file path (.pin file)
  -mgf mgf              Path for mgf file (.mgf file) need for MS2Rescore if results files not given
  -peprec peprec        Path for peprec (.peprec file) need for MS2Rescore if file not given generate from idXML
  -feat_config feat_config
                        Path for feature config (.json file) need for features used for rescoring
  -entrap               Entrapment testing {bool}
  -actual_db actual_db  Path for database (.fasta file) actual protein correspond to actual protocol
  -plot_results Plots PseudoROC comparison plot, percolator weight plot {bool}

```
### What format of file should be given for analysis? <br />
&emsp;[.idXML](https://pyopenms.readthedocs.io/en/latest/user_guide/identification_data.html) format of identification file<br />
For extraction of MS2PIP intensities or MS2Rescore features<br />
&emsp;[.peprec](https://psm-utils.readthedocs.io/en/v0.3.0/api/psm_utils.io/) if not given, will generated from idXML<br />
&emsp;[.mgf](https://abibuilder.cs.uni-tuebingen.de/archive/openms/Documentation/release/2.7.0/html/TOPP_FileConverter.html) require <br />
If already MS2Rescore features extracted <br />
&emsp;[.pin](https://github.com/compomics/ms2rescore) MS2Rescore feature file <br />

### How to do different analysis? <br />
#### Used only retention time features in rescoring<br />
&emsp;```nuxl_rescore run -id -model_path -unimod -calibration -perc_exec -perc_adapter -out``` <br />

#### Used only intensity features in rescoring<br />
&emsp;```nuxl_rescore run -id -rt_model None -perc_exec -perc_adapter -out -ms2pip (store_true) -ms2pip_path  or -mgf``` <br /> 

#### Used only MS2Rescore features in rescoring<br />
&emsp;```nuxl_rescore run -id -rt_model None -perc_exec -perc_adapter -out -ms2pip_rescore (store_true) -ms2pip_rescore_path  or -mgf``` <br /> 

#### *will work for adaptation of multiple features e-g RT+intensities as <br /> 
&emsp;```nuxl_rescore run -id model_path -calibration -unimod -perc_exec -perc_adapter -out -ms2pip (store_true) -ms2pip_path  or -mgf``` <br />

#### entrapment testing <br />
&emsp;```nuxl_rescore run.py -entrap (store_true) -actual_db (actual database of sample)``` <br />

## Feature configuration

The corresponding features can be update from features-config.json
```{"features":
  { 
  "RT_features": ["rt_diff", "rt_diff_best", "observed_retention_time_best", "predicted_retention_time_best"],
  "MSPIP_features":["ions_series", "ions_mz", "ions_pred", "ions_targ"],
  "//comment": "ions extract from MSPIP_features with no. of ions_b, ions_y e-g b1, b2, b3 & y1, y2, y3",
  "ions_b":3, 
  "ions_y":3, 
  "//comment": "specify in intensities so, it will extract correspondings _pred: predictions ; _targ: Target ; _diff: Target - predictions; _mz: M/Z of intensities of ions, if want all feat leave empty, b_y_corr compulsory",
  "intensities":["b_y_corr"],
  "//comment": "please specify, if want to use all ions intensity correlation or not", 
  "corr_all": false,
  "MSPIP_rescore_features":["spec_pearson_norm", "ionb_pearson_norm", "iony_pearson_norm", "spec_mse_norm", "ionb_mse_norm", 
                            "iony_mse_norm", "min_abs_diff_norm",	"max_abs_diff_norm", "abs_diff_Q1_norm", 
                            "abs_diff_Q2_norm", "abs_diff_Q3_norm", "mean_abs_diff_norm", "std_abs_diff_norm",
                           	"ionb_min_abs_diff_norm", "ionb_max_abs_diff_norm", "ionb_abs_diff_Q1_norm", 
                            "ionb_abs_diff_Q2_norm", "ionb_abs_diff_Q3_norm", "ionb_mean_abs_diff_norm", 
                            "ionb_std_abs_diff_norm",	"iony_min_abs_diff_norm", "iony_max_abs_diff_norm", 
                            "iony_abs_diff_Q1_norm", "iony_abs_diff_Q2_norm", "iony_abs_diff_Q3_norm", 
                            "iony_mean_abs_diff_norm",	"iony_std_abs_diff_norm", "dotprod_norm", "dotprod_ionb_norm",
                            "dotprod_iony_norm", "cos_norm", "cos_ionb_norm", "cos_iony_norm", "spec_pearson",	
                            "ionb_pearson", "iony_pearson", "spec_spearman", "ionb_spearman", "iony_spearman", 
                            "spec_mse", "ionb_mse", "iony_mse", "min_abs_diff_iontype",	"max_abs_diff_iontype", 
                            "min_abs_diff", "max_abs_diff", "abs_diff_Q1", "abs_diff_Q2", "abs_diff_Q3", "mean_abs_diff", 
                            "std_abs_diff", "ionb_min_abs_diff",	"ionb_max_abs_diff", "ionb_abs_diff_Q1", "ionb_abs_diff_Q2", 
                            "ionb_abs_diff_Q3", "ionb_mean_abs_diff", "ionb_std_abs_diff", "iony_min_abs_diff", 
                            "iony_max_abs_diff", "iony_abs_diff_Q1", "iony_abs_diff_Q2", "iony_abs_diff_Q3", "iony_mean_abs_diff", 
                            "iony_std_abs_diff", "dotprod", "dotprod_ionb", "dotprod_iony", "cos", "cos_ionb",	"cos_iony"],
  "//comment": "modification for ms2pip e-g Carbamidomethyl,57.021464,opt,C ",
  "ms2pip_mod":["Oxidation,15.994915,opt,M"] 
  }
}

```

## Output
### Rescoring analysis output
#### Not included any extra features in rescoring  <br /> 
&emsp;1% XL FDR XLs and peptides output (will be the same name of input file name)<br /> 
##### Included extra features in rescoring  <br /> 
&emsp;1% XL FDR XLs and peptides output (start with updated_ input file name)<br /> 
#### Extra file  <br />
&emsp; All_extra_features.csv, percolator.weights, percolator feature plot, 1% XL FDR report (.csv)<br /> 
*All identifications ouput files will be in .idXML format  <br /> 

## Fine tunning and feature extraction
### Fine tunning for protein-RNA XL protocols
we fine tunned one generic and four specific models (4SU, UV, NM, and DEB) with the help [DeepLCRetrainer](https://github.com/RobbinBouwmeester/DeepLCRetrainer)<br />
The set of three models are used to finetunned for protein-RNA crosslinking protocols as <br />
```
models = deeplcretrainer.retrain(
    [df_train_file], #traning file DeepLC format
    mods_transfer_learning=[
        base_model +"/full_hc_train_1fd8363d9af9dcad3be7553c39396960.hdf5",
        base_model +"/full_hc_train_8c22d89667368f2f02ad996469ba157e.hdf5",
        base_model +"/full_hc_train_cb975cfdd4105f97efa0b3afffe075cc.hdf5"
    ],
    #other hyper parameters
)

```
### Taking predictions from fine-tunned model
The set of three fine tunned models are used to take predictions from generic/specific models with the help of [DeepLC](https://github.com/compomics/DeepLC) as <br />
```
dlc = DeepLC(
        path_model=[
                generic_model + "/full_hc_Train_RNA_All_1fd8363d9af9dcad3be7553c39396960.hdf5",
                generic_model + "/full_hc_Train_RNA_All_8c22d89667368f2f02ad996469ba157e.hdf5",
                generic_model + "/full_hc_Train_RNA_All_cb975cfdd4105f97efa0b3afffe075cc.hdf5"
        ]
        
)

```
## Intensities and MS2Rescore feature
we extract the MS2PIP intensities and MS2Rescore features from [MS2Rescore](https://github.com/compomics/ms2rescore) repository, the config file as <br />
```
CONFIG = {  'ms2rescore': 
                {   'tmp_path': '', 
                    'spectrum_path': mgf_file, 
                    'output_path': out_pin_file,
                    'psm_file': psm_file,
                    'psm_id_pattern': None, 
                    'spectrum_id_pattern': ".*_(controllerType=0 controllerNumber=1 scan=[0-9]+)_.*", 
                    'num_cpu': 32}, 
                'ms2pip': {
                    'model': 'HCD', 
                    'frag_error': 0.02}
        }
```
## Run example script
Can run the nuxl_rescore pipline from example_script/run_rescore_pipeline.py. it will automatically download the nuxl_rescore resources and example files. </br> here is the example files and nuxl_rescore resources: https://github.com/Arslan-Siraj/NuXL_rescore_resources/tree/main

