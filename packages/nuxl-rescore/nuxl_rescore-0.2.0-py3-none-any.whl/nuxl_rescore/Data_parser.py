import pandas as pd
import json
import re
import math
from Bio import SeqIO
import numpy as np
from scipy.stats import pearsonr
from functools import reduce

def read_pin_file(file_name:str ):
    """
    read pin file: MS2rescore feature file
    Returns:
      dataframe of pin file
    """
    file = open(file_name, 'r')
    Lines = file.readlines()

    Lines_sp = []
    for i in Lines:
        x = i.split('\t')
        Lines_sp.append(x)
    Lines_df = pd.DataFrame(Lines_sp)
    Lines_df.columns = Lines_df.iloc[0]
    Lines_df_ = Lines_df.drop([0])
    Lines_df_.reset_index(drop=True, inplace=True)
    spectra_ids = list(Lines_df_['SpecId'])
    
    rank = 0
    rank_list = []
    PSMid_temp = spectra_ids[0] 

    for i in spectra_ids:
      if(i == PSMid_temp):
        rank_list.append(rank)
        rank = rank +1
      else:
        rank = 0 
        PSMid_temp = i 
        rank_list.append(rank) 
        rank = rank +1
        
    Lines_df_['rank'] = rank_list
    Lines_df_.rename(columns = {'SpecId':'spec_id'}, inplace = True)
    return Lines_df_


def read_features_config(file_: str):
    """
    read feature-config file
    Returns:
      all features setting provided in config file
    """
    with open(file_, 'r') as f:
        Feature = json.load(f)

    rt_features = Feature["features"]["RT_features"]
    ms2pip_features = Feature["features"]["MSPIP_features"]
    b_ions = Feature["features"]["ions_b"]
    y_ions = Feature["features"]["ions_y"]
    corr_all = Feature["features"]["corr_all"]
    intensities_feat = Feature["features"]["intensities"]
    ms2pip_rescore_features = Feature["features"]["MSPIP_rescore_features"]
    ms2pip_mod= Feature["features"]["ms2pip_mod"]
    return rt_features, ms2pip_features, b_ions, y_ions, corr_all, intensities_feat, ms2pip_rescore_features , ms2pip_mod
    
    
def read_fasta(file_: str):
    """
    read fasta file
    Returns:
      protein ID list of all sequences
    """
    prot_ls = []
    fasta_sequences = SeqIO.parse(open(file_),'fasta')
    for fasta in fasta_sequences:
        prot_id, sequence = fasta.id, str(fasta.seq)
        prot_ls.append(prot_id)
    return prot_ls
   
