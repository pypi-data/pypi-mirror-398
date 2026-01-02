import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pyopenms import *
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_error

def get_extra_feat(keys, values, extra_feat_ls):
    """
    helping function to take extra features and non-extra feature (NuXL_feature) with corresponding percolator weight value
    """
    extra_keys = []
    extra_values = []
    keys_ = []
    values_ = []
    if extra_feat_ls is not None:
      for k, v in zip(keys, values):
          if k in extra_feat_ls:
              extra_keys.append(k)
              extra_values.append(v)
          else:
              keys_.append(k)
              values_.append(v)
    else:
      keys_ = keys
      values_= values

    return extra_keys, extra_values, keys_, values_

def plot_weights_perc(weight_path : str, extra_feat_names : list = None):
    """
    plot the weight of percolator feature importance in all folds (means)
    """
    weights_epoch=[]
    weights_mean=[]
    weights_name=[]
    epoch_perc=3
    df=pd.read_csv(weight_path, sep='\t')
    for column in df:
        for iteration in range(epoch_perc):
            weights_epoch.append(np.abs(np.float(df[column].values[3*iteration])))
        #print('mean:', column, np.mean(weights_epoch))
        weights_mean.append(np.mean(weights_epoch))
        weights_name.append(column)
        weights_epoch=[]

    dic_weights = dict(zip(weights_name, weights_mean))
    sorted_dic_weights = dict(sorted(dic_weights.items(), key=lambda x:x[1]))
    extra_keys, extra_values, keys_, values_ = get_extra_feat(list(sorted_dic_weights.keys()), list(sorted_dic_weights.values()), extra_feat_names)
    
    plt.rcParams["figure.figsize"] = [18.50, 20.50]
    plt.rcParams["figure.autolayout"] = True
    width = 0.6
    plt.barh(extra_keys, extra_values, width, color='red', align='center')
    plt.barh(keys_, values_, width, color='blue', align='center')
    file_ = weight_path.split('.')
    plt.savefig(file_[0]+".png",bbox_inches='tight')
    #plt.show()
    
    return True
    
def get_score_idXML(idXML_file : str):
    """
    get score list of identification data
    """
    protein_ids = []
    peptide_ids = []
    IdXMLFile().load(idXML_file, protein_ids, peptide_ids) 
    Psm_score_list = []
    for pep_id in peptide_ids:
        for hit in pep_id.getHits():
            Psm_score_list.append(hit.getScore())
    
    return Psm_score_list
          

def plot_comparison_PSMs(feat_perc_idXML : str, perc_idXML: str):
    """
    plot comparison of two identification file distribution
    """
    import seaborn as sns
    XL_01_feat = np.array(get_score_idXML(feat_perc_idXML))
    XL_01 = np.array(get_score_idXML(perc_idXML))
    
    sns.set_style("darkgrid")
    plt.figure(figsize=(10,7))
    plt.title("1% XL FDR PSMs "f" without_extra_feat_(XLs): {len(XL_01)} \n with_extra_feat_(XLs): {len(XL_01_feat)} ")
    sns.kdeplot(data=XL_01_feat, color='b', label='XLs_wFeat')
    sns.kdeplot(data=XL_01, color='c', label='XLs_w/o_Feat')
    #plt.axvline(0.01, 0, linewidth=1, color='r')
    plt.legend()
    file_ = perc_idXML.split('.')
    plt.savefig(file_[0]+ '_0.0100_FDR.png')
    #plt.show()
    print("1% XL FDR PSMs "f" without_extra_feat_(XLs): {len(XL_01)} with_extra_feat_(XLs): {len(XL_01_feat)} ")
    
def comparison_PSMs(feat_perc_idXML : str, perc_idXML: str):
    """
    write the no. of 1% CSM FDR comparison of two identification file
    """
    XL_01_feat = get_score_idXML(feat_perc_idXML)
    XL_01 = get_score_idXML(perc_idXML)
    print("--->>>>> 1% XL FDR without extra features: ", len(XL_01))
    print("--->>>>> 1% XL FDR with extra features: ",len(XL_01_feat))
    file_ = perc_idXML.split('.')
    with open(file_[0]+ '_0.0100_FDR_report.csv', 'w') as f:
     f.write(file_[0]+'\n')
     f.write("1% XL FDR without extra features: " + str(len(XL_01)))
     f.write('\n')
     f.write("1% XL FDR with extra features: " + str(len(XL_01_feat)))
    
