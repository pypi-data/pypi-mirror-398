from .idXML2df import readAndProcessIdXML
from pyopenms import *
import matplotlib.pyplot as plt

def calcQ(df, scoreColName = 'q-value CSMs', labelColName = 'entrapment'):
    """
    calculate the entrapment q values/FDR 
    Returns:
      dataframe contains entrapment q-val
    """
    
    df.sort_values(scoreColName, ascending=True, inplace = True)
    
    #df['entrapment FDR'] = (range(1, len(df) + 1)/df[labelColName].cumsum()) - 1
    
    df['entrapment FDR'] = df[labelColName].cumsum() / range(1, len(df) + 1)
    df['entrapment q-val'] = df['entrapment FDR'][::-1].cummin()[::-1]
    return df

def entrapment_calculations(idXML_f , idXML_feat_f, True_prot):
    """
    entrapment testing, take the two identification file, calculate the entrapment q-value
    plot entrapment FDR vs Decoy FDR
    """
    print(">>>>>>>>>>>>>>>>> entreperate entrapment without extra feat <<<<<<<<<<<<")
    idXML_df = readAndProcessIdXML(idXML_f)
    idXML_df_filtered = idXML_df[~idXML_df['accessions'].str.contains(';')]
    entrapment_ = []
    t_PSMs = 0
    f_PSMs = 0
    for i in list(idXML_df_filtered["accessions"]):
        if i in True_prot:
            entrapment_.append(0)
            t_PSMs = t_PSMs + 1
        else:
            entrapment_.append(1)
            f_PSMs = f_PSMs + 1

    print("------------- without extra feature PSMS at 100% XL FDR unique PSMs-----")
    print("All data, T_PSMs: ",t_PSMs, " F_PSMs: ", f_PSMs)

    idXML_df_filtered["entrapment"] = entrapment_
    idXML_df_filtered["q-value CSMs"]=idXML_df_filtered["Score"]
    ent_idXML_df_filtered = calcQ(idXML_df_filtered)

    print(">>>>>>>>>>>>>>>> entreperate entrapment with extra feat <<<<<<<<<<<<")
    idXML_feat_df = readAndProcessIdXML(idXML_feat_f)
    idXML_feat_df_filtered = idXML_feat_df[~idXML_feat_df['accessions'].str.contains(';')]

    entrapment_feat = []
    t_PSMs = 0
    f_PSMs = 0
    for i in list(idXML_feat_df_filtered["accessions"]):
        if i in True_prot:
            entrapment_feat.append(0)
            t_PSMs = t_PSMs + 1
        else:
            entrapment_feat.append(1)
            f_PSMs = f_PSMs + 1

    print("------------- without extra feature PSMS at 100% XL FDR unique PSMs-----")
    print("All data, T_PSMs: ",t_PSMs, " F_PSMs: ", f_PSMs)

    idXML_feat_df_filtered["entrapment"] = entrapment_feat
    idXML_feat_df_filtered["q-value CSMs"]=idXML_feat_df_filtered["Score"]
    ent_idXML_feat_df_filtered = calcQ(idXML_feat_df_filtered)

    outfile_path = idXML_f.split(".")

    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot()
    plt.plot(idXML_df_filtered['q-value CSMs'], idXML_df_filtered['entrapment q-val'], color='red', label = 'no extra feat',linewidth=2.0)
    plt.plot(idXML_feat_df_filtered['q-value CSMs'], idXML_feat_df_filtered['entrapment q-val'], color='blue', label ='extra feat',linewidth=2.0)
    ax.plot([0,1],[0,1], color='green')
    plt.title("CSM FDR entrapment plot")
    #plt.axis([-0.1, 1.2, 0, 2500])
    plt.xlabel("CSM FDR q-value", fontsize=12)
    plt.ylabel("False match rate (# of Entrapment CSMs / # of Target CSMs)", fontsize=12) 
    #plt.axvline(x = 0.01, color = 'green', linestyle='-')
    #plt.axvline(x = 0.01, color = 'green', linestyle='-')
    #ax.set_xlim(-0.0, 0.1)
    #ax.set_ylim(0.0, 0.06)
    ax.set_yscale('log', base=10) 
    ax.set_xscale('log', base=10)
    #plt.xlim(0.0, 1.0)
    #plt.ylim(0.0, 1.0)
    #ax.set_xscale('log')
    plt.legend()
    plt.savefig(outfile_path[0] + "_CSM_FDR_entrapment_log_1.0.pdf") 
    #plt.show()

    