def peptide_ids_to_dataframe(pep_ids: list) -> pd.DataFrame:
    """
    Parse a given list of peptide identification to a pandas DataFrame compatible with DeepLC.
    See https://github.com/compomics/DeepLC input-files for more information.
    Args:
        pep_ids: List containing PeptideIdentification
    Returns:
        pandas DataFrame contains columns needed for DeepLC
    """
    # ["seq", "modifications", "tr"] : DeepLC columns
    # ["sequence", "mod_sites", "nAA", "mods", "rt_norm"] : Alphapeptdeep columns

    columns = ["seq", "spec_id", "rank", "modifications", "tr", "sequence","NA_modification", "nAA", "mod_sites","mods", "rt_norm"]
    sequences = []
    spec_id = []
    rank = []
    modifications = []
    tr = []
    mod_seq_ls = []
    XL_loc_ls = []
    nAA_ls = []
    mod_site_ls = []
    mods_ls = []
    NA_modification_ls = []
    
    for pep_id in pep_ids:
        rt = pep_id.getRT()
        #id_ = pep_id.getIdentifier()
        rank_ = 0;
        for hit in pep_id.getHits():
            seq = hit.getSequence()
            mod_seq_ls.append(hit.getSequence())
            rank.append(rank_)
            sequences.append(seq.toUnmodifiedString())
            nAA_ls.append(len(seq.toUnmodifiedString()))
            tr.append(rt)
            spec_id.append(pep_id.getMetaValue('spectrum_reference'))
            hit_mods = []
            XL_loc = hit.getMetaValue("NuXL:best_localization_position")
            XL_NA = hit.getMetaValue("NuXL:NA")
            isXL = hit.getMetaValue("NuXL:isXL")
            rank_ = rank_ +1
           
            NA_modification_ls.append(hit.getMetaValue("NuXL:NA"))

            if(XL_loc == -1 and isXL == True):
                XL_loc = int(len(seq.toUnmodifiedString())/2)
            
            for pos in range(0, seq.size()):
                residue = seq.getResidue(pos)
                if residue.isModified():
                        hit_mods.append("|".join([str(pos + 1), residue.getModificationName()]))
                        
            fixed_mod = "|".join(hit_mods)

            if(XL_loc != -1):
                if(fixed_mod == ""):
                    NA_Fixed_mod = "|".join([str(XL_loc), XL_NA+'@RNA_XL']) 
                    modifications.append(NA_Fixed_mod)
                    mod_site_ls.append(str(XL_loc))
                    mods_ls.append(str(XL_NA+'@RNA_XL'))
                else:
                    fixed_NA_mod_ = fixed_mod +"|"+"|".join([str(XL_loc), XL_NA+'@RNA_XL']) 
                    fixed_mod_list = fixed_NA_mod_.split("|")
                    mod_names = []
                    mod_sites = []
                    hit_NA_mod = []
                    for i in range(0,len(fixed_mod_list)-1, 2):
                        mod_sites.append(int(fixed_mod_list[i]))
                        mod_names.append(fixed_mod_list[i+1])

                    mod_sites_sort, mod_names_sort = zip(*sorted(zip(mod_sites, mod_names)))
                    
                    alpha_sites =[]
                    alpha_mods = []
                    for m_site, m_name in zip(mod_sites_sort, mod_names_sort):
                        hit_NA_mod.append("|".join([str(m_site), m_name]))
                        alpha_sites.append(str(m_site))
                        if (m_name == "Oxidation"):
                            alpha_mods.append("Oxidation@M")
                        elif (m_name == "Carbamidomethyl"):
                            alpha_mods.append("Carbamidomethyl@C")
                        else:
                            alpha_mods.append(m_name)

                    modifications.append("|".join(hit_NA_mod))
                    mod_site_ls.append(";".join(alpha_sites))
                    mods_ls.append(";".join(alpha_mods))
            else:
                modifications.append(fixed_mod)
                alpha_sites =[]
                alpha_mods = []
                fixed_mod_list_ = fixed_mod.split("|")
                for i in range(0,len(fixed_mod_list_)-1, 2):
                        alpha_sites.append(str(fixed_mod_list_[i]))
                        m_name = str(fixed_mod_list_[i+1])
                        if ( m_name == "Oxidation"):
                            alpha_mods.append("Oxidation@M")
                        elif (m_name == "Carbamidomethyl"):
                            alpha_mods.append("Carbamidomethyl@C")
                        else:
                            alpha_mods.append(m_name)

                mod_site_ls.append(";".join(alpha_sites))
                mods_ls.append(";".join(alpha_mods))

            XL_loc_ls.append(int(XL_loc))

    data = {
        "seq": sequences,
        "spec_id": spec_id,
        "rank": rank,
        "modifications": modifications,
        "tr": tr,
        "sequence": sequences,
        "NA_modification": NA_modification_ls,
        "nAA": nAA_ls,
        "mod_sites": mod_site_ls,
        "mods": mods_ls,
        "rt_norm": tr,
    }
    #print("write in file for test...")
    #x = pd.DataFrame(data, columns=columns)
    #x.to_csv("test_RT.csv")
    return pd.DataFrame(data, columns=columns)

def pearson_correlation(x, y):
    """
    calculate pearson correlation
    Returns:
      correlation cofficient
    """

    x_mean = np.mean(x)
    y_mean = np.mean(y)

    x_std = np.std(x)
    y_std = np.std(y)

    epsilon = 1e-9  
    x_std += epsilon
    y_std += epsilon

    cov = np.cov(x, y, ddof=0)[0, 1]
    corr_coef = cov / (x_std * y_std)

    return corr_coef
    
