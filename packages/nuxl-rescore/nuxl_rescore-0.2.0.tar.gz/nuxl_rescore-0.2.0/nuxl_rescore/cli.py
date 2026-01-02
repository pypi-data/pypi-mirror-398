import os
import argparse
from .run import run_pipeline
from pathlib import Path


def build_parser():
    parser = argparse.ArgumentParser(prog="nuxl_rescore",
        description="NuXL rescoring pipeline"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run")

    p_run.add_argument(
        '-id', 
        type=str,
        required=False,
        help="Input file (idXML format) …",
        metavar='id'
    )
    p_run.add_argument(
        '-rt_model',
        type=str,
        required=False,
        default="DeepLC",
        metavar='rt_model'
    )
    p_run.add_argument(
        '-calibration',
        type=str,
        required=False,
        default=os.getcwd()+"/calibration_data/RNA_All.csv",
        metavar='calibration'
    )
    p_run.add_argument(
        '-model_path',
        type=str,
        required=False,
        default=os.getcwd()+"/RT_deeplc_model/generic_model/full_hc_Train_RNA_All",
        metavar='model_path'
    )
    p_run.add_argument(
        '-unimod',
        type=str,
        required=False,
        default=os.getcwd()+"/unimod/unimod_to_formula.csv",
        metavar='unimod'
    )
    p_run.add_argument(
        '-out',
        type=str,
        required=False,
        default=os.getcwd()+"/rescore_output/",
        metavar='out'
    )
    p_run.add_argument('-ms2pip', required=False, action='store_true')
    p_run.add_argument('-ms2pip_rescore', required=False, action='store_true')
    p_run.add_argument(
        '-perc_exec',
        type=str,
        required=False,
        default="percolator",
        metavar='perc_exec'
    )
    p_run.add_argument(
        '-perc_adapter',
        type=str,
        required=False,
        default="PercolatorAdapter",
        metavar='perc_adapter'
    )
    p_run.add_argument('-feat_out', required=False, action='store_true')
    p_run.add_argument('-ms2pip_path', type=str, required=False, default=None)
    p_run.add_argument('-ms2pip_rescore_path', type=str, required=False, default=None)
    p_run.add_argument('-mgf', type=str, required=False, default=None)
    p_run.add_argument('-peprec', type=str, required=False, default=None)
    p_run.add_argument(
        '-feat_config',
        type=str,
        required=False,
        default=os.getcwd()+"/features-config.json",
        metavar='feat_config'
    )
    p_run.add_argument('-entrap', required=False, action='store_true')
    p_run.add_argument(
        '-actual_db',
        type=str,
        required=False,
        default="None",
        metavar='actual_db'
    )
    p_run.add_argument('-plot_results', required=False, action='store_true')

    return parser

def run_from_CLI(args):
         
    if args.command == "run":

        out_dir = Path(args.out)

        # Create directory automatically if missing
        if not out_dir.exists():
            print("Ouput dir not exist!")
            out_dir.mkdir(parents=True, exist_ok=True)
            print("made dir at: ", out_dir)
            
        run_pipeline(_id=args.id, _calibration=args.calibration, _unimod=args.unimod, _feat_config=args.feat_config, _feat_out=args.feat_out,
        _model_path=args.model_path, _ms2pip=args.ms2pip, _ms2pip_path=args.ms2pip_path,
        _ms2pip_rescore=args.ms2pip_rescore, _ms2pip_rescore_path=args.ms2pip_rescore_path,
        _rt_model=args.rt_model, _entrap=args.entrap, _actual_db=args.actual_db, _out=args.out, _peprec_path=args.peprec, _mgf_path=args.mgf,
        _perc_exec=args.perc_exec, _perc_adapter=args.perc_adapter, _plot_results=args.plot_results
        )

