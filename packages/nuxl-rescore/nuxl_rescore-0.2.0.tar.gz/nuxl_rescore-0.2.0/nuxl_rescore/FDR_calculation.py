import os 
import sys
import subprocess
import pandas as pd
from pyopenms import *
from pathlib import Path

def FDR_filtering_perc(perc_result_path: str):
    """
    Calculate FDR and generate FDR controlled file 1%, 100% FDR (percolator results)
    Args:
        perc_result_path: percolator result path 
    Returns:
        outfile_path[0]: output file path 
    """ 

    print("==> FDR filtering percolator results")
    perc_proteins = []
    perc_peptides = []
  
    IdXMLFile().load(perc_result_path, perc_proteins, perc_peptides)
    
    pept_IDFilter = IDFilter()
    pept_IDFilter.keepBestPeptideHits(perc_peptides, True) #keep the best hit only if its score is unique
            
    XL_peptides = []
    nonXL_peptides = []
    for pep_id in perc_peptides:
        for hit in pep_id.getHits():
            if(hit.getMetaValue("NuXL:isXL")): 
               XL_peptides.append(pep_id)
            else:
               nonXL_peptides.append(pep_id)
    
    # calculate 100% XL FDR
    XL_peptides_ =XL_peptides.copy()
    fdr = FalseDiscoveryRate()
    fdr.apply(XL_peptides_)
    idfilter = IDFilter()
    idfilter.filterHitsByScore(XL_peptides_, 1.0)
    #idfilter.keepBestPeptideHits(XL_peptides_, True)
    idfilter.removeDecoyHits(XL_peptides_)
    idfilter.removeEmptyIdentifications(XL_peptides_)
    
    perc_proteins_ = perc_proteins.copy()
    idfilter.removeUnreferencedProteins(perc_proteins_, XL_peptides_)
    
    print("length of XLs at 100% CSM: ", len(XL_peptides_))
    
    outfile_path = perc_result_path.split(".")
    IdXMLFile().store(outfile_path[0] + "_1.0000_XLs.idXML", perc_proteins_, XL_peptides_)
    print("Written 100% XL FDR idXML perc file: ", outfile_path[0] + "_1.0000_XLs.idXML")
    
    # calculate 1% XL FDR 
    fdr = FalseDiscoveryRate()
    fdr.apply(XL_peptides)
    idfilter = IDFilter()
    #idfilter.keepBestPeptideHits(XL_peptides, True)
    idfilter.filterHitsByScore(XL_peptides, 0.01)
    idfilter.removeDecoyHits(XL_peptides)
    idfilter.removeEmptyIdentifications(XL_peptides)
    
    '''pept_IDFilter = IDFilter()
    pept_IDFilter.keepBestPeptideHits(XL_peptides, True) #keep the best hit only if its score is unique
    
    outfile_path = perc_result_path.split(".")
    IdXMLFile().store(outfile_path[0] + "_0.0100_XLs_test.idXML", perc_proteins_XL, XL_peptides)
    print("Written 1% XL FDR idXML perc file: ", outfile_path[0] + "_0.0100_XLs.idXML")'''
    
    perc_proteins_XL = perc_proteins.copy()
    idfilter.removeUnreferencedProteins(perc_proteins_XL, XL_peptides)
    
    print("length of XLs at 1% CSM: ", len(XL_peptides))
    
    outfile_path = perc_result_path.split(".")
    IdXMLFile().store(outfile_path[0] + "_0.0100_XLs.idXML", perc_proteins_XL, XL_peptides)
    print("Written 1% XL FDR idXML perc file: ", outfile_path[0] + "_0.0100_XLs.idXML")
     
    # calculate 100% nonXL FDR peptides
    '''nonXL_peptides_ = nonXL_peptides.copy()
    fdr.apply(nonXL_peptides_)
    idfilter = IDFilter()
    idfilter.filterHitsByScore(nonXL_peptides_, 1.0)
    idfilter.removeDecoyHits(nonXL_peptides_)
    idfilter.removeEmptyIdentifications(nonXL_peptides_)
    
    perc_proteins_1 = perc_proteins.copy()
    idfilter.removeUnreferencedProteins(perc_proteins_1, nonXL_peptides_)
    
    print("length of peptides at 100% CSM: ", len(nonXL_peptides_), "\n")
    
    IdXMLFile().store(outfile_path[0] + "_1.0000_peptides.idXML", perc_proteins_1, nonXL_peptides_)
    print("Written 100% nonXL FDR idXML perc file: ", outfile_path[0] + "_1.0000_peptides.idXML")'''
    
    # calculate 1% nonXL FDR peptides
    fdr.apply(nonXL_peptides)
    idfilter = IDFilter()
    idfilter.filterHitsByScore(nonXL_peptides, 0.01)
    idfilter.removeDecoyHits(nonXL_peptides)
    idfilter.removeEmptyIdentifications(nonXL_peptides)
    
    idfilter.removeUnreferencedProteins(perc_proteins, nonXL_peptides)
    
    print("length of peptides at 1% CSM: ", len(nonXL_peptides), "\n")
    
    IdXMLFile().store(outfile_path[0] + "_0.0100_peptides.idXML", perc_proteins, nonXL_peptides)
    print("Written 1% nonXL FDR idXML perc file: ", outfile_path[0] + "_0.0100_peptides.idXML")
    
    
    return outfile_path[0]