def filter_str(string_):
    pattern = r'[[]'
    x = re.sub(pattern, '', string_)
    #print("filtered: ", x) 
    return x.replace("]", "")

def extract_intensities(MS2PIP_feat_df, b_ions, y_ions, corr_all: False):
    """
    Extract ms2pip intensties according to b_ions, y_ions specify in config
    MS2PIP_feat_df: Dataframe of intensities format ms2pip_features.py Take_MS2PIP_features()
    b_ions/y_ions: specify prefix/suffix ions
    return:
      intensities features, header of dataframe
    """
    MSPIP_features = ["ions_series", "ions_mz", "ions_pred", "ions_targ"]

    MSPIP_feat = []
    len_ions = list(MS2PIP_feat_df['ions_series'].str.split(','))
    len_ions_ = [len(value) for value in len_ions]
    max_b_y = int(min(len_ions_)/2)
    if (b_ions>max_b_y) or (y_ions>max_b_y):
        print("Error: Please check the ions_b and ions_y max can be:", max_b_y)
    else:
        for index, row in MS2PIP_feat_df.iterrows():
            #print("----b_ions----")
            #print(row["spec_id"])
            feat_list = []
            #feat_list.append(row["spec_id"])
            ions_series = row['ions_series'].split(',')
            ions_mz = row["ions_mz"].split(',')
            ions_pred = row['ions_pred'].split(',')
            ions_targ = row["ions_targ"].split(',')
            
            b_targ_ = []
            b_pred_ = []
            for b in range(b_ions):
                #feat_list.append(filter_str(ions_series[b]))
                feat_list.append(float(filter_str(ions_mz[b])))
                b_pred = float(filter_str(ions_pred[b]))
                feat_list.append(b_pred)
                b_pred_.append(b_pred)
                b_targ = float(filter_str(ions_targ[b]))
                b_targ_.append(b_targ)
                feat_list.append(b_targ)
                b_diff = abs(b_targ - b_pred)
                feat_list.append(b_diff) 
                
            y_targ_ = []
            y_pred_ = []
            for y in range(int(len(ions_series)/2), y_ions+int(len(ions_series)/2)):
                #feat_list.append(filter_str(ions_series[y]))
                feat_list.append(float(filter_str(ions_mz[y])))
                y_pred = float(filter_str(ions_pred[y]))
                feat_list.append(y_pred)
                y_pred_.append(y_pred)
                y_targ = float(filter_str(ions_targ[y]))
                feat_list.append(y_targ)
                y_targ_.append(y_targ)
                y_diff = abs(y_targ - y_pred)
                feat_list.append(y_diff)
            
            if corr_all:
              # all ions correlation consideration 
              b_ions_pred = np.array([float(filter_str(x)) for x in ions_pred[:len(ions_pred)//2]])
              y_ions_pred = np.array([float(filter_str(x)) for x in ions_pred[len(ions_pred)//2:]])
              b_ions_targ = np.array([float(filter_str(x)) for x in ions_targ[:len(ions_targ)//2]])
              y_ions_targ = np.array([float(filter_str(x)) for x in ions_targ[len(ions_targ)//2:]])
      
              b_corr_coef, __ = pearsonr(b_ions_pred, b_ions_targ)
              y_corr_coef, __ = pearsonr(y_ions_pred, y_ions_targ)

            else:
              b_corr_coef = pearson_correlation(np.array(b_pred_), np.array(b_targ_))
              y_corr_coef = pearson_correlation(np.array(y_pred_), np.array(y_targ_))
          
            feat_list.append(max(b_corr_coef, y_corr_coef))
            MSPIP_feat.append(feat_list)
    
    #print("# of both nan correlations found: ", both_corr_nan)
    header = []
    if len(MSPIP_feat)!=0:
        len_col = len(MSPIP_feat[0])
        #header.append("spec_id")
        for b in range(b_ions):
            #header.append("b"+str(b+1))
            header.append("b"+str(b+1)+"_mz")
            header.append("b"+str(b+1)+"_pred")
            header.append("b"+str(b+1)+"_targ")
            header.append("b"+str(b+1)+"_diff")
        for y in range(b_ions):
            #header.append("y"+str(y+1))
            header.append("y"+str(y+1)+"_mz")
            header.append("y"+str(y+1)+"_pred")
            header.append("y"+str(y+1)+"_targ")
            header.append("y"+str(y+1)+"_diff")
            
        header.append("b_y_corr")

    if (len(header)!=0 and len(MSPIP_feat)!=0):
        MSPIP_df = pd.DataFrame(MSPIP_feat, columns= header) 
    
    MSPIP_df['spec_id'] = MS2PIP_feat_df['spec_id']
    MSPIP_df['rank'] = MS2PIP_feat_df['rank']
    
    return MSPIP_df, header

def Conversion_to_DF(file_name):
    """
    convert the (.mzTab) format results to the dataframe format
    In: mzTab file 
    Return: Desriptions, Proteins, PSMs DataFrame
    """
    full_file_name = file_name
    print(full_file_name)
    file1 = open(full_file_name, 'r')
    Lines = file1.readlines()
    
    lines = len(Lines)
    indices = [index for index, element in enumerate(Lines) if element == "\n"]

    MetaValue = Lines[0:indices[0]]
    Proteins = Lines[indices[0]+1:indices[1]]
    PSMs = Lines[indices[1]+1:lines]

    MetaValue_sp = []
    for i in MetaValue:
        x = i.split('\t')
        MetaValue_sp.append(x)
    Desc_df = pd.DataFrame(MetaValue_sp)

    Proteins_sp = []
    for i in Proteins:
        x = i.split('\t')
        Proteins_sp.append(x)
    Proteins_df_ = pd.DataFrame(Proteins_sp)

    PSMs_sp = []
    for i in PSMs:
        x = i.split('\t')
        PSMs_sp.append(x)
    PSMs_df_ = pd.DataFrame(PSMs_sp)

    Proteins_df_.columns = Proteins_df_.iloc[0]
    Proteins_df= Proteins_df_.drop([0])

    PSMs_df_.columns = PSMs_df_.iloc[0]
    PSMs_df= PSMs_df_.drop([0])

    return Desc_df, Proteins_df, PSMs_df 
    
    
def annotate_features(feature_config_path: str, feature_out: bool, out_dir: str, prot_ids: list, pep_ids: list, RT_feature: pd.DataFrame = None, MS2PIP_feature: pd.DataFrame = None, MS2PIP_rescore_feature: pd.DataFrame = None) -> list:
    """
    Adds a custom meta value containing the RT predictions, intensities features.
    Args:
        feature_config_path: str: path to feature config file
        prot_ids:       protein identifications
        pep_ids:        peptide identifications
        RT_feature:     A Dataframe RT predictions features
        MS2PIP_feature: A Dataframe contains intensities
        MS2PIP_rescore_feature: A Dataframe contains ms2pip rescore features
    Returns:
        Annotated protein and peptide ids, extra feature names
    """
    rt_feat_l, ms2pip_feat_l, b_ions, y_ions, corr_all, inten_feat, ms2pip_rescore_feat_l, ms2pip_mod =  read_features_config(feature_config_path)
   
    list_feat_df = []
    if RT_feature is not None:
      if len(rt_feat_l)!=0:
         rt_feat_l.append('spec_id')
         rt_feat_l.append('rank')
         list_feat_df.append(RT_feature[rt_feat_l])
         print("--->rt_features_added: ", RT_feature.shape)
         
    if MS2PIP_feature is not None:
      if(b_ions>0 and y_ions>0):
          selected_intensities, ms2pip_columns = extract_intensities(MS2PIP_feature, b_ions, y_ions, corr_all)
          print("selecting just Predictions: ", inten_feat)
          if len(inten_feat)==1 and inten_feat[0] == "b_y_corr":
             ms2pip_columns = [] 
             ms2pip_columns.append('spec_id')
             ms2pip_columns.append('b_y_corr')
             ms2pip_columns.append('rank')
             selected_intensities = selected_intensities[ms2pip_columns]
             print("ms2pip_just_pred_", ms2pip_columns)
             
          elif len(inten_feat)>1 and inten_feat[0] == "b_y_corr":
             inten_feat.pop(0)
             ms2pip_columns_ = []
             for end_with in inten_feat:
               ms2pip_columns_.append([x for x in ms2pip_columns if x.endswith(end_with)])
             ms2pip_columns = [item for sublist in ms2pip_columns_ for item in sublist]
             
             ms2pip_columns.append('spec_id')
             ms2pip_columns.append('b_y_corr')
             ms2pip_columns.append('rank')
             selected_intensities = selected_intensities[ms2pip_columns]
             print("ms2pip_just_pred_", ms2pip_columns)
            
          list_feat_df.append(selected_intensities)
          
    if MS2PIP_rescore_feature is not None:
      if len(rt_feat_l)!=0:
         ms2pip_rescore_feat_l.append('spec_id')
         ms2pip_rescore_feat_l.append('rank')
         selected_MS2PIP_rescore_feat = MS2PIP_rescore_feature[ms2pip_rescore_feat_l] 
         print("--->MSPIP_rescore_features_added: ",selected_MS2PIP_rescore_feat.shape)
         list_feat_df.append(selected_MS2PIP_rescore_feat)

    check_RT = False
    if (RT_feature is not None and MS2PIP_feature is None and MS2PIP_rescore_feature is None):
      print("Test Retention Time Features ")
      final_df = pd.concat(list_feat_df, axis=1)
      if(feature_out):
        final_df.to_csv(out_dir + "All_extra_features.csv")
        print("All new features written at: ", out_dir + "All_extra_features.csv")
        
      extra_feat_name = list(final_df.columns)
      print("extra_feat_name: ", extra_feat_name)
      extra_feat_name.remove('spec_id')
      extra_feat_name.remove('rank')
        
      All_new_feat = final_df[extra_feat_name]          
      if All_new_feat is not None:
        iteratable_list = []
        extra_feat_name = All_new_feat.columns
        #print("All_extra_columns: ", extra_feat_name)
        for column in extra_feat_name: 
          column_x = pd.to_numeric(All_new_feat[column], errors='coerce')
          column_x_ = column_x.fillna(0) 
          iteratable_list.append(iter(list(column_x_)))
          
        #print("len_iteratable_list: ", len(iteratable_list))
        
        for pep_id in pep_ids:
            new_hits = []
            for hit in pep_id.getHits():
                for i in range(len(extra_feat_name)):
                  try:
                    hit.setMetaValue(extra_feat_name[i], next(iteratable_list[i]))
                  except StopIteration:
                    raise SystemExit("Error: Number of predictions and peptide hits does not match.", extra_feat_name[i])
                new_hits.append(hit)
            pep_id.setHits(new_hits) 
      
        search_parameters = prot_ids[0].getSearchParameters()
        export_to_perc = search_parameters.getMetaValue('extra_features')
        export_to_perc = export_to_perc + "," + ",".join(extra_feat_name)
        search_parameters.setMetaValue('extra_features', export_to_perc)
        prot_ids[0].setSearchParameters(search_parameters)       
        print("successfully annotated extra features")  
        check_RT = True      
    
    if(check_RT == False):
      All_new_feat = None
      if len(list_feat_df)!=0:
        it = iter(list_feat_df)
        the_len = len(next(it))
        if not all(len(l) == the_len for l in it) or len(pep_ids)!=the_len:
            print('---not all extracted features have same length!---')
        
            final_df = reduce(lambda df1,df2: pd.merge(df1,df2,how='inner', on=['spec_id', 'rank']), list_feat_df)
            final_df['spec_id'] = final_df['spec_id'].astype(str)
            final_df['rank'] = final_df['rank'].astype(str)
            final_df['spec_id_rank'] = final_df['spec_id'] + '_' + final_df['rank']
            
            if(feature_out):
              final_df.to_csv(out_dir + "All_extra_features.csv")
              print("All new features written at: ", out_dir + "All_extra_features.csv")
            
            extra_feat_name = list(final_df.columns)
            extra_feat_name.remove('spec_id')
            extra_feat_name.remove('rank')
            extra_feat_name.remove('spec_id_rank')
            
            
            print("extra_feat_name: ", extra_feat_name, '\n')
            
            ex_rank_id = list(final_df['spec_id_rank'])
            ex_spec_id = list(final_df['spec_id'])
            
            filter_pepIds = []
            
            spec_id_rank = []
            rank = []
            spec_id = []
            just_check = 0
            for pep_id in pep_ids:
              rank_ = 0
              pep_spec_id = pep_id.getMetaValue('spectrum_reference')
              if pep_spec_id in ex_spec_id:
                filt_hit = []
                for hit in pep_id.getHits():
                    id_rank = pep_id.getMetaValue('spectrum_reference') + '_' + str(rank_)
                    if id_rank in ex_rank_id: 
                      filt_hit.append(hit)
                      just_check = just_check + 1
                    else:
                      print("Hit not found: ", id_rank)
                    rank_ = rank_ + 1 
                pep_id.setHits(filt_hit)
                filter_pepIds.append(pep_id)
              else:
                print("peptide id not found in ext_features_id: " ,pep_spec_id)
            
            
            print("Remains filter_pepIds: ", len(filter_pepIds)," filter pep_id_hits: ", just_check)
                  
            All_new_feat = final_df[extra_feat_name]
            if All_new_feat is not None:
              iteratable_list = []
              extra_feat_name = All_new_feat.columns
              for column in extra_feat_name: 
                column_x = pd.to_numeric(All_new_feat[column], errors='coerce')
                column_x_ = column_x.fillna(0) 
                iteratable_list.append(iter(list(column_x_)))        
              
            for pep_id in filter_pepIds:
                new_hits = []
                for hit in pep_id.getHits():
                    for i in range(len(extra_feat_name)):
                      try:
                        hit.setMetaValue(extra_feat_name[i], next(iteratable_list[i]))
                      except StopIteration:
                        raise SystemExit("Error: Number of predictions and peptide hits does not match.", extra_feat_name[i])
                    new_hits.append(hit)
                pep_id.setHits(new_hits)
                
            search_parameters = prot_ids[0].getSearchParameters()
            export_to_perc = search_parameters.getMetaValue('extra_features')
            export_to_perc = export_to_perc + "," + ",".join(extra_feat_name)
            search_parameters.setMetaValue('extra_features', export_to_perc)
            prot_ids[0].setSearchParameters(search_parameters)       
            print("successfully annotated extra features") 
            pep_ids = filter_pepIds
                          
            
        else:
          final_df = pd.concat(list_feat_df, axis=1)
          if(feature_out):
            final_df.to_csv(out_dir) + "All_extra_features.csv"
            print("All new features written at: ", out_dir + "All_extra_features.csv")
            
          extra_feat_name = list(final_df.columns)
          print("extra_feat_name: ", extra_feat_name)
          extra_feat_name.remove('spec_id')
          extra_feat_name.remove('rank')
            
          All_new_feat = final_df[extra_feat_name]          
          if All_new_feat is not None:
            All_new_feat = All_new_feat.loc[:, ~All_new_feat.columns.duplicated()]
            iteratable_list = []
            extra_feat_name = All_new_feat.columns
            #print("All_extra_columns: ", extra_feat_name)
            for column in extra_feat_name: 
              column_x = pd.to_numeric(All_new_feat[column], errors='coerce')
              column_x_ = column_x.fillna(0) 
              iteratable_list.append(iter(list(column_x_)))
              
            #print("len_iteratable_list: ", len(iteratable_list))
            
            for pep_id in pep_ids:
                new_hits = []
                for hit in pep_id.getHits():
                    for i in range(len(extra_feat_name)):
                      try:
                        hit.setMetaValue(extra_feat_name[i], next(iteratable_list[i]))
                      except StopIteration:
                        raise SystemExit("Error: Number of predictions and peptide hits does not match.", extra_feat_name[i])
                    new_hits.append(hit)
                pep_id.setHits(new_hits) 
          
            search_parameters = prot_ids[0].getSearchParameters()
            export_to_perc = search_parameters.getMetaValue('extra_features')
            export_to_perc = export_to_perc + "," + ",".join(extra_feat_name)
            search_parameters.setMetaValue('extra_features', export_to_perc)
            prot_ids[0].setSearchParameters(search_parameters)       
            print("successfully annotated extra features")        
          
    return prot_ids, pep_ids, extra_feat_name
    