def evaluate_linear_regression_plot_(df:pd.DataFrame, x="rt_norm", y="rt_pred", name="evaluate_regression", output_dir: str = None):
    """
    calculate regression evaluation parameters
    """
    ci=95
    n_sample=10000000
    if len(df) > n_sample:
        df = df.sample(n_sample, replace=False)
    gls = sm.GLS(df[y], sm.add_constant(df[x]))
    res = gls.fit()
    summary = res.summary(alpha=1-ci/100.0)
    dfs = []
    results_as_html = summary.tables[0].as_html()
    dfs.append(pd.read_html(results_as_html, index_col=None)[0])
    results_as_html = summary.tables[1].as_html()
    dfs.append(pd.read_html(results_as_html, index_col=None)[0])
    summary = pd.concat(dfs, ignore_index=True)
    R_square = float(summary.loc[0,3])
    R = np.sqrt(R_square)
    n,b,w = summary.loc[[5,10,11],1].values.astype(float)
    
    MAE = mean_absolute_error (df[x], df[y])
    perc95_calib = np.percentile(abs(df[x]-df[y]),95)*2
    
    plt.figure(figsize=(6,6.5))
    plt.title(name + f" MAE: {round(MAE,2)} \n R: {round(R,3)} R_Square: {round(R_square,3)}")
    # slope: {round(w,3)} intercept: {round(b,3)} samples: {n}"95th percentile: {round(perc95_calib,2)} )
    plt.scatter(df[x],df[y],s=1,alpha=0.6, color="tab:blue")
    plt.xlabel("Observed retention time ")
    plt.ylabel("Predicted retention time ") 
    #plt.ylim([1, 10])
    plt.savefig(output_dir + name+".pdf")

    return pd.DataFrame(
        dict(
            MAE=[MAE],perc95_calib=[perc95_calib], R_square=[R_square],R=[R],
            slope=[w],intercept=[b],test_num=[n]
        )
    )
    
    
def plot_RT_predictions(idXML_file:str,name = 'RT_results'):
    """
      retention time comparison plot of given identification file.
    """
    prot_ids = []
    pep_ids = []
    IdXMLFile().load(idXML_file, prot_ids, pep_ids) 

    Observed_RT = []
    Predicted_RT= []

    for pep_id in pep_ids:
        Observed_RT.append(pep_id.getRT())
        for hit in pep_id.getHits():
            Predicted_RT.append(float(hit.getMetaValue("predicted_retention_time_best")))

    RT_df = pd.DataFrame({"Observed_RT": Observed_RT, "Predicted_RT": Predicted_RT}, columns=["Observed_RT", "Predicted_RT"])
     
    evaluate_linear_regression_plot_(RT_df, x='Observed_RT', y='Predicted_RT', name = name)
    

def plot_RT_predictions_comparison(idXML_XL_file:str, idXML_pep_file:str, name = 'RT_comparison', output_dir: str = None):
    """
      retention time comparison plot of XL (idXML:XL_file) and nonXL file (idXML_pep_file).
    """
    XL_prot_ids = []
    XL_pep_ids = []
    IdXMLFile().load(idXML_XL_file, XL_prot_ids, XL_pep_ids) 

    XL_Observed_RT = []
    XL_Predicted_RT= []

    for pep_id in XL_pep_ids:
        XL_Observed_RT.append(pep_id.getRT())
        for hit in pep_id.getHits():
            XL_Predicted_RT.append(float(hit.getMetaValue("predicted_retention_time_best")))

    #RT_df = pd.DataFrame({"Observed_RT": Observed_RT, "Predicted_RT": Predicted_RT}, columns=["Observed_RT", "Predicted_RT"])
    
    prot_ids = []
    pep_ids = []
    IdXMLFile().load(idXML_pep_file, prot_ids, pep_ids) 

    Observed_RT = []
    Predicted_RT= []

    for pep_id in pep_ids:
        Observed_RT.append(pep_id.getRT())
        for hit in pep_id.getHits():
            Predicted_RT.append(float(hit.getMetaValue("predicted_retention_time_best")))
            
    
    plt.figure(figsize=(6,6.5))
    plt.scatter(XL_Observed_RT,XL_Predicted_RT,s=1,alpha=0.6, color="tab:blue", label = "XL_RT")
    plt.scatter(Observed_RT,Predicted_RT,s=1,alpha=0.6, color="tab:red", label = "nonXL_RT")
    plt.xlabel("Observed retention time ")
    plt.ylabel("Predicted retention time ") 
    #plt.ylim([1, 10])
    plt.legend()
    #plt.show()
    plt.savefig(output_dir + name+".pdf")