def FDR_unique_PSMs(perc_result_path: str):
    """
    Calculate FDR and keep the unique peptide per protein, genrate the unique PSMs file
    Args:
        perc_result_path: percolator result path 
    Returns:
        outfile_path[0]: output file path 
    """ 
    perc_proteins = []
    perc_peptides = []

    IdXMLFile().load(perc_result_path, perc_proteins, perc_peptides)

    pept_IDFilter = IDFilter()
    pept_IDFilter.keepBestPeptideHits(perc_peptides, True) #keep the best hit only if its score is unique
            
    XL_peptides = []
    nonXL_peptides = []
    for pep_id in perc_peptides:
        for hit in pep_id.getHits():
            if(hit.getMetaValue("NuXL:isXL")):
                XL_peptides.append(pep_id)
            else:
                nonXL_peptides.append(pep_id)


    # calculate 100% XL FDR
    XL_peptides_ =XL_peptides.copy()
    idfilter = IDFilter()
    idfilter.keepUniquePeptidesPerProtein(XL_peptides_)
    fdr = FalseDiscoveryRate()
    fdr.apply(XL_peptides_)

    idfilter.filterHitsByScore(XL_peptides_, 1.0)
    idfilter.removeDecoyHits(XL_peptides_)
    idfilter.removeEmptyIdentifications(XL_peptides_)

    perc_proteins_ = perc_proteins.copy()
    idfilter.removeUnreferencedProteins(perc_proteins_, XL_peptides_)

    print("length of unique XLs at 100% CSM: ", len(XL_peptides_), "\n")
    print("length of unique non-XLs at 100% CSM: ", len(nonXL_peptides), "\n")

    outfile_path = perc_result_path.split(".")
    IdXMLFile().store(outfile_path[0] + "_unique_1.0000_XLs.idXML", perc_proteins_, XL_peptides_)
    print("file Written 100% XL unique FDR idXML perc file: ", outfile_path[0] + "_unique_1.0000_XLs.idXML")

    return  outfile_path[0] + "_unique_1.0000_XLs.idXML"

def run_percolator(infile: str, perc_path: str, percadapter_path: str, out_dir: str):
    """
    Perform rescoring with Percolator.

    Parameters
    ----------
    infile : str
        Path to idXML file containing identifications with added meta-values.
    perc_path : str
        Path to the Percolator executable.
    percadapter_path : str
        Path to the OpenMS PercolatorAdapter executable.
    out_dir : str
        Output directory.
    """

    infile = Path(infile).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = infile.stem

    out_idxml = out_dir / f"{stem}_perc.idXML"
    out_pin = out_dir / f"{stem}_perc_pin.tab"
    out_weights = out_dir / f"{stem}_perc.weights"

    print("==> Running Percolator")
    percadapter_command = [
        percadapter_path,
        "-in", str(infile),
        "-out", str(out_idxml),
        "-percolator_executable", perc_path,
        "-out_pin", str(out_pin),
        "-weights", str(out_weights),
        "-train_best_positive",
        "-unitnorm",
        "-post_processing_tdc",
        "-score_type", "svm",
    ]

    subprocess.run(percadapter_command, check=True)

    return str(out_dir / f"{stem}_perc")