def plot_FDR_plot(idXML_id, idXML_extra):
    """
    FDR plot of two input idXML identifications format file
    idXML_id: without extra feature
    idXML_extra: with adopted extra feature   
    """

    protein_ids = []
    peptide_ids = []
    IdXMLFile().load(idXML_id, protein_ids, peptide_ids)
    
    ### Without extra features
    Psm_score_list = []
    for pep_id in peptide_ids:
        for hit in pep_id.getHits():
            Psm_score_list.append(float(hit.getScore()))
            
    list_results = [] 
    q_values = []
    x = -0.0002

    for i in range(10001):
        values = sum(j < x for j in Psm_score_list)
        #print(j < x for j in Psm_score_list)
        list_results.append(values)
        q_values.append(x)
        x = x + 0.0001


    ### With extra features
    protein_ids_extra = []
    peptide_ids_extra = []
    IdXMLFile().load(idXML_extra, protein_ids_extra, peptide_ids_extra)
    
    Psm_score_list_extra = []
    for pep_id in peptide_ids_extra:
        for hit in pep_id.getHits():
            Psm_score_list_extra.append(float(hit.getScore()))
            
    list_results_extra = [] 
    q_values_extra = []
    x = -0.0002

    len_3000 = 0
    for i in range(100001):
      values = sum(j < x for j in Psm_score_list_extra)
      #print(j < x for j in Psm_score_list)
      list_results_extra.append(values)
      q_values_extra.append(x)
      x = x + 0.0001
      if (i == 3000):
        len_3000 = values

    #### plotting 

    outfile_path = idXML_id.split(".")
    
    fig, ax = plt.subplots(figsize=(8,7))
    plt.plot(q_values,list_results, color = 'red', label = 'no extra feat', linewidth=1.0)
    plt.plot(q_values_extra, list_results_extra, color = 'blue', label ='extra feat',linewidth=1.0)
    plt.title("pseudo-ROC curve CSM FDR")
    #plt.axis([-0.1, 1.2, 0, 2500])
    plt.axvline(x = 0.01, color = 'green', linestyle='-', linewidth=1.0)
    plt.xlabel("CSM FDR q-value", fontsize=12)
    plt.ylabel("no. of CSMs", fontsize=12) 
    ax.set_xlim(-0.01, 0.1)
    ax.set_ylim(0, len_3000)
    plt.legend()
    plt.savefig(outfile_path[0] + "_CSM_FDR_PSM_0.01.pdf")
    #plt.show()

    fig, ax = plt.subplots(figsize=(8,7))
    plt.plot(q_values,list_results, color = 'red', label = 'no extra feat', linewidth=1.0)
    plt.plot(q_values_extra, list_results_extra, color = 'blue', label ='extra feat',linewidth=1.0)
    plt.title("pseudo-ROC curve CSM FDR")
    #plt.axis([-0.1, 1.2, 0, 2500])
    plt.axvline(x = 0.01, color = 'green', linestyle='-', linewidth=1.0)
    plt.xlabel("CSM FDR q-value", fontsize=12)
    plt.ylabel("no. of CSMs", fontsize=12) 
    #ax.set_xscale('log', base=10)
    ax.set_xlim(-0.01, 0.2)
    ax.set_ylim(0, len_3000)
    plt.legend()
    plt.savefig(outfile_path[0] + "_CSM_FDR_PSM_0.02.pdf")
    #plt.show()
    
    fig, ax = plt.subplots(figsize=(8,7))
    plt.plot(q_values,list_results, color = 'red', label = 'no extra feat', linewidth=1.0)
    plt.plot(q_values_extra, list_results_extra, color = 'blue', label ='extra feat',linewidth=1.0)
    plt.title("pseudo-ROC curve CSM FDR")
    #plt.axis([-0.1, 1.2, 0, 2500])
    plt.axvline(x = 0.01, color = 'green', linestyle='-',  linewidth=1.0)
    plt.xlabel("CSM FDR q-value", fontsize=12)
    plt.ylabel("no. of CSMs", fontsize=12) 
    ax.set_xlim(-0.01, 1.0)
    #ax.set_xscale('log', base=10)
    plt.legend()
    plt.savefig(outfile_path[0] + "_CSM_FDR_PSM_1.0.pdf")
    #plt.show()
   
    

   
