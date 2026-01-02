import time, os, copy, datetime, math, random, warnings
from typing import Dict, List, Tuple, Optional
import subprocess, sys
import numpy as np
import pandas as pd
from scipy import stats, signal

import matplotlib.pyplot as plt
from matplotlib import cm, colormaps
import matplotlib as mpl
from matplotlib.pyplot import figure
from matplotlib.patches import Rectangle
# sys.setrecursionlimit(100000)
from sklearn import cluster, mixture

from importlib_resources import files

SCANVPY = True
try:
    import scanpy as sc
    import anndata
except ImportError:
    print('WARNING: scanpy not installed.')
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scanpy"])
        import scanpy as sc
        import anndata
        print('INFO: scanpy was sucessfully installed.')
    except:
        print('WARNING: Cannot install scanpy.')
        SCANVPY = False

STATANNOT = True
try:
    # from statannot import add_stat_annotation
    from statannotations.Annotator import Annotator
except ImportError:
    print('WARNING: statannot not installed or not available. ')
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "statannotations"])
        from statannotations.Annotator import Annotator
        print('INFO: statannotations was sucessfully installed.')
    except:
        print('WARNING: Cannot install statannotations.')
        STATANNOT = False

SEABORN = True
try:
    import seaborn as sns
except ImportError:
    print('WARNING: seaborn not installed or not available. ')
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "seaborn"])
        import seaborn as sns
        print('INFO: seaborn was sucessfully installed.')
    except:
        print('WARNING: Cannot install seaborn.')
        SEABORN = False

try:
    import plotly.graph_objects as go
except ImportError:
    print('WARNING: plotly not installed.')
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
        import plotly.graph_objects as go
        print('INFO: plotly was sucessfully installed.')
    except:
        print('WARNING: Cannot install plotly.')
    
from .supp import get_abbreviations


def get_sample_to_group_dict( samples, conditions ):
    
    samples = np.array(samples)
    conditions = np.array(conditions)
    
    slst = list(set(list(samples)))
    slst.sort()
    glst = []
    for s in slst:
        b = samples == s
        g = conditions[b][0]
        glst.append(g)
        
    dct = dict(zip(slst, glst))
    return dct


def get_sample_to_group_map( samples, conditions ):
    return get_sample_to_group_dict( samples, conditions )


# df_cnt, df_pct= get_population( adata_s.obs['sid'], 
#                                 adata_s.obs['minor'], sort_by = [] )
def get_population( args_in, cts_in, sort_by = [], sample_col = 'sample' ):

    if isinstance( args_in, pd.Series ) & isinstance( cts_in, pd.Series ):
        pids = args_in.copy(deep = True)
        cts = cts_in.copy(deep = True)
        sg_map = None
        
    elif isinstance( args_in, anndata.AnnData ) & isinstance( cts_in, str ):
        try:
            pids = args_in.obs[sample_col]
            cts = args_in.obs[cts_in]
            sg_map = get_sample_to_group_map( args_in.obs[sample_col], args_in.obs['condition'] )
        except:
            print('ERROR: %s not in obs columns. ' % cts_in)
            return None, None            
    else:
        print('ERROR: Invalid input. The 1st argument must be AnnData or pandas.Series. ')
        return None, None

    pid_lst = list(set(list(pids)))
    pid_lst.sort()
    celltype_lst = list(set(list(cts)))
    celltype_lst.sort()

    df_celltype_cnt = pd.DataFrame(index = pid_lst, columns = celltype_lst)
    df_celltype_cnt.loc[:,:] = 0

    for pid in pid_lst:
        b = np.array(pids) == pid
        ct_sel = np.array(cts)[b]

        for ct in celltype_lst:
            bx = ct_sel == ct
            df_celltype_cnt.loc[pid, ct] = np.sum(bx)

    df_celltype_pct = (df_celltype_cnt.div(df_celltype_cnt.sum(axis = 1), axis = 0)*100).astype(float)
    
    if len(sort_by) > 0:
        df_celltype_pct.sort_values(by = sort_by, inplace = True)

    if sg_map is None:
        slst, clst = get_sample_and_group_from_sample_ext( df_celltype_cnt.index.values )                
        sg_map = dict(zip( slst, clst ))

    df_celltype_cnt.insert(0, 'Group', list(df_celltype_cnt.index.values))
    df_celltype_cnt['Group'] = df_celltype_cnt['Group'].replace( sg_map )
    df_celltype_pct.insert(0, 'Group', list(df_celltype_pct.index.values))
    df_celltype_pct['Group'] = df_celltype_pct['Group'].replace( sg_map )
    
    return df_celltype_cnt, df_celltype_pct


def get_population_per_sample( args_in, cts_in, sort_by = [], sample_col = 'sample' ):
    return get_population( args_in, cts_in, sort_by, sample_col = sample_col )


def get_gene_expression_mean( adata, genes = [], group_col = 'sample', nz_pct = True ): 

    sample_col = group_col
    slst = adata.obs[sample_col].unique().tolist()
    slst.sort()

    sg_map = get_sample_to_group_map( adata.obs[sample_col], adata.obs['condition'] )
    
    if genes is None:
        Xs = adata.to_df()
        df = pd.DataFrame(index = slst, columns = adata.var.index)
    elif len(genes) == 0:
        Xs = adata.to_df()
        df = pd.DataFrame(index = slst, columns = adata.var.index)
    else:
        Xs = adata[:, genes].to_df()
        df = pd.DataFrame(index = slst, columns = genes)

    if nz_pct:
        for s in slst:
            b = adata.obs[sample_col] == s
            mns = (Xs.loc[b,:] > 0).mean(axis = 0)
            df.loc[s,:] = list(mns)
    
        df = df.astype(float)
    else:
        Xs['Group'] = adata.obs[sample_col]
        df = Xs.groupby('Group').mean(numeric_only=True)
        
    df.insert(0, 'Group', list(df.index.values))
    df['Group'] = df['Group'].replace( sg_map )
                  
    return df


def get_cci_means( cci_df_dct, cci_idx_lst = None, 
                   cells = [], genes = [], pval_cutoff = 0.05 ):

    if cci_idx_lst is None:
        ## get coomon cci index
        for j, key in enumerate(cci_df_dct.keys()):
            b = cci_df_dct[key]['pval'] <= pval_cutoff
            if len(cells) > 0:
                b = b & (cci_df_dct[key]['cell_A'].isin(cells) | cci_df_dct[key]['cell_B'].isin(cells))
            if len(genes) > 0:
                b = b & (cci_df_dct[key]['gene_A'].isin(genes) | cci_df_dct[key]['gene_B'].isin(genes))
                         
            if j == 0:
                idx_union = list(cci_df_dct[key].index.values[b])
            else:
                idx_union = list(set(idx_union).union(list(cci_df_dct[key].index.values[b])))
        cci_idx_lst = idx_union
    
    tlst = cci_idx_lst
    slst = list(cci_df_dct.keys())

    df = pd.DataFrame(index = slst, columns = tlst)
    df.loc[:,:] = None
    
    for s in slst:
        dfv = cci_df_dct[s]
        idx = list(dfv.index.values)
        clst = list(set(tlst).intersection(idx))
        df.loc[s, clst] = dfv.loc[clst, 'mean'].astype(float)   
                
    df = df.astype(float)
    
    slst2, clst = get_sample_and_group_from_sample_ext( df.index.values )                
    # sample_group_map = dict(zip( slst, clst ))    
    df.insert( 0, 'Group', clst )
    
    return df
    

def cci_get_diff_interactions( df_cci_sample, sample_group_map = None, 
                               ref_group = None, pval_cutoff = 0.05 ):
    
    df = df_cci_sample.copy(deep = True)
    if 'Group' in list(df.columns.values):
        sample_group_map = dict(zip( df.index.values, df['Group'] ))
        df = df.drop( columns = ['Group'] )

    group = []
    for k in list(df.index.values):
        group.append( sample_group_map[k] )
        
    glst = list(set(group))
    glst.sort()
    group = pd.Series(group, index = df.index)
    
    df_res = pd.DataFrame(index = list(df.columns.values))
    
    if ref_group is None:
        for i, g1 in enumerate(glst):
            
            b_r = (group == g1) # & (~df[item].isnull())
            n_r = np.sum(b_r)
            if n_r > 0:
                for j, g2 in enumerate(glst):
                    if i > j:
                        b_o = (group == g2) 
                        n_o = np.sum(b_o)
                        if n_o > 0:
                            bx = ((~df.loc[b_r,:].isna()).sum() > 1) & ((~df.loc[b_o,:].isna()).sum() > 1)
                            bx = bx & (df.loc[b_r,:].std() >= 1e-8) & (df.loc[b_o,:].std() >= 1e-8)
                            res = stats.ttest_ind(df.loc[b_r,bx], 
                                                  df.loc[b_o,bx], axis=0, 
                                                  equal_var=False,  
                                                  nan_policy='omit', 
                                                  permutations=None, 
                                                  random_state=None, 
                                                  alternative='two-sided', 
                                                  trim=0)
                            df_res.loc[bx, '%s_vs_%s' % (g1, g2)] = res.pvalue
            
    elif ref_group in glst:
    
        b_ref = group == ref_group
        for g in glst:
            if g != ref_group:
                b_r = (group == g)  
                n_r = np.sum(b_r)
    
                b_o = b_ref 
                n_o = np.sum(b_o)
                bx = ((~df.loc[b_r,:].isna()).sum() > 1) & ((~df.loc[b_o,:].isna()).sum() > 1)
                bx = bx & (df.loc[b_r,:].std() >= 1e-8) & (df.loc[b_o,:].std() >= 1e-8)
                res = stats.ttest_ind(df.loc[b_r,bx], 
                                      df.loc[b_o,bx], axis=0, 
                                      equal_var=False, 
                                      nan_policy='omit',  
                                      permutations=None, 
                                      random_state=None, 
                                      alternative='two-sided', 
                                      trim=0)
                df_res.loc[bx, '%s_vs_%s' % (g, ref_group)] = res.pvalue
    
    b = df_res.isnull()
    df_res[b] = 1
    
    pv_min = df_res.min(axis = 1)
    df_res = df_res.loc[pv_min <= pval_cutoff,:]

    df_res['ss'] = (df_res <= pval_cutoff).sum(axis = 1)
    df_res['pp'] = -np.log10(df_res.prod(axis = 1) + 1e-30)
    df_res.sort_values(by = ['ss', 'pp'], ascending = False, inplace = True)
       
    return df_res.iloc[:,:-2]


def test_group_diff( df_sample_by_items, sample_group_map = None, 
                     ref_group = None, pval_cutoff = 0.05 ):
    
    return cci_get_diff_interactions( df_sample_by_items, sample_group_map, 
                               ref_group, pval_cutoff )


### Remove common CCI
def cci_remove_common( df_dct ):
    
    idx_dct = {}
    idxo_dct = {}
    celltype_lst = []

    for j, g in enumerate(df_dct.keys()):
        idx_dct[g] = list(df_dct[g].index.values)
        if j == 0:
            idx_c = idx_dct[g]
        else:
            idx_c = list(set(idx_c).intersection(idx_dct[g]))

        ctA = list(df_dct[g]['cell_A'].unique())
        ctB = list(df_dct[g]['cell_B'].unique())
        celltype_lst = list(set(celltype_lst).union(ctA + ctB))

    for g in df_dct.keys():
        idxo_dct[g] = list(set(idx_dct[g]) - set(idx_c))

    dfs_dct = {}
    for g in df_dct.keys():
        dfs_dct[g] = df_dct[g].loc[idxo_dct[g],:]

    celltype_lst.sort()
    # len(idx_c), celltype_lst
    
    return dfs_dct


## Get matrices summarizing the num CCIs for each condition
def cci_get_ni_mat( df_dct, remove_common = True ):
    
    if remove_common: 
        dfs_dct = cci_remove_common( df_dct )
    else:
        dfs_dct = df_dct
        
    celltype_lst = []
    for j, g in enumerate(dfs_dct.keys()):
        ctA = list(dfs_dct[g]['cell_A'].unique())
        ctB = list(dfs_dct[g]['cell_B'].unique())
        celltype_lst = list(set(celltype_lst).union(ctA + ctB))

    celltype_lst.sort()
    
    df_lst = {} 
    for g in dfs_dct.keys():
        b = dfs_dct[g]['cell_A'].isin(celltype_lst) & (dfs_dct[g]['cell_B'].isin(celltype_lst))
        dfs = dfs_dct[g].loc[b,:]
        df = pd.DataFrame(index = celltype_lst, columns = celltype_lst)
        df.loc[:] = 0
        for a, b in zip(dfs['cell_A'], dfs['cell_B']):
            df.loc[a,b] += 1

        df_lst[g] = df
                
    return df_lst

def get_cci_ni_mat( df_dct, remove_common = True ):
    return cci_get_ni_mat( df_dct, remove_common )


def cci_get_df_to_plot( df_dct, pval_cutoff = 0.01, mean_cutoff = 1, target_cells = None ):

    idx_lst_all = []
    for k in df_dct.keys():
        b = df_dct[k]['pval'] <= pval_cutoff
        b = b & df_dct[k]['mean'] >= mean_cutoff
        if target_cells is not None:
            if isinstance(target_cells, list):
                b1 = df_dct[k]['cell_A'].isin(target_cells)
                b2 = df_dct[k]['cell_B'].isin(target_cells)
                b = b & (b1 | b2)
                
        idx_lst_all = idx_lst_all + list(df_dct[k].index.values[b])

    idx_lst_all = list(set(idx_lst_all))
    display('Union of Interactions: %i' % len(idx_lst_all))    

    df_dct_to_plot = {}
    for k in df_dct.keys():
        df = df_dct[k]
        dfv = pd.DataFrame(index = idx_lst_all, columns = df.columns)
        dfv['mean'] = 0
        dfv['pval'] = 1

        idxt = list(set(idx_lst_all).intersection(list(df.index.values)))
        cols = list(df.columns.values)
        cols.remove('mean')
        cols.remove('pval')
        dfv.loc[idxt, cols] = df.loc[idxt, cols]
        dfv.loc[idxt, 'mean'] = df.loc[idxt, 'mean']
        dfv.loc[idxt, 'pval'] = df.loc[idxt, 'pval']

        gp, cp, ga, gb, ca, cb = [], [], [], [], [], []
        for s in list(dfv.index.values):
            gpt, cpt, gat, gbt, cat, cbt = cpdb_get_gp_n_cp(s)

            gp = gp + [gpt]
            cp = cp + [cpt]
            ga = ga + [gat]
            gb = gb + [gbt]
            ca = ca + [cat]
            cb = cb + [cbt]

        dfv['gene_pair'] = gp
        dfv['cell_pair'] = cp
        dfv['gene_A'] = ga
        dfv['gene_B'] = gb
        dfv['cell_A'] = ca
        dfv['cell_B'] = cb
        
        df_dct_to_plot[k] = dfv
        # print(dfv.shape)
        
    return df_dct_to_plot


####################################
### Function to get markers dict ###

def get_markers_from_deg( df_dct, ref_col = 'score',  N_mkrs = 30, 
                          # nz_pct_test_min = 0.5, nz_pct_ref_max = 0.1,
                          rem_common = True ):
## Get markers from DEG results

    df_deg = df_dct
    mkr_dict = {}
    b = True
    for key in df_deg.keys():
        if ref_col not in list(df_deg[key].columns.values):
            b = False
            break
    
    if not b:
        print('ERROR: %s not found in column name of DEG results.' % ref_col)
        return None

    for key in df_deg.keys():

        g = key.split('_vs_')[0]
        df = df_deg[key].copy(deep = True)
        df = df.sort_values([ref_col], ascending = False)
        mkr_dict[g] = list(df.iloc[:N_mkrs].index.values)

    ## Remove common markers
    if rem_common:
        lst = list(mkr_dict.keys())
        cmm = []
        for j, k1 in enumerate(lst):
            for i, k2 in enumerate(lst):
                if (k1 != k2) & (j < i):
                    lc = list(set(mkr_dict[k1]).intersection(mkr_dict[k2]))
                    cmm = cmm + lc
        cmm = list(set(cmm))

        for j, k in enumerate(lst):
            mkr_dict[k] = list(set(mkr_dict[k]) - set(cmm))

    return mkr_dict


# import pkg_resources
from importlib.resources import files

def load_surfaceome_genes( ):
    
    # data_path = pkg_resources.resource_filename('scodaviz', 'data')
    data_path = None
    try:
        # data_path = pkg_resources.resource_filename('scoda', 'default_optional_files')
        data_path = str( files('scoda').joinpath('default_optional_files') )
        if not os.path.isdir(data_path):
            data_path = None
    except:
        pass
    
    if data_path is None:
        try:
            # data_path = pkg_resources.resource_filename('scodaviz', 'data')
            data_path = str( files('scodaviz').joinpath('data') )
            if not os.path.isdir(data_path):
                data_path = None
        except:
            pass

    if data_path is None:
        return data_path
        
    with open( data_path + '/surfaceome_genes.txt', 'r' ) as f:
        lines = f.readlines()
        gene_lst = []
        for l in lines:
            gene_lst.append(l[:-1])

    gene_lst = ['%s' % (g.lower())  for g in gene_lst]
        
    return gene_lst


def find_condition_specific_markers( df_deg_dct, 
                                     score_col = 'nz_pct_score',
                                     pval_col = 'nz_pct_pval',
                                     n_markers_max = 100,
                                     score_cutoff = 0.25,
                                     pval_cutoff = 0.05,
                                     nz_pct_fc_cutoff = 1.2,
                                     verbose = False,
                                     surfaceome_only = True ):

    """
    ------------------------------------------------------------
    📌 Extract **condition-specific marker genes** from multi-group DEG results
    ------------------------------------------------------------

    This function screens DEG tables for each condition/group
    and selects genes that are enriched in a target group
    relative to others based on expression prevalence metrics.

    Supports surfaceome-restricted marker mining (optional).

    Parameters
    ----------
    df_deg_dct : dict
        { group_name : DEG dataframe }
        Required columns:
            - score_col (e.g. 'nz_pct_score')
            - pval_col (e.g. 'nz_pct_pval')
            - 'nz_pct_test', 'nz_pct_ref'  (if using NZ-percentage test mode)

    score_col : str (default='nz_pct_score')
        Ranking metric column for marker selection.

    pval_col : str (default='nz_pct_pval')
        Significance column used for filtering.

    n_markers_max : int (default=100)
        Maximum markers returned per condition.

    score_cutoff : float (default=0.25)
        Minimum enrichment score to be considered.

    pval_cutoff : float (default=0.05)
        P-value threshold for significance.

    nz_pct_fc_cutoff : float (default=1.2)
        Fold-change threshold when using non-zero percentage score:
            test > ref × fc_cutoff

    surfaceome_only : bool (default=True)
        If True → retain only genes listed in surfaceome DB

    verbose : bool
        Print number of filtered candidates & final counts

    ------------------------------------------------------------
    Returns
    -------
    mkr_dict : dict
        { group_name : [ selected_marker_genes ] }

    df_deg_dct_updated : dict
        Filtered DEG tables per condition
        (after applying cutoff + optional surfaceome filter)

    ------------------------------------------------------------
    Usage
    ------
    >>> mkr_dict, df_filtered = find_condition_specific_markers(
            df_deg_dct,
            score_col='nz_pct_score',
            score_cutoff=0.3,
            pval_cutoff=0.01,
            surfaceome_only=True
        )

    >>> mkr_dict["TNBC"][:10]     # top TNBC-specific markers
    ['CXADR','ITGA2','KRT5','EGFR',...]

    >>> len(mkr_dict), sum(len(v) for v in mkr_dict.values())
    """
    
    if surfaceome_only:
        surfaceome_gene_lst = load_surfaceome_genes( )
        if surfaceome_gene_lst is None:
            surfaceome_only = False
            
    s = ''
    df_deg_dct_updated = {}
    for k in df_deg_dct.keys():

        b = df_deg_dct[k][score_col] >= score_cutoff
        b = b & (df_deg_dct[k][pval_col] <= pval_cutoff)  
        if (nz_pct_fc_cutoff > 1) & (score_col == 'nz_pct_score'):
            b = b & (df_deg_dct[k]['nz_pct_test'] > df_deg_dct[k]['nz_pct_ref']*nz_pct_fc_cutoff)
        
        '''
        b = df_deg_dct[k][score_col] >= score_cutoff
        if score_col == 'nz_pct_score':
            if 'nz_pct_pval' in list(df_deg_dct[k].columns.values):
                b = b & (df_deg_dct[k]['nz_pct_pval'] <= pval_cutoff)  
            else:
                b = b & (df_deg_dct[k]['pval'] <= pval_cutoff)                  
            b = b & (df_deg_dct[k]['nz_pct_test'] > df_deg_dct[k]['nz_pct_ref']*nz_pct_fc_cutoff)  
        else:            
            b = b & (df_deg_dct[k]['pval'] <= pval_cutoff)  
        '''
        
        if surfaceome_only:
            glst = [g.lower() for g in list(df_deg_dct[k].index.values)]
            glst = pd.Series( glst )
            b = b & np.array(glst.isin(surfaceome_gene_lst))
        df_deg_dct_updated[k] = df_deg_dct[k].loc[b,:].drop(columns = ['Rp']).copy(deep = True)
        df_deg_dct_updated[k].set_index('gene', inplace = True)
        s = s + '   %s (%i -> %i) \n' % (k, len(b), np.sum(b))
        
    if verbose: print('N_markers: \n' + s[:-2])
    
    mkr_dict = get_markers_from_deg( df_deg_dct_updated, 
                                     N_mkrs = n_markers_max, 
                                     ref_col = score_col,
                                     rem_common = False )
    
    s = ''
    for k in mkr_dict.keys():
        s = s + '%s (%i), ' % (k, len(mkr_dict[k]))
    if verbose: print('N_markers_selected: ' + s[:-2])
    
    ## Print results
    mkrs_all = []
    for key in mkr_dict.keys():
        mkr_dict[key].sort()
        lst = mkr_dict[key]
        mkrs_all = mkrs_all + lst
        # if verbose: print('%s (%i): ' % (key, len(lst)), lst)

    return mkr_dict, df_deg_dct_updated 


def save_to_excel( df_dct, file_name, index = True ):
    
    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
        if isinstance(df_dct, pd.DataFrame):
            df.to_excel(writer, index=index)
            b = True                    
        elif isinstance(df_dct, dict):
            for key in df_dct.keys():
                df = df_dct[key]
                if df.shape[0] > 0:
                    df.to_excel(writer, sheet_name=key, index=index)
        elif isinstance(df_dct, list):
            for j, df in enumerate(df_dct):
                if df.shape[0] > 0:
                    df.to_excel(writer, sheet_name='Sheet%i' % (j+1), index=index)
    return




def find_tumor_origin( adata, tid_col = 'ploidy_dec', ref_taxo_level = 'celltype_major',
                       tumor_name = 'Aneuploid'):
    
    b = adata.obs[tid_col] == tumor_name
    pcnt = adata.obs.loc[b, ref_taxo_level].value_counts()
    tumor_origin = [pcnt.index[0]]
    tumor_origin_celltype = pcnt.index[0]
    if (tumor_origin_celltype == 'unassigned'):
        if len(pcnt) > 1:
            if (pcnt[1] >= pcnt[0]*0.05):
                tumor_origin = tumor_origin + [pcnt.index[1]]
                tumor_origin_celltype = pcnt.index[1]
    #'''
    elif len(pcnt) > 1:
        if pcnt.index[1] == 'unassigned':
            tumor_origin = tumor_origin + ['unassigned']
    #'''
    return tumor_origin_celltype


def filter_gsa_result( dct, neg_log_p_cutoff ):
    
    dct_t = {}
    for kk in dct.keys():
        dft = dct[kk]
        b = dft['-log(p-val)'] >= neg_log_p_cutoff
        dct_t[kk] = dft.loc[b,:]
    return dct_t


### Example 
# lst = [adata_t.obs['cell_type_major_pred'], adata_t.obs['tumor_dec'], adata_t.obs['subtype']] #, 
# plot_sankey_e( lst, title = None, fs = 12, WH = (800, 600), th = 0, title_y = 0.85 )

def plot_sankey( lst, title = None, fs = 12, WH = (700, 800), th = 0, title_y = 0.85 ):

    """
    ------------------------------------------------------------
    📌 Sankey plot for multi-step category / label transitions
    ------------------------------------------------------------

    Visualizes how samples (or items) move/overlap across multiple
    categorical layers.  

    Example use cases:
    - Cluster transition across analysis stages
    - Cell-state / condition mapping comparisons
    - Sample classification shifts between methods
    - CNV-state → subtype → response → prognosis linkage

    Parameters
    ----------
    lst : list of lists (or Series-like objects)
        Ordered categorical layers.
        Must contain >= 2 elements.
        Example:
            lst = [
                cluster_day0_labels,
                cluster_day3_labels,
                cluster_day7_labels
            ]

    title : str or None
        Plot title.

    fs : int
        Title font size.

    WH : tuple(int,int)  (default = (700,800))
        Figure (width,height) in pixels.

    th : int (default=0)
        Minimum connection count required to draw a link.
        (filters out weak edges)

    title_y : float
        Title vertical position in normalized figure coordinates.

    ------------------------------------------------------------
    Returns
    -------
    None
        Displays interactive Sankey diagram using plotly.

    ------------------------------------------------------------
    Usage Example
    -------------
    >>> plot_sankey(
            [labels_T0, labels_T1, labels_T2],
            title = "Cell state transition across time"
        )

    >>> plot_sankey(
            [cluster_v1, cluster_v2],
            th=3,
            title="Cluster mapping (freq >= 3)"
        )

    ------------------------------------------------------------
    Notes
    -----
    • Internally converts categories into node labels:  
          L1_A, L1_B → L2_A, L2_B → ...  
    • `th` is useful for removing noisy/rare transitions  
    • Interactive hover + zoom support (Plotly)
    """
    
    if len(lst) < 2:
        print('ERROR: Input must have length of 2 or more.')
        return
    
    W = WH[0]
    H = WH[1]

    sall = []
    tall = []
    vall = []
    lbl_all = []
    label_lst = []
    
    nn_cnt = 0
    for nn in range(len(lst)-1):
        source_in = ['L%i_%s' % (nn+1, a) for a in list(lst[nn])]
        target_in = ['L%i_%s' % (nn+2, a)  for a in list(lst[nn+1])]
                
        source = pd.Series(source_in).astype(str)
        b = source.isna()
        source[b] = 'N/A'
        target = pd.Series(target_in).astype(str)
        b = target.isna()
        target[b] = 'N/A'

        src_lst = list(set(source))
        tgt_lst = list(set(target))
        src_lst.sort()
        tgt_lst.sort()

        if th > 0:
            bx = np.full(len(source), True)
            for k, s in enumerate(src_lst):
                bs = source == s
                for m, t in enumerate(tgt_lst):
                    bt = target == t
                    b = bs & bt
                    if np.sum(b) < th:
                        bx[b] = False
            source = source[bx]
            target = target[bx]

            src_lst = list(set(source))
            tgt_lst = list(set(target))
            src_lst.sort()
            tgt_lst.sort()

        src = []
        tgt = []
        val = []
        sl_lst = []
        tl_lst = []
        Ns = len((src_lst))
        for k, s in enumerate(src_lst):
            bs = source == s
            for m, t in enumerate(tgt_lst):
                bt = target == t
                b = bs & bt
                if (np.sum(b) > 0):
                    if s not in sl_lst:
                        sn = len(sl_lst)
                        sl_lst.append(s)
                    else:
                        for n, lbl in enumerate(sl_lst):
                            if s == lbl:
                                sn = n
                                break

                    if t not in tl_lst:
                        tn = len(tl_lst) + Ns
                        tl_lst.append(t)
                    else:
                        for n, lbl in enumerate(tl_lst):
                            if t == lbl:
                                tn = n + Ns
                                break

                    src.append(sn)
                    tgt.append(tn)
                    val.append(np.sum(b))
                    label_lst = sl_lst + tl_lst
                    nn_cnt += 1

        if (nn == 0): # | (nn_cnt == 0):
            src2 = src
            tgt2 = tgt
        else:
            lbl_ary = np.array(lbl_all)
            sseq = np.arange(len(lbl_ary))
            src2 = []
            for a in src:
                s = sl_lst[a]
                b = lbl_ary == s
                if np.sum(b) == 1:
                    m = sseq[b][0]
                    src2.append(m)
                else:
                    print('ERROR ... S')
            
            # src2 = [(a + len(lbl_all) - len(sl_lst)) for a in src]
            tgt2 = [(a + len(lbl_all) - len(sl_lst)) for a in tgt]
        
        sall = sall + copy.deepcopy(src2)
        tall = tall + copy.deepcopy(tgt2)
        vall = vall + copy.deepcopy(val)
        if nn == 0:
            lbl_all = copy.deepcopy(label_lst)
        else:
            lbl_all = lbl_all + copy.deepcopy(tl_lst)
    '''
    mat = np.array([sall,tall,vall])
    print(mat)
    print(lbl_all)
    '''      
        
    link = dict(source = sall, target = tall, value = vall)
    node = dict(label = lbl_all, pad=50, thickness=5)
    data = go.Sankey(link = link, node=node)
    layout = go.Layout(height = H, width = W)
    # plot
    fig = go.Figure(data, layout)
    if title is not None:
        fig.update_layout(
            title={
                'text': '<span style="font-size: ' + '%i' % fs + 'px;">' + title + '</span>',
                'y':title_y,
                'x':0.5,
                # 'font': 12,
                'xanchor': 'center',
                'yanchor': 'top'})    
    fig.show()   
    return


### Example 
# plot_population(df_pct, figsize=(6, 4), dpi = 80, return_fig = False)
# df_cnt
    
def plot_population(df_pct, bar_width = 0.6, title = None, title_fs = 12, ylabel = None,
                    label_fs = 11, tick_fs = 10, xtick_rot = 45, xtick_ha = 'center',
                    legend_fs = 10, legend_loc = 'upper left', bbox_to_anchor = (1,1), 
                    legend_ncol = 1, cmap = 'Spectral', figsize=(5, 3), dpi = 100):    

    """
    ------------------------------------------------------------
    📌 Population Composition / Stacked Bar Plot
    ------------------------------------------------------------
    Visualizes category proportions across groups as a stacked bar chart.
    Each column in `df_pct` is treated as one population/category.

    Parameters
    ----------
    df_pct : pd.DataFrame
        Index → groups/samples  
        Columns → categories (values should be fractions or %)

    bar_width : float (default=0.6)
        Width of each bar.

    title : str or None
        Plot title.

    title_fs, label_fs, tick_fs : int
        Font sizes.

    ylabel : str or None
        Y-axis label (e.g., "Proportion", "Percentage (%)").

    xtick_rot : int
        X-tick rotation angle.

    xtick_ha : {"left","center","right"}
        Tick label alignment.

    legend_fs : int
        Legend font size.

    legend_loc : str
        Matplotlib-compatible legend location.

    bbox_to_anchor : tuple
        Legend anchor position.

    legend_ncol : int
        Number of columns in legend.

    cmap : str or matplotlib colormap
        Colormap used to generate stacked bar colors (default: Spectral).

    figsize : (float,float)
        Figure size (inches).

    dpi : int
        Image resolution.

    Returns
    -------
    None
        Displays a stacked bar plot of the population (%) distribution.


    ------------------------------
    🔹 Example Usage
    ------------------------------
    >>> df = pd.DataFrame({
    ...     "Tumor":   [0.3, 0.6, 0.5],
    ...     "Immune":  [0.5, 0.3, 0.4],
    ...     "Stroma":  [0.2, 0.1, 0.1]
    ... }, index=["Pt1","Pt2","Pt3"])

    >>> plot_population(
    ...     df,
    ...     title="Cell Population Composition",
    ...     ylabel="Fraction",
    ...     xtick_rot=30
    ... )
    """
    
    if cmap is None:
        cmap = 'Spectral'
    color_map = plt.get_cmap(cmap)
    color = color_map(np.arange(df_pct.shape[1])/df_pct.shape[1])

    fig = plt.figure(dpi = dpi)
    ax = df_pct.plot.bar(stacked = True, rot = xtick_rot, figsize = figsize, 
                         color = color, width = bar_width)
    ax.legend( list(df_pct.columns.values), bbox_to_anchor=bbox_to_anchor, 
               loc = legend_loc, fontsize = legend_fs, ncol = legend_ncol )
    plt.xticks(fontsize=tick_fs, ha = xtick_ha)
    plt.yticks(fontsize=tick_fs)
    if isinstance(ylabel, str):
        plt.ylabel(ylabel, fontsize = label_fs)
    plt.title(title, fontsize = title_fs)
    plt.show()
    return


def get_sample_and_group_from_sample_ext( sample_ext ):

    idx = list(sample_ext)
    slst = []
    clst = []
    for i in idx:
        p = i.find(' ')
        if p >= 0:
            clst.append(i[:p])
            slst.append(i[(p+1):])
        else:
            clst.append('-')
            slst.append(i)
            
    return slst, clst

    
def plot_population_grouped(
    df_pct,
    sample_group_map = None,
    sort_by = [],
    bar_width = 0.6,
    title = None,
    title_y_pos = 1.1,
    title_fs = 14,
    ylabel = None,
    label_fs = 11,
    tick_fs = 10,
    xtick_rot = 45,
    xtick_ha = 'center',
    legend_fs = 10,
    legend_loc = 'upper left',
    bbox_to_anchor = (1,1),
    legend_ncol = 1,
    cmap = 'Spectral',
    figsize=(5, 3),
    dpi = 100,
    wspace=0.06,
    hspace=0.25,
):

    """
    ------------------------------------------------------------
    📌 Group-wise stacked bar plot of population composition
    ------------------------------------------------------------
    Draws separate stacked bar plots for each sample group (e.g.
    condition, cohort, cluster), where each bar corresponds to a
    sample and each stack represents a population/category.

    Group information can be provided in three ways:
      1) `df_pct` already has a 'Group' column
      2) `sample_group_map` dict: {sample_id → group_name}
      3) Parsable sample name extension via
         `get_sample_and_group_from_sample_ext(...)`

    Parameters
    ----------
    df_pct : pd.DataFrame
        Rows   → samples  
        Columns→ populations/categories (plus optional 'Group')

    sample_group_map : dict or None
        Mapping from sample ID (index of df_pct) to group label.
        If None:
            - If 'Group' column exists: use that
            - Else: infer (sample, group) from index names via helper

    sort_by : list (default=[])
        If non-empty, used as column name(s) to sort samples within
        each group (e.g. sort_by=["Tumor"]).

    bar_width : float
        Width of each bar.

    title : str or None
        Overall figure title (suptitle).

    title_y_pos : float
        Suptitle y position (0~1).

    title_fs, label_fs, tick_fs : int
        Font sizes for title, axis labels, and ticks.

    ylabel : str or None
        Y-axis label for the first panel (e.g. "Fraction").

    xtick_rot : int
        X-tick rotation angle.

    xtick_ha : {"left","center","right"}
        X-tick horizontal alignment.

    legend_fs : int
        Legend font size.

    legend_loc : str
        Legend anchor location (matplotlib style).

    bbox_to_anchor : tuple
        Legend anchor coordinates.

    legend_ncol : int
        Number of columns in the legend.

    cmap : str or matplotlib colormap
        Colormap for stacked categories (default: 'Spectral').

    figsize : (float,float)
        Base figure size per panel; total width is scaled by
        number of panels and panel widths.

    dpi : int
        Figure resolution.

    wspace, hspace : float
        Horizontal and vertical spacing between subplots.

    ------------------------------------------------------------
    Returns
    -------
    None
        Displays a multi-panel stacked bar plot:
          • One panel per Group
          • Bars = samples, stacks = categories

    ------------------------------------------------------------
    Example
    -------
    >>> plot_population_grouped(
            df_pct,
            title="Cell-type proportion by cohort",
            ylabel="Fraction",
            sort_by=["Tumor"]
        )
    """
    
    df = df_pct.copy(deep = True)
    if 'Group' in list(df.columns.values):
        sample_group_map = dict(zip( df.index.values, df['Group'] ))
        # df = df.drop( columns = ['Group'] )  
    elif sample_group_map is None:
        slst, clst = get_sample_and_group_from_sample_ext( df_pct.index.values )                
        sample_group_map = dict(zip( slst, clst ))
        
        df = pd.DataFrame( np.array(df), index = slst, columns = df_pct.columns )
        df['Group'] = clst
    else:
        df['Group'] = list(df.index.values)
        df['Group'] = df['Group'].replace(sample_group_map)

    if cmap is None:
        cmap = 'Spectral'
    color_map = plt.get_cmap(cmap)
    color = color_map(np.arange(df.drop(columns = ['Group']).shape[1])/df.drop(columns = ['Group']).shape[1])

    num_p = []

    glst = list(df['Group'].unique())
    glst.sort()

    cnt = df['Group'].value_counts()
    for g in glst:
        num_p.append(cnt.loc[g])

    nr, nc = 1, len(glst)
    fig, axes = plt.subplots(nrows=nr, ncols=nc, constrained_layout=False, 
                             gridspec_kw={'width_ratios': num_p}, dpi = dpi)
    fig.tight_layout() 
    if title is not None: 
        fig.suptitle(title, x = 0.5, y = title_y_pos, fontsize = title_fs, ha = 'center')
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=wspace, hspace=hspace)

    cnt = 0
    for j, g in enumerate(glst):
        b = df['Group'] == g
        dft = df.loc[b,:].drop(columns = ['Group'])
        if len(sort_by) > 0:
            dft = dft.sort_values(sort_by)

        if nc <= 1: ax_sel = axes
        else: ax_sel = axes[j+cnt]
            
        ax = dft.plot.bar(width = bar_width, stacked = True, ax = ax_sel, 
                          figsize = figsize, legend = None, color = color)
        ax.set_title('%s' % (g), fontsize = title_fs-2)
        if j != 0:
            # ax.set_yticks([])
            pass
        else:
            if isinstance(ylabel, str):
                ax.set_ylabel(ylabel, fontsize = label_fs)

        ax.tick_params(axis='x', labelsize=tick_fs) # , rotation = xtick_rot)
        ax.tick_params(axis='y', labelsize=tick_fs)
        labels = ax.get_xticklabels()
        ax.set_xticklabels(labels, rotation=xtick_rot, ha=xtick_ha)
            
        if g == glst[-1]: 
            ax.legend(dft.columns.values, loc = legend_loc, bbox_to_anchor = bbox_to_anchor, 
                       fontsize = legend_fs, ncol = legend_ncol)  
        else:
            pass
    plt.show()
    
    return


def plot_pct_box(
    df_pct,
    sg_map = None,
    ncols = 3,
    figsize = None,
    dpi = 100,
    title = None,
    title_y_pos = 1.05,
    title_fs = 14,
    rename_cells = None,
    label_fs = 11,
    tick_fs = 10,
    xtick_rot = 0,
    xtick_ha = 'center',
    group_order = None,
    annot = True,
    annot_ref = None,
    annot_fmt = 'simple',
    annot_fs = 10,
    ws_hs = (0.3, 0.3),
    ylabel = None,
    cmap = 'tab10',
    stripplot = True,
    stripplot_ms = 1,
    stripplot_jitter = True,
):
    """
    ------------------------------------------------------------
    📌 Boxplot of population proportions by group (multi-panel)
    ------------------------------------------------------------
    For each column (e.g., cell type / population) in df_pct, this
    function draws a boxplot across groups (conditions/cohorts) and
    arranges them in a grid of subplots.

    Optionally:
      • Infers group from 'Group' column or `sg_map`
      • Re-labels cell names using `rename_cells`
      • Adds significance annotations via statannotations (Annotator)
      • Overlays stripplot points on top of the boxplot

    Parameters
    ----------
    df_pct : pd.DataFrame
        Rows   → samples  
        Columns→ populations (plus optional 'Group' column)

    sg_map : dict or pd.Series or None
        Mapping from sample ID (index of df_pct) to group label.
        If df_pct has 'Group' column, that is used and removed.
        If Series, index = sample, value = group.

    ncols : int
        Number of subplot columns (grid layout).

    figsize : (float,float) or None
        Base panel size. If None:
            width ≈ 3 * ncols, height ≈ 3 * nrows

    dpi : int
        Figure resolution.

    title : str or None
        Global figure title (suptitle).

    title_y_pos : float
        Suptitle y position.

    title_fs : int
        Suptitle font size.

    rename_cells : dict or None
        Mapping used to rename columns (e.g., markers or cell types)
        in subplot titles:
            { "Tumor_CD8": "CD8⁺ Tumor", ... }

    label_fs, tick_fs : int
        Font sizes for axis labels and tick labels.

    xtick_rot : int
        X-axis tick rotation angle.

    xtick_ha : {"left","center","right"}
        X-tick alignment.

    group_order : list or None
        Explicit order of group labels on the x-axis.

    annot : bool
        If True, add statistical annotations using
        `statannotations.Annotator`.

    annot_ref : str or None
        Reference group name for pairwise tests.
        If provided and present in groups:
            pairs = (annot_ref, other_group)
        Else:
            all pairwise combinations are used.

    annot_fmt : str
        Format of annotation text (e.g., 'simple', 'star').

    annot_fs : int
        Font size of annotation text.

    ws_hs : (float,float)
        (wspace, hspace) spacing between subplots.

    ylabel : str or None
        Y-axis label for leftmost plots.

    cmap : str or palette
        Color palette for box and strip plots.

    stripplot : bool
        If True, overlay scatter points on top of boxplots.

    stripplot_ms : float
        Stripplot marker size.

    stripplot_jitter : bool
        Whether to jitter stripplot points horizontally.

    ------------------------------------------------------------
    Returns
    -------
    None
        Displays a grid of boxplots, one per population/column in df_pct.

    ------------------------------------------------------------
    Example
    -------
    >>> plot_pct_box(
            df_pct,
            sg_map=sample_group_series,
            ncols=4,
            title="Cell-type fractions per condition",
            ylabel="Fraction",
            annot=True,
            annot_ref="CTRL"
        )
    """

    title2_fs = None
    if title2_fs is None:
        title2_fs = title_fs - 2
        
    df = df_pct.copy(deep = True)
    if 'Group' in list(df.columns.values):
        sg_map = dict(zip( df.index.values, df['Group'] ))
        df = df.drop( columns = ['Group'] )
    elif isinstance(sg_map, pd.Series):
        sg_map = dict(zip( df.index.values, sg_map ))
    
    ## index 이름에서 '--'를 '\n'로 대체
    idx_org = list(df.columns.values)
    idx_new = [s.replace('--', '\n') for s in idx_org]
    rend = dict(zip(idx_org, idx_new))
    df = df.rename(columns = rend)
        
    # nr, nc = nr_nc
    nc = ncols
    nr = int(np.ceil(df.shape[1]/nc))
    if figsize is None:
        figsize = (3*nc,3*nr)
    else:
        figsize = (figsize[0]*nc,figsize[1]*nr)
        
    ws, hs = ws_hs
    fig, axes = plt.subplots(figsize = figsize, dpi=dpi, nrows=nr, ncols=nc, constrained_layout=False)
    fig.tight_layout() # Or equivalently,  "plt.tight_layout()"
    if title is not None:
        fig.suptitle('%s' % title, x = 0.5, y = title_y_pos, fontsize = title_fs, ha = 'center')
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=ws, hspace=hs)

    items = list(df.columns.values)

    df['Group'] = list(df.index.values)
    df['Group'] = df['Group'].replace(sg_map)

    lst = df['Group'].unique()

    cnt = 0
    for kk, item in enumerate(items):
        plt.subplot(nr,nc,cnt+1)
        b = df[item].isnull()
        pcnt = df.loc[~b,'Group'].value_counts()
        b1 = pcnt > 1
        group_sel = pcnt.index.values[b1].tolist()

        if len(group_sel) > 1:
            b = (~b) & df['Group'].isin(group_sel)
            
            lst = df.loc[b, 'Group'].unique()
            lst_pair = []
            if annot_ref in lst:
                for k, l1 in enumerate(lst):
                    if l1 != annot_ref:
                        lst_pair.append((annot_ref, l1))
            else:
                for k, l1 in enumerate(lst):
                    for j, l2 in enumerate(lst):
                        if j <  k:
                            lst_pair.append((l1, l2))
        
            ax = sns.boxplot(data = df.loc[b,:], x = 'Group', y = item, order = group_order,
                             hue = 'Group', palette=cmap )
            if stripplot:
                sns.stripplot(x='Group', y=item, data=df.loc[b,:],  
                              color="black", order = group_order, size = stripplot_ms, 
                              jitter = stripplot_jitter )
            if cnt%nc == 0: 
                ax.set_ylabel(ylabel, fontsize = label_fs)                
            else: 
                ax.set_ylabel(None)
                
            if cnt >= nc*(nr-1): 
                ax.set_xlabel('Condition', fontsize = label_fs)
            else: 
                ax.set_xlabel(None)

            title = item
            if (rename_cells is not None) & isinstance(rename_cells, dict):
                for key in rename_cells.keys():
                    title = title.replace(key, rename_cells[key])
            ax.set_title(title, fontsize = title2_fs)
            
            if cnt < (nr*nc - nc):
                # plt.xticks([])
                plt.xticks(rotation = xtick_rot, ha = xtick_ha, fontsize = tick_fs)
                plt.yticks(fontsize = tick_fs)
            else:
                plt.xticks(rotation = xtick_rot, ha = xtick_ha, fontsize = tick_fs)
                plt.yticks(fontsize = tick_fs)
    
            if annot:
                '''
                add_stat_annotation(ax, data=df.loc[b,:], x = 'Group', y = item, 
                                    order = group_order,
                            box_pairs=lst_pair, loc='inside', fontsize = annot_fs,
                            test='t-test_ind', text_format=annot_fmt, verbose=0)
                '''
                annotator = Annotator(ax, pairs=lst_pair, data=df.loc[b,:], 
                                      x="Group", y=item, order=group_order)
                annotator.configure(test='t-test_ind', text_format=annot_fmt, 
                                    loc='inside', verbose=False, show_test_name=False,
                                    fontsize = annot_fs)
                annotator.apply_and_annotate()   

            cnt += 1
            #'''
    
    if (cnt < (nr*nc)):
        if (nr == 1):
            for k in range(nr*nc - cnt):
                axes[cnt%nc + k].axis("off")
        else:
            for k in range(nr*nc - cnt):
                r = nr - int(k/nc)
                axes[r-1][nc - k%nc -1].axis("off")
        
    plt.show()
    return 


import numbers

def plot_violin(
    df,
    genes_lst,
    group_col = 'group',
    scale = 'width',
    group_order = None,
    inner = 'box',
    width = 0.9,
    linewidth = 0.3,
    bw = 'scott',
    figsize = (3,2),
    dpi = 100,
    text_fs = 10,
    title = 'Title',
    title_fs = 14,
    title_y_pos = 1,
    label_fs = 11,
    tick_fs = 10,
    xtick_rot = 0,
    xtick_ha = 'center',
    ncols = 2,
    wspace = 0.15,
    hspace = 0.4,
    ylim = None,
    ylabel = None,
    cmap = 'tab10',
):
    """
    ------------------------------------------------------------
    📌 Multi-gene violin plots of expression by group
    ------------------------------------------------------------
    For each gene in `genes_lst`, this function draws a violin plot
    stratified by `group_col` (e.g., condition, cluster, batch) and
    arranges them in a grid of subplots.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain:
          • expression columns for genes in `genes_lst`
          • a grouping column `group_col` (e.g. 'cluster')

    genes_lst : list of str
        List of gene (or feature) column names to plot.

    group_col : str
        Column in `df` used for grouping on the x-axis.

    scale : {"width","area","count"}
        violinplot `density_norm` argument controlling scaling.

    group_order : list or None
        Explicit order of groups on the x-axis.

    inner : {"box","quartile","point",None}
        Seaborn `inner` style for violinplot.

    width : float
        Total width of each violin.

    linewidth : float
        Line width of violin border.

    bw : str or float
        Bandwidth method passed to seaborn (`bw_method`).

    figsize : (float,float)
        Base per-panel size; final figure scales with `ncols` and rows.

    dpi : int
        Figure resolution.

    text_fs : int
        Reserved (not heavily used; can be used for annotations).

    title : str or None
        Global figure title (suptitle).

    title_fs : int
        Suptitle font size.

    title_y_pos : float
        Suptitle vertical position (0~1).

    label_fs, tick_fs : int
        Font sizes for axes labels and ticks.

    xtick_rot : int
        Rotation angle of x-axis tick labels.

    xtick_ha : {"left","center","right"}
        Horizontal alignment of x tick labels.

    ncols : int
        Number of subplot columns (grid layout).

    wspace, hspace : float
        Horizontal / vertical spacing between subplots.

    ylim : list, tuple, or list-of-lists or None
        Y-axis range control:
          • single [ymin, ymax] → applied to all plots
          • list of per-gene ranges: [[ymin1,ymax1], [ymin2,ymax2], ...]

    ylabel : str or None
        Y-axis label for the first column.

    cmap : str or palette
        Color palette for violin hues (based on `group_col`).

    ------------------------------------------------------------
    Returns
    -------
    None
        Displays a grid of violin plots, one per gene.

    ------------------------------------------------------------
    Example
    -------
    >>> plot_violin(
            df_expr,
            genes_lst=["CXCL8","NAMPT","IL1B"],
            group_col="condition",
            ncols=2,
            ylabel="log2 TPM + 1",
            title="Key inflammatory genes"
        )
    """
    
    nr, nc = int(np.ceil(len(genes_lst)/ncols)), int(ncols) # len(df_deg_dct.keys())
    fig, axes = plt.subplots(figsize = (figsize[0]*nc,figsize[1]*nr), nrows=nr, ncols=nc, # constrained_layout=True, 
                             gridspec_kw={'width_ratios': [1]*nc}, dpi = dpi)
    fig.tight_layout() 
    if title is not None:
        fig.suptitle(title, x = 0.5, y = title_y_pos, fontsize = title_fs, ha = 'center')
        
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, 
                        wspace=wspace, hspace=hspace)
    cnt = 0
    for j, gene in enumerate(genes_lst): 
    
        plt.subplot(nr,nc, int(j+1))
        sns.violinplot(x = group_col, y = gene, data = df, density_norm = scale, 
                       linewidth = linewidth, hue = group_col, palette=cmap,
                       order = group_order, width = width, inner = inner, bw_method = bw)
        '''
        plt.title('%s' % (gene), fontsize = label_fs + 1)
        plt.yticks(fontsize = tick_fs)
        plt.xticks(None, rotation = xtick_rot, ha = xtick_ha, fontsize = tick_fs)
        plt.xlabel(None)
        if j%nc == 0: plt.ylabel('Log exp.', fontsize = label_fs)
        else: plt.ylabel(None)
        '''
        if ylim is not None:
            if isinstance( ylim, list ):
                if isinstance( ylim[0], numbers.Number ):
                    plt.ylim(ylim)
                elif isinstance( ylim[0], list ) & (len(ylim) > j):
                    plt.ylim(ylim[j])
        
        plt.title('%s' % (gene), fontsize = label_fs + 1)
        if j%nc == 0: 
            if isinstance( ylabel, str ):
                plt.ylabel( ylabel, fontsize = label_fs )
        else: plt.ylabel(None)
            
        if j >= nc*(nr-1): plt.xlabel('Condition', fontsize = label_fs)
        else: plt.xlabel(None)
        if j < (nr*nc - nc):
            plt.xticks([])
            plt.yticks(fontsize = tick_fs)
        else:
            plt.xticks(rotation = xtick_rot, ha = xtick_ha, fontsize = tick_fs)
            plt.yticks(fontsize = tick_fs)
        
        cnt += 1

    if nc*nr > len(genes_lst):
        for j in range(nc*nr-len(genes_lst)):
            k = j + len(genes_lst) + 1
            ax = plt.subplot(nr,nc,k)
            ax.axis('off')

    plt.show()
    return


## CPDB plot

###################################
### Plot functions for CellPhoneDB

def cci_get_all_pairs( cci_df_dct ):
    
    lst = list(cci_df_dct.keys())
    lst.sort()
    
    gps = []
    cps = []
    for g in lst:
        dfv = cci_df_dct[g]
        gps = gps + list(dfv['gene_pair'])
        cps = cps + list(dfv['cell_pair'])
    
    gps = list(set(gps))
    cps = list(set(cps))

    return gps, cps


def plot_cci_dot_( dfv, n_gene_pairs = None, 
                  pval_cutoff = 0.05, mean_cutoff = 0.1, 
                  target_cells = [], target_genes = [], 
                  legend_fs = 11, legend_mkr_sz = 6, rename_cells = None,
                  tick_fs = 6, xtick_rot = 90, xtick_ha = 'center', 
                  title = None, title_fs = 14, dot_size_max = 1,
                  dpi = 100, swap_ax = False, cmap = None,
                  gene_pair_lst = None, cell_pair_lst = None, y_scale = 1.2 ):
                  # plot_all_gene_pairs = False, plot_all_cell_pairs = False ):

    """
    -------------------------------------------------------------------------
    📌 Dotplot visualization for Cell–Cell Interaction (CCI) results
    -------------------------------------------------------------------------
    Plots ligand–receptor interaction signals using dot sizes for
    significance (-log10(p)) and dot color for interaction strength
    (log2(mean expression or L-R communication score)).

    This function is designed for CellPhoneDB/CellChat/NicheNet-like results,
    where each row represents one ligand–receptor pair between two cell types.

    Parameters
    ----------
    dfv : pd.DataFrame
        Must contain columns:
            ['cell_A','cell_B','gene_A','gene_B','gene_pair','cell_pair',
             'mean','pval']
    
    n_gene_pairs : int or None
        If None → filter by cutoff (p ≤ pval_cutoff & mean ≥ mean_cutoff)
        If int  → select top N gene-pairs ranked by p-value & mean.

    pval_cutoff : float
        Interaction significance threshold.

    mean_cutoff : float
        Minimum mean expression/interaction score.

    target_cells : list
        Filter only interactions where both cell types ∈ this list.

    target_genes : list
        Filter only gene pairs involving any gene in this list.

    rename_cells : dict or None
        Maps cell names to short labels → useful for figure layout.

    swap_ax : bool
        If True  → X-axis = genes, Y-axis = cell pairs
        If False → X-axis = cell pairs, Y-axis = gene pairs

    cmap : matplotlib colormap
        Dot color → log2(mean score)

    gene_pair_lst / cell_pair_lst : list or None
        Custom ordering for row/column layout.

    y_scale : float
        Vertical stretching factor to improve readability.

    Returns
    -------
    None
        Shows dotplot directly.

    Interpretation
    --------------
    • Dot SIZE  → -log10(p)  (larger = more significant)
    • Dot COLOR → log2(mean score) (darker = stronger communication)
    • X-axis    → Cell pair interaction
    • Y-axis    → Ligand–Receptor gene pair

    Example
    -------
    plot_cci_dot_(
        df_cci,
        pval_cutoff=0.05,
        mean_cutoff=0.1,
        target_cells=["T", "Cancer", "Fibroblast"],
        title="TME interaction map",
        cmap="viridis"
    )
    -------------------------------------------------------------------------
    """    
    '''
    gene_pair_lst = None
    cell_pair_lst = None
    if plot_all_gene_pairs | plot_all_cell_pairs:
        gps, cps = cci_get_all_pairs( cci_df_dct )
        if plot_all_gene_pairs: gene_pair_lst = gps
        if plot_all_cell_pairs: cell_pair_lst = cps
    #'''
    
    dfs = dfv.copy(deep = True)
    
    if isinstance(target_cells, list):
        if (len(target_cells) > 0):
            b = (dfs['cell_A'].isin(target_cells) & dfs['cell_B'].isin(target_cells))
            dfs = dfs.loc[b,:]
        
    if isinstance(target_genes, list):
        if (len(target_genes) > 0):
            b = (dfs['gene_A'].isin(target_genes) | dfs['gene_B'].isin(target_genes))
            dfs = dfs.loc[b,:]
    
    if n_gene_pairs is None:
        dfs = dfs.sort_values(by = ['gene_pair', 'cell_pair'])
        b = dfs['pval'] <= pval_cutoff
        b = b & dfs['mean'] >= mean_cutoff    
        dfp = dfs.loc[b,:]
    else:
        dfs['neg_mean'] = -dfs['mean']
        dfp = dfs.sort_values(by = ['pval', 'neg_mean'], ascending = True)
        ilst = dfp['gene_pair'].tolist()
        ilst2 = []
        j = 0
        for j, i in enumerate(ilst):
            if len(list(set(ilst[:j]))) > n_gene_pairs:
                break                
        dfp = dfp.iloc[:j]
    
    if dfp.shape[0] == 0:
        print('WARNING: no interactions met the conditions you provide. ')
        return
    else:
        if (rename_cells is not None) & isinstance(rename_cells, dict):
            cell_pairs = list(dfp['cell_pair'])
            cell_pairs_new = []
            for i in cell_pairs:
                for key in rename_cells.keys():
                    i = i.replace(key, rename_cells[key])
                cell_pairs_new.append(i)
            dfp['cell_pair'] = cell_pairs_new
                
        dfp = dfp.sort_values(by = ['gene_pair', 'cell_pair'])
        if swap_ax == False:
            a = 'gene_pair'
            b = 'cell_pair'
            apl = gene_pair_lst
            bpl = cell_pair_lst
        else:
            b = 'gene_pair'
            a = 'cell_pair'
            apl = cell_pair_lst 
            bpl = gene_pair_lst

        if apl is None:
            y = len(set(dfp[a]))
        else:
            y = len(apl)
            
        if bpl is None:
            x = len(set(dfp[b]))
        else:
            x = len(bpl)
        
        print('%i %ss, %i %ss found' % (y, a, x, b))
        
        pv = -np.log10(dfp['pval']+1e-10).round()
        pvmn, pvmx = int(np.min(pv)), int(np.max(pv))
        
        mn = np.log2((1+dfp['mean']))
        np.min(mn), np.max(mn)    
        
        w = x/6
        # sc.settings.set_figure_params(figsize=(w, w*y_scale*(y/x)), 
        #                               dpi=dpi, facecolor='white')
        plt.rcParams['figure.figsize'] = (w, w*y_scale*(y/x))      
        plt.rcParams['figure.dpi'] = dpi             
        fig, ax = plt.subplots()

        if apl is None:
            a_lst = list(dfp[a].unique())
        else:
            a_lst = apl
        a_lst.sort()
        
        if bpl is None:
            b_lst = list(dfp[b].unique())
        else:
            b_lst = bpl
        b_lst.sort()

        ax.autoscale(False)
        # Set the sorted y-ticks.
        La = len(a_lst)
        ax.set_yticks(np.arange(La))
        ax.set_yticklabels(a_lst)
        ax.set_ylim([-1, La])
        y_map = dict(zip(a_lst, list(np.arange(La))))
        
        # Set the x-ticks.
        Lb = len(b_lst)
        ax.set_xticks(np.arange(Lb))
        ax.set_xticklabels(b_lst)  # `ax.set_xticklabels("abcde")` would work too.
        ax.set_xlim([-1, Lb])
        x_map = dict(zip(b_lst, list(np.arange(Lb))))
        
        mul = legend_mkr_sz*dot_size_max*0.6
        lst_b = [x_map[x] for x in list(dfp[b])]
        lst_a = [y_map[y] for y in list(dfp[a])]
        
        scatter = ax.scatter(lst_b, lst_a, s = pv*mul, c = mn, 
                             linewidth = 0, cmap = cmap)
    
        kw = dict(prop="colors", num=5, fmt="{x:.1f}", # color=scatter.cmap(0.7), 
                  func=lambda s: (s))
        legend1 = ax.legend(*scatter.legend_elements(**kw),
                            loc='upper left', 
                            bbox_to_anchor=(1+1/x, 0.5), 
                            title=' log2(m) ', 
                            fontsize = legend_fs)
        legend1.get_title().set_fontsize(legend_fs)
        ax.add_artist(legend1)
    
        # produce a legend with a cross section of sizes from the scatter
        kw = dict(prop="sizes", num=4, fmt="{x:.0f}", # color=scatter.cmap(0.7), 
                  func=lambda s: (s/mul))
        legend2 = ax.legend(*scatter.legend_elements(**kw),
                            loc='lower left', 
                            bbox_to_anchor=(1+1/x, 0.5), 
                            title='-log10(p)', 
                            fontsize = legend_fs)        
        legend2.get_title().set_fontsize(legend_fs)
    
        if title is not None: plt.title(title, fontsize = title_fs)
        plt.yticks(fontsize = tick_fs)
        plt.xticks(rotation = xtick_rot, ha=xtick_ha, fontsize = tick_fs)
        plt.margins(x=0.6/x, y=0.6/y)
        plt.grid()
        plt.show()   
    return


def plot_cci_dot( cci_df_dct, n_gene_pairs = None, 
                  target_cells = [], target_genes = [], 
                  pval_cutoff = 0.05, mean_cutoff = 0.1, 
                  legend_fs = 11, legend_mkr_sz = 6, rename_cells = None,
                  tick_fs = 6, xtick_rot = 90, xtick_ha = 'center', 
                  title = None, title_fs = 14, dot_size_max = 1,
                  dpi = 100, swap_ax = False, cmap = None,
                  gene_pair_lst = None, cell_pair_lst = None, y_scale = 1.2 ):

    """
    -------------------------------------------------------------------------
    📌 Wrapper for CCI dotplot — supports single DF or multiple groups
    -------------------------------------------------------------------------
    If input is a single DataFrame → draw one dotplot.
    If input is dict(group → DataFrame) → draw one plot per group.

    Parameters
    ----------
    cci_df_dct : pd.DataFrame or dict of pd.DataFrame
        - Single CCI result table OR
        - Dictionary:  { "Tumor": df, "Normal": df, ... }

    n_gene_pairs : int or None
        If None → filter by cutoff (p ≤ pval_cutoff & mean ≥ mean_cutoff)
        If int  → select top N gene-pairs ranked by p-value & mean.

    pval_cutoff : float
        Interaction significance threshold.

    mean_cutoff : float
        Minimum mean expression/interaction score.

    target_cells : list
        Filter only interactions where both cell types ∈ this list.

    target_genes : list
        Filter only gene pairs involving any gene in this list.

    rename_cells : dict or None
        Maps cell names to short labels → useful for figure layout.

    swap_ax : bool
        If True  → X-axis = genes, Y-axis = cell pairs
        If False → X-axis = cell pairs, Y-axis = gene pairs

    cmap : matplotlib colormap
        Dot color → log2(mean score)

    gene_pair_lst / cell_pair_lst : list or None
        Custom ordering for row/column layout.

    y_scale : float
        Vertical stretching factor to improve readability.

    Returns
    -------
    If input = DataFrame  → single plot
    If input = dict       → list of plot objects

    Usage Examples
    --------------
    # 1) Single CCI dataset
    plot_cci_dot(df_cci, title="Interaction landscape")

    # 2) Compare multiple conditions
    plot_cci_dot(
        { "Tumor": df_tumor, "Normal": df_normal },
        target_cells=["T cell","Fibroblast"],
        n_gene_pairs=25
    )

    -------------------------------------------------------------------------
    """    
    '''
    if rename_cells is not None:
        if rename_cells == True:
            deg_base = adata.uns['analysis_parameters']['CCI_DEG_BASE']
            rename_dct = get_abbreviations()
            rename_cells = rename_dct[deg_base]
        elif isinstance( rename_cells, dict ):
            pass
        else:
            rename_cells = None
    '''

    if isinstance(cci_df_dct, pd.DataFrame):
        dfv = cci_df_dct
        ax = plot_cci_dot_( dfv, n_gene_pairs = n_gene_pairs, 
                      target_cells = target_cells, target_genes = target_genes, 
                      pval_cutoff = pval_cutoff, mean_cutoff = mean_cutoff, 
                      legend_fs = legend_fs, legend_mkr_sz = legend_mkr_sz, rename_cells = rename_cells,
                      tick_fs = tick_fs, xtick_rot = xtick_rot, xtick_ha = xtick_ha, 
                      title = title, title_fs = title_fs, dot_size_max = dot_size_max,
                      dpi = dpi, swap_ax = swap_ax, cmap = cmap,
                      gene_pair_lst = gene_pair_lst, cell_pair_lst = cell_pair_lst, y_scale = y_scale )
        return ax
    elif isinstance(cci_df_dct, dict):
        axes = []
        for g in cci_df_dct.keys():
            dfv = cci_df_dct[g]
            ax = plot_cci_dot_( dfv, n_gene_pairs = n_gene_pairs, 
                          target_cells = target_cells, target_genes = target_genes, 
                          pval_cutoff = pval_cutoff, mean_cutoff = mean_cutoff, 
                          legend_fs = legend_fs, legend_mkr_sz = legend_mkr_sz, rename_cells = rename_cells,
                          tick_fs = tick_fs, xtick_rot = xtick_rot, xtick_ha = xtick_ha, 
                          title = 'CCI for %s' % g, title_fs = title_fs, dot_size_max = dot_size_max,
                          dpi = dpi, swap_ax = swap_ax, cmap = cmap,
                          gene_pair_lst = gene_pair_lst, cell_pair_lst = cell_pair_lst, y_scale = y_scale )
            axes.append(ax)            
        return axes
        
    else:
        print('ERROR: The input was not suitably formatted. ')
        return None
        
    return


def cpdb_get_gp_n_cp(idx):
    
    items = idx.split('--')
    gpt = items[0]
    cpt = items[1]
    gns = gpt.split('_')
    ga = gns[0]
    gb = gns[1]
    cts = cpt.split('|')
    ca = cts[0]
    cb = cts[1]
    
    return gpt, cpt, ga, gb, ca, cb
    
###########################    
### Circle plot for CCI ###
    
def center(p1, p2):
    return (p1[0]+p2[0])/2, (p1[1]+p2[1])/2

def norm( p ):
    n = np.sqrt(p[0]**2 + p[1]**2)
    return n

def vrot( p, s ):
    v = (np.array([[0, -1], [1, 0]]).dot(np.array(p)))
    v = ( v/norm(v) )
    return v #, v2
    
def vrot2( p, t ):
    v = (np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]]).dot(p))
    return v #, v2
    
def get_arc_pnts( cp, R, t1, t2, N):
    
    a = (t1 - t2)
    if a >= math.pi:
        t2 = t2 + 2*math.pi
    elif a <= -math.pi:
        t1 = t1 + 2*math.pi
    
    N1 = (N*np.abs(t1 - t2)/(2*math.pi))
    # print(N1)
    s = np.sign(t1 - t2)
    t = t2 + np.arange(N1+1)*(s*2*math.pi/N)
    # if t.max() > (math.pi*2): t = t - math.pi*2
    
    x = np.sin(t)*R + cp[0]
    y = np.cos(t)*R + cp[1]
    x[-1] = np.sin(t1)*R + cp[0]
    y[-1] = np.cos(t1)*R + cp[1]
        
    return x, y, a

def get_arc( p1, p2, R, N ):
    
    A = norm(p1 - p2)
    pc = center(p1, p2)
    
    a = np.sqrt((R*A)**2 - norm(p1 - pc)**2)
    c = pc + vrot(p1 - pc, +1)*a

    d1 = p1 - c
    t1 = np.arctan2(d1[0], d1[1])
    d2 = p2 - c
    t2 = np.arctan2(d2[0], d2[1])

    x, y, t1 = get_arc_pnts( c, R*A, t2, t1, N)
    
    return x, y, c


def get_circ( p1, R, N ):
    
    pp = np.arange(N)*(2*math.pi/N)
    px = np.sin(pp)*0.5
    py = np.cos(pp)
    pnts = np.array([px, py])
    
    t = -np.arctan2(p1[0], p1[1])
    pnts = vrot2( pnts, t+math.pi )*R
    pnts[0,:] = pnts[0,:] + p1[0]*(1+R)
    pnts[1,:] = pnts[1,:] + p1[1]*(1+R)
    x = pnts[0,:]
    y = pnts[1,:]
    c = np.array([0,0])
    
    return x, y, c


def plot_cci_circ( df_in, figsize = (10, 10), dpi = 10, title = None, title_fs = 16, 
                   text_fs = 14, num_fs = 12, margin = 0.08, alpha = 0.5, 
                   linewidth_max = 10, linewidth_log = False, 
                   R_curvature = 4, node_size = 10, rot = True, 
                   cmap = 'Spectral', ax = None, show = True):

    """
    -------------------------------------------------------------------------
    📌 Circular CCI plot (cell–cell interaction chord diagram style)
    -------------------------------------------------------------------------
    Draws a circular diagram where each node is a cell type and each edge
    represents directional interaction strength (e.g., number of significant
    ligand–receptor pairs or aggregated interaction score).

    The input is assumed to be a square matrix (cell × cell), where
    rows = sender cells and columns = receiver cells.

    Parameters
    ----------
    df_in : pd.DataFrame
        Square matrix of interaction strengths.
        - index : sender cell types
        - columns : receiver cell types
        - values : interaction weight (e.g., # of LR pairs, sum of scores)

    figsize : tuple
        Figure size passed to matplotlib if `ax` is None.

    dpi : int
        Resolution of the figure.

    title : str or None
        Main title of the plot.

    title_fs : int
        Font size for the title.

    text_fs : int
        Font size for node labels (cell type names).

    num_fs : int
        Font size for numeric labels along edges (interaction strength).

    margin : float
        Extra margin around the circular diagram.

    alpha : float
        Transparency for edges (0 = fully transparent, 1 = opaque).

    linewidth_max : float
        Maximum line width used for the strongest interaction.
        All other edges are scaled relative to this using `df_in.max().max()`.

    linewidth_log : bool
        If True, applies log2-transform to the line width after scaling.

    R_curvature : float
        Curvature parameter controlling how “bent” the connecting arcs are.
        Larger values → more curved paths.

    node_size : float
        Marker size for cell-type nodes on the circle.

    rot : bool
        If True, rotates node labels to better follow the circle direction.

    cmap : str or Colormap
        Matplotlib colormap name or object used for assigning colors
        to source cell types.

    ax : matplotlib.axes.Axes or None
        If provided, drawing is done on this axis.
        If None, a new figure and axis are created.

    show : bool
        If True, calls `plt.show()` at the end.

    Returns
    -------
    None
        The function draws the circular CCI plot in-place.

    Interpretation
    --------------
    • Each node around the circle is a cell type.
    • A curved arrow from cell A to cell B represents A → B communication.
    • Edge width  ~ interaction strength.
    • Edge color  ~ color assigned to the source cell type.
    • Numeric label at arc mid-point  ~ underlying value in df_in[A, B].

    Example
    -------
    # df_cci_mat: cell × cell matrix of interaction counts
    plot_cci_circ(
        df_cci_mat,
        title="Cell–cell interaction (Tumor sample)",
        linewidth_max=8,
        cmap="Spectral"
    )
    -------------------------------------------------------------------------
    """
    
    linewidth_scale = 0
    log_lw = linewidth_log
    lw_max = linewidth_max
    lw_scale = linewidth_scale
    
    Rs = 0.1
    N = 500
    R = R_curvature
    df = df_in.copy(deep = True)
    mxv = df_in.max().max()
    
    if ax is None: 
        plt.figure(figsize = figsize, dpi = dpi)
        ax = plt.gca()
        
    # color_lst = ['orange', 'navy', 'green', 'gold', # 'lime', 'magenta', \
    #         'turquoise', 'red', 'royalblue', 'firebrick', 'gray']
    # color_map = cm.get_cmap(cmap)
    color_map = colormaps[cmap]
    if df.shape[0] > 1:
        color_lst = [color_map(i/(df.shape[0]-1)) for i in range(df.shape[0])]
    else:
        mmm = 10
        color_lst = [color_map(i/(mmm-1)) for i in range(mmm)]

    clst = list(df.index.values) 

    M = df.shape[0]
    if M > 1:
        pp = np.arange(M)*(2*math.pi/M)
    else:
        pp = np.arange(mmm)*(2*math.pi/mmm)
    px = np.sin(pp)
    py = np.cos(pp)
    pnts = np.array([px, py])
    
    for j in range(M):
        p1 = pnts[:,j]
        for k in range(M):
            p2 = pnts[:,k]
            
            val = df.loc[clst[j], clst[k]]
            if lw_scale > 0:
                lw = val*lw_scale
            elif lw_max > 0:
                lw = val*lw_max/mxv
            else:
                lw = val
            if log_lw: lw = np.log2(lw)                    
                    
            if (df.loc[clst[j], clst[k]] != 0): # & (j!= k):

                if j == k:
                    x, y, c = get_circ( p1, 0.1, N )
                    K = int(len(x)*0.5)
                    d = vrot(p1, 1)
                    d = d*0.05/norm(d)
                elif (j != k) :
                    x, y, c = get_arc( p1, p2, R, N )

                    K = int(len(x)*0.5)
                    d = (p2 - p1)
                    d = d*0.05/norm(d)

                q2 = np.array([x[K], y[K]])
                q1 = np.array([x[K] - d[0], y[K] - d[1]])

                s = norm(q1 - q2)
                
                ha = 'center'
                if c[0] < -1:
                    ha = 'left'
                elif c[0] > 1:
                    ha = 'right'
                    
                va = 'center'
                if c[1] < -1:
                    va = 'bottom'
                elif c[1] > 1:
                    va = 'top'
                    
                if norm(q2) <= 0.7: # mnR*2:
                    ha = 'center'
                    va = 'center'
                    
                if ax is None: 
                    plt.plot(x, y, c = color_lst[j], linewidth = lw, alpha = alpha)
                    if j != k:
                        plt.arrow(q1[0], q1[1], q2[0]-q1[0], q2[1]-q1[1], linewidth = lw,
                              head_width=s/2, head_length=s, 
                              fc=color_lst[j], ec=color_lst[j])
                    plt.text( q2[0], q2[1], ' %i ' % val, fontsize = num_fs, 
                              va = va, ha = ha)
                else:
                    ax.plot(x, y, c = color_lst[j], linewidth = lw, alpha = alpha)
                    if j != k:
                        ax.arrow(q1[0], q1[1], q2[0]-q1[0], q2[1]-q1[1], linewidth = lw,
                              head_width=0.05*lw/lw_max, head_length=s, alpha = alpha, 
                              fc=color_lst[j], ec=color_lst[j])
                    ax.text( q2[0], q2[1], '%i' % val, fontsize = num_fs, 
                             va = va, ha = ha)

            elif (df.loc[clst[j], clst[k]] != 0) & (j== k):
                x, y, c = get_circ( p1, Rs, N )
                K = int(len(x)*0.5)
                d = vrot(p1, 1)
                d = d*0.05/norm(d)

                q2 = np.array([x[K], y[K]])
                q1 = np.array([x[K] - d[0], y[K] - d[1]])

                s = norm(q1 - q2)
                
                ha = 'center'
                if c[0] < -1:
                    ha = 'left'
                elif c[0] > 1:
                    ha = 'right'
                    
                va = 'center'
                if c[1] < -1:
                    va = 'bottom'
                elif c[1] > 1:
                    va = 'top'
                    
                if norm(q2) <= 0.7: # mnR*2:
                    ha = 'center'
                    va = 'center'
                    
                if ax is None: 
                    plt.plot(x, y, c = color_lst[j], linewidth = lw, alpha = alpha)
                    plt.arrow(q1[0], q1[1], q2[0]-q1[0], q2[1]-q1[1], linewidth = lw,
                              head_width=s/2, head_length=s, 
                              fc=color_lst[j], ec=color_lst[j])
                    plt.text( q2[0], q2[1], ' %i ' % val, fontsize = num_fs, 
                              va = va, ha = ha)
                else:
                    ax.plot(x, y, c = color_lst[j], linewidth = lw, alpha = alpha)
                    ax.arrow(q1[0], q1[1], q2[0]-q1[0], q2[1]-q1[1], linewidth = lw,
                              head_width=0.05*lw/lw_max, head_length=s, alpha = alpha, 
                              fc=color_lst[j], ec=color_lst[j])
                    ax.text( q2[0], q2[1], '%i' % val, fontsize = num_fs, 
                             va = va, ha = ha)
    if rot:
        rotation = 90 - 180*np.abs(pp)/math.pi
        b = rotation < -90
        rotation[b] = 180+rotation[b]
    else:
        rotation = np.zeros(M)
        
    for j in range(pnts.shape[1]):
        (x, y) = (pnts[0,j], pnts[1,j])
        
        ha = 'center'
        if x < 0:
            ha = 'right'
        else: 
            ha = 'left'
        va = 'center'
        if y == 0:
            pass
        elif y < 0:
            va = 'top'
        else: 
            va = 'bottom'
            
        if j < M:
            ct = clst[j]
            a = (df.loc[ct, ct] != 0)*(Rs*2)
            rot = rotation[j]
            cc = color_lst[j]
        else:
            ct = ''
            a = 0
            rot = 0
            cc = 'gray'
            
        if ax is None: 
            plt.plot( x, y, 'o', ms = node_size, c = cc)
            plt.text( x, y, ' %s ' % ct, fontsize = text_fs, 
                      ha = ha, va = va, rotation = rot)
        else:
            ax.plot( x, y, 'o', ms = node_size, c = cc)
            ax.text( x*(1+a), y*(1+a), '  %s  ' % ct, fontsize = text_fs, 
                     ha = ha, va = va, rotation = rot)

    if ax is None: 
        plt.xticks([])
        plt.yticks([])
        plt.margins(x=margin, y=margin)
    else:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.margins(x=margin, y=margin)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False) 
        
    if title is not None: ax.set_title(title, fontsize = title_fs )
        
    if show: plt.show()
    return


def plot_cci_circ_group( df_dct, target = [], 
                         rename_cells = None, remove_common = False,
                         ncol = 3, figsize = (8,7), dpi = 100,
                         title = None, title_y_pos = 1, title_fs = 18, 
                         text_fs = 16, num_fs = 12, margin = 0.08, alpha = 0.5, 
                         linewidth_max = 10, linewidth_log = False,  
                         R_curvature = 3, node_size = 10, rot = False, 
                         cmap = 'Spectral', wspace = 0.35, hspace = 0.2 ):

    """
    -------------------------------------------------------------------------
    📌 Multi-condition circular CCI plots (facet by group)
    -------------------------------------------------------------------------
    Wrapper around `plot_cci_circ` for comparing multiple conditions
    (e.g., Normal vs Tumor, or different time points).

    Internally uses `get_cci_ni_mat(df_dct, remove_common)` to convert
    each entry in `df_dct` into a cell × cell interaction matrix.

    Parameters
    ----------
    df_dct : dict
        Dictionary of CCI results per condition.
        - keys   : condition labels (e.g., "Normal", "Tumor")
        - values : pd.DataFrame
            Square matrix of interaction strengths.
            - index : sender cell types
            - columns : receiver cell types
            - values : interaction weight (e.g., # of LR pairs, sum of scores)

    target : list
        List of cell types to keep. If empty or None, use all cells.
        If non-empty, each condition must contain all target cell types
        (otherwise an error is raised).

    rename_cells : dict or None
        Optional mapping {old_name: new_name} applied to cell type names
        in all panels (useful for shortening long labels).

    remove_common : bool
        If True, `get_cci_ni_mat` removes interactions that are common
        across conditions (so each panel focuses on condition-specific
        interactions). Behavior depends on the implementation of
        `get_cci_ni_mat`.

    ncol : int
        Number of columns in the subplot grid.

    figsize : tuple
        Base figure size for a single panel; total figure size is
        scaled by (ncol, nrow).

    dpi : int
        Figure resolution.

    title : str or None
        Suptitle for the whole multi-panel figure.

    title_y_pos : float
        Y-position of the suptitle (in figure coordinates).

    title_fs : int
        Font size of the suptitle.

    text_fs : int
        Font size for node labels (cell type names) inside each panel.

    num_fs : int
        Font size for edge numeric values.

    margin : float
        Margin around each circular diagram.

    alpha : float
        Transparency of edges.

    linewidth_max : float
        Global maximum line width used for scaling.
        Actual per-panel line width is additionally scaled by each
        panel’s maximum value so that visual contrast is preserved.

    linewidth_log : bool
        If True, uses log2-transformed widths inside `plot_cci_circ`.

    R_curvature : float
        Curvature parameter passed to `plot_cci_circ`.

    node_size : float
        Node size passed to `plot_cci_circ`.

    rot : bool
        Whether to rotate node labels inside each panel.

    cmap : str or Colormap
        Color map passed to `plot_cci_circ`.

    wspace, hspace : float
        Horizontal and vertical spacing between subplot panels.

    Returns
    -------
    None
        Draws a grid of circular CCI plots, one per condition.

    Example
    -------
    # df_dct: { "Normal": df_norm_cci, "Tumor": df_tumor_cci }
    plot_cci_circ_group(
        df_dct,
        target=["T cell","B cell","Myeloid","Cancer"],
        rename_cells={"CD4+ T cells":"CD4T", "CD8+ T cells":"CD8T"},
        ncol=2,
        title="Cell–cell interactions across conditions"
    )
    -------------------------------------------------------------------------
    """
    
    df_lst = get_cci_ni_mat( df_dct, remove_common )
    if isinstance(rename_cells, dict):
        for k in df_lst.keys():
            df_lst[k].rename(columns = rename_cells, index = rename_cells, inplace = True)

    if target is None:
        df_lst2 = df_lst
    elif not isinstance(target, list):
        print('ERROR: targte must be a list of celltypes.')
        return 
    elif len(target) == 0:
        df_lst2 = df_lst
    else:
        ## check if target exists in the data
        b = True
        for key in df_lst.keys():
            celltypes = df_lst[key].columns.values.tolist()
            b = len(list(set(target).intersection(celltypes))) == len(target)
            if not b: break

        if not b:
            s = ''
            for t in target:
                s = s + '%s,' % t
            s = s[:-1]
            print('ERROR: %s not exists in the data.' % s)
            return
        else:
            df_lst2 = {}
            for key in df_lst.keys():
                df = df_lst[key]
                msk = df.copy(deep = True)
                msk.loc[:,:] = 0
                msk.loc[target,:] = 1
                msk.loc[:,target] = 1
                df_lst2[key] = df*msk
   
    n_max = 0
    for k in df_lst2.keys():
        n_max = max( df_lst2[k].max().max(), n_max )
    linewidth_scale = linewidth_max/(n_max + 0.01)
    lw_max_dict = {}
    for k in df_lst2.keys():
        lw_max_dict[k] = df_lst2[k].max().max()*linewidth_scale
    
    cond_lst = list(df_lst2.keys())
    cond_lst.sort()
    ws_hs = [wspace, hspace]
    
    R = R_curvature
    N = 500
    nc = ncol
    nr = int(np.ceil(len(cond_lst)/nc))
    # nr, nc = 1, int(len(cond_lst))
    fig, axes = plt.subplots(figsize = (figsize[0]*nc,figsize[1]*nr), nrows=nr, ncols=nc, # constrained_layout=False, 
                             gridspec_kw={'width_ratios': [1]*nc}, dpi = dpi)
    fig.tight_layout() 
    plt.subplots_adjust(left=0.025, bottom=0.025, right=0.975, top=0.975, wspace=ws_hs[0], hspace=ws_hs[1])
    if title is not None: plt.suptitle(title, fontsize = title_fs, y = title_y_pos)

    cnt = 0
    for j, k in enumerate(cond_lst):

        df = df_lst2[k]*(df_lst2[k] > 0).copy(deep = True)
        if df.shape[0] > 0:
            cnt += 1
            plt.subplot(nr,nc,cnt)

            if nr == 1: ax = axes[int(j)]
            else: ax = axes[int(j/nc)][j%nc]

            plot_cci_circ( df, title = k, title_fs = text_fs + 2, 
                           text_fs = text_fs, num_fs = num_fs, margin = margin, alpha = alpha, 
                           R_curvature = R_curvature, 
                           linewidth_max = lw_max_dict[k], # linewidth_max, 
                           # linewidth_scale = 0, # linewidth_scale, 
                           linewidth_log = linewidth_log, 
                           node_size = node_size, rot = rot, cmap = cmap, 
                           ax = ax, show = False)

    if cnt < (nr*nc):
        for k in range(int(nr*nc - cnt)):
            j = k + cnt
            ax = plt.subplot(nr,nc,j+1)
            ax.axis('off')

    plt.show()
    return


def plot_cnv_250810( adata_in, groupby = 'ploidy_dec', N_cells_min = 20,
              title = 'log2(CNR)', title_fs = 14, title_y_pos = 1.1, 
              label_fs = 12, tick_fs = 12, figsize = (12, 6), swap_axes = False, 
              var_group_rotation = 45, cmap='RdBu_r', vmax = 1, spot_llst = None,
              cnv_obsm_key = 'X_cnv', cnv_uns_key = 'cnv', spot_resample = 100,
              xlabel = 'Genomic spot', xtick_rot = 0, xtick_ha = 'center', 
              show_ticks = True, alpha = 0.3 ):

    pcnt = adata_in.obs[groupby].value_counts()
    bp = pcnt >= N_cells_min
    b = adata_in.obs[groupby].isin(list(pcnt.index.values[bp]))
    adata = adata_in[b,:].copy()
    
    X_cnv = adata.obsm[cnv_obsm_key]
    chrs = np.array([' ']*X_cnv.shape[1])

    if isinstance(cnv_uns_key, str):
        
        '''
        # clst = adata.uns[cnv_uns_key]['spot_to_chr_map']        
        # df_chr = pd.DataFrame( {'chr': clst} )
        
        df_chr_pos = adata.uns[cnv_uns_key]['df_chr_pos']        
        vg_pos = []
        vg_labels = []
        for c in df_chr_pos.index:
            start = df_chr_pos.loc[c,'start']
            end = df_chr_pos.loc[c,'end']
            vg_pos.append((start+5, end-5))
            vg_labels.append(c)
        '''
        
        chr_pos = adata.uns[cnv_uns_key]['chr_pos']
        df_chr_pos = pd.DataFrame({'chr_pos': list(chr_pos.values()), 'chr': list(chr_pos.keys()) }, index = chr_pos.keys())
        df_chr_pos = df_chr_pos.sort_values('chr_pos')
        # display(df_chr_pos)
        
        ## Get chromosome name for each loci in X_cnv
        chrs = []
        for i in range(df_chr_pos.shape[0]):
            if i < (df_chr_pos.shape[0]-1):
                start = list(df_chr_pos.iloc[i])[0]
                end = list(df_chr_pos.iloc[i+1])[0]
            else:
                start = list(df_chr_pos.iloc[i])[0]
                end = X_cnv.shape[1]
        
            chrs = chrs + list([df_chr_pos.index.values[i]]*int(end-start))
        
        df_chr = pd.DataFrame({'chr': chrs})
        
        lst = list(df_chr_pos['chr']) # list(df_chr['chr'].unique())
    
        ## Get vg_pos & vg_labels
        cnt = 0
        vg_pos = []
        vg_labels = []
        for i in lst:
            b = df_chr['chr'] == i
            vg_pos.append((cnt+5, cnt+np.sum(b)-5))
            vg_labels.append(i)
            cnt += np.sum(b)
        
        ## Create AnnData for plot
        ad = anndata.AnnData(X = X_cnv, var = df_chr, obs = adata.obs)
    else:
        vg_pos = None
        vg_labels = None
        ad = anndata.AnnData(X = X_cnv, obs = adata.obs)
        
    ad.var['spot_no'] = np.arange(len(ad.var.index.values))
    ad.var['spot_no'] = ad.var['spot_no'].astype(str)
    ad.var.set_index('spot_no', inplace = True)
    
    X = np.abs(ad.to_df())
    vmax = X.quantile([0.99]).mean(axis = 1)*2

    ax_dict = sc.pl.heatmap(ad, var_names = ad.var.index.values, groupby = groupby, 
                            show = False, figsize = figsize, swap_axes = swap_axes, 
                            var_group_positions = vg_pos, var_group_labels = vg_labels, 
                            var_group_rotation = var_group_rotation, 
                            cmap=cmap, vmax = vmax, vmin = -vmax, show_gene_labels = show_ticks)

    if spot_llst is not None:
        if isinstance(spot_llst, list):
            nlst = []
            for lst in spot_llst:
                s = '%i ~ %i' % (lst[0], lst[-1])
                nlst.append( s )
            slst = spot_llst
        else:
            nlst = list(spot_llst.keys())
            slst = list(spot_llst.values())
                
    ax_dict['heatmap_ax'].set_title(title, fontsize = title_fs, y = title_y_pos)
    if swap_axes:
        xtick_ha = 'right'
        
        if 'groupby_ax' in list(ax_dict.keys()):
            ax_dict['groupby_ax'].set_xlabel(groupby, fontsize = label_fs)
            ticks = ax_dict['groupby_ax'].get_xticklabels()
            ax_dict['groupby_ax'].set_xticklabels(ticks, fontsize = tick_fs)
        
        if xlabel is not None:
            ax_dict['heatmap_ax'].set_ylabel(xlabel, fontsize = label_fs)

        x_ticks = np.arange(0, len(ad.var.index.values), spot_resample)
        ax_dict['heatmap_ax'].set_yticks(x_ticks, x_ticks, rotation=xtick_rot, ha=xtick_ha, fontsize = tick_fs)

        if spot_llst is not None:
            for name, lst in zip (nlst, slst):
                L = ad.obs.shape[0]
                ax_dict['heatmap_ax'].add_patch(Rectangle((0, lst[0]), L, lst[-1]-lst[0], fill = True, 
                                                           edgecolor = 'gold', facecolor = 'gold', 
                                                           lw = 0.5, alpha = alpha))
                ax_dict['heatmap_ax'].text(int(L*0.01), lst[0], name, fontsize = tick_fs, 
                                           rotation = 0, va = 'center', ha = 'left')    
        pass
    else:
        if 'groupby_ax' in list(ax_dict.keys()):
            ax_dict['groupby_ax'].set_ylabel(groupby, fontsize = label_fs)
            ticks = ax_dict['groupby_ax'].get_yticklabels()
            ax_dict['groupby_ax'].set_yticklabels(ticks, fontsize = tick_fs)
        
        if xlabel is not None:
            ax_dict['heatmap_ax'].set_xlabel(xlabel, fontsize = label_fs)

        x_ticks = np.arange(0, len(ad.var.index.values), spot_resample)
        ax_dict['heatmap_ax'].set_xticks(x_ticks, x_ticks, rotation=xtick_rot, ha=xtick_ha, fontsize = tick_fs)

        if spot_llst is not None:
            for name, lst in zip (nlst, slst):
                L = ad.obs.shape[0]
                ax_dict['heatmap_ax'].add_patch(Rectangle((lst[0], -0.5), lst[-1]-lst[0], L, fill = True, 
                                                           edgecolor = 'gold', facecolor = 'gold', 
                                                           lw = 0.5, alpha = 0.3))
                ax_dict['heatmap_ax'].text(lst[0], int(L*0.01)-0.4, name, fontsize = tick_fs, 
                                           rotation = -90, va = 'top', ha = 'left')        
    
    # plt.show()
    return ax_dict


def plot_cnv( adata_in, groupby = 'ploidy_dec', N_cells_min = 50, N_cells_max = 0,
              title = 'log2(CNR)', title_fs = 14, title_y_pos = 1.1, show_cna_spots = False,
              label_fs = 12, tick_fs = 12, figsize = (12, 6), swap_axes = False, 
              var_group_rotation = 45, cmap='RdBu_r', vmax = 1, spot_llst = None,
              cnv_obsm_key = 'X_cnv', cnv_uns_key = 'cnv', spot_resample = 100,
              xlabel = 'Genomic spot', xtick_rot = 0, xtick_ha = 'center', 
              show_ticks = True, alpha = 0.3, Ns_min = 0.5, cna_std_scale = 0.7 ):

    """
    -------------------------------------------------------------------------
    📌 CNV heatmap by group (optionally highlight CNA hotspots)
    -------------------------------------------------------------------------
    Plot chromosome-wide CNV profiles from an AnnData object, grouped by
    a categorical variable (e.g., ploidy_dec, sample ID, patient ID).

    This is a wrapper around `scanpy.pl.heatmap` using a precomputed CNV
    matrix stored in `adata.obsm[cnv_obsm_key]`. Optionally, it can call
    `find_signif_CNV_gain_regions` to detect CNV gain hotspots and highlight
    those genomic spot ranges on the heatmap.

    Internally:
    - Filters groups in `adata.obs[groupby]` that have at least `N_cells_min`
      cells.
    - Optionally downsamples each group to `N_cells_max` cells for balanced
      comparison.
    - Builds a chromosome annotation (`ad.var['chr']`) from
      `adata.uns[cnv_uns_key]['chr_pos']` when available.
    - Plots a grouped heatmap with optional highlighted CNA gain regions.

    Parameters
    ----------
    adata_in : AnnData
        Input AnnData object containing:
        - `adata_in.obsm[cnv_obsm_key]` : 2D CNV matrix (cells × genomic spots).
        - `adata_in.obs[groupby]`       : group labels per cell.
        - Optional: `adata_in.uns[cnv_uns_key]['chr_pos']` :
          dict {chromosome: start_index} used to define chromosome blocks.

    groupby : str
        Column name in `adata.obs` used to group cells in the heatmap
        (e.g., "ploidy_dec", "sample", "patient").

    N_cells_min : int or float
        Minimum number of cells required per group.
        - If `N_cells_min >= 1` : interpreted as an absolute cell count.
        - If `0 < N_cells_min < 1` and `N_cells_max` is given as a quantile:
          it is interpreted as a fraction of `N_cells_max`
          (i.e., `N_cells_min * N_cells_max`).

    N_cells_max : int or float
        Maximum number of cells to use per group.
        - 0 : no downsampling.
        - If `0 < N_cells_max <= 1` : treated as a quantile of the group
          size distribution (e.g., 0.9 → 90th percentile).
          The corresponding integer is then used as the hard cap.
        When a group has more cells than `N_cells_max`, cells are randomly
        sampled to match `N_cells_max`.

    title : str
        Main title of the heatmap (e.g., "log2(CNR)").

    title_fs : int
        Font size for the heatmap title.

    title_y_pos : float
        Y-position of the heatmap title in axis coordinates.

    show_cna_spots : bool
        If True, run `find_signif_CNV_gain_regions` on the filtered/possibly
        downsampled `adata` and return its result along with the axis dict.
        Significant gain regions are also highlighted on the heatmap.

    label_fs : int
        Font size for axis labels (x/y axis labels).

    tick_fs : int
        Font size for tick labels (group labels and genomic spot ticks).

    figsize : tuple
        Figure size passed to `scanpy.pl.heatmap` (width, height).

    swap_axes : bool
        If False (default):
            - X-axis : genomic spots.
            - Y-axis : grouped categories (e.g., ploidy_dec).
        If True:
            - X-axis : grouped categories.
            - Y-axis : genomic spots.
        All tick/label logic is automatically adjusted.

    var_group_rotation : int
        Rotation angle for chromosome labels shown above/beside the heatmap
        (when chromosome grouping is available from `cnv_uns_key`).

    cmap : str or Colormap
        Colormap passed to `scanpy.pl.heatmap` (e.g., "RdBu_r" for CNV).

    vmax : float
        Symmetric limit for color scaling; data are plotted in
        [-vmax, +vmax]. If not set or left as the default, it is
        re-estimated from the 99–99.5% quantile of |CNV| values.

    spot_llst : list or dict or None
        Pre-defined genomic spot intervals to highlight.
        - If list: list of index ranges, e.g., [[10,11,...,25], [100,...,130]].
          They will be converted into labels like "10 ~ 25".
        - If dict: {label: index_list}. Labels are used directly.
        - If None and `show_cna_spots=True`: regions are detected via
          `find_signif_CNV_gain_regions`.

    cnv_obsm_key : str
        Key in `adata.obsm` where the CNV matrix is stored (default "X_cnv").

    cnv_uns_key : str or None
        Key in `adata.uns` where chromosome position metadata is stored.
        Expected format:
        `adata.uns[cnv_uns_key]['chr_pos'] = {chrom: start_index}`.
        If None or not a string, chromosome grouping and labels are skipped.

    spot_resample : int
        Interval at which genomic spot indices are shown as tick labels
        to reduce crowding (e.g., every 100 spots).

    xlabel : str or None
        Label for the genomic axis ("Genomic spot" by default).
        If None, the label is omitted.

    xtick_rot : int
        Rotation angle for genomic spot ticks.

    xtick_ha : str
        Horizontal alignment of genomic spot tick labels
        (e.g., "center", "left", "right").

    show_ticks : bool
        If True, show all spot tick labels as generated by scanpy.
        If False, gene/spot labels are suppressed.

    alpha : float
        Transparency of the highlighted CNA patches (0–1).

    Ns_min : float
        Minimum number (or fraction) of samples/observations per region
        to be considered when calling `find_signif_CNV_gain_regions`.
        Passed as `n_samples_min`.

    cna_std_scale : float
        Scaling factor for the standard deviation threshold used by
        `find_signif_CNV_gain_regions`. Larger values are more stringent
        (require stronger deviations from the mean CNV).

    Returns
    -------
    ax_dict : dict
        Dictionary of matplotlib axes returned by `scanpy.pl.heatmap`.
        Typical keys include:
        - "heatmap_ax" : main heatmap axis.
        - "groupby_ax" : group annotation axis (if available).

    results : dict or None
        - If `show_cna_spots=True`: dictionary returned by
          `find_signif_CNV_gain_regions`, including at least:
            - `results['spots']` : list of detected CNV gain regions
              (spot index ranges).
        - If `show_cna_spots=False`: returns None.

    Example
    -------
    # Basic CNV heatmap grouped by ploidy_dec
    ax_dict, _ = plot_cnv(
        adata_in,
        groupby="ploidy_dec",
        N_cells_min=50,
        N_cells_max=0,
        title="log2(CNR)"
    )

    # Highlight automatically detected CNA gain regions (swap axes)
    ax_dict, results = plot_cnv(
        adata_in,
        groupby="ploidy_dec",
        N_cells_min=50,
        N_cells_max=200,
        show_cna_spots=True,
        swap_axes=True,
        xlabel="Genomic spot"
    )
    -------------------------------------------------------------------------
    """
    
    if groupby not in list( adata_in.obs.columns.values ):
        print('ERROR: %s not in the obs.columns. ' % groupby )
        return None, None
    else:
        pcnt = adata_in.obs[groupby].value_counts()    
        if (N_cells_max > 0) & (N_cells_max < 1):
            N_cells_max = int(pcnt.quantile(N_cells_max))
            if (N_cells_min > 0) & (N_cells_min < 1): 
                N_cells_min = int(N_cells_max*N_cells_min)
            print('N_cells_max: %i, %i (%i, %i) ' % (N_cells_max, N_cells_min, pcnt[0], pcnt[-1]))

        bp = pcnt >= N_cells_min
        b = adata_in.obs[groupby].isin(list(pcnt.index.values[bp]))
        adata = adata_in[b,:] #.copy()
        
        if N_cells_max > 0:
            ## Resample cells to balance cell counts across samples 
            slst = adata.obs[groupby].unique()
            idx_all = adata.obs.index.values
            idx_sel = []
            for s in slst:
                b = adata.obs[groupby] == s
                
                if np.sum(b) <= N_cells_max:
                    idx_sel = idx_sel + list(idx_all[b])
                else:
                    idx_sel = idx_sel + random.sample(list(idx_all[b]), N_cells_max)
            
            adata = adata_in[idx_sel,:]


    if spot_llst is None:
        if show_cna_spots:                
            results = find_signif_CNV_gain_regions( adata, 
                                                    N_cells_min = N_cells_min, N_cells_max = N_cells_max,
                                                    std_scale = cna_std_scale, # gmm_ncomp_t = 3, gmm_ncomp_n = 1, 
                                                    n_samples_min = Ns_min, N_spots_min = 10 )
            spot_llst = results['spots']
            
            
    X_cnv = adata.obsm[cnv_obsm_key]
    chrs = np.array([' ']*X_cnv.shape[1])

    if isinstance(cnv_uns_key, str):
        
        chr_pos = adata.uns[cnv_uns_key]['chr_pos']
        df_chr_pos = pd.DataFrame({'chr_pos': list(chr_pos.values()), 'chr': list(chr_pos.keys()) }, index = chr_pos.keys())
        df_chr_pos = df_chr_pos.sort_values('chr_pos')
        
        ## Get chromosome name for each loci in X_cnv
        chrs = []
        for i in range(df_chr_pos.shape[0]):
            if i < (df_chr_pos.shape[0]-1):
                start = list(df_chr_pos.iloc[i])[0]
                end = list(df_chr_pos.iloc[i+1])[0]
            else:
                start = list(df_chr_pos.iloc[i])[0]
                end = X_cnv.shape[1]
        
            chrs = chrs + list([df_chr_pos.index.values[i]]*int(end-start))
        
        df_chr = pd.DataFrame({'chr': chrs})
        
        lst = list(df_chr_pos.index.values) # list(adata.uns[cnv_uns_key]['df_chr_pos'].index.values)
        
        ## Get vg_pos & vg_labels
        cnt = 0
        vg_pos = []
        vg_labels = []
        for i in lst:
            b = df_chr['chr'] == i
            vg_pos.append((cnt+5, cnt+np.sum(b)-5))
            vg_labels.append(i)
            cnt += np.sum(b)
        
        ## Create AnnData for plot
        ad = anndata.AnnData(X = X_cnv, var = df_chr, obs = adata.obs)
    else:
        vg_pos = None
        vg_labels = None
        ad = anndata.AnnData(X = X_cnv, obs = adata.obs)

        
    ad.var['spot_no'] = np.arange(len(ad.var.index.values))
    ad.var['spot_no'] = ad.var['spot_no'].astype(str)
    ad.var.set_index('spot_no', inplace = True)
    
    if isinstance( ad.X, np.ndarray ):
        vmax = np.quantile( np.abs(ad.X), 0.99).mean()*2
    else:
        vmax = np.quantile( np.abs(ad.X.data), 0.995 )

    ax_dict = sc.pl.heatmap(ad, var_names = ad.var.index.values, groupby = groupby, 
                            show = False, figsize = figsize, swap_axes = swap_axes, 
                            var_group_positions = vg_pos, var_group_labels = vg_labels, 
                            var_group_rotation = var_group_rotation, 
                            cmap=cmap, vmax = vmax, vmin = -vmax, show_gene_labels = show_ticks)

    if spot_llst is not None:
        if isinstance(spot_llst, list):
            nlst = []
            for lst in spot_llst:
                s = '%i ~ %i' % (lst[0], lst[-1])
                nlst.append( s )
            slst = spot_llst
        else:
            nlst = list(spot_llst.keys())
            slst = list(spot_llst.values())
                
    ax_dict['heatmap_ax'].set_title(title, fontsize = title_fs, y = title_y_pos)
    if swap_axes:
        xtick_ha = 'right'
        
        if 'groupby_ax' in list(ax_dict.keys()):
            ax_dict['groupby_ax'].set_xlabel(groupby, fontsize = label_fs)
            ticks = ax_dict['groupby_ax'].get_xticklabels()
            ax_dict['groupby_ax'].set_xticklabels(ticks, fontsize = tick_fs)
        
        if xlabel is not None:
            ax_dict['heatmap_ax'].set_ylabel(xlabel, fontsize = label_fs)

        x_ticks = np.arange(0, len(ad.var.index.values), spot_resample)
        ax_dict['heatmap_ax'].set_yticks(x_ticks, x_ticks, rotation=xtick_rot, ha=xtick_ha, fontsize = tick_fs)

        if spot_llst is not None:
            for name, lst in zip (nlst, slst):
                L = ad.obs.shape[0]
                ax_dict['heatmap_ax'].add_patch(Rectangle((0, lst[0]), L, lst[-1]-lst[0], fill = True, 
                                                           edgecolor = 'gold', facecolor = 'gold', 
                                                           lw = 0.5, alpha = alpha))
                ax_dict['heatmap_ax'].text(int(L*0.01), lst[0], name, fontsize = tick_fs, 
                                           rotation = 0, va = 'center', ha = 'left')    
        pass
    else:
        if 'groupby_ax' in list(ax_dict.keys()):
            ax_dict['groupby_ax'].set_ylabel(groupby, fontsize = label_fs)
            ticks = ax_dict['groupby_ax'].get_yticklabels()
            ax_dict['groupby_ax'].set_yticklabels(ticks, fontsize = tick_fs)
        
        if xlabel is not None:
            ax_dict['heatmap_ax'].set_xlabel(xlabel, fontsize = label_fs)

        x_ticks = np.arange(0, len(ad.var.index.values), spot_resample)
        ax_dict['heatmap_ax'].set_xticks(x_ticks, x_ticks, rotation=xtick_rot, ha=xtick_ha, fontsize = tick_fs)

        if spot_llst is not None:
            for name, lst in zip (nlst, slst):
                L = ad.obs.shape[0]
                ax_dict['heatmap_ax'].add_patch(Rectangle((lst[0], -0.5), lst[-1]-lst[0], L, fill = True, 
                                                           edgecolor = 'gold', facecolor = 'gold', 
                                                           lw = 0.5, alpha = 0.3))
                ax_dict['heatmap_ax'].text(lst[0], int(L*0.01)-0.4, name, fontsize = tick_fs, 
                                           rotation = -90, va = 'top', ha = 'left')        

    if show_cna_spots:
        return ax_dict, results
    else:
        return ax_dict, None


def get_normal_pdf( x, mu, var, nbins):
    
    MIN_ABS_VALUE = 1e-8
    y = np.array(x)
    mn_x = y.min()
    mx_x = y.max()
    dx = mx_x - mn_x
    mn_x -= dx/4
    mx_x += dx/4
    L = 100
    # dx = len(y)*(mx_x-mn_x)/L
    dx = (mx_x-mn_x)/nbins
    xs = np.arange(mn_x,mx_x, dx )
    pdf = (dx*len(y))*np.exp(-((xs-mu)**2)/(2*var+MIN_ABS_VALUE))/(np.sqrt(2*math.pi*var)+MIN_ABS_VALUE) + MIN_ABS_VALUE
    return pdf, xs


def plot_td_stats( params, n_bins = 30, title = None, title_fs = 14,
                   label_fs = 12, tick_fs = 11, legend_fs = 11, 
                   legend_loc = 'upper left', bbox_to_anchor = (1, 1),
                   figsize = (4,3), log = True, alpha = 0.8 ):
    
    th = params['th']
    m0 = params['m0']
    v0 = params['v0']
    w0 = params['w0']
    m1 = params['m1']
    v1 = params['v1']
    w1 = params['w1']
    df = params['df']
        
    mxv = df['cmean'].max()
    mnv = df['cmean'].min()
    Dv = mxv - mnv
    dv = Dv/200

    x = np.arange(mnv,mxv,dv)
    pdf0, xs0 = get_normal_pdf( x, m0, v0, 100)
    pdf1, xs1 = get_normal_pdf( x, m1, v1, 100)
    
    pr = pdf1/(pdf1 + pdf0) # get_malignancy_prob( xs0, [w0, m0, v0, w1, m1, v1] )
    bx = (xs0 >= m0) & ((xs1 <= m1))

    nn = len(df['cmean'])
    pdf0 = pdf0*(w0*nn*(200/n_bins)/pdf0.sum())
    pdf1 = pdf1*(w1*nn*(200/n_bins)/(pdf1.sum())) 

    max_pdf = max(pdf0.max(), pdf1.max())
    
    plt.figure(figsize = figsize)
    ax = plt.gca()
    
    counts, bins = np.histogram(df['cmean'], bins = n_bins)
    # max_cnt = np.max(counts)

    legend_labels = []
    
    max_cnt = 0
    b = df['tumor_dec'] == 'Normal'
    if np.sum(b) > 0:
        legend_labels.append('Normal')
        counts, bins_t, bar_t = plt.hist(df.loc[b, 'cmean'], bins = bins, alpha = alpha)
        max_cnt = max(max_cnt, np.max(counts))
    b = df['tumor_dec'] == 'Tumor'
    if np.sum(b) > 0:
        legend_labels.append('Tumor')
        counts, bins_t, bar_t = plt.hist(df.loc[b, 'cmean'], bins = bins, alpha = alpha)
        max_cnt = max(max_cnt, np.max(counts))
    b = df['tumor_dec'] == 'unclear'
    if np.sum(b) > 0:
        legend_labels.append('unclear')
        counts, bins_t, bar_t = plt.hist(df.loc[b, 'cmean'], bins = bins, alpha = alpha)
        max_cnt = max(max_cnt, np.max(counts))
    
    sf = 0.9*max_cnt/max_pdf
    plt.plot(xs0, pdf0*sf)
    plt.plot(xs1, pdf1*sf)
    plt.plot([th, th], [0, max_cnt]) # max(pdf0.max()*sf, pdf1.max()*sf)])
    plt.plot(xs0[bx], pr[bx]*max_cnt)

    if title is not None: plt.title(title, fontsize = title_fs)
    plt.xlabel('CNV_score', fontsize = label_fs)
    plt.ylabel('Number of clusters', fontsize = label_fs)
    plt.legend(['Normal distr.', 'Tumor distr.', 'Threshold', 'Tumor Prob.'], #, 'Score hist.'], 
               loc = legend_loc, bbox_to_anchor = bbox_to_anchor, fontsize = legend_fs)
    if log: plt.yscale('log')
    ax.tick_params(axis='x', labelsize=tick_fs)
    ax.tick_params(axis='y', labelsize=tick_fs)
    plt.grid()
    plt.show()
        
    return 

############################
############################
###### Plot dot (OLD) ######

def remove_common( mkr_dict, prn = True ):

    cts = list(mkr_dict.keys())
    mkrs_all = []
    for c in cts:
        mkrs_all = mkrs_all + list(mkr_dict[c])
    mkrs_all = list(set(mkrs_all))
    df = pd.DataFrame(index = mkrs_all, columns = cts)
    df.loc[:,:] = 0

    for c in cts:
        df.loc[mkr_dict[c], c] = 1
    Sum = df.sum(axis = 1)
    
    to_del = []
    s = ''
    for c in cts:
        b = (df[c] > 0) & (Sum == 1)
        mkrs1 = list(df.index.values[b])
        if prn & (len(mkr_dict[c]) != len(mkrs1)):
            s = s + '%s: %i > %i, ' % (c, len(mkr_dict[c]), len(mkrs1))
        
        if len(mkrs1) == 0:
            to_del.append(c)
        else:
            mkr_dict[c] = mkrs1

    if prn & len(s) > 0:
        print(s[:-2])

    if len(to_del) > 0:
        for c in cts:
            if c in to_del:
                del mkr_dict[c]
                
    return mkr_dict


def get_markers_all4(mkr_file, target_lst, genes = None, 
                    rem_cmn = False ):
    
    # target = 'Myeloid cell'
    if isinstance(mkr_file, dict):
        mkr_dict = mkr_file
    else:
        print('ERROR: marker input must be a dictionary.')
        return None
    
    if target_lst is not None:
        if len(target_lst) > 0:
            mkr_dict_new = {}
            for c in target_lst:
                if c in list(mkr_dict.keys()):
                    mkr_dict_new[c] = mkr_dict[c]
            mkr_dict = mkr_dict_new
            
    if rem_cmn:
        mkr_dict = remove_common( mkr_dict, prn = True )
        
    mkrs_all = [] #['SELL']
    mkrs_cmn = []
    for ct in mkr_dict.keys():
        if genes is not None:
            ms = list(set(mkr_dict[ct]).intersection(genes))
        else: 
            ms = mkr_dict[ct]
        mkrs_all = mkrs_all + ms
        if len(mkrs_cmn) == 0:
            mkrs_cmn = ms
        else:
            mkrs_cmn = list(set(mkrs_cmn).intersection(ms))

    mkrs_all = list(set(mkrs_all))
    if genes is not None:
        mkrs_all = list(set(mkrs_all).intersection(genes))
    
    return mkrs_all, mkr_dict


def remove_mac_common_markers(mkrs_dict):   

    lst2 = list(mkrs_dict.keys())
    lst = []
    Mono = None
    for item in lst2:
        if item[:3] == 'Mac':
            lst.append(item)
        if item[:4] == 'Mono':
            Mono = item
            
    if len(lst) > 1:
        mac_common = mkrs_dict[lst[0]]
        for item in lst[1:]:
            mac_common = list(set(mac_common).intersection(mkrs_dict[item]))
            
        for item in lst:
            for mkr in mac_common:
                mkrs_dict[item].remove(mkr)
#         if Mono is not None:
#             mono_lst = mkrs_dict[Mono]
#             del mkrs_dict[Mono]
#             mkrs_dict[Mono] = mono_lst
            
    return mkrs_dict

    
def update_markers_dict2(mkrs_all, mkr_dict, X, y, rend = None, cutoff = 0.3, 
                        Nall = 20, Npt = 20, Npt_tot = 0):
    
    if rend is None:
        lst = list(mkr_dict.keys())
        lst.sort()
        rend = dict(zip(lst, lst))
    else:
        lst = list(rend.keys())
        
    df = pd.DataFrame(index = lst, columns = mkrs_all)
    df.loc[:,:] = 0
        
    for ct in lst:
        if ct in list(mkr_dict.keys()):
            b = y == ct
            ms = list(set(mkr_dict[ct]).intersection(mkrs_all))
            pe = list((X.loc[b,ms] > 0).mean(axis = 0))
            for j, m in enumerate(ms):
                df.loc[ct, m] = pe[j]

    if df.shape[0] == 1:
        mkrs_all = list(df.columns.values)
        mkrs_dict = {}
        
        pe_lst = []
        pex_lst = []
        
        for ct in lst:
            b = y == ct
            ms = list(set(mkr_dict[ct]).intersection(mkrs_all))
            pe = np.array((X.loc[b,ms] > 0).mean(axis = 0))
            pex = np.array((X.loc[~b,ms] > 0).mean(axis = 0))
            odr = np.array(-pe).argsort()
            ms_new = []
            for o in odr:
                if (pe[o] >= cutoff):
                    ms_new.append(ms[o])

            pe = pe[~np.isnan(pe)]
            pex = pex[~np.isnan(pex)]
            pe_lst = pe_lst + list(pe)
            pex_lst = pex_lst + list(pex)
            
            if len(ms_new) > 0:
                mkrs_dict[rend[ct]] = ms_new[:min(Npt,len(ms_new))]
            else:
                mkrs_dict[rend[ct]] = ms[:min(Npt,len(ms))]
                
        mkrs_dict2 = mkrs_dict
    else:
        p1 = df.max(axis = 0)
        p2 = p1.copy(deep = True)
        p2[:] = 0
        idx = df.index.values
        # print(df)
        for m in list(df.columns.values):
            odr = np.array(-df[m]).argsort()
            p2[m] = df.loc[idx[odr[1]], m]
        nn = (df >= 0.5).sum(axis = 0)

        b0 = p1 > 0
        b1 = (p2/(p1 + 0.0001)) < 0.5
        b2 = nn < 4
        b = b0 # & b1 & b2
        df = df.loc[:,b]
        mkrs_all = list(df.columns.values)

        mkrs = [] 
        cts = [] 
        pes = [] 
        mkrs_dict = {}
        pe_dict = {}
        pex_dict = {}
        # mkrs_all = [] 
        for ct in lst:
            b = y == ct
            if ct in list(mkr_dict.keys()):
                ms = list(set(mkr_dict[ct]).intersection(mkrs_all))
                p2t = np.array(p2[ms])
                p1t = np.array(p1[ms])
                pe = np.array((X.loc[b,ms] > 0).mean(axis = 0))
                pex = np.array((X.loc[~b,ms] > 0).mean(axis = 0))
                odr = np.array(-pe).argsort()
                ms_new = []
                pe_new = []
                pex_new = []
                for o in odr:
                    if (pe[o] >= cutoff) & (~np.isnan(pe[o])):
                        ms_new.append(ms[o])

                        pe_new.append(pe[o])
                        pex_new.append(pex[o])
                '''
                pe = pe[~np.isnan(pe)]
                pex = pex[~np.isnan(pex)]
                pe_lst = pe_lst + list(pe)
                pex_lst = pex_lst + list(pex)
                '''

                if len(ms_new) > 0:
                    mkrs_dict[rend[ct]] = ms_new[:min(Npt,len(ms_new))]
                    pe_dict[rend[ct]] = pe_new[:min(Npt,len(ms_new))]
                    pex_dict[rend[ct]] = pex_new[:min(Npt,len(ms_new))]
                else:
                    mkrs_dict[rend[ct]] = ms[:min(Npt,len(ms))]
                    pe_dict[rend[ct]] = list(pe)[:min(Npt,len(ms))]
                    pex_dict[rend[ct]] = list(pex)[:min(Npt,len(ms))]
             
        mkr_lst = []
        pe_lst = []
        pex_lst = []
        cnt2 = 0
        for ct in lst:
            if ct in list(mkr_dict.keys()):
                pe_lst = pe_lst + pe_dict[rend[ct]]
                pex_lst = pex_lst + pex_dict[rend[ct]]
                mkr_lst = mkr_lst + mkrs_dict[rend[ct]]
                cnt2 += len(mkrs_dict[rend[ct]])
            
        if (Npt_tot is not None) & (Npt_tot > 20) & (len(pe_lst) > 0):
            odr = (np.array(pe_lst)).argsort()
            if len(odr) > Npt_tot:
                pe_th = pe_lst[odr[int(len(odr)-Npt_tot)]]
            else:
                pe_th = pe_lst[odr[0]]

            pe_lst = []
            pex_lst = []
            cnt = 0
            for ct in lst:
                if ct in list(mkr_dict.keys()):
                    pe = np.array(pe_dict[rend[ct]]) 
                    b = pe >= pe_th
                    mkrs_dict[rend[ct]] = list(np.array(mkrs_dict[rend[ct]])[b])
                    cnt += len(mkrs_dict[rend[ct]])
                    pe_lst = pe_lst + list(np.array(pe_dict[rend[ct]])[b])
                    pex_lst = pex_lst + list(np.array(pex_dict[rend[ct]])[b])
                
            print('Num markers selected: %i -> %i' % (cnt2, cnt))
            
        mkrs_dict2 = {}
        for m in mkr_dict.keys():
            if (rend is not None) & (m in rend.keys()):
                m = rend[m]                
            if m in list(mkrs_dict.keys()):
                mkrs_dict2[m] = mkrs_dict[m]
            
    return mkrs_dict2, df, pe_lst, pex_lst                                


def get_best_markers(adata, markers_in = None, var_group_col = None, 
                    nz_frac_cutoff = 0.1, 
                    rem_mkrs_common_in_N_groups_or_more = 3, N_cells_min = 20,  
                    N_markers_per_group_max = 15, N_markers_total = 200 ): 

    Npt = N_markers_per_group_max
    Npt_tot = N_markers_total
    show_unassigned = False
    # show = True
    rend = None    
    other_genes = []

    if markers_in is None:
        markers = copy.deepcopy( adata.uns['Celltype_marker_DB']['subset_markers_dict'] )
        var_group_col = 'celltype_subset'
    else:
        markers = copy.deepcopy(markers_in)

    target_lst = list(markers.keys()) 
    target_lst.sort()

    target = ','.join(target_lst)
    genes = list(adata.var.index.values)
    
    mkrs_all, mkr_dict = get_markers_all4(markers, target_lst, 
                                         genes, rem_cmn = False)
    
    target_lst2 = list(mkr_dict.keys())
    y = adata.obs[var_group_col]
    
    if show_unassigned:
        if np.sum(y.isin(['unassigned'])) > 10:
            mkr_dict['unassigned'] = []
            target_lst2 = list(mkr_dict.keys())

    b = y.isin(target_lst2)
    adata_t = adata[b, list(set(mkrs_all).union(other_genes))].copy()
    X = adata_t.to_df()
    y = adata_t.obs[var_group_col]

    mkrs_dict, df, pe_lst, pex_lst = update_markers_dict2(mkrs_all, mkr_dict, X, y, rend, 
                                        cutoff = 0, Npt = Npt*2, Npt_tot = 0)
    
    mkrs_dict = remove_mac_common_markers(mkrs_dict)
    if rend is not None: 
        adata_t.obs[var_group_col] = adata_t.obs[var_group_col].replace(rend)
        
    ## Get number of marker genes for each cell type
    mkall = []
    for key in mkrs_dict.keys():
        mkall = mkall + mkrs_dict[key]
    mkall = list(set(mkall))
    nmkr = dict(zip(mkall, [0]*len(mkall)))
    for key in mkrs_dict.keys():
        for m in mkrs_dict[key]:
            nmkr[m] += 1
            
    ## remove the marker genes appering in 3 or more cell types
    if rem_mkrs_common_in_N_groups_or_more > 0:
        to_del = []
        for key in nmkr.keys():
            if nmkr[key] >= rem_mkrs_common_in_N_groups_or_more: 
                to_del.append(key)

        if len(to_del) > 0:
            for m in to_del:
                for key in mkrs_dict.keys():
                    if m in mkrs_dict[key]:
                        mkrs_dict[key].remove(m)
                        
    ## Select only the cell types that exist in the data and the number of cells >= N_cells_min
    #'''
    ps_cnt = adata_t.obs[var_group_col].value_counts()
    lst_prac = list(ps_cnt.index.values) 
    mkrs_dict2 = {}
    for m in mkrs_dict.keys():
        if m in lst_prac: 
            if ps_cnt[m] >= N_cells_min:
                mkrs_dict2[m] = mkrs_dict[m]
    mkrs_dict = mkrs_dict2        
    #'''
    
    ## Remove cell types for which the number of cells below N_cells_min
    target_lst2 = list(mkrs_dict.keys())
    y = adata_t.obs[var_group_col]
    
    if show_unassigned:
        if np.sum(y.isin(['unassigned'])) > 10:
            mkrs_dict['unassigned'] = []
            target_lst2 = list(mkrs_dict.keys())
    
    if len(target_lst2) == 0:
        return None, None

    #'''
    b = y.isin(target_lst2)
    adata_t = adata_t[b, :]
    if rend is not None: 
        adata_t.obs[var_group_col] = adata_t.obs[var_group_col].replace(rend)
    
    X = adata_t.to_df()
    y = adata_t.obs[var_group_col]
    
    ## Get number of marker genes for each cell type
    mkrs_all = []
    for key in mkrs_dict.keys():
        mkrs_all = mkrs_all + mkrs_dict[key]
    mkrs_all = list(set(mkrs_all))
    
    mkrs_dict, df, pe_lst, pex_lst = update_markers_dict2(mkrs_all, mkrs_dict, X, y, None, 
                                        cutoff = nz_frac_cutoff, Npt = Npt, Npt_tot = Npt_tot)

    lst = list(mkrs_dict.keys())
    for k in lst:
        if len(mkrs_dict[k]) == 0:
            del mkrs_dict[k]
                
    #'''
    if markers_in is None:
        adata_t.obs[var_group_col] = adata_t.obs[var_group_col].astype(str)
        b = adata_t.obs[var_group_col].isin(list(mkrs_dict.keys()))
        adata_t = adata_t[b,:]
    #'''
    return mkrs_dict, adata_t, var_group_col
                                

def plot_marker_exp_inner(adata, markers, var_group_col = 'celltype_subset', 
                    cell_group_col = None, # group_categ_col = None,
                    title = None, title_y_pos = 1.1, title_fs = 14, 
                    text_fs = 12, linewidth = 1.5, 
                    var_group_height = 1.2, var_group_rotation = 0, standard_scale = 'var', 
                    nz_frac_max = 0.5, # nz_frac_cutoff = 0.1, 
                    # rem_mkrs_common_in_N_groups_or_more = 3, N_cells_min = 20,  
                    # N_markers_per_group_max = 15, N_markers_total = 200, 
                    mean_only_expressed = False, 
                    figsize = (20, 4), swap_ax = False, legend = False, add_rect = True,
                    cmap = 'Reds', rect_color = 'royalblue'):

    group_categ_col = var_group_col
    group_col = cell_group_col
    mkrs_dict = markers
    # Npt = N_markers_per_group_max
    # Npt_tot = N_markers_total
    # show_unassigned = False
    show = True
    # rend = None    
    # other_genes = []
    # target_lst = list(markers.keys()) 
    # target_lst.sort()
    
    Lw = linewidth
    hgt = var_group_height
    title_fontsize = title_fs
    
    SCANPY = True
    try:
        import scanpy as sc
    except ImportError:
        SCANPY = False
    
    if (not SCANPY):
        print('ERROR: scanpy not installed. ')   
        return
    
    # target = ','.join(target_lst)
    # genes = list(adata.var.index.values)
        
    mkrs_all = []
    for key in mkrs_dict.keys():
        mkrs_all = mkrs_all + mkrs_dict[key]
    # mkrs_all = list(set(mkrs_all))
    
    adata_t = adata[:, list(set(mkrs_all))]

    sx = len(mkrs_all)
    if group_col is None:
        sy = len(adata_t.obs[var_group_col].unique().tolist())
    else:
        sy = len(adata_t.obs[group_col].unique().tolist())

    if swap_ax or (markers is None):
        figsize = None        
    else:
        if figsize is None:
            figsize = (sx/3.2, 4)
            
        if swap_ax:
            lx = figsize[1]
            ly = figsize[0]
        
            ly = lx*sy/sx
            figsize = (ly, lx)
            title_y_pos = (sx + title_y_pos)/sx
        else:
            lx = figsize[0]
            ly = figsize[1]
        
            ly = lx*sy/sx
            figsize = (lx, ly)
            title_y_pos = (sy + title_y_pos)/sy
    
    if show:
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if group_col is None:
                Type_level = var_group_col
                categ_order = list(mkrs_dict.keys())
                # categ_order.sort()
            else:
                #'''
                var_group_lst = list(mkrs_dict.keys())
                var_group_lst.sort()
                mkrs_dict2 = {}
                for c in var_group_lst:
                    mkrs_dict2[c] = mkrs_dict[c]
                mkrs_dict = mkrs_dict2    
                #'''
                Type_level = group_col
                if group_categ_col is None:
                    categ_order = list(adata_t.obs[Type_level].unique())
                    categ_order.sort()
                else:
                    group_categ_lst = list(adata_t.obs[group_categ_col].unique())
                    group_categ_lst.sort()
                    categ_order = []
                    num_groups_per_group_categ = {}
                    for gc in group_categ_lst:
                        b = adata_t.obs[group_categ_col] == gc
                        lst_tmp = list(adata_t[b,:].obs[Type_level].unique())
                        lst_tmp.sort()

                        # print((gc, np.array(var_group_lst)))
                        if gc in var_group_lst:
                            genes = mkrs_dict[gc]
                        else:
                            genes = mkrs_all
                        Xx = (adata_t[b, genes].to_df() > 0)
                        Xx['group'] = adata_t[b,:].obs[Type_level]                            
                        X = Xx.groupby('group').mean()
                        # display(X)
                        # linked = linkage(X, 'single')
                        # idx_odrd = leaves_list(linked)
                        # lst_tmp = list( np.array(lst_tmp)[idx_odrd][::-1] )
                        X['mean'] = X.mean(axis = 1)
                        lst_tmp = X.sort_values(by = 'mean', ascending = False).index.values.tolist()

                        categ_order = categ_order + lst_tmp
                        num_groups_per_group_categ[gc] = len(lst_tmp)

            # print(categ_order)
            dp = sc.pl.dotplot(adata_t, mkrs_dict, groupby = Type_level, 
                               categories_order = categ_order, 
                               return_fig = True, log = True, figsize = figsize,
                               var_group_rotation = var_group_rotation, show = False, # 
                               standard_scale = standard_scale, cmap = cmap, 
                               mean_only_expressed = mean_only_expressed,
                               dot_max = nz_frac_max, swap_axes = swap_ax )
                               # colorbar_title = 'mean expression', size_title = 'percent cells' ) 
            dp.add_totals() # .style(dot_edge_color='black', dot_edge_lw=0.5).show()
        

        ax_dict = dp.get_axes()    
        ax = ax_dict['mainplot_ax']
        
        if title is not None:
            ax.set_title(title, fontsize = title_fontsize, y = title_y_pos) 
        ax.tick_params(labelsize=text_fs)
        
        ## add Rectangles in main plot
        ylabels = []
        for j, key in enumerate(mkrs_dict.keys()):
            ylabels = ylabels + mkrs_dict[key]
        
        if add_rect:
            if group_col is None: 
                cnt = 0
                ylabels = []
                bar_length = 80
                for j, key in enumerate(mkrs_dict.keys()):
                    L = len(mkrs_dict[key])
                    if swap_ax:
                        ax.add_patch(Rectangle((j, cnt), 1, L, fill = False, edgecolor = rect_color, lw = Lw))
                    else:
                        ax.add_patch(Rectangle((cnt, j), L, 1, fill = False, edgecolor = rect_color, lw = Lw))
                    cnt += L
                    ylabels = ylabels + mkrs_dict[key]
    
                if categ_order is not None:
                    jj = j
                    L_tot = cnt        
                    outer_loops = int(len(categ_order)/len(list(mkrs_dict.keys())))
                    for kk in range(outer_loops-1):
                        cnt = 0
                        for j1, key in enumerate(mkrs_dict.keys()):
                            j = j + 1
                            L = len(mkrs_dict[key])
                            if swap_ax:
                                ax.add_patch(Rectangle((j, cnt), 1, L, fill = False, 
                                                       edgecolor = rect_color, lw = Lw))
                            else:
                                ax.add_patch(Rectangle((cnt, j), L, 1, fill = False, 
                                                       edgecolor = rect_color, lw = Lw))
                            cnt += L
            elif group_categ_col is not None:
                #'''
                cnt_x = 0
                cnt_y = 0
                # ylabels = []
                vg_lst = list(mkrs_dict.keys())
                if set(group_categ_lst).issubset(set(vg_lst)) | set(vg_lst).issubset(set(group_categ_lst)):
                    if set(group_categ_lst).issubset(set(vg_lst)):
                        super_list =vg_lst
                    else:
                        super_list =group_categ_lst
                    for gc in super_list: 
                        if gc in vg_lst:
                            L_x = len(mkrs_dict[gc])
                        else:
                            L_x = 0
                        if gc in group_categ_lst:
                            L_y = num_groups_per_group_categ[gc]
                        else:
                            L_y = 0
                        if swap_ax:
                            ax.add_patch(Rectangle((cnt_y, cnt_x), L_y, L_x, fill = False, edgecolor = rect_color, lw = Lw))
                        else:
                            ax.add_patch(Rectangle((cnt_x, cnt_y), L_x, L_y, fill = False, edgecolor = rect_color, lw = Lw))
                        cnt_x += L_x
                        cnt_y += L_y
                        # ylabels = ylabels + mkrs_dict[key]
                else:
                    cnt = 0
                    width = len(mkrs_all)
                    for gc in (group_categ_lst[:-1]): 
                        cnt += num_groups_per_group_categ[gc]
                        if swap_ax:
                            ax.plot([cnt, cnt], [0, width], rect_color, lw = Lw)
                        else:
                            ax.plot([0, width], [cnt, cnt], rect_color, lw = Lw)
    
                    cnt = 0
                    height = len(categ_order)
                    vg_lst = list(mkrs_dict.keys())
                    for vg in vg_lst[:-1]: 
                        cnt += len(mkrs_dict[vg])
                        if swap_ax:
                            ax.plot([0, height], [cnt, cnt], rect_color, lw = Lw)
                        else:
                            ax.plot([cnt, cnt], [0, height], rect_color, lw = Lw)
                                
        ## color/dot size legend 
        ax2 = ax_dict['color_legend_ax']
        ax3 = ax_dict['size_legend_ax']
        
        if not legend:
            ax2.remove()
            ax3.remove()
        else:
            # pass
            #'''
            if swap_ax == False:
                box = ax2.get_position()
                dx = (box.x1 - box.x0)*0.3
                box.x0 = box.x0 + dx
                box.x1 = box.x1 + dx
                ax2.set_position(box)
                
                box2 = ax3.get_position()
                dx = (box2.x1 - box2.x0)*0.3
                box2.x0 = box2.x0 + dx
                box2.x1 = box2.x1 + dx

                dy = (box2.y1 - box2.y0)
                if box2.y0 > (box.y1 + dy*2):
                    Dy = box2.y0 - (box.y1 + dy*2)
                    box2.y0 = box2.y0 - Dy
                    box2.y1 = box2.y1 - Dy
                else:
                    Dy = (box.y1 + dy*2) - box2.y0
                    box2.y0 = box2.y0 + Dy
                    box2.y1 = box2.y1 + Dy                    
                ax3.set_position(box2)
            #'''

        ## Variable Group plot
        axa = ax_dict['gene_group_ax']
        axa.clear()
        axa.set_frame_on(False)
        axa.grid(False)
        cnt = 0
        gap = 0.2

        n_cells = []
        for ct in mkrs_dict.keys():
            b = adata_t.obs[var_group_col] == ct
            n_cells.append(np.sum(b))
        n_cells = np.array(n_cells)
        p_cells = n_cells/n_cells.sum()

        for j, key in enumerate(mkrs_dict.keys()):
            L = len(mkrs_dict[key])
            '''
            pct = (1000*p_cells[j])
            if pct < 1:
                pct = '<0.1%'
            elif pct < 10:
                pct = '%3.1f' % (pct/10) + '%'
            else:
                pct = '%i' % int(pct/10) + '%'
            #'''    
            if swap_ax:
                axa.plot([hgt, hgt], [cnt+gap, cnt+L-gap], 'k', lw = 1.5) #Lw)
                axa.plot([hgt, 0], [cnt+gap, cnt+gap], 'k', lw = 1.5) #Lw)
                axa.plot([hgt, 0], [cnt+L-gap, cnt+L-gap], 'k', lw = 1.5) #Lw)
                axa.text(hgt*var_group_height, cnt+L/2, ' ' + key, fontsize = text_fs + 1, rotation = 0, ha = 'left', va = 'center')
            else:
                axa.plot([cnt+gap, cnt+L-gap], [hgt, hgt], 'k', lw = 1.5) #Lw)
                axa.plot([cnt+gap, cnt+gap], [hgt, 0], 'k', lw = 1.5) #Lw)
                axa.plot([cnt+L-gap, cnt+L-gap], [hgt, 0], 'k', lw = 1.5) #Lw)
                Ha = 'center'
                if (var_group_rotation > 0) & (var_group_rotation < 90):
                    Ha = 'left'
                elif (var_group_rotation < 0) & (var_group_rotation > -90):
                    Ha = 'right'                    
                axa.text(cnt+L/2, hgt*var_group_height, ' ' + key, fontsize = text_fs + 1, 
                         rotation = var_group_rotation, ha = Ha)
            cnt += L

        ## group extra plot
        axb = ax_dict['group_extra_ax']
        
        if swap_ax == False:
            pass
        else:
            box_main = ax.get_position()
            box = axb.get_position()
            box.y1 = box_main.y0 - (box.y1 - box.y0)
            box.y0 = box_main.y0
            axb.set_position(box)
        
        axb.clear()
        axb.set_frame_on(False)
        axb.get_xaxis().set_visible(False)
        axb.get_yaxis().set_visible(False)
        
        n_cells2 = []
        if categ_order is None:
            categ_order = list(mkrs_dict.keys())
            
        for ct in categ_order:
            b = adata_t.obs[Type_level] == ct
            n_cells2.append(np.sum(b))
        n_cells2 = np.array(n_cells2)
        p_cells2 = np.sqrt(n_cells2)
        # p_cells2 = p_cells2 - np.min(p_cells2*0.9)
        # p_cells2 = n_cells2/n_cells2.sum()
        p_cells2 = p_cells2/np.max(p_cells2)
        
        for j, key in enumerate(categ_order):
            if swap_ax:
                y = p_cells2[j]
                axb.add_patch(Rectangle((j+0.2, 0), 0.6, y, fill = True, 
                                        facecolor = 'firebrick', edgecolor = 'black', lw = 1.5)) #Lw))
                axb.text( j+0.5, y, ' %i ' % n_cells2[j], rotation = 90, ha = 'center', va = 'top', fontsize = text_fs)
            else:
                y = p_cells2[j]
                axb.add_patch(Rectangle((0, j+0.2), y, 0.6, fill = True, 
                                        facecolor = 'firebrick', edgecolor = 'black', lw = 1.5)) #Lw))
                axb.text( y, j+0.5, ' %i ' % n_cells2[j], rotation = 0, ha = 'left', va = 'center', fontsize = text_fs)
        
        ## Set x/y ticks again
        if swap_ax:
            ax.set_yticks( ticks = list(np.arange(len(ylabels))+0.5))
            ax.set_yticklabels(ylabels)
            ax.xaxis.set_ticks_position('top')
            ax.set_xticks( ticks = list(np.arange(len(categ_order))+0.5))
            ax.set_xticklabels(categ_order)
        else:
            ax.set_xticks( ticks = list(np.arange(len(ylabels))+0.5))
            ax.set_xticklabels(ylabels)
            ax.yaxis.set_ticks_position('left')
            ax.set_yticks( ticks = list(np.arange(len(categ_order))+0.5))
            ax.set_yticklabels(categ_order)
                
    plt.show()
    return 
                                                                

def plot_marker_exp(adata, markers = None, celltype_selection = None, var_group_col = None, cell_group_col = None,
                    N_cells_per_group_min = 20, N_markers_per_group_max = 15, N_markers_total = 200, 
                    title = None, title_y_pos = 1.1, title_fs = 14, text_fs = 12, linewidth = 1.5, 
                    var_group_height = 1.2, var_group_rotation = 0, standard_scale = 'var', 
                    nz_frac_max = 0.5, nz_frac_cutoff = 0.1, rem_mkrs_common_in_N_groups_or_more = 3,
                    mean_only_expressed = False, legend = False, figsize = (20, 4), swap_ax = False, 
                    add_rect = True, cmap = 'Reds', linecolor = 'royalblue' ):
    """
    -------------------------------------------------------------------------
    📌 Marker expression dot plots (auto-select best markers per group)
    -------------------------------------------------------------------------
    High-level wrapper to visualize marker gene expression across groups
    (e.g., cell types, conditions, samples) using a dot plot.

    This function:
      1) Chooses the appropriate subset of cells (`adata_s`) based on
         `celltype_selection`, `var_group_col`, and `cell_group_col`.
      2) Calls `get_best_markers(...)` to refine/trim the marker list:
         - removes markers that are too broadly shared,
         - enforces minimum cell counts per group,
         - limits per-group and total number of markers.
      3) Calls `plot_marker_exp_inner(...)` to generate a Scanpy
         dotplot with optional rectangles and group annotations.

    Parameters
    ----------
    adata : AnnData
        Input AnnData object. Expected to contain:
        - `adata.obs[var_group_col]` : primary grouping variable
          (e.g., cell subtype, condition).
        - `adata.obs[cell_group_col]` : secondary grouping variable
          (e.g., sample ID, patient ID), if used.
        - If `markers is None`:
            `adata.uns['Celltype_marker_DB']['subset_markers_dict']`
            is used as the initial marker dictionary.
        - If `celltype_selection` is used:
            `adata.uns['DEG_grouping_vars']` and
            `adata.uns['analysis_parameters']['CCI_DEG_BASE']`
            are used to infer grouping columns.

    markers : dict or None
        Dictionary of initial marker genes:
        - keys   : group names (e.g., cell types),
        - values : list of marker genes.
        If None, markers are taken from
        `adata.uns['Celltype_marker_DB']['subset_markers_dict']`.

    celltype_selection : str or None
        If provided and present in
        `adata.uns['DEG_grouping_vars']`, this is used to:
        - subset `adata` to a relevant cell type (or tumor-only subset
          for names containing "tumor"/"cancer"), and
        - automatically set `var_group_col` and `cell_group_col` from
          `DEG_grouping_vars[celltype_selection]`.
        If None, you must specify `var_group_col` and `cell_group_col`
        explicitly.

    var_group_col : str or None
        Column in `adata.obs` specifying the *group* to plot on one axis
        (e.g., refined cell type / condition). If `markers is None`,
        this is often `"celltype_subset"` (set internally inside
        `get_best_markers`), but can be overridden by the logic above.

    cell_group_col : str or None
        Column in `adata.obs` specifying a higher-level group such as
        sample or patient. Used to:
        - filter out samples with fewer than `N_cells_per_group_min`
          cells,
        - define the layout of group annotations in the dotplot.
        If not provided, the plot is grouped only by `var_group_col`.

    N_cells_per_group_min : int
        Minimum number of cells per sample group (`cell_group_col`)
        required to keep that sample in the analysis.

    N_markers_per_group_max : int
        Maximum number of marker genes to keep per group in the final
        marker set (upper limit; actual number may be smaller).

    N_markers_total : int
        Approximate global maximum for the total number of markers
        across all groups (used inside `get_best_markers` for trimming
        the most weakly expressed markers).

    title : str or None
        Plot title passed through to `plot_marker_exp_inner`.

    title_y_pos : float
        Vertical position of the title in axis coordinates.

    title_fs : int
        Font size of the main title.

    text_fs : int
        Base font size for axis ticks and group labels.

    linewidth : float
        Line width for rectangle outlines and auxiliary annotations.

    var_group_height : float
        Height scale for the variable-group outline panel
        (used in `plot_marker_exp_inner`).

    var_group_rotation : float
        Rotation angle (in degrees) for variable-group labels.

    standard_scale : {'var', 'group', None}
        Passed to `scanpy.pl.dotplot` to apply z-score–like scaling
        along variables or groups (see Scanpy docs).

    nz_frac_max : float
        Maximum fraction of non-zero values (dot size scaling) used
        for the size legend in the dot plot.

    nz_frac_cutoff : float
        Minimum fraction of non-zero cells required (per group) for a
        gene to be retained as a marker in the final selection.

    rem_mkrs_common_in_N_groups_or_more : int
        Marker genes that appear as markers in this many or more groups
        are removed (to favor more specific markers).

    mean_only_expressed : bool
        Passed to `scanpy.pl.dotplot`; if True, the color represents
        the mean of non-zero values only.

    legend : bool
        If True, keep color and dot-size legends; if False, remove them.

    figsize : tuple
        Base figure size; may be adaptively rescaled in
        `plot_marker_exp_inner` depending on the number of markers
        and groups, unless `swap_ax` is True.

    swap_ax : bool
        If False (default), markers are on the x-axis and groups on the y-axis.
        If True, axes are swapped and all annotations are adjusted
        accordingly.

    add_rect : bool
        If True, draw rectangular outlines to visually separate
        marker blocks or group categories.

    cmap : str or Colormap
        Colormap for the dot color (e.g., "Reds").

    linecolor : str
        Color used for rectangles and structural lines
        (passed as `rect_color` to `plot_marker_exp_inner`).

    Returns
    -------
    None
        This function generates the dot plot via matplotlib/Scanpy and
        returns the result of `plot_marker_exp_inner` (which is
        typically None). The main effect is the rendered figure.

    Example
    -------
    # 1) Automatic marker selection using Celltype_marker_DB
    plot_marker_exp(
        adata,
        markers=None,
        var_group_col="celltype_subset",
        cell_group_col="sample",
        N_cells_per_group_min=30,
        N_markers_per_group_max=10,
        N_markers_total=150,
        title="Selected markers per cell subset",
        legend=True
    )

    # 2) Using a custom marker dictionary and a predefined DEG setup
    #    (celltype_selection must exist in adata.uns['DEG_grouping_vars'])
    plot_marker_exp(
        adata,
        markers=my_marker_dict,
        celltype_selection="Myeloid",
        N_cells_per_group_min=20,
        nz_frac_cutoff=0.15,
        rem_mkrs_common_in_N_groups_or_more=3,
        swap_ax=True,
        title="Best markers for myeloid subsets"
    )
    -------------------------------------------------------------------------
    """

    N_cells_min = N_cells_per_group_min
    if var_group_col is not None: 
        adata.obs[var_group_col] = adata.obs[var_group_col].astype(str)

    b_pass = False
    if markers is None:
        adata_s = adata[:,:].copy()
        b_pass = True
    elif celltype_selection is not None:
        if celltype_selection in list(adata.uns['DEG_grouping_vars'].keys()):
            deg_base = adata.uns['analysis_parameters']['CCI_DEG_BASE']
            b = adata.obs[deg_base] == celltype_selection
            adata_s = adata[b,:].copy()

            if (var_group_col is None) | (cell_group_col is None):
                var_group_col = adata_s.uns['DEG_grouping_vars'][celltype_selection]['condition col']
                cell_group_col = adata_s.uns['DEG_grouping_vars'][celltype_selection]['sample col']
                b_pass = True
            elif (var_group_col in list(adata.obs.columns.values)) & (cell_group_col in list(adata.obs.columns.values)):
                adata_s = adata[:,:]
                b_pass = True
        elif ('tumor' in celltype_selection.lower()) | ('cancer' in celltype_selection.lower()):
            b = adata.obs['tumor_origin_ind']
            adata_s = adata[b,:].copy()
            pcnt = adata_s.obs['celltype_major'].value_counts()
            target_celltype = None
            for i in pcnt.index:
                if (i != 'unassigned'):
                    target_celltype = i
                    break
            if target_celltype is not None:
                if target_celltype in list(adata.uns['DEG_grouping_vars'].keys()):
                    celltype_selection = target_celltype
                    var_group_col = adata_s.uns['DEG_grouping_vars'][celltype_selection]['condition col']
                    cell_group_col = adata_s.uns['DEG_grouping_vars'][celltype_selection]['sample col']
                    b_pass = True
                
    if not b_pass:
        if (var_group_col is not None) & (cell_group_col is not None):
            if (var_group_col in list(adata.obs.columns.values)) & (cell_group_col in list(adata.obs.columns.values)):
                adata_s = adata[:,:].copy()
                b_pass = True
            
    if not b_pass:
        print('ERROR: You need to specify either \'celltype_selection\' or \'var_group_col\' & \'cell_group_col\'.')
        return None
        
    if cell_group_col is not None: 
        adata_s.obs[cell_group_col] = adata_s.obs[cell_group_col].astype(str)

        ## Select samples with its No. of cells greater than 40
        pcnt = adata_s.obs[cell_group_col].value_counts()
        b = pcnt >= N_cells_min
        plst = list(pcnt.index.values[b])
        b = adata_s.obs[cell_group_col].isin(plst)
        adata_s = adata_s[b,:]
    
    selected_mkr_dict, adata_sss, var_group_col = get_best_markers( adata_s, 
                      markers_in = markers, var_group_col = var_group_col,  
                      nz_frac_cutoff = nz_frac_cutoff, N_cells_min = N_cells_min,
                      rem_mkrs_common_in_N_groups_or_more = rem_mkrs_common_in_N_groups_or_more, 
                      N_markers_per_group_max = N_markers_per_group_max, 
                      N_markers_total = N_markers_total )

    '''
    if cell_group_col is not None:
        lst = list(selected_mkr_dict.keys())
        for k in lst:
            if len(selected_mkr_dict[k]) == 0:
                del selected_mkr_dict[k]
    '''
    
    rv = plot_marker_exp_inner( adata_sss, markers = selected_mkr_dict, var_group_col = var_group_col, 
                      cell_group_col = cell_group_col, # group_categ_col = group_categ_col,
                      title = title, title_y_pos = title_y_pos, title_fs = title_fs,
                      text_fs = text_fs, linewidth = linewidth, standard_scale = standard_scale,
                      var_group_rotation = var_group_rotation, var_group_height = var_group_height,
                      nz_frac_max = nz_frac_max, figsize = figsize, swap_ax = swap_ax, 
                      mean_only_expressed = mean_only_expressed, 
                      legend = legend, add_rect = add_rect, cmap = cmap, rect_color = linecolor )
    return rv


############################
############################
###### Plot dot (NEW) ######

# -------------------------------------------------------------------------
# 1) Helper: 공통 marker 제거 (cell type 특이 marker만 남기기)
# -------------------------------------------------------------------------
def remove_common(mkr_dict, prn=True):
    """
    기존 정의 유지:
    - 입력: {cell_type: [marker1, marker2, ...]}
    - 출력: 공통 marker 제거된 dict (cell type별로 유일하게 등장하는 marker만)
    - prn=True일 때 cell type별 marker 수 변화 출력
    """
    cts = list(mkr_dict.keys())
    # flatten & unique
    mkrs_all = sorted(set(m for ct in cts for m in mkr_dict[ct]))

    # presence matrix
    df = pd.DataFrame(0, index=mkrs_all, columns=cts, dtype=int)
    for c in cts:
        df.loc[mkr_dict[c], c] = 1

    Sum = df.sum(axis=1)

    new_dict = {}
    msg_parts = []
    for c in cts:
        b = (df[c] > 0) & (Sum == 1)
        mkrs1 = df.index[b].tolist()
        if prn and (len(mkr_dict[c]) != len(mkrs1)):
            msg_parts.append(f"{c}: {len(mkr_dict[c])} > {len(mkrs1)}")

        if len(mkrs1) > 0:
            new_dict[c] = mkrs1

    if prn and msg_parts:
        print(", ".join(msg_parts))

    return new_dict


# -------------------------------------------------------------------------
# 2) Helper: marker dict에서 target celltype만 추출 + 공통 제거 옵션
# -------------------------------------------------------------------------
def get_markers_all4(mkr_file, target_lst, genes=None, rem_cmn=False):
    """
    기존 정의 유지:
    - mkr_file: dict (celltype → marker list)
    - target_lst: 사용할 celltype 리스트
    - genes: adata.var.index 등 전체 gene 리스트 (intersection에 사용)
    - rem_cmn: True면 celltype 간 공통 marker 제거
    - 반환: (mkrs_all, mkr_dict)
        mkrs_all : 최종 marker들의 union
        mkr_dict : celltype별 marker dict
    """
    if not isinstance(mkr_file, dict):
        print('ERROR: marker input must be a dictionary.')
        return None

    # 1) target celltype만 서브셋
    mkr_dict = {}
    if target_lst is not None and len(target_lst) > 0:
        for c in target_lst:
            if c in mkr_file:
                mkr_dict[c] = list(mkr_file[c])
    else:
        mkr_dict = {k: list(v) for k, v in mkr_file.items()}

    # 2) 공통 marker 제거 옵션
    if rem_cmn:
        mkr_dict = remove_common(mkr_dict, prn=True)

    # 3) gene 리스트와 교차
    mkrs_all = []
    mkrs_cmn = []
    for ct, mkrs in mkr_dict.items():
        if genes is not None:
            ms = list(set(mkrs).intersection(genes))
        else:
            ms = mkrs

        if not ms:
            continue

        mkrs_all.extend(ms)
        if len(mkrs_cmn) == 0:
            mkrs_cmn = ms
        else:
            mkrs_cmn = list(set(mkrs_cmn).intersection(ms))

    mkrs_all = list(set(mkrs_all))
    if genes is not None:
        mkrs_all = list(set(mkrs_all).intersection(genes))

    return mkrs_all, mkr_dict


# -------------------------------------------------------------------------
# 3) Helper: Mac* celltype 간 공통 marker 제거
# -------------------------------------------------------------------------
def remove_mac_common_markers(mkrs_dict):
    """
    기존 정의 유지:
    - 'Mac' 로 시작하는 celltype들 간 공통 marker 제거
    - Mono*는 일단 그대로 두고, Mac 계열에서만 공통 제거
    """
    keys = list(mkrs_dict.keys())
    mac_keys = [k for k in keys if k.startswith('Mac')]
    mono_key = next((k for k in keys if k.startswith('Mono')), None)

    if len(mac_keys) <= 1:
        return mkrs_dict

    # Mac 계열 공통 marker 구하기
    mac_common = set(mkrs_dict[mac_keys[0]])
    for k in mac_keys[1:]:
        mac_common &= set(mkrs_dict[k])

    if not mac_common:
        return mkrs_dict

    # 새 dict 생성 (in-place mutation 최소화)
    new_dict = {}
    for k in keys:
        mkrs = mkrs_dict[k]
        if k in mac_keys:
            new_dict[k] = [m for m in mkrs if m not in mac_common]
        else:
            new_dict[k] = list(mkrs)

    # Mono 관련 처리는 기존 코드와 동일 (현재는 주석 처리 상태 유지)
    # if mono_key is not None:
    #     mono_lst = new_dict[mono_key]
    #     del new_dict[mono_key]
    #     new_dict[mono_key] = mono_lst

    return new_dict


# -------------------------------------------------------------------------
# 4) Helper: marker dict를 실제 발현 데이터(X, y) 기반으로 다듬기
# -------------------------------------------------------------------------
def update_markers_dict2(mkrs_all, mkr_dict, X, y,
                         rend=None, cutoff=0.3,
                         Nall=20, Npt=20, Npt_tot=0):
    """
    기존 시그니처/반환값 유지:
    - 입력:
        mkrs_all : 전체 candidate marker 리스트
        mkr_dict : {celltype: [markers...]}
        X        : (cell × gene) expression DataFrame
        y        : celltype (index=X.index와 align)
        rend     : rename dict {old: new} or None
        cutoff   : within-group nz fraction threshold
        Npt      : group당 최대 marker 수
        Npt_tot  : 전체 marker 수 제한 (0이면 사용 안함)
    - 출력:
        mkrs_dict2 : 최종 celltype별 marker dict
        df         : celltype × marker non-zero fraction matrix
        pe_lst     : 최종 선택된 marker들의 pe 리스트
        pex_lst    : 최종 선택된 marker들의 pex 리스트
    """
    # ------------------------------------------------------------------
    # 4-1) celltype 목록 및 rename dict 정리
    # ------------------------------------------------------------------
    if rend is None:
        ct_list = sorted(mkr_dict.keys())
        rend = dict(zip(ct_list, ct_list))
    else:
        ct_list = list(rend.keys())

    # presence fraction matrix (celltype × marker)
    df = pd.DataFrame(0.0, index=ct_list, columns=mkrs_all, dtype=float)

    # group별 non-zero fraction 계산
    for ct in ct_list:
        if ct not in mkr_dict:
            continue
        b = (y == ct)
        ms = list(set(mkr_dict[ct]).intersection(mkrs_all))
        if len(ms) == 0:
            continue
        pe = (X.loc[b, ms] > 0).mean(axis=0).values
        df.loc[ct, ms] = pe

    # ------------------------------------------------------------------
    # 4-2) special case: celltype이 1개뿐인 경우
    # ------------------------------------------------------------------
    if df.shape[0] == 1:
        mkrs_all = list(df.columns.values)
        mkrs_dict = {}
        pe_lst, pex_lst = [], []

        for ct in ct_list:
            if ct not in mkr_dict:
                continue
            b = (y == ct)
            ms = list(set(mkr_dict[ct]).intersection(mkrs_all))
            if len(ms) == 0:
                continue

            pe = np.array((X.loc[b, ms] > 0).mean(axis=0))
            pex = np.array((X.loc[~b, ms] > 0).mean(axis=0))

            # pe 기준으로 내림차순 정렬
            odr = np.argsort(-pe)
            ms_new = [ms[o] for o in odr if pe[o] >= cutoff]

            # pe/pex 저장
            pe_valid = pe[~np.isnan(pe)]
            pex_valid = pex[~np.isnan(pex)]
            pe_lst.extend(pe_valid.tolist())
            pex_lst.extend(pex_valid.tolist())

            if len(ms_new) > 0:
                mkrs_dict[rend[ct]] = ms_new[:min(Npt, len(ms_new))]
            else:
                mkrs_dict[rend[ct]] = ms[:min(Npt, len(ms))]

        mkrs_dict2 = mkrs_dict
        return mkrs_dict2, df, pe_lst, pex_lst

    # ------------------------------------------------------------------
    # 4-3) 일반적인 multi-group 경우
    # ------------------------------------------------------------------
    # p1: 각 marker에서 max(nz_frac), p2: 두 번째로 큰 nz_frac
    p1 = df.max(axis=0)
    p2 = pd.Series(0.0, index=p1.index)

    idx = df.index.values
    for m in df.columns:
        vals = df[m].values
        odr = np.argsort(-vals)
        if len(odr) > 1:
            p2[m] = vals[odr[1]]
        else:
            p2[m] = 0.0

    nn = (df >= 0.5).sum(axis=0)

    # 기본 필터: p1 > 0만 유지 (원래는 & b1 & b2 고려했으나 코드상 주석 처리되어 있었음)
    b0 = p1 > 0
    # b1 = (p2/(p1 + 0.0001)) < 0.5
    # b2 = nn < 4
    b = b0  # 원 코드와 동일한 동작 (b1, b2는 사실상 사용 안함)
    df = df.loc[:, b]
    mkrs_all = list(df.columns)

    mkrs_dict = {}
    pe_dict = {}
    pex_dict = {}

    # ------------------------------------------------------------------
    # 4-4) 각 celltype에 대해 marker 선택
    # ------------------------------------------------------------------
    for ct in ct_list:
        b_ct = (y == ct)
        if ct not in mkr_dict:
            continue

        ms = list(set(mkr_dict[ct]).intersection(mkrs_all))
        if len(ms) == 0:
            continue

        pe = np.array((X.loc[b_ct, ms] > 0).mean(axis=0))
        pex = np.array((X.loc[~b_ct, ms] > 0).mean(axis=0))

        odr = np.argsort(-pe)
        ms_new, pe_new, pex_new = [], [], []

        for o in odr:
            if (pe[o] >= cutoff) and (not np.isnan(pe[o])):
                ms_new.append(ms[o])
                pe_new.append(pe[o])
                pex_new.append(pex[o])

        if len(ms_new) > 0:
            mkrs_dict[rend[ct]] = ms_new[:min(Npt, len(ms_new))]
            pe_dict[rend[ct]] = pe_new[:min(Npt, len(ms_new))]
            pex_dict[rend[ct]] = pex_new[:min(Npt, len(ms_new))]
        else:
            mkrs_dict[rend[ct]] = ms[:min(Npt, len(ms))]
            pe_dict[rend[ct]] = list(pe)[:min(Npt, len(ms))]
            pex_dict[rend[ct]] = list(pex)[:min(Npt, len(ms))]

    # ------------------------------------------------------------------
    # 4-5) 전체 marker 수를 Npt_tot 이하로 제한하는 로직
    # ------------------------------------------------------------------
    mkr_lst, pe_lst, pex_lst = [], [], []
    cnt2 = 0
    for ct in ct_list:
        if ct not in mkr_dict:
            continue
        if rend[ct] not in mkrs_dict:
            continue
        pe_lst.extend(pe_dict[rend[ct]])
        pex_lst.extend(pex_dict[rend[ct]])
        mkr_lst.extend(mkrs_dict[rend[ct]])
        cnt2 += len(mkrs_dict[rend[ct]])

    if (Npt_tot is not None) and (Npt_tot > 20) and (len(pe_lst) > 0):
        odr = np.argsort(pe_lst)
        if len(odr) > Npt_tot:
            pe_th = pe_lst[odr[len(odr) - Npt_tot]]
        else:
            pe_th = pe_lst[odr[0]]

        pe_lst, pex_lst = [], []
        cnt = 0
        for ct in ct_list:
            if ct not in mkr_dict:
                continue
            key = rend[ct]
            pe_arr = np.array(pe_dict.get(key, []))
            if pe_arr.size == 0:
                continue
            b_keep = pe_arr >= pe_th
            mkrs_dict[key] = list(np.array(mkrs_dict[key])[b_keep])
            cnt += len(mkrs_dict[key])
            pe_lst.extend(list(pe_arr[b_keep]))
            pex_lst.extend(list(np.array(pex_dict[key])[b_keep]))

        print('Num markers selected: %i -> %i' % (cnt2, cnt))

    # ------------------------------------------------------------------
    # 4-6) 최종 dict 생성 (rend 적용)
    # ------------------------------------------------------------------
    mkrs_dict2 = {}
    for m in mkr_dict.keys():
        new_name = rend.get(m, m)
        if new_name in mkrs_dict:
            mkrs_dict2[new_name] = mkrs_dict[new_name]

    return mkrs_dict2, df, pe_lst, pex_lst


# -------------------------------------------------------------------------
# 5) get_best_markers: adata에서 최적 marker 선택
# -------------------------------------------------------------------------
def get_best_markers(adata, markers_in=None, var_group_col=None,
                     nz_frac_cutoff=0.1,
                     rem_mkrs_common_in_N_groups_or_more=3, N_cells_min=20,
                     N_markers_per_group_max=15, N_markers_total=200):
    """
    기존 입력/출력 유지:
    - 입력:
        adata
        markers_in: dict or None
        var_group_col: obs 컬럼명
        nz_frac_cutoff, N_cells_min, ...
    - 출력:
        mkrs_dict : 선정된 marker dict
        adata_t   : marker 기반으로 subset 된 AnnData
        var_group_col : 실제 사용한 group 컬럼명
    """
    Npt = N_markers_per_group_max
    Npt_tot = N_markers_total
    show_unassigned = False
    rend = None
    other_genes = []

    # 1) marker dict 준비
    if markers_in is None:
        markers = copy.deepcopy(adata.uns['Celltype_marker_DB']['subset_markers_dict'])
        var_group_col = 'celltype_subset'
    else:
        markers = copy.deepcopy(markers_in)

    target_lst = sorted(markers.keys())
    genes = list(adata.var.index.values)

    # 2) 전체 marker set 및 dict 만들기
    mkrs_all, mkr_dict = get_markers_all4(markers, target_lst, genes, rem_cmn=False)
    target_lst2 = list(mkr_dict.keys())

    y = adata.obs[var_group_col]

    # unassigned 추가 옵션 (현재는 기본 False)
    if show_unassigned and (np.sum(y.isin(['unassigned'])) > 10):
        mkr_dict['unassigned'] = []
        target_lst2 = list(mkr_dict.keys())

    # 3) 해당 group들만 포함하는 AnnData subset
    b = y.isin(target_lst2)
    adata_t = adata[b, list(set(mkrs_all).union(other_genes))].copy()
    X = adata_t.to_df()
    y = adata_t.obs[var_group_col]

    # 4) 1차 marker refinement (cutoff=0으로 넉넉히 잡고, Npt*2까지)
    mkrs_dict, df, pe_lst, pex_lst = update_markers_dict2(
        mkrs_all, mkr_dict, X, y, rend,
        cutoff=0, Npt=Npt * 2, Npt_tot=0
    )

    # 5) Mac 계열 공통 marker 제거
    mkrs_dict = remove_mac_common_markers(mkrs_dict)

    if rend is not None:
        adata_t.obs[var_group_col] = adata_t.obs[var_group_col].replace(rend)

    # 6) marker 사용 빈도 계산 (너무 많은 celltype에 등장하는 marker 제거)
    mkall = sorted({m for v in mkrs_dict.values() for m in v})
    nmkr = dict(zip(mkall, [0] * len(mkall)))
    for key, mkrs in mkrs_dict.items():
        for m in mkrs:
            nmkr[m] += 1

    if rem_mkrs_common_in_N_groups_or_more > 0:
        overused = [m for m, cnt in nmkr.items()
                    if cnt >= rem_mkrs_common_in_N_groups_or_more]
        if overused:
            for m in overused:
                for key in mkrs_dict.keys():
                    if m in mkrs_dict[key]:
                        mkrs_dict[key].remove(m)

    # 7) 각 group별 cell 수 >= N_cells_min 인 group만 유지
    ps_cnt = adata_t.obs[var_group_col].value_counts()
    valid_groups = [g for g in mkrs_dict.keys()
                    if (g in ps_cnt.index) and (ps_cnt[g] >= N_cells_min)]
    mkrs_dict = {g: mkrs_dict[g] for g in valid_groups}

    target_lst2 = list(mkrs_dict.keys())
    y = adata_t.obs[var_group_col]

    if show_unassigned and (np.sum(y.isin(['unassigned'])) > 10):
        mkrs_dict['unassigned'] = []
        target_lst2 = list(mkrs_dict.keys())

    if len(target_lst2) == 0:
        return None, None

    # 8) 다시 해당 group들만 남기고 refine 한 번 더 (이번에는 nz_frac_cutoff 사용)
    b = y.isin(target_lst2)
    adata_t = adata_t[b, :]

    if rend is not None:
        adata_t.obs[var_group_col] = adata_t.obs[var_group_col].replace(rend)

    X = adata_t.to_df()
    y = adata_t.obs[var_group_col]

    mkrs_all_final = sorted({m for v in mkrs_dict.values() for m in v})

    mkrs_dict, df, pe_lst, pex_lst = update_markers_dict2(
        mkrs_all_final, mkrs_dict, X, y, None,
        cutoff=nz_frac_cutoff, Npt=Npt, Npt_tot=Npt_tot
    )

    # 빈 marker 리스트 가진 group 제거
    for k in list(mkrs_dict.keys()):
        if len(mkrs_dict[k]) == 0:
            del mkrs_dict[k]

    # markers_in이 None이면, marker 없는 group 제외한 adata_t 반환
    if markers_in is None:
        adata_t.obs[var_group_col] = adata_t.obs[var_group_col].astype(str)
        b = adata_t.obs[var_group_col].isin(list(mkrs_dict.keys()))
        adata_t = adata_t[b, :]

    return mkrs_dict, adata_t, var_group_col


# -------------------------------------------------------------------------
# 6) plot_marker_exp_inner: 실제 dotplot 그리는 부분
# -------------------------------------------------------------------------
def plot_marker_exp_inner(adata, markers, var_group_col='celltype_subset',
                          cell_group_col=None,
                          title=None, title_y_pos=1.1, title_fs=14,
                          text_fs=12, linewidth=1.5,
                          var_group_height=1.2, var_group_rotation=0,
                          standard_scale='var',
                          nz_frac_max=0.5,
                          mean_only_expressed=False,
                          figsize=(20, 4), swap_ax=False, legend=False,
                          add_rect=True,
                          cmap='Reds', rect_color='royalblue'):
    """
    기존 함수 시그니처/출력 유지.
    내부를 섹션별로 조금 읽기 쉽게 재구성만 했습니다.
    """

    group_categ_col = var_group_col
    group_col = cell_group_col
    mkrs_dict = markers
    show = True

    Lw = linewidth
    hgt = var_group_height
    title_fontsize = title_fs

    # Scanpy 존재 여부 체크
    try:
        import scanpy as sc  # noqa:F401
        SCANPY = True
    except ImportError:
        SCANPY = False

    if not SCANPY:
        print('ERROR: scanpy not installed.')
        return

    # 1) marker 리스트 및 subset
    mkrs_all = []
    for key in mkrs_dict.keys():
        mkrs_all.extend(mkrs_dict[key])

    adata_t = adata[:, list(set(mkrs_all))]

    sx = len(mkrs_all)
    if group_col is None:
        sy = adata_t.obs[var_group_col].nunique()
    else:
        sy = adata_t.obs[group_col].nunique()

    # 2) figsize 재조정 (swap_ax 여부에 따라)
    if swap_ax or (markers is None):
        figsize_used = None
    else:
        if figsize is None:
            figsize_used = (sx / 3.2, 4)
        else:
            figsize_used = list(figsize)

        if swap_ax:
            lx, ly = figsize_used[1], figsize_used[0]
            ly = lx * sy / sx
            figsize_used = (ly, lx)
            title_y_pos = (sx + title_y_pos) / sx
        else:
            lx, ly = figsize_used
            ly = lx * sy / sx
            figsize_used = (lx, ly)
            title_y_pos = (sy + title_y_pos) / sy

    # 3) dotplot용 group 순서(categ_order) 계산
    if not show:
        return

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        if group_col is None:
            Type_level = var_group_col
            categ_order = list(mkrs_dict.keys())
        else:
            var_group_lst = sorted(mkrs_dict.keys())
            mkrs_dict = {c: mkrs_dict[c] for c in var_group_lst}

            Type_level = group_col
            if group_categ_col is None:
                categ_order = sorted(adata_t.obs[Type_level].unique())
            else:
                group_categ_lst = sorted(adata_t.obs[group_categ_col].unique())
                categ_order = []
                num_groups_per_group_categ = {}

                for gc in group_categ_lst:
                    b = (adata_t.obs[group_categ_col] == gc)
                    lst_tmp = sorted(adata_t[b, :].obs[Type_level].unique())

                    if gc in var_group_lst:
                        genes = mkrs_dict[gc]
                    else:
                        genes = mkrs_all

                    Xx = (adata_t[b, genes].to_df() > 0)
                    Xx['group'] = adata_t[b, :].obs[Type_level]
                    X = Xx.groupby('group').mean()
                    X['mean'] = X.mean(axis=1)
                    lst_tmp = X.sort_values(by='mean', ascending=False).index.tolist()

                    categ_order.extend(lst_tmp)
                    num_groups_per_group_categ[gc] = len(lst_tmp)

        dp = sc.pl.dotplot(
            adata_t, mkrs_dict, groupby=Type_level,
            categories_order=categ_order,
            return_fig=True, log=True, figsize=figsize_used,
            var_group_rotation=var_group_rotation, show=False,
            standard_scale=standard_scale, cmap=cmap,
            mean_only_expressed=mean_only_expressed,
            dot_max=nz_frac_max, swap_axes=swap_ax
        )
        dp.add_totals()

    ax_dict = dp.get_axes()
    ax = ax_dict['mainplot_ax']

    # 제목 및 tick label 세팅
    if title is not None:
        ax.set_title(title, fontsize=title_fontsize, y=title_y_pos)
    ax.tick_params(labelsize=text_fs)

    # ------------------------------------------------------------------
    # Rectangles for marker blocks
    # ------------------------------------------------------------------
    ylabels = []
    for key in mkrs_dict.keys():
        ylabels.extend(mkrs_dict[key])

    if add_rect:
        if group_col is None:
            # group_col이 없는 기본 상황
            cnt = 0
            for j, key in enumerate(mkrs_dict.keys()):
                L = len(mkrs_dict[key])
                if swap_ax:
                    ax.add_patch(Rectangle((j, cnt), 1, L, fill=False,
                                           edgecolor=rect_color, lw=Lw))
                else:
                    ax.add_patch(Rectangle((cnt, j), L, 1, fill=False,
                                           edgecolor=rect_color, lw=Lw))
                cnt += L

            if categ_order is not None:
                j = len(mkrs_dict.keys()) - 1
                L_tot = cnt  # 사용은 하지 않지만 원 구조 유지
                outer_loops = int(len(categ_order) / len(mkrs_dict.keys()))
                for kk in range(outer_loops - 1):
                    cnt = 0
                    for j1, key in enumerate(mkrs_dict.keys()):
                        j += 1
                        L = len(mkrs_dict[key])
                        if swap_ax:
                            ax.add_patch(Rectangle((j, cnt), 1, L, fill=False,
                                                   edgecolor=rect_color, lw=Lw))
                        else:
                            ax.add_patch(Rectangle((cnt, j), L, 1, fill=False,
                                                   edgecolor=rect_color, lw=Lw))
                        cnt += L
        else:
            # group_categ_col이 있는 보다 복잡한 상황 그대로 유지
            group_categ_lst = sorted(adata_t.obs[group_categ_col].unique())
            cnt_x = cnt_y = 0
            vg_lst = list(mkrs_dict.keys())
            num_groups_per_group_categ = {}

            # 위에서 이미 계산했으면 재사용 가능하지만,
            # 여기서는 원 코드 구조를 크게 바꾸지 않고 유지
            for gc in group_categ_lst:
                b = (adata_t.obs[group_categ_col] == gc)
                lst_tmp = sorted(adata_t[b, :].obs[group_col].unique())
                num_groups_per_group_categ[gc] = len(lst_tmp)

            if set(group_categ_lst).issubset(set(vg_lst)) or set(vg_lst).issubset(set(group_categ_lst)):
                if set(group_categ_lst).issubset(set(vg_lst)):
                    super_list = vg_lst
                else:
                    super_list = group_categ_lst

                for gc in super_list:
                    L_x = len(mkrs_dict[gc]) if gc in vg_lst else 0
                    L_y = num_groups_per_group_categ[gc] if gc in group_categ_lst else 0
                    if swap_ax:
                        ax.add_patch(Rectangle((cnt_y, cnt_x), L_y, L_x, fill=False,
                                               edgecolor=rect_color, lw=Lw))
                    else:
                        ax.add_patch(Rectangle((cnt_x, cnt_y), L_x, L_y, fill=False,
                                               edgecolor=rect_color, lw=Lw))
                    cnt_x += L_x
                    cnt_y += L_y
            else:
                cnt = 0
                width = len(mkrs_all)
                for gc in group_categ_lst[:-1]:
                    cnt += num_groups_per_group_categ[gc]
                    if swap_ax:
                        ax.plot([cnt, cnt], [0, width], rect_color, lw=Lw)
                    else:
                        ax.plot([0, width], [cnt, cnt], rect_color, lw=Lw)

                cnt = 0
                height = len(categ_order)
                for vg in vg_lst[:-1]:
                    cnt += len(mkrs_dict[vg])
                    if swap_ax:
                        ax.plot([0, height], [cnt, cnt], rect_color, lw=Lw)
                    else:
                        ax.plot([cnt, cnt], [0, height], rect_color, lw=Lw)

    # ------------------------------------------------------------------
    # legend 위치 정리
    # ------------------------------------------------------------------
    ax2 = ax_dict['color_legend_ax']
    ax3 = ax_dict['size_legend_ax']

    if not legend:
        ax2.remove()
        ax3.remove()
    else:
        if not swap_ax:
            box = ax2.get_position()
            dx = (box.x1 - box.x0) * 0.3
            box.x0 += dx
            box.x1 += dx
            ax2.set_position(box)

            box2 = ax3.get_position()
            dx2 = (box2.x1 - box2.x0) * 0.3
            box2.x0 += dx2
            box2.x1 += dx2

            dy = (box2.y1 - box2.y0)
            if box2.y0 > (box.y1 + dy * 2):
                Dy = box2.y0 - (box.y1 + dy * 2)
                box2.y0 -= Dy
                box2.y1 -= Dy
            else:
                Dy = (box.y1 + dy * 2) - box2.y0
                box2.y0 += Dy
                box2.y1 += Dy
            ax3.set_position(box2)

    # ------------------------------------------------------------------
    # Variable Group Ax (marker block 위/옆 레이블)
    # ------------------------------------------------------------------
    axa = ax_dict['gene_group_ax']
    axa.clear()
    axa.set_frame_on(False)
    axa.grid(False)

    cnt = 0
    gap = 0.2

    # 각 celltype별 cell 수 비율
    n_cells = []
    for ct in mkrs_dict.keys():
        b = (adata_t.obs[var_group_col] == ct)
        n_cells.append(np.sum(b))
    n_cells = np.array(n_cells)
    p_cells = n_cells / n_cells.sum()

    for j, key in enumerate(mkrs_dict.keys()):
        L = len(mkrs_dict[key])
        if swap_ax:
            axa.plot([hgt, hgt], [cnt + gap, cnt + L - gap], 'k', lw=1.5)
            axa.plot([hgt, 0], [cnt + gap, cnt + gap], 'k', lw=1.5)
            axa.plot([hgt, 0], [cnt + L - gap, cnt + L - gap], 'k', lw=1.5)
            axa.text(hgt * var_group_height, cnt + L / 2, ' ' + key,
                     fontsize=text_fs + 1, rotation=0,
                     ha='left', va='center')
        else:
            axa.plot([cnt + gap, cnt + L - gap], [hgt, hgt], 'k', lw=1.5)
            axa.plot([cnt + gap, cnt + gap], [hgt, 0], 'k', lw=1.5)
            axa.plot([cnt + L - gap, cnt + L - gap], [hgt, 0], 'k', lw=1.5)
            Ha = 'center'
            if 0 < var_group_rotation < 90:
                Ha = 'left'
            elif -90 < var_group_rotation < 0:
                Ha = 'right'
            axa.text(cnt + L / 2, hgt * var_group_height, ' ' + key,
                     fontsize=text_fs + 1,
                     rotation=var_group_rotation, ha=Ha)
        cnt += L

    # ------------------------------------------------------------------
    # group_extra_ax: 각 group별 cell 수 bar 표시
    # ------------------------------------------------------------------
    axb = ax_dict['group_extra_ax']

    if swap_ax:
        box_main = ax.get_position()
        box = axb.get_position()
        box.y1 = box_main.y0 - (box.y1 - box.y0)
        box.y0 = box_main.y0
        axb.set_position(box)

    axb.clear()
    axb.set_frame_on(False)
    axb.get_xaxis().set_visible(False)
    axb.get_yaxis().set_visible(False)

    n_cells2 = []
    if categ_order is None:
        categ_order = list(mkrs_dict.keys())

    for ct in categ_order:
        b = (adata_t.obs[Type_level] == ct)
        n_cells2.append(np.sum(b))
    n_cells2 = np.array(n_cells2)
    p_cells2 = np.sqrt(n_cells2)
    p_cells2 = p_cells2 / np.max(p_cells2) if np.max(p_cells2) > 0 else p_cells2

    for j, key in enumerate(categ_order):
        yv = p_cells2[j]
        if swap_ax:
            axb.add_patch(Rectangle((j + 0.2, 0), 0.6, yv, fill=True,
                                    facecolor='firebrick', edgecolor='black', lw=1.5))
            axb.text(j + 0.5, yv, f' {n_cells2[j]} ', rotation=90,
                     ha='center', va='top', fontsize=text_fs)
        else:
            axb.add_patch(Rectangle((0, j + 0.2), yv, 0.6, fill=True,
                                    facecolor='firebrick', edgecolor='black', lw=1.5))
            axb.text(yv, j + 0.5, f' {n_cells2[j]} ', rotation=0,
                     ha='left', va='center', fontsize=text_fs)

    # ------------------------------------------------------------------
    # 최종 tick 재설정
    # ------------------------------------------------------------------
    if swap_ax:
        ax.set_yticks(list(np.arange(len(ylabels)) + 0.5))
        ax.set_yticklabels(ylabels)
        ax.xaxis.set_ticks_position('top')
        ax.set_xticks(list(np.arange(len(categ_order)) + 0.5))
        ax.set_xticklabels(categ_order)
    else:
        ax.set_xticks(list(np.arange(len(ylabels)) + 0.5))
        ax.set_xticklabels(ylabels)
        ax.yaxis.set_ticks_position('left')
        ax.set_yticks(list(np.arange(len(categ_order)) + 0.5))
        ax.set_yticklabels(categ_order)

    plt.show()
    return


# -------------------------------------------------------------------------
# 7) plot_marker_exp: high-level wrapper (외부에서 직접 호출하는 함수)
# -------------------------------------------------------------------------
def plot_marker_exp(adata, markers=None, celltype_selection=None, var_group_col=None, cell_group_col=None,
                    N_cells_per_group_min=20, N_markers_per_group_max=15, N_markers_total=200,
                    title=None, title_y_pos=1.1, title_fs=14, text_fs=12, linewidth=1.5,
                    var_group_height=1.2, var_group_rotation=0, standard_scale='var',
                    nz_frac_max=0.5, nz_frac_cutoff=0.1, rem_mkrs_common_in_N_groups_or_more=3,
                    mean_only_expressed=False, legend=False, figsize=(20, 4), swap_ax=False,
                    add_rect=True, cmap='Reds', linecolor='royalblue'):

    """
    -------------------------------------------------------------------------
    📌 Marker expression dot plots (auto-select best markers per group)
    -------------------------------------------------------------------------
    High-level wrapper to visualize marker gene expression across groups
    (e.g., cell types, conditions, samples) using a dot plot.

    This function:
      1) Chooses the appropriate subset of cells (`adata_s`) based on
         `celltype_selection`, `var_group_col`, and `cell_group_col`.
      2) Calls `get_best_markers(...)` to refine/trim the marker list:
         - removes markers that are too broadly shared,
         - enforces minimum cell counts per group,
         - limits per-group and total number of markers.
      3) Calls `plot_marker_exp_inner(...)` to generate a Scanpy
         dotplot with optional rectangles and group annotations.

    Parameters
    ----------
    adata : AnnData
        Input AnnData object. Expected to contain:
        - `adata.obs[var_group_col]` : primary grouping variable
          (e.g., cell subtype, condition).
        - `adata.obs[cell_group_col]` : secondary grouping variable
          (e.g., sample ID, patient ID), if used.
        - If `markers is None`:
            `adata.uns['Celltype_marker_DB']['subset_markers_dict']`
            is used as the initial marker dictionary.
        - If `celltype_selection` is used:
            `adata.uns['DEG_grouping_vars']` and
            `adata.uns['analysis_parameters']['CCI_DEG_BASE']`
            are used to infer grouping columns.

    markers : dict or None
        Dictionary of initial marker genes:
        - keys   : group names (e.g., cell types),
        - values : list of marker genes.
        If None, markers are taken from
        `adata.uns['Celltype_marker_DB']['subset_markers_dict']`.

    celltype_selection : str or None
        If provided and present in
        `adata.uns['DEG_grouping_vars']`, this is used to:
        - subset `adata` to a relevant cell type (or tumor-only subset
          for names containing "tumor"/"cancer"), and
        - automatically set `var_group_col` and `cell_group_col` from
          `DEG_grouping_vars[celltype_selection]`.
        If None, you must specify `var_group_col` and `cell_group_col`
        explicitly.

    var_group_col : str or None
        Column in `adata.obs` specifying the *group* to plot on one axis
        (e.g., refined cell type / condition). If `markers is None`,
        this is often `"celltype_subset"` (set internally inside
        `get_best_markers`), but can be overridden by the logic above.

    cell_group_col : str or None
        Column in `adata.obs` specifying a higher-level group such as
        sample or patient. Used to:
        - filter out samples with fewer than `N_cells_per_group_min`
          cells,
        - define the layout of group annotations in the dotplot.
        If not provided, the plot is grouped only by `var_group_col`.

    N_cells_per_group_min : int
        Minimum number of cells per sample group (`cell_group_col`)
        required to keep that sample in the analysis.

    N_markers_per_group_max : int
        Maximum number of marker genes to keep per group in the final
        marker set (upper limit; actual number may be smaller).

    N_markers_total : int
        Approximate global maximum for the total number of markers
        across all groups (used inside `get_best_markers` for trimming
        the most weakly expressed markers).

    title : str or None
        Plot title passed through to `plot_marker_exp_inner`.

    title_y_pos : float
        Vertical position of the title in axis coordinates.

    title_fs : int
        Font size of the main title.

    text_fs : int
        Base font size for axis ticks and group labels.

    linewidth : float
        Line width for rectangle outlines and auxiliary annotations.

    var_group_height : float
        Height scale for the variable-group outline panel
        (used in `plot_marker_exp_inner`).

    var_group_rotation : float
        Rotation angle (in degrees) for variable-group labels.

    standard_scale : {'var', 'group', None}
        Passed to `scanpy.pl.dotplot` to apply z-score–like scaling
        along variables or groups (see Scanpy docs).

    nz_frac_max : float
        Maximum fraction of non-zero values (dot size scaling) used
        for the size legend in the dot plot.

    nz_frac_cutoff : float
        Minimum fraction of non-zero cells required (per group) for a
        gene to be retained as a marker in the final selection.

    rem_mkrs_common_in_N_groups_or_more : int
        Marker genes that appear as markers in this many or more groups
        are removed (to favor more specific markers).

    mean_only_expressed : bool
        Passed to `scanpy.pl.dotplot`; if True, the color represents
        the mean of non-zero values only.

    legend : bool
        If True, keep color and dot-size legends; if False, remove them.

    figsize : tuple
        Base figure size; may be adaptively rescaled in
        `plot_marker_exp_inner` depending on the number of markers
        and groups, unless `swap_ax` is True.

    swap_ax : bool
        If False (default), markers are on the x-axis and groups on the y-axis.
        If True, axes are swapped and all annotations are adjusted
        accordingly.

    add_rect : bool
        If True, draw rectangular outlines to visually separate
        marker blocks or group categories.

    cmap : str or Colormap
        Colormap for the dot color (e.g., "Reds").

    linecolor : str
        Color used for rectangles and structural lines
        (passed as `rect_color` to `plot_marker_exp_inner`).

    Returns
    -------
    None
        This function generates the dot plot via matplotlib/Scanpy and
        returns the result of `plot_marker_exp_inner` (which is
        typically None). The main effect is the rendered figure.

    Example
    -------
    # 1) Automatic marker selection using Celltype_marker_DB
    plot_marker_exp(
        adata,
        markers=None,
        var_group_col="celltype_subset",
        cell_group_col="sample",
        N_cells_per_group_min=30,
        N_markers_per_group_max=10,
        N_markers_total=150,
        title="Selected markers per cell subset",
        legend=True
    )

    # 2) Using a custom marker dictionary and a predefined DEG setup
    #    (celltype_selection must exist in adata.uns['DEG_grouping_vars'])
    plot_marker_exp(
        adata,
        markers=my_marker_dict,
        celltype_selection="Myeloid",
        N_cells_per_group_min=20,
        nz_frac_cutoff=0.15,
        rem_mkrs_common_in_N_groups_or_more=3,
        swap_ax=True,
        title="Best markers for myeloid subsets"
    )
    -------------------------------------------------------------------------
    """
    '''
    기존 시그니처/출력 동일.
    - 내부적으로:
        1) 사용할 adata_s 서브셋 결정
        2) get_best_markers로 marker 선정
        3) plot_marker_exp_inner로 dotplot 그리기
    '''
    
    N_cells_min = N_cells_per_group_min

    if var_group_col is not None:
        adata.obs[var_group_col] = adata.obs[var_group_col].astype(str)

    b_pass = False

    # ------------------------------------------------------------------
    # 1) markers 및 celltype_selection 로직에 따라 adata_s 결정
    # ------------------------------------------------------------------
    if markers is None:
        adata_s = adata[:, :].copy()
        b_pass = True
    elif celltype_selection is not None:
        if ('DEG_grouping_vars' in adata.uns) and (celltype_selection in adata.uns['DEG_grouping_vars']):
            deg_base = adata.uns['analysis_parameters']['CCI_DEG_BASE']
            b = (adata.obs[deg_base] == celltype_selection)
            adata_s = adata[b, :].copy()

            if (var_group_col is None) or (cell_group_col is None):
                var_group_col = adata_s.uns['DEG_grouping_vars'][celltype_selection]['condition col']
                cell_group_col = adata_s.uns['DEG_grouping_vars'][celltype_selection]['sample col']
                b_pass = True
            elif (var_group_col in adata.obs.columns) and (cell_group_col in adata.obs.columns):
                adata_s = adata[:, :]
                b_pass = True
        elif ('tumor' in celltype_selection.lower()) or ('cancer' in celltype_selection.lower()):
            b = adata.obs['tumor_origin_ind']
            adata_s = adata[b, :].copy()
            pcnt = adata_s.obs['celltype_major'].value_counts()
            target_celltype = None
            for i in pcnt.index:
                if i != 'unassigned':
                    target_celltype = i
                    break
            if target_celltype is not None:
                if ('DEG_grouping_vars' in adata.uns) and (target_celltype in adata.uns['DEG_grouping_vars']):
                    celltype_selection = target_celltype
                    var_group_col = adata_s.uns['DEG_grouping_vars'][celltype_selection]['condition col']
                    cell_group_col = adata_s.uns['DEG_grouping_vars'][celltype_selection]['sample col']
                    b_pass = True

    if not b_pass:
        if (var_group_col is not None) and (cell_group_col is not None):
            if (var_group_col in adata.obs.columns) and (cell_group_col in adata.obs.columns):
                adata_s = adata[:, :].copy()
                b_pass = True

    if not b_pass:
        print("ERROR: You need to specify either 'celltype_selection' or "
              "'var_group_col' & 'cell_group_col'.")
        return None

    # ------------------------------------------------------------------
    # 2) sample 수 필터링 (cell_group_col 기준)
    # ------------------------------------------------------------------
    if cell_group_col is not None:
        adata_s.obs[cell_group_col] = adata_s.obs[cell_group_col].astype(str)
        pcnt = adata_s.obs[cell_group_col].value_counts()
        b = pcnt >= N_cells_min
        valid_samples = list(pcnt.index.values[b])
        b = adata_s.obs[cell_group_col].isin(valid_samples)
        adata_s = adata_s[b, :]

    # ------------------------------------------------------------------
    # 3) get_best_markers를 이용해 marker 선택
    # ------------------------------------------------------------------
    selected_mkr_dict, adata_sss, var_group_col = get_best_markers(
        adata_s,
        markers_in=markers, var_group_col=var_group_col,
        nz_frac_cutoff=nz_frac_cutoff, N_cells_min=N_cells_min,
        rem_mkrs_common_in_N_groups_or_more=rem_mkrs_common_in_N_groups_or_more,
        N_markers_per_group_max=N_markers_per_group_max,
        N_markers_total=N_markers_total
    )

    if selected_mkr_dict is None or adata_sss is None:
        print("No markers selected or no valid groups.")
        return None

    # ------------------------------------------------------------------
    # 4) 실제 dotplot 그리기
    # ------------------------------------------------------------------
    rv = plot_marker_exp_inner(
        adata_sss, markers=selected_mkr_dict, var_group_col=var_group_col,
        cell_group_col=cell_group_col,
        title=title, title_y_pos=title_y_pos, title_fs=title_fs,
        text_fs=text_fs, linewidth=linewidth, standard_scale=standard_scale,
        var_group_rotation=var_group_rotation, var_group_height=var_group_height,
        nz_frac_max=nz_frac_max, figsize=figsize, swap_ax=swap_ax,
        mean_only_expressed=mean_only_expressed,
        legend=legend, add_rect=add_rect, cmap=cmap, rect_color=linecolor
    )
    return rv


############################
######## DEG/GSEA ##########

def plot_deg( df_deg_dct, reference = 'log2_FC', n_genes_to_show = 30, pval_cutoff = 0.05, 
              figsize = (6,4), dpi = 100, text_fs = 10, title_fs = 12, label_fs = 11, 
              tick_fs = 10, ncols = 2, wspace = 0.15, hspace = 0.2, 
              deg_stat_dct = None, show_log_pv = True ):

    """
    ------------------------------------------------------------
    📌 Visualize **multi-group DEG summary** with ranked gene plots
    ------------------------------------------------------------

    This function plots DEG profiles across multiple conditions/groups,
    displaying top-ranked genes per group using a score metric
    (e.g. log2_FC, nz_pct_score). Significantly enriched genes are filtered
    by P-value and annotated with their names and adjusted significance.

    Supports multi-panel grid visualization for group comparison.

    Parameters
    ----------
    df_deg_dct : dict
        { group_name : DEG result dataframe }
        Required columns:
            - 'pval' or 'nz_pct_pval'
            - reference metric column (default='log2_FC')
            - (optional) 'pval_adj' for log-scaled annotation

    reference : str (default='log2_FC')
        Column used for ranking genes on the y-axis.
        If set to 'nz_pct_score', filtering is based on 'nz_pct_pval'.

    n_genes_to_show : int (default=30)
        Maximum number of top-ranked genes displayed per group/panel.

    pval_cutoff : float (default=0.05)
        DEG significance threshold for gene filtering.

    figsize : tuple (default=(6,4))
        Base figure size per column (scaled automatically by number of groups).

    dpi : int (default=100)
        Plot resolution.

    text_fs, title_fs, label_fs, tick_fs : int
        Font sizes for gene labels, subplot titles, x/y labels, axis ticks.

    ncols : int (default=2)
        Number of columns in the subplot layout.

    wspace, hspace : float
        Horizontal & vertical spacing between subplots.

    deg_stat_dct : dict or None
        { group_name : { metric_name:value }}  
        If provided → summary stats displayed in subplot titles.

    show_log_pv : bool (default=True)
        Show -log10(adjusted P-value) next to gene labels.

    ------------------------------------------------------------
    Returns
    -------
    None
        Displays a multi-panel gene-rank plot window.

    ------------------------------------------------------------
    Usage
    ------
    >>> plot_deg(df_deg_dct,
                 reference='log2_FC',
                 n_genes_to_show=25,
                 pval_cutoff=0.01,
                 show_log_pv=True)

    # With DEG statistics annotated in titles
    >>> plot_deg(df_deg_dct, deg_stat_dct=deg_summary_dict)
    """
    
    nr, nc = int(np.ceil(len(df_deg_dct.keys())/ncols)), int(ncols) # len(df_deg_dct.keys())
    fig, axes = plt.subplots(figsize = (figsize[0]*nc,figsize[1]*nr), nrows=nr, ncols=nc, # constrained_layout=True, 
                             gridspec_kw={'width_ratios': [1]*nc}, dpi = dpi)
    fig.tight_layout() 
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, 
                        wspace=wspace, hspace=hspace)

    for j, key in enumerate(df_deg_dct.keys()):
        if reference == 'nz_pct_score':
            b = df_deg_dct[key]['nz_pct_pval'] <= pval_cutoff
        else:
            b = df_deg_dct[key]['pval'] <= pval_cutoff
        if np.sum(b) > 0:
            dfs = df_deg_dct[key].loc[b,:].sort_values(reference, ascending = False)
            dfs = dfs.iloc[:min(n_genes_to_show, np.sum(b))]
    
            plt.subplot(nr,nc,j+1)
            # plt.figure(figsize = (6,4), dpi = 100)
            X = list(np.arange(dfs.shape[0]))
            Y = list(dfs[reference])
            plt.plot(X, Y)
            m = (np.max(Y)-np.min(Y))
            plt.ylim([np.min(Y)-m*0.4, np.max(Y) + m*0.5])
            tlst = list(dfs.index.values)
            for x, y, t in zip(X, Y, tlst):
                plt.text(x, y, '  %s' % (t), rotation = 90, fontsize = text_fs)
                if show_log_pv:
                    lpv =  -np.log10(dfs.loc[t,'pval_adj'])
                    plt.text(x, y, '(%3.1f) ' % (lpv), rotation = 90, va = 'top', fontsize = text_fs)
            if deg_stat_dct is None:
                plt.title(key, fontsize = title_fs)
            else:
                s = ' ('
                for kk in deg_stat_dct[key].keys():
                    s = s + '%s: %i, ' % (kk, deg_stat_dct[key][kk])
                s = '%s)' % s[:-2]
                plt.title(key + s, fontsize = title_fs)
                
            plt.xlabel('Genes', fontsize = label_fs)
            plt.yticks(fontsize=tick_fs)
            plt.xticks(fontsize=tick_fs)
            if j%nc == 0: plt.ylabel(reference, fontsize = label_fs)
            plt.grid('on')

    if nc*nr > len(df_deg_dct.keys()):
        for j in range(nc*nr-len(df_deg_dct.keys())):
            k = j + len(df_deg_dct.keys()) + 1
            ax = plt.subplot(nr,nc,k)
            ax.axis('off')

    plt.show()
    return


def plot_gsa_result( df_res, items_to_plot, dpi = 100, bar_width = 1,
                  title = None, title_pos = (0.5, 1), title_fs = 16, title_ha = 'center', 
                  label_fs = 10, tick_fs = 8, wspace=0.1, hspace=0.25, Ax = None, 
                  facecolor = 'firebrick', edgecolor = 'black'):

    """
    ------------------------------------------------------------
    📌 Display **Gene Set Analysis (GSA / GSEA) results** as ranked bar-plots
    ------------------------------------------------------------

    This function generates horizontal bar plots for enrichment statistics
    from GSEA/GSA result tables, allowing comparison across selected metrics
    such as -log(q-value), enrichment score, or NES score.

    Multiple result attributes can be plotted side-by-side as sub-panels.

    Parameters
    ----------
    df_res : pd.DataFrame
        Result table containing enrichment statistics.
        Recommended columns include:
            - 'Term'     : pathway or gene set name
            - 'NES'      : normalized enrichment score
            - '-log(q)'  : significance metric or similar

    items_to_plot : list of str
        Column names to visualize. ('NES' removed automatically if absent)

    dpi : int (default=100)
        Figure resolution.

    bar_width : float (0–1, default=1)
        Scale factor to adjust bar thickness.

    title : str or None
        Title placed over combined multi-panel result figure.

    title_pos : tuple (default=(0.5,1))
        (x,y) coordinates of figure title.

    title_fs, label_fs, tick_fs : int
        Font sizes for title, axes labels, and tick labels.

    wspace, hspace : float
        Spacing between subplot columns.

    Ax : matplotlib.axes or None
        If provided, barplot will be drawn into given axis object.

    facecolor, edgecolor : str
        Colors used for bar rendering.

    ------------------------------------------------------------
    Returns
    -------
    True : bool
        Returned after plot is rendered successfully.

    ------------------------------------------------------------
    Usage
    ------
    >>> plot_gsa_result(df_gsea,
                        items_to_plot=['NES','-log(q)'],
                        title='TNBC vs Normal — GSEA pathways')

    >>> plot_gsa_result(df_kegg, ['-log(q)'], bar_width=0.7)
    """

    if 'NES' not in list(df_res.columns.values):
        items_to_plot.remove('NES')
        
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ## draw result
        # sc.settings.set_figure_params(figsize = (4,(df_res.shape[0]*1.1 + 8)/9), dpi=100)
        plt.rcParams['figure.figsize'] = (4,(df_res.shape[0]*1.1 + 8)/9)      
        plt.rcParams['figure.dpi'] = dpi             

        nr, nc = 1, len(items_to_plot)
        fig, axes = plt.subplots(nrows=nr, ncols=nc, constrained_layout=False, dpi = dpi)
        fig.tight_layout() # Or equivalently,  "plt.tight_layout()"
        plt.subplots_adjust(left=None, bottom=None, right=None, top=None, 
                            wspace=wspace, hspace=hspace)
        if title is not None: 
            fig.suptitle(title, x = title_pos[0], y = title_pos[1], 
                         fontsize = title_fs, ha = title_ha)

        ylabel = 'Term'

        for k, x in enumerate(items_to_plot): # , '-log(q-val)-enr', 'NES-pr']):
            plt.subplot(1,nc,k+1)
            xlabel = x
            logpv_max = max( np.ceil( df_res[xlabel].max() ), 2 )
            ax = sns.barplot(data = df_res, y = ylabel, x = xlabel, 
                             facecolor = facecolor, orient = 'h', 
                             edgecolor = edgecolor, linewidth = 1, ax = Ax )

            if bar_width < 1:
                for patch in ax.patches:
                    current_height = patch.get_height()
                    # patch.set_y(patch.get_y() + current_height * bar_width/4)  
                    patch.set_height(current_height * bar_width)             
    
            # plt.xticks(fontsize = tick_fs)
            ax.tick_params(axis='both', which='major', labelsize = tick_fs)
            ax.set_xlabel(xlabel, fontsize = label_fs)
            if k == 0:
                ax.set_ylabel(ylabel, fontsize = label_fs)
            else:
                plt.yticks([])
                ax.set_ylabel(None)
            if x == 'NES':
                plt.xlim([-logpv_max, logpv_max])
            else:
                plt.xlim([0, logpv_max])

        plt.show()
    return True


def plot_gsa_bar_( df_res, pval_cutoff = 1e-2, nes_cutoff = 0, dpi = 100, N_max_to_show = 30,
                  title = None, title_pos = (0.5, 1), title_fs = 16, title_ha = 'center', 
                  label_fs = 10, tick_fs = 8, wspace=0.1, hspace=0.25, Ax = None,
                  items_to_plot = ['-log(p-val)', 'NES', '-log(q-val)'], bar_width = 1,
                  facecolor = 'firebrick', edgecolor = 'black' ):

    ## p-value cutoff 조건에 맞는 term들만 선택
    neg_log_p_cutoff = -np.log10(pval_cutoff)
    df = df_res.copy(deep = True)
    df = df.loc[df['-log(p-val)'] >= neg_log_p_cutoff ]
    if 'NES' in list(df.columns.values):
        df = df.loc[df['NES'] >= nes_cutoff ]
    df = df.sort_values(by = '-log(p-val)', ascending = False).iloc[:min(df.shape[0], N_max_to_show)]
    terms_sel = list(df.index.values)
    
    plot_gsa_result( df, copy.deepcopy(items_to_plot), dpi, bar_width,
                  title, title_pos, title_fs, title_ha, 
                  label_fs, tick_fs, wspace, hspace, Ax,
                  facecolor = facecolor, edgecolor = edgecolor )
    return df


def plot_gsa_bar( df_res, pval_cutoff = 1e-2, nes_cutoff = 0, dpi = 100, N_max_to_show = 30,
                  title = None, title_pos = (0.5, 1), title_fs = 16, title_ha = 'center', 
                  label_fs = 10, tick_fs = 8, wspace=0.1, hspace=0.25, Ax = None,
                  bar_width = 1, items_to_plot = ['-log(p-val)', 'NES', '-log(q-val)'],
                  facecolor = 'firebrick', edgecolor = 'black' ):

    """
    ------------------------------------------------------------
    📌 High-level wrapper for **single or multi-sample GSA visualization**
    ------------------------------------------------------------

    This function extends `plot_gsa_bar_()` by allowing either a single
    result table (`pd.DataFrame`) or multiple results (`dict`) to be plotted.
    - If `df_res` is a DataFrame → one bar plot is drawn and the table returned.
    - If `df_res` is dict → each key is plotted separately and filtered results
      are returned per group.

    Convenient when comparing pathway enrichment across conditions/cell types.

    Parameters
    ----------
    df_res : pd.DataFrame or dict
        - DataFrame → one GSA result table
        - dict      → { group_name : GSEA/GSA dataframe }

    pval_cutoff : float (default=1e-2)
        Minimum significance criterion.

    nes_cutoff : float (default=0)
        Minimum enrichment score threshold.

    N_max_to_show : int (default=30)
        Maximum plotted terms per dataset.

    dpi : int (default=100)
        Plot resolution.

    title, title_pos, title_fs, title_ha
        Figure title formatting options.

    label_fs, tick_fs : int
        Font sizes for label/ticks.

    wspace, hspace : float
        Panel spacing.

    Ax : matplotlib.axes or None
        External axis input for embedding.

    bar_width : float (default=1)
        Bar thickness scaling.

    items_to_plot : list
        Columns to visualize, forwarded to `plot_gsa_bar_()`.

    facecolor, edgecolor : str
        Bar color style.

    ------------------------------------------------------------
    Returns
    -------
    DataFrame or dict
        - If input is DataFrame → returns filtered df
        - If input is dict     → returns {key : filtered_df}

    ------------------------------------------------------------
    Usage
    ------
    🔹 Single GSA result
    >>> df_filtered = plot_gsa_bar(df_kegg, pval_cutoff=5e-3)

    🔹 Multiple GSA results (multi-condition comparison)
    >>> res = plot_gsa_bar(
            {
                "TNBC"  : df_kegg_tnbc,
                "HER2+" : df_kegg_her2,
                "ER+"   : df_kegg_er
            },
            pval_cutoff=1e-3,
            nes_cutoff=1.2
        )

    >>> list(res.keys())
    ['TNBC', 'HER2+', 'ER+']
    """
    
    if isinstance( df_res, pd.DataFrame ):
        df = plot_gsa_bar_( df_res, pval_cutoff = pval_cutoff, 
                            nes_cutoff = nes_cutoff, N_max_to_show = N_max_to_show,
                            title = title, title_pos = title_pos, title_fs = title_fs, title_ha = title_ha, 
                            label_fs = label_fs, tick_fs = tick_fs, wspace=wspace, hspace=hspace, Ax = Ax,
                            bar_width = bar_width, dpi = dpi, items_to_plot = items_to_plot,
                            facecolor = facecolor, edgecolor = edgecolor )
        return df
    elif isinstance( df_res, dict ):
        df_sel = {}
        for key in df_res.keys():        
            if df_res[key].shape[0] > 0:
                df = plot_gsa_bar_( df_res[key], pval_cutoff = pval_cutoff, 
                                    nes_cutoff = nes_cutoff, N_max_to_show = N_max_to_show,
                            title = key, title_pos = title_pos, title_fs = title_fs, title_ha = title_ha, 
                            label_fs = label_fs, tick_fs = tick_fs, wspace=wspace, hspace=hspace, Ax = Ax,
                            bar_width = bar_width, dpi = dpi, items_to_plot = items_to_plot,
                            facecolor = facecolor, edgecolor = edgecolor )
                df_sel[key] = df
        return df_sel
    else:
        return None
                

import matplotlib.pyplot as plt
import matplotlib as mpl

def get_gsa_summary( gsa_res, max_log_p = 10 ):

    """
    ------------------------------------------------------------
    📌 Summarize GSEA/GSA results into pathway × sample matrices
    ------------------------------------------------------------

    This function collects multiple GSEA/GSA result tables and produces
    a unified summary matrix indexed by pathway/gene-set terms.
    Both –log10(P-value) and NES matrices are returned (if NES available).

    Useful for dot-plot visualization and multi-condition comparison.

    Parameters
    ----------
    gsa_res : dict
        Nested result structure:
            { condition_group : { sample : GSEA_dataframe } }
        Each dataframe must contain:
            - '-log(p-val)' (for significance)
            - 'NES' (optional; returned only if present)

    max_log_p : float (default=10)
        Cap applied to P-value significance to avoid extreme scaling.

    ------------------------------------------------------------
    Returns
    -------
    df_qv : pd.DataFrame
        Pathway × sample matrix of -log10(P-value)

    df_es : pd.DataFrame or None
        Pathway × sample NES matrix (None if NES column missing)

    ------------------------------------------------------------
    Usage
    ------
    >>> df_qv, df_es = get_gsa_summary(gsa_res, max_log_p=8)

    >>> df_qv.head()
    >>> df_es.head()   # only if NES present
    """
    
    df_gse_all = {}
    gsa_res_keys = gsa_res.keys()
    for ck in gsa_res_keys:
        df_dct = gsa_res[ck]
        for cs in df_dct.keys():
            if len(gsa_res_keys) == 1:
                case = '%s' % (cs)
            else:
                case = '%s: %s' % (ck, cs)
            df_gse_all[case] = df_dct[cs]

    case_lst = list(df_gse_all.keys())
    pws = []
    for key in df_gse_all.keys():
        df = df_gse_all[key]
        pws = list(set(pws).union(list(df.index.values)))

    pws.sort(reverse = True)

    dfc_qv = pd.DataFrame(0, index = pws, columns = case_lst, dtype = float)
    dfc_es = pd.DataFrame(0, index = pws, columns = case_lst, dtype = float)
    cnt_es = 0

    for case in df_gse_all.keys():

        df = df_gse_all[case]

        col1 = '%s' % case
        col2 = '%s' % case

        dfc_qv.loc[:,col1] = 0
        dfc_es.loc[:,col2] = 0

        b = ~df['-log(p-val)'].isnull()
        dfc_qv.loc[list(df.index.values[b]), col1] = list(df.loc[b, '-log(p-val)'])
        if 'NES' in list(df.columns.values):
            b = ~df['NES'].isnull()
            cnt_es += np.sum(b)
            dfc_es.loc[list(df.index[b]), col2] = list(df.loc[b, 'NES'])

    # display(dfc_qv.head())

    pw_sel = pws

    if cnt_es > 0:
        b = dfc_es.max(axis = 1) > 0
        df_qv = dfc_qv.loc[b,:] 
        df_es = dfc_es.loc[b,:] 
    else:
        df_qv = dfc_qv
        df_es = None

    df_qv = df_qv.clip(upper = max_log_p)
    
    return df_qv, df_es


def plot_gsa_dot( gsa_res, pval_cutoff = 1e-2,
                  title = 'Test', title_fs = 14, 
                  tick_fs = 10, xtick_rot = 90, xtick_ha = 'center',
                  label_fs = 10, legend_fs = 10, swap_ax = True, 
                  figsize = None, dpi = 100, dot_size = 14, 
                  cbar_frac = 0.05, cbar_aspect = 20, cmap = 'Reds' ):

    """
    ------------------------------------------------------------
    📌 Dot-plot visualization of pathway enrichment (GSEA/GSA)
    ------------------------------------------------------------

    Generates a bubble-plot where:
        ● X/Y axis = Samples or Pathways
        ● Dot size = -log10(P-value)
        ● Dot color = NES (or –log10(P) if NES unavailable)

    Automatically merges multi-sample enrichment results
    using `get_gsa_summary()` and visualizes with colorbar + size legend.

    Parameters
    ----------
    gsa_res : dict
        { condition_group : { sample : dataframe } }  
        or { sample : dataframe }  
        Must contain '-log(p-val)' column; NES optional.

    pval_cutoff : float (default=1e-2)
        Significance threshold used for filtering prior to plotting.

    title : str (default='Test')
        Figure title text.

    title_fs, tick_fs, xtick_rot, xtick_ha, label_fs, legend_fs : int/str
        Font and axis tick formatting options.

    swap_ax : bool (default=True)
        If True  → Pathways on X-axis, Samples on Y-axis  
        If False → Axes reversed

    figsize : tuple or None
        Plot size auto-scaled if None.

    dpi : int (default=100)

    dot_size : int (default=14)
        Maximum dot size (scaled relative to –log10(p)).

    cbar_frac, cbar_aspect : float
        Colorbar sizing parameters.

    cmap : str (default='Reds')
        Colormap applied for NES or –logP value gradient.

    ------------------------------------------------------------
    Returns
    -------
    None  
        Displays dot-plot figure.

    ------------------------------------------------------------
    Usage
    ------
    >>> plot_gsa_dot(gsa_res, title="TNBC vs HER2+ vs ER+ — GSEA")

    # Reverse axes (sample × pathways)
    >>> plot_gsa_dot(gsa_res, swap_ax=False, cmap='Blues')
    """
    
    neg_log_p_cutoff = -np.log10(pval_cutoff)
    if isinstance( gsa_res, dict ):
        key_t = list(gsa_res.keys())[0]
        if isinstance( gsa_res[key_t], pd.DataFrame ):
            gsa_res_t = {'AAA': filter_gsa_result( gsa_res, neg_log_p_cutoff )}
        elif isinstance( gsa_res[key_t], dict ):
            gsa_res_t = {}
            for key in gsa_res.keys():
                gsa_res_t[key] = filter_gsa_result( gsa_res[key], neg_log_p_cutoff )
        else:
            print('ERROR: The input seems not suitably formatted. ')
            return None
    else:
        print('ERROR: The input seems not suitably formatted. ')
        return None
        
    df_qv, df_es = get_gsa_summary(gsa_res_t, max_log_p = 10)
    
    df1 = df_qv
    df2 = df_es
    alabel = 'Cases'
    n = df1.shape[0]

    mx_pnt_size = dot_size
    mx_pv = np.ceil(df1.max().max())
    ssf = mx_pnt_size/mx_pv
    
    mn, mx = 0, 1
    if df2 is not None:
        mn, mx = np.floor(df2.min().min()), np.ceil(df2.max().max())
        cbar_title = 'NES'
    else:
        mn, mx = np.floor(df1.min().min()), np.ceil(df1.max().max())
        cbar_title = '-log10(P)'
        
    norm = mpl.colors.Normalize(vmin=mn, vmax=mx)

    # plt.figure(figsize = (2+1, 2*df1.shape[0]/df1.shape[1]))
    if figsize is None:
        sf = 1/6
        if swap_ax:
            xs = (df1.shape[0] + 2) 
            ys = (df1.shape[1] + 2)
        else:
            xs = (df1.shape[1] + 2) 
            ys = (df1.shape[0] + 2)
            
        figsize = (sf*xs, sf*ys)
        fig, ax = plt.subplots(figsize = figsize, dpi = dpi) 
    else:
        fig, ax = plt.subplots(figsize = figsize, dpi = dpi) # figsize = (sf*xs, sf*ys)) 
    # ax = plt.figure(figsize = figsize)

    x = []
    y = []
    ss = []
    cc = []
    for j, c in enumerate(list(df1.columns.values)):
        if swap_ax:
            y = y + [j]*n
            x = x + list(np.arange(n))
        else:
            x = x + [j]*n
            y = y + list(np.arange(n))
        ss = ss + list(df1[c]*ssf)
        if df2 is None:
            cc = cc + list(df1[c])
        else:
            cc = cc + list(df2[c])

    p = ax.scatter( x, y, s = ss, c = cc, cmap = cmap )

    # plt.colorbar(p,cax=ax)
    ax.grid('off')  
    ax.set_title(title, fontsize = title_fs)

    # Set number of ticks for x-axis
    if swap_ax:
        plt.ylabel(alabel, fontsize = label_fs)
        ix, iy, yt_label, xt_label, fr = 0, 1, df1.columns.values, df1.index.values, 1 
    else:
        plt.xlabel(alabel, fontsize = label_fs)
        ix, iy, yt_label, xt_label, fr = 1, 0, df1.index.values, df1.columns.values, 0.1

    plt.ylim([-1, df1.shape[iy]])
    plt.xlim([-1, df1.shape[ix]])

    x = np.arange(df1.shape[ix])
    ax.set_xticks(x)
    # Set ticks labels for x-axis
    x_ticks_labels = list(xt_label)
    ax.set_xticklabels(x_ticks_labels, rotation=xtick_rot, ha = xtick_ha, fontsize=tick_fs)

    # Set number of ticks for x-axis
    y = np.arange(df1.shape[iy])
    ax.set_yticks(y)
    # Set ticks labels for x-axis
    y_ticks_labels = list(yt_label)
    a = ax.set_yticklabels(y_ticks_labels, rotation=0, fontsize=tick_fs)

    # Adding the colorbar
    cmap = p.cmap
    if swap_ax:
        lgap = 0.01
        frac = cbar_frac*0.05*figsize[0]/figsize[1]
        # cbaxes = fig.add_axes([0.91, 0.6, 0.1*df1.shape[1]/df1.shape[0], 0.25]) 
        cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),ax=ax, pad = frac*2, #cbar_gap,
                            fraction = frac, aspect = cbar_aspect, # shrink = cbar_shrink,
                            location = 'top', anchor = (1,1)) #, cax = cbaxes)
            
        # if df2 is not None:
        cbar.set_label(cbar_title, fontsize = legend_fs)
        for t in cbar.ax.get_xticklabels():
            t.set_fontsize(tick_fs)
    else:
        lgap = 0.02 
        frac = cbar_frac*0.05*figsize[1]/figsize[0]
        r = df1.shape[1]/df1.shape[0]
        # cbaxes = fig.add_axes([1, 1, 0.1*(1-df1.shape[1]/30), 0.1]) 
        cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),ax=ax, pad = frac*2, #cbar_gap, 
                            fraction = frac, aspect = cbar_aspect, 
                            location = 'right', anchor = (0,0)) #, cax = cbaxes)
            
        # if df2 is not None:
        cbar.set_label(cbar_title, fontsize = legend_fs)
        for t in cbar.ax.get_yticklabels():
            t.set_fontsize(tick_fs)

    #'''
    if swap_ax:
        nn = 5 # list(np.arange(1,mx_pv,2)) 
        kw = dict(prop="sizes", num=nn, fmt="{x:1.0f}", func=lambda s: s/ssf, color = 'grey')
        legend = ax.legend(*p.legend_elements(**kw), title = '-log(P)',
                       fontsize = legend_fs, title_fontsize=legend_fs,
                       loc = 'upper left', bbox_to_anchor = (1+lgap, 1) )
    else:
        nn = 5 # int(mx_pv)
        kw = dict(prop="sizes", num=nn, fmt="{x:1.0f}", func=lambda s: s/ssf, color = 'grey')
        legend = ax.legend(*p.legend_elements(**kw), title = '-log(P)',
                       fontsize = legend_fs, title_fontsize=legend_fs,
                       loc = 'upper left', bbox_to_anchor = (1+lgap, 1) )
    #'''
    plt.show()
    return


def plot_gsa_all( gsa_res, 
                  title = 'Test', title_fs = 14, 
                  tick_fs = 10, xtick_rot = 90, xtick_ha = 'center',
                  label_fs = 10, legend_fs = 10, swap_ax = True, 
                  figsize = None, dot_size = 14, cbar_frac = 0.2, cbar_aspect = 20,
                  cmap = 'Reds' ):

    """
    ------------------------------------------------------------
    📌 Convenient wrapper to show full GSA/GSEA dot-plot summary
    ------------------------------------------------------------

    Thin interface over `plot_gsa_dot()` for rapid visualization.
    Ideal for inspecting overall enrichment landscape across groups.

    Parameters
    ----------
    gsa_res : dict
        GSEA/GSA results in input format accepted by `plot_gsa_dot()`.

    title, title_fs : str/int
        Figure title text + font size.

    tick_fs, xtick_rot, xtick_ha : int/float/str
        Tick labeling configuration.

    label_fs, legend_fs : int
        Axis label + legend text size.

    swap_ax : bool (default=True)
        If True  → pathways on X-axis  
        If False → samples on X-axis

    figsize : tuple or None (auto-sized)
    dot_size : int (default=14)
    cbar_frac : float (default=0.2)
    cbar_aspect : float (default=20)
    cmap : str (default='Reds')

    ------------------------------------------------------------
    Returns
    -------
    None  
        Displays the full dot-plot.

    ------------------------------------------------------------
    Usage
    ------
    >>> plot_gsa_all(gsa_res, title="Pathway activity landscape")

    # Custom size + colormap
    >>> plot_gsa_all(gsa_res, figsize=(8,6), cmap='coolwarm')
    """
    
    plot_gsa_dot( gsa_res, 
                  title, title_fs, 
                  tick_fs, xtick_rot, xtick_ha,
                  label_fs, legend_fs, swap_ax, 
                  figsize, dot_size, cbar_frac, cbar_aspect, cmap )    
    return


###############################
###############################
### CNV related UI function ###

def find_chrm_of_genomic_spots( adata_s, spots ):

    spot_lst = []
    if isinstance(spots, int):
        spot_lst = [spots]
    elif isinstance(spots, list) | isinstance(spots, np.ndarray):
        spot_lst = list(spots)

    genes = {}
    for s in spot_lst:
        b = adata_s.var['spot_no'].isin([s])
        genes[s] = adata_s.var['chr'][b].value_counts().index.values[0]

    return genes


def find_genes_in_genomic_spots( adata_s, spots, spot_ext = 0 ):

    """
    ------------------------------------------------------------
    📌 Retrieve genes located within specified genomic CNV spots
    ------------------------------------------------------------

    Given a CNV-annotated AnnData object, this function extracts genes
    corresponding to selected genomic "spots" (CNV windows).  
    Supports ± extension (`spot_ext`) around each target spot index.

    Useful for identifying regional gene amplifications/deletions.

    Parameters
    ----------
    adata_s : AnnData
        Single-cell data containing inferred CNV profiles.
        Required:
            - adata_s.obsm['X_cnv']   : CNV matrix (#cells × #spots)
            - adata_s.var['spot_no']  : Genomic mapping of genes → CNV spot index

    spots : int, list, or ndarray
        Target CNV spot indices to retrieve genes from.

    spot_ext : int (default=0)
        Genomic window extension (spot ± spot_ext included).
        Example: spot=12, spot_ext=2 → includes [10,11,12,13,14]

    ------------------------------------------------------------
    Returns
    -------
    genes : dict
        { spot_index : [ list_of_genes ] }

    ------------------------------------------------------------
    Usage
    ------
    >>> genes = find_genes_in_genomic_spots(adata_s, spots=[10,14], spot_ext=1)

    >>> genes[10][:10]   # first 10 genes near CNV hotspot
    ['ERBB2','GRB7','PGAP3',...]
    """
    
    spot_lst = []
    if isinstance(spots, int):
        spot_lst = [spots]
    elif isinstance(spots, list) | isinstance(spots, np.ndarray):
        spot_lst = list(spots)

    s_max = adata_s.obsm['X_cnv'].shape[1]
    genes = {}
    for s in spot_lst:
        slst = []
        for i in np.arange(-spot_ext, spot_ext+1, 1 ):
            si = s + i
            if si >= 0:
                slst.append(si)
            if si <= (s_max-1):
                slst.append(si)
        b = adata_s.var['spot_no'].isin(slst)
        genes[s] = adata_s.var.index.values[b]

    return genes


def find_genomic_spots_of_cnv_peaks( adata_s, group_col = None, width = 5, std_scale = 1, q = None, spot_ext = 1 ): #

    """
    ------------------------------------------------------------
    📌 Identify CNV peak regions & extract genes in hotspot loci
    ------------------------------------------------------------

    Detects CNV-amplified genomic hotspots from AnnData CNV profile (X_cnv)
    using peak-detection (`scipy.signal.find_peaks`). 
    Genes overlapping with discovered peak regions are then retrieved using
    `find_genes_in_genomic_spots()`.

    Supports grouped analysis (per cluster/sample/subtype) via obs column.

    Parameters
    ----------
    adata_s : AnnData
        Single-cell object with CNV matrix:
            - adata_s.obsm['X_cnv'] (cells × genomic_spots)
            - adata_s.var['spot_no'] must map each gene to genomic spot index

    group_col : str or None (default=None)
        If None   → detect CNV peaks globally
        If column exists in adata.obs → peak detection performed per group

    width : int (default=5)
        Minimum peak width passed to `find_peaks()`.

    std_scale : float (default=1)
        Peaks must exceed (mean + std×std_scale) or quantile threshold.

    q : float or None
        If provided, use quantile(q) instead of mean to determine peak baseline.

    spot_ext : int (default=1)
        Gene lookup extension (spot±spot_ext) around each peak.

    ------------------------------------------------------------
    Returns
    -------
    dict
        If group_col is None:
            { peak_index : [genes] }
        If group_col exists:
            { group : { peak_index : [genes] } }

    ------------------------------------------------------------
    Usage
    ------
    🔹 Global CNV-hotspot gene extraction
    >>> peaks = find_genomic_spots_of_cnv_peaks(adata_s, spot_ext=2)
    >>> peaks[12][:15]   # genes around hotspot index 12

    🔹 Per cluster / subtype CNV hotspot discovery
    >>> peaks_by_group = find_genomic_spots_of_cnv_peaks(
            adata_s, group_col='celltype', width=6, std_scale=1.2
        )
    >>> peaks_by_group['Tumor']['chr17p'][:10]
    """
    
    if group_col is None:
        ## Use q-quantile CNV to find peaks
        if q is None:
            mean_cnv = pd.DataFrame( adata_s.obsm['X_cnv'].todense() ).mean() # quantile(q)
        else:
            mean_cnv = pd.DataFrame( adata_s.obsm['X_cnv'].todense() ).quantile(q)
            
        std = mean_cnv.std()*std_scale
        peaks, peak_info = signal.find_peaks(mean_cnv, height = std, width = width)

        genes_in_gspots = find_genes_in_genomic_spots( adata_s, peaks, spot_ext )
        return genes_in_gspots

    elif group_col in list(adata_s.obs.columns.values):

        genes = {}
        lst = list(adata_s.obs[group_col].unique())
        for g in lst:
            b = adata_s.obs[group_col] == g
            adata_ss = adata_s[b,:]
            
            ## Use q-quantile CNV to find peaks
            if q is None:
                mean_cnv = pd.DataFrame( adata_ss.obsm['X_cnv'].todense() ).mean() # quantile(q)
            else:
                mean_cnv = pd.DataFrame( adata_ss.obsm['X_cnv'].todense() ).quantile(q)
            std = mean_cnv.std()*std_scale
            peaks, peak_info = signal.find_peaks(mean_cnv, height = std, width = width)

            genes_in_gspots = find_genes_in_genomic_spots( adata_ss, peaks, spot_ext )
            genes[g] = genes_in_gspots
            
        return genes
    else:
        return None

    return 


def get_band_from_a_spot( spot, adata, g2cgloc ):

    gene_first = None
    gene_last = None
    dct = find_genes_in_genomic_spots(adata, list(spot), spot_ext = 0)
    # dct = spots_dct
    

    if g2cgloc is not None:
        g2cgloc_keys = list(g2cgloc.keys())
    else:
        g2cgloc_keys = []
        for k in dct.keys():
            glst = dct[k]
            g2cgloc_keys = g2cgloc_keys + glst
    
    b = False
    genes_lst = []
    for k in dct.keys():
        glst = dct[k]
        for g in glst:
            if g in list(g2cgloc_keys):
                if not b:
                    gene_first = g
                    b = True
                if g not in genes_lst:
                    genes_lst.append(g)
                # break
        # if b: break

    if gene_first is not None:
        b = False
        for k in reversed( list(dct.keys()) ):
            glst = dct[k]
            for g in reversed(glst):
                if g in list(g2cgloc_keys):
                    gene_last = g
                    b = True
                    break
            if b: break

    if (gene_first is not None) & (g2cgloc is not None):
        s = '%s:%s' % (g2cgloc[gene_first], g2cgloc[gene_last])
        band_lst = []
        for g in genes_lst:
            bnd = g2cgloc[g]
            if bnd not in band_lst:
                band_lst.append(bnd)
    else:
        s = 'Unknown band'
        band_lst = []

    return s, np.array(genes_lst), np.array(band_lst)
    

def get_band_from_spot_list( spot_llst, adata, g2cgloc ):

    slst = []
    glst = []
    blst = []
    for lst in spot_llst:
        s, genes_lst, band_lst = get_band_from_a_spot( lst, adata, g2cgloc )
        slst.append(s)
        glst.append(genes_lst)
        blst.append(band_lst)

    return slst, glst, blst


def get_mean_and_std_from_gmm_250318( gmm ):
    
    mt = gmm.means_.max(axis = 0)
    idx_t = gmm.means_.argmax(axis = 0)
    vt = gmm.covariances_[idx_t, range(len(mt))]
    st = np.sqrt(vt) #/len(idx_t))

    return mt, st

def break_regions( loci, n_ext, lmax ):
    
    lst = []
    s = [loci[0]]
    if n_ext > 0:
        for j in range(n_ext):
            if s[0]-1 < 0: break
            else:
                s = [s[0]-1] + s
            
    for i in loci[1:]:
        if i == (s[-1]+1):
            s = s + [i]
        else:
            if n_ext > 0:
                for j in range(n_ext):
                    if s[-1]+1 >= lmax: break
                    else:
                        s = s + [s[-1]+1]
            lst.append(np.array(s))
            s = [i]
            if n_ext > 0:
                for j in range(n_ext):
                    if s[0]-1 < 0: break
                    else:
                        s = [s[0]-1] + s
            
    if len(s) > 0:
        if n_ext > 0:
            for j in range(n_ext):
                if s[-1]+1 >= lmax: break
                else:
                    s = s + [s[-1]+1]
        lst.append(np.array(s))
    return lst


def get_mean_and_std_from_gmm( gmm ):
    
    mt = gmm.means_.max(axis = 0)
    idx_t = gmm.means_.argmax(axis = 0)
    vt = gmm.covariances_[idx_t, range(len(mt))]
    st = np.sqrt(vt) #/len(idx_t))
    wt = gmm.weights_[idx_t]

    return mt, st, wt


def get_cnv_gain_dec(mt, st, mn, sn, std_scale, t_gain_min):

    z = (mt - mn)/(st + sn)    
    # bx = ((mt - st*std_scale) > (mn + sn*std_scale)) & (mt >= t_gain_min) 
    bx = (z >= std_scale) & (mt >= t_gain_min)
    return bx


def check_cnv_hit( cnv_spot_lst, adata, gmm_ncomp_t = 4, gmm_ncomp_n = 2, sample_col = 'sample',
                   cov_type = 'diag', reg_covar = 1e-3, std_scale = 1, t_gain_min = 0.05, 
                   n_cells_min = 50, n_ext = 1, med_filter_len = 5 ):

    """
    ------------------------------------------------------------
    📌 Evaluate **sample-wise CNV gain support** for predefined regions
    ------------------------------------------------------------

    For each sample, this function:
      1) Fits a GMM to diploid-like cells (reference CNV baseline)
      2) Fits a GMM to aneuploid tumor cells of that sample
      3) Computes a z-like gain score per genomic spot
      4) Aggregates gain scores over user-defined CNV regions

    The output is a matrix (samples × regions) of average gain statistics.

    Parameters
    ----------
    cnv_spot_lst : list or dict
        CNV regions to test.
        - If list  → [ array_of_spot_indices, ... ]
        - If dict  → { region_name : array_of_spot_indices }

    adata : AnnData
        CNV-annotated data with:
            - adata.obsm['X_cnv']          : CNV matrix
            - adata.obs['celltype_for_cci']
            - adata.obs['tumor_origin_ind']
            - adata.obs[sample_col]

    gmm_ncomp_t : int (default=4)
        Number of mixture components for tumor/aneuploid GMM per sample.

    gmm_ncomp_n : int (default=2)
        Number of mixture components for normal/diploid GMM.

    sample_col : str (default='sample')
        Column in adata.obs indicating sample ID.

    cov_type : str (default='diag')
        Covariance type for sklearn.mixture.GaussianMixture.

    reg_covar : float (default=1e-3)
        Regularization added to the diagonal of covariance matrices.

    std_scale : float (default=1)
        Threshold in z-like scale for CNV gain detection.

    t_gain_min : float (default=0.05)
        Minimum CNV amplitude required to be considered a gain.

    n_cells_min : int (default=50)
        Minimum number of aneuploid cells per sample required to test that sample.

    n_ext : int (default=1)
        Extension (in spot index) added when grouping CNV spots into regions.

    med_filter_len : int (default=5)
        Median filter kernel size applied to the gain decision vector.

    ------------------------------------------------------------
    Returns
    -------
    df : pd.DataFrame
        Sample × region matrix of CNV gain statistics (average z-like scores).
        Columns are:
            - region names (dict input) or
            - "start-end" strings (list input)

    ------------------------------------------------------------
    Usage
    ------
    >>> cnv_regions = [np.array([120,121,122]), np.array([340,341,342])]
    >>> df_hit = check_cnv_hit(cnv_regions, adata, std_scale=1.2, t_gain_min=0.08)

    >>> df_hit.head()
    """
    
    b = adata.obs['tumor_origin_ind']
    pcnt = adata.obs.loc[b, 'celltype_major'].value_counts()
    target = pcnt.index.values[0]
    if target == 'unassigned':
        target = pcnt.index.values[1]
    
    X_cnv = np.array(adata.obsm['X_cnv'].todense())

    bn = (adata.obs['celltype_for_cci'] == 'Diploid %s' % target) | (adata.obs['celltype_for_cci'] == target)
    gmm_normal = mixture.GaussianMixture(n_components = int(gmm_ncomp_n), covariance_type = cov_type, 
                                        random_state = 0, reg_covar = reg_covar)
    gmm_normal.fit( X_cnv[bn,:] )
    mn, sn, wn = get_mean_and_std_from_gmm( gmm_normal )

    slst = list( adata.obs[sample_col].unique() )

    if isinstance( cnv_spot_lst, list ):
        s_llst = cnv_spot_lst
        df = pd.DataFrame( columns = range(len(s_llst)), dtype = int )
    else:
        s_llst = list(cnv_spot_lst.values())
        nlst = list(cnv_spot_lst.keys())
        df = pd.DataFrame( columns = nlst, dtype = int )
    
    spot_lst_all = []
    for s in slst:
    
        bt = (adata.obs['celltype_for_cci'] == 'Aneuploid %s' % target) & (adata.obs[sample_col] == s)
        if np.sum(bt) >= n_cells_min:
            ## intentionally used 'gmm_ncomp_n' for aneuploid cells
            gmm_tumor_sample = mixture.GaussianMixture(n_components = int(gmm_ncomp_t), 
                                                covariance_type = cov_type, 
                                                random_state = 0, reg_covar = reg_covar)
            gmm_tumor_sample.fit( X_cnv[bt,:] )
            mta, sta, wta = get_mean_and_std_from_gmm( gmm_tumor_sample )

            z = (mta - mn)/(sta + sn)            
            # b = ((mta - sta*std_scale) > (mn + sn*std_scale)) & (mta >= t_gain_min) # (z > 0.5) & (mt >= 0.08)
            b = get_cnv_gain_dec(mta, sta, mn, sn, std_scale, t_gain_min)
            if med_filter_len >1:
                b = signal.medfilt(b.astype(int), med_filter_len).astype(bool)
            
            if np.sum(b) > 0:
                llst = break_regions( list(np.arange(len(mta))[b]), n_ext = n_ext, lmax = X_cnv.shape[1] )
    
                icnt = []
                z_ave = []
                for j, w in enumerate(s_llst):
                    cnt = 0
                    zs = 0
                    for t in llst:
                        c = list(set(list(w)).intersection(list(t)))
                        if len(c) > 0:
                            cnt = 1
                            zst = np.mean(z[list(w)])
                            if zst > zs:
                                zs = zst
                    icnt.append(cnt)
                    z_ave.append(zs)
    
                df.loc[s,:] = z_ave # icnt
            else:
                df.loc[s,:] = 0

    if isinstance( cnv_spot_lst, list ):
        rngs = []
        for lst in s_llst:
            s = '%i-%i' % (lst[0], lst[-1])
            rngs.append(s)

        idx = df.columns.values
        rend = dict(zip(idx, rngs))
        df.rename( columns = rend, inplace = True)

    return df # .astype(int)


def find_signif_CNV_gain_regions_( adata, # target, 
                                  gmm_ncomp_t = 4, gmm_ncomp_n = 2, gmm_ncomp_t_per_sample = 2, 
                                  cov_type = 'diag', reg_covar = 1e-3,
                                  std_scale = 1, t_gain_min = 0.05, sample_col = 'sample', cond_col = 'condition',
                                  n_cells_min = 50, n_samples_min = 2, n_ext = 2, med_filter_len = 5, N_spots_min = 10 ):

    ## adata is assumed to contain only tumor cells
    if n_samples_min < 1:
        b1 = (adata.obs['ploidy_dec'] == 'Aneuploid') 
        pcnt = adata[b1,:].obs[sample_col].value_counts()
        bx = pcnt >= n_cells_min
        ilst = list( pcnt.index.values[bx] )
        b2 = adata.obs[sample_col].isin( ilst )
        b = b1 & b2
        cond_lst = list( adata[b,:].obs[cond_col].unique() )
        
        ns_mins = {}
        for c in cond_lst:
            b = adata.obs[cond_col] == c
            slst_t = list( adata.obs.loc[b, sample_col].unique() )
            ns_mins[c] = len(slst_t)

        n_samples_min = max( 2, np.min(list(ns_mins.values()))*n_samples_min )
        # print(ns_mins, n_samples_min)
                
    b = adata.obs['tumor_origin_ind']
    pcnt = adata.obs.loc[b, 'celltype_major'].value_counts()
    target = pcnt.index.values[0]
    if target == 'unassigned':
        target = pcnt.index.values[1]
    
    X_cnv = np.array(adata.obsm['X_cnv'].todense())
    b = adata.obs['ploidy_dec'] == 'Aneuploid'
    
    bt = (adata.obs['celltype_for_cci'] == 'Aneuploid %s' % target)
    gmm_tumor = mixture.GaussianMixture(n_components = int(gmm_ncomp_t), covariance_type = cov_type, 
                                        random_state = 0, reg_covar = reg_covar)
    gmm_tumor.fit( X_cnv[bt,:] )
    
    bn = (adata.obs['celltype_for_cci'] == 'Diploid %s' % target) | (adata.obs['celltype_for_cci'] == target)
    gmm_normal = mixture.GaussianMixture(n_components = int(gmm_ncomp_n), covariance_type = cov_type, 
                                        random_state = 0, reg_covar = reg_covar)
    gmm_normal.fit( X_cnv[bn,:] )

    n_t = np.sum(bt)
    n_n = np.sum(bn)
    
    mt, st, wt = get_mean_and_std_from_gmm( gmm_tumor )
    mn, sn, wn = get_mean_and_std_from_gmm( gmm_normal )
    
    # z = (mt - mn)/(st + sn)    
    # bx = ((mt - st*std_scale) > (mn + sn*std_scale)) & (mt >= t_gain_min) 
    #'''
    bx = get_cnv_gain_dec(mt, st, mn, sn, std_scale, t_gain_min)
    bx = signal.medfilt(bx.astype(int), med_filter_len).astype(bool)
    
    spot_lst = list(np.arange(len(mt))[bx])
    #'''

    llst = {}
    pcnt = None
    if (sample_col is not None) & (sample_col in list(adata.obs.columns.values)):
        slst = list( adata.obs[sample_col].unique() )
        spot_lst_all = []
        df_z = pd.DataFrame(index = slst, columns = range(X_cnv.shape[1]))
        df_z.loc[:,:] = 0
        for s in slst:
        
            bt = (adata.obs['celltype_for_cci'] == 'Aneuploid %s' % target) & (adata.obs[sample_col] == s)
            if np.sum(bt) >= n_cells_min:
                ## intentionally used 'gmm_ncomp_n' for aneuploid cells
                gmm_tumor_sample = mixture.GaussianMixture(n_components = int(gmm_ncomp_t_per_sample), 
                                                    covariance_type = cov_type, 
                                                    random_state = 0, reg_covar = reg_covar)
                gmm_tumor_sample.fit( X_cnv[bt,:] )
                mta, sta, wta = get_mean_and_std_from_gmm( gmm_tumor_sample )
                
                z = (mta - mn)/(sta + sn)            
                # b = ((mta - sta*std_scale) > (mn + sn*std_scale)) & (mta >= t_gain_min) # (z > 0.5) & (mt >= 0.08)
                b = get_cnv_gain_dec(mta, sta, mn, sn, std_scale, t_gain_min)
                if med_filter_len > 1:
                    b = signal.medfilt(b.astype(int), med_filter_len).astype(bool)

                df_z.loc[s,:] = list(z*b)
                spot_lst_all = spot_lst_all + list(np.arange(len(mta))[b])
    
        spot_lst_all = pd.Series(spot_lst_all, name = 'spot')
        pcnt = spot_lst_all.value_counts()
        # b = pcnt >= n_samples_min
        # spot_lst_c = list(pcnt.index.values[b])

        #'''
        n_samples_min_org = n_samples_min
        nM = 10
        for i in range(nM):
            n_samples_min = n_samples_min_org*(nM - i)/nM
            bz = (df_z > 0).sum() >= n_samples_min
            spot_lst_c = list(df_z.columns.values[bz])
        
            spot_lst = spot_lst_c # list(set(spot_lst).intersection(spot_lst_c))
            spot_lst.sort()
    
            if len(spot_lst) > 0:
                bx[:] = False
                bx[spot_lst] = True
                if med_filter_len > 1:
                    bx = signal.medfilt(bx.astype(int), med_filter_len).astype(bool)
                spot_lst = list(np.arange(len(mt))[bx])
                if len(spot_lst) > 0:
                    llst = break_regions( spot_lst, n_ext = n_ext, lmax = X_cnv.shape[1] )
                    
            if len(llst) >= N_spots_min:
                break
            n_samples_min = max(2, n_samples_min)            

        print('INFO: n_samples_min: %i -> %i ' % (n_samples_min_org, n_samples_min))
            
    # if ('gene_to_band_map' in list(adata.uns.keys())) & (llst is not None):
    if (llst is not None):
        # g2cgloc = adata.uns['gene_to_band_map']
        b = ~adata.var['cytogenetic_band'].isnull()
        glst = list(adata.var.index.values[b])
        blst = list(adata.var['cytogenetic_band'].values[b])
        g2cgloc = dict(zip(glst, blst))

        bname_lst, genes_llst, band_llst = get_band_from_spot_list( llst, adata, g2cgloc )
        
        spot_llst = dict(zip(bname_lst, llst))
        band_llst = dict(zip(bname_lst, band_llst))
        gene_llst = dict(zip(bname_lst, genes_llst))
    else:
        spot_llst = llst
        band_llst = None
        gene_llst = None
        

    dct_r = {}
    dct_r['genes'] = gene_llst
    dct_r['bands'] = band_llst
    dct_r['spots'] = spot_llst
    dct_r['gmm (Aneuploid)'] = gmm_tumor
    dct_r['gmm (Diploid)'] = gmm_normal
    dct_r['N_cells_used'] = {'Aneuploid': n_t, 'Diploid': n_n}
    dct_r['dfZ'] = df_z

    if pcnt is not None:
        cnt = np.zeros([len(llst)])
        for s in spot_lst:
            for j, lst in enumerate(llst):
                if (s in lst) & (s in list(pcnt.index.values)):
                    cnt[j] += pcnt[s]
                    
        for j, lst in enumerate(llst):
            cnt[j] = cnt[j]/len(lst)

        # if 'gene_to_band_map' in list(adata.uns.keys()):
        if (llst is not None):
            dct_r['sample_count'] = dict(zip(bname_lst, cnt.round(2)))
        else:
            dct_r['sample_count'] = cnt.round(2)

    return dct_r

def find_signif_CNV_gain_regions( adata_in, groupby = 'sample_ext_for_deg', 
                                  N_cells_min = 50, N_cells_max = 0.5,
                                  gmm_ncomp_t = 3, gmm_ncomp_n = 1, gmm_ncomp_t_per_sample = 2, 
                                  cov_type = 'diag', reg_covar = 1e-3,
                                  std_scale = 1, t_gain_min = 0.05, sample_col = 'sample',
                                  n_samples_min = 0.5, n_ext = 2, med_filter_len = 3, N_spots_min = 8 ):

    """
    ------------------------------------------------------------
    📌 Discover **recurrent CNV gain regions** and quantify sample-level support
    ------------------------------------------------------------

    High-level wrapper that:
      1) Filters and (optionally) downsamples cells by a grouping column
      2) Calls `find_signif_CNV_gain_regions_` to:
           - Fit GMMs for aneuploid vs diploid cells
           - Detect significantly gained CNV spots
           - Merge them into contiguous CNV regions
           - Map regions to cytobands & genes
      3) Uses `check_cnv_hit` to compute per-sample gain scores
         for each detected CNV region.

    Parameters
    ----------
    adata_in : AnnData
        Input AnnData containing tumor + normal cells with:
            - obsm['X_cnv']
            - obs['ploidy_dec'], obs['celltype_for_cci'],
            - obs['tumor_origin_ind'], obs[groupby], obs[sample_col],
            - var['cytogenetic_band'] (for band mapping)

    groupby : str (default='sample_ext_for_deg')
        Column in adata.obs used to:
            - count cells per group
            - optionally rebalance by subsampling

    N_cells_min : int or float (default=50)
        Minimum number of cells per group:
            - If int   → absolute cell count threshold
            - If float (0 < x < 1) → fraction of N_cells_max

    N_cells_max : int or float (default=0.5)
        Maximum cells per group:
            - If int   → hard cap per group
            - If float (0 < x < 1) → quantile of group sizes

    gmm_ncomp_t, gmm_ncomp_n, gmm_ncomp_t_per_sample : int
        GMM mixture components for tumor (global), normal, tumor-per-sample.

    cov_type : str (default='diag')
        Covariance type for GMMs.

    reg_covar : float (default=1e-3)
        Regularization term for GMM covariance.

    std_scale : float (default=1)
        Z-like threshold scale for CNV gain calling.

    t_gain_min : float (default=0.05)
        Minimum gain amplitude threshold.

    sample_col : str (default='sample')
        Sample ID column used downstream.

    n_samples_min : int or float (default=0.5)
        Minimal number (or fraction) of samples supporting a spot to keep it.

    n_ext : int (default=2)
        Extension size when merging adjacent CNV spots into regions.

    med_filter_len : int (default=3)
        Median filter kernel size for smoothing gain calls.

    N_spots_min : int (default=8)
        Minimum number of CNV regions required (used in internal threshold search).

    ------------------------------------------------------------
    Returns
    -------
    results : dict
        {
          'genes'          : { band_name : np.ndarray of genes },
          'bands'          : { band_name : np.ndarray of cytobands },
          'spots'          : { band_name : np.ndarray of spot indices },
          'gmm (Aneuploid)': fitted tumor GMM,
          'gmm (Diploid)'  : fitted normal GMM,
          'N_cells_used'   : {'Aneuploid': int, 'Diploid': int},
          'dfZ'            : per-sample z-score matrix (samples × spots),
          'sample_count'   : per-region supporting-sample statistic (optional),
          'cnv_peaks_pos'  : DataFrame of region-level gain scores (from check_cnv_hit)
        }

    ------------------------------------------------------------
    Usage
    ------
    >>> res = find_signif_CNV_gain_regions(
            adata_in,
            groupby='sample_ext_for_deg',
            N_cells_min=100,
            n_samples_min=0.6
        )

    >>> res['spots'].keys()      # cytoband / region labels
    >>> res['cnv_peaks_pos'].head()
    """
    
    if groupby not in list( adata_in.obs.columns.values ):
        print('ERROR: %s not in the obs.columns. ' % groupby )
        return None
    else:
        pcnt = adata_in.obs[groupby].value_counts()
        if (N_cells_max > 0) & (N_cells_max < 1):
            N_cells_max = int(pcnt.quantile(N_cells_max))
            if (N_cells_min > 0) & (N_cells_min < 1): 
                N_cells_min = int(N_cells_max*N_cells_min)
            print('N_cells_max: %i, %i (%i, %i) ' % (N_cells_max, N_cells_min, pcnt[0], pcnt[-1]))
            
        bp = pcnt >= N_cells_min
        b = adata_in.obs[groupby].isin(list(pcnt.index.values[bp]))
        adata = adata_in[b,:].copy()
    
        if N_cells_max > 0:
            ## Resample cells to balance cell counts across samples 
            slst = adata.obs[groupby].unique()
            idx_all = adata.obs.index.values
            idx_sel = []
            for s in slst:
                b = adata.obs[groupby] == s
                
                if np.sum(b) <= N_cells_max:
                    idx_sel = idx_sel + list(idx_all[b])
                else:
                    idx_sel = idx_sel + random.sample(list(idx_all[b]), N_cells_max)
            
            adata = adata[idx_sel,:]

    results = find_signif_CNV_gain_regions_( adata, 
                                             gmm_ncomp_t = gmm_ncomp_t, gmm_ncomp_n = gmm_ncomp_n, 
                                             gmm_ncomp_t_per_sample = gmm_ncomp_t_per_sample,
                                             cov_type = cov_type, reg_covar = reg_covar,
                                             std_scale = std_scale, t_gain_min = t_gain_min, sample_col = sample_col,
                                             n_cells_min = N_cells_min, n_samples_min = n_samples_min, 
                                             n_ext = n_ext, med_filter_len = med_filter_len, N_spots_min = N_spots_min )

    df = check_cnv_hit( results['spots'], adata, 
                        gmm_ncomp_t = gmm_ncomp_t, gmm_ncomp_n = gmm_ncomp_n, 
                        sample_col = sample_col, std_scale = std_scale, t_gain_min = t_gain_min, 
                        n_cells_min = N_cells_min, med_filter_len = med_filter_len )
    results['cnv_peaks_pos'] = df
    
    return results
        


def get_col_colors( n, cmap_name = 'tab10'):
    
    cmap = plt.cm.get_cmap(cmap_name, n)
    clrs = [mpl.colors.to_hex(cmap(i)) for i in range(n)]
    return clrs


def plot_cnv_stat( adata, cna_info, rgn, # x_lower, x_upper, gmm_tumor, gmm_normal,
                   title_fs = 12, label_fs = 11, legend_fs = 9,
                   tick_fs = 9, xtick_rot = -90, xtick_ha = 'center', 
                   std_scale = 1, figsize = (8,3), ax = None, cmap = 'tab10', 
                   grid = True, text_pos_adj = 0.6, rng_ext = 12, 
                   known_cna_markers = [], title = None ):

    """
    ------------------------------------------------------------
    📌 Visualize CNV profiles around a **significant gain region**
    ------------------------------------------------------------

    Plots mean CNV profiles for aneuploid vs diploid cells
    around a selected CNV gain region:
      - Mean CNV ± σ for Aneuploid and Diploid
      - Highlighted region of significant gain
      - Text panel listing genomic spots and their genes
        (optionally highlighting known CNA marker genes in bold)

    Parameters
    ----------
    adata : AnnData
        CNV-annotated data with:
            - obsm['X_cnv']
            - var index = gene names

    cna_info : dict
        Result from `find_signif_CNV_gain_regions` (or compatible dict) with:
            - 'gmm (Aneuploid)'
            - 'gmm (Diploid)'
            - 'spots' : { region_name : np.array of spot indices }

    rgn : str or hashable
        Key of the region in cna_info['spots'] to visualize.

    title_fs, label_fs, legend_fs, tick_fs : int
        Font sizes for title, labels, legend, ticks.

    xtick_rot : int or float (default=-90)
        Rotation angle for x-axis tick labels.

    xtick_ha : str (default='center')
        Horizontal alignment for x-tick labels.

    std_scale : float (default=1)
        Number of standard deviations used for shaded areas.

    figsize : tuple (default=(8,3))
        Figure size.

    ax : matplotlib.axes or None
        Axes to draw into; if None, a new figure+axes is created.

    cmap : str (default='tab10')
        Colormap for line colors.

    grid : bool (default=True)
        Toggle background grid.

    text_pos_adj : float (default=0.6)
        Controls vertical position of gene annotation text block.

    rng_ext : int (default=12)
        Number of genomic spots to extend on each side of the focal region.

    known_cna_markers : list (default=[])
        Optional list of known CNA marker genes to highlight in the text panel.

    title : str or None
        Custom plot title; if None, a default title is generated.

    ------------------------------------------------------------
    Returns
    -------
    ax : matplotlib.axes
        Axes object containing the CNV profile plot.

    ------------------------------------------------------------
    Usage
    ------
    >>> ax = plot_cnv_stat(
            adata,
            cna_info=res,
            rgn='17q12',
            known_cna_markers=['ERBB2','GRB7','PGAP3']
        )
    """
    
    some_known_markers_list = ['ESR1', 'ERBB2', 'EGFR', 'KRAS', 'CDKN2A', 'TP53', 'SMAD4', 'GATA6', 
                      'NFASC', 'ACOT1', 'GSDMD', 'SOX2', 'BRAF', 'ALK', 'ROS1', 'RET', 'NTRK',
                      'INTS8', 'ECT2', 'LSM1', 'DDHD2', 'COPS5', 'EIF3E', 'TPD52']

    if isinstance( known_cna_markers, list ):
        some_known_markers_list = list(set(some_known_markers_list).union(known_cna_markers))
    
    gmm_tumor =  cna_info['gmm (Aneuploid)']
    gmm_normal = cna_info['gmm (Diploid)']
    spot_llst = cna_info['spots']

    x_lower = spot_llst[rgn][0]
    x_upper = spot_llst[rgn][-1]
    
    mt, st, wt = get_mean_and_std_from_gmm( gmm_tumor )
    mn, sn, wn = get_mean_and_std_from_gmm( gmm_normal )

    M = rng_ext
    sw = std_scale
    x_lower_e = x_lower - M
    x_upper_e = x_upper + M+1
        
    dct = find_genes_in_genomic_spots(adata, list(np.arange(adata.obsm['X_cnv'].shape[1])), spot_ext = 0)
    
    bold_blue = "\033[1;34m"  # 1: Bold, 34: Blue
    reset = "\033[0m"
    
    x_e = np.arange(x_lower_e, x_upper_e)
    
    xx = []
    for i in range(x_lower, x_upper+1):
        glst = dct[i]
        s = '%4i (' % i
        for g in glst:
            if g in some_known_markers_list:
                s = s + r'$\bf{%s}$, ' % g
            else:
                s = s + '%s, ' % g
        s = s[:-2] + ')'
        xx.append(s)

    colors = get_col_colors( 10, cmap_name = cmap )
    
    if ax is None:
        fig, axes = plt.subplots(figsize = figsize, dpi=100, nrows=1, ncols=1, constrained_layout=False)
        fig.tight_layout() 
        ax = axes
    
    ax.plot( x_e, mt[x_lower_e:x_upper_e], color = colors[0], label = 'mean CNV (Aneuploid)' )
    ax.plot( x_e, mn[x_lower_e:x_upper_e], color = colors[1], label = 'mean CNV (Diploid)' )
    
    ax.fill_between(x_e, 
                     mt[x_lower_e:x_upper_e] - st[x_lower_e:x_upper_e]*sw, 
                     mt[x_lower_e:x_upper_e] + st[x_lower_e:x_upper_e]*sw, 
                     color = colors[0], alpha=.2, label = 'mean CNV $\pm$ $\sigma$ (Aneuploid)')
    
    ax.fill_between(x_e, 
                     mn[x_lower_e:x_upper_e] - sn[x_lower_e:x_upper_e]*sw, 
                     mn[x_lower_e:x_upper_e] + sn[x_lower_e:x_upper_e]*sw, 
                     color = colors[1], alpha=.2, label = 'mean CNV $\pm$ $\sigma$ (Diploid)')
    
    ylim = plt.gca().get_ylim()
    xlim = plt.gca().get_xlim()
    # plt.fill_between(x, ylim[0], ylim[1], color = colors[2], alpha=.2)
    ax.fill_between([x_lower-0.5, x_upper+0.5], ylim[0], ylim[1], color = colors[2], alpha=.2, label = 'Region of signif. gain')
    
    
    ax.legend(fontsize = legend_fs, loc = 'upper left')
    
    ax.set_xlabel('Genomic spot', fontsize = label_fs)
    ax.set_ylabel('CNV', fontsize = label_fs)
    if title is None:
        ax.set_title('Genomic spots around %i - %i' % (x_lower, x_upper), fontsize = title_fs )
    else:
        ax.set_title(title, fontsize = title_fs )
    
    # plt.plot( np.arange(x_lower, x_upper)[b[x_lower:x_upper]], 0.25*(b[x_lower:x_upper])[b[x_lower:x_upper]], 'r+' )

    #'''
    if xtick_rot == 0:
        ax.tick_params(axis='x', which='major', labelsize=tick_fs, rotation = xtick_rot)
    else:
        ax.set_xticks( x_e, x_e, rotation = xtick_rot, ha = xtick_ha, fontsize = tick_fs)
    #'''
    ax.tick_params(axis='y', labelsize=tick_fs)

    ss = r'$\bf{Spot}$ $\bf{(Genes)}$:'
    ss = ss + '\n'
    for xt in xx:
        ss = ss + '%s\n' % xt
    ax.text( xlim[0], ylim[0] - (ylim[1]-ylim[0])*text_pos_adj, ss, fontsize = tick_fs, va = 'top' )
    if grid: ax.grid(True)
    
    return ax


def get_genomic_spot_containing_gene( gene, dct, known_markers_list = None, verbose = True ):

    bold_blue = "\033[1;34m"  # 1: Bold, 34: Blue
    reset = "\033[0m"

    loc = -1
    s = ''
    for k in dct.keys():
        if gene in list(dct[k]):
            s = ''
            for g in dct[k]:
                if known_markers_list is None:
                    s = s + '%s, ' % g
                elif g in known_markers_list:
                    s = s + '%s%s%s, ' % (bold_blue, g, reset)
                else:
                    s = s + '%s, ' % g
            s = s[:-2]
            if verbose: print( '%12s: %4i - %s' % (gene, k, s))
            loc = k
            break
            
    return loc, s


def get_amp_regions_for_known_markers(adata, spot_llst, known_markers_list, verbose = False ):

    plst = []
    rngs_dct = {}
    loc_lst = []
    for j, key in enumerate(spot_llst.keys()):
        lst = spot_llst[key]    
        glst_dct = find_genes_in_genomic_spots(adata, list(lst), spot_ext = 0)
        glst_sel = []
        for g in known_markers_list:
            loc, gene_s = get_genomic_spot_containing_gene( g, glst_dct, known_markers_list, verbose = False )
            if (loc >= 0):
                if loc not in loc_lst:
                    loc_lst.append(loc)
                    if verbose: 
                        print('%15s (%4i-%4i): %6s in %4i - %s' % (key, lst[0], lst[-1], g, loc, gene_s))
                if (key not in plst):
                    plst.append(key)
                glst_sel.append(g)
    
        if len(glst_sel) > 0:
            gs = ''
            for g in glst_sel:
                gs = gs + '%s, ' % g
            rngs_dct[key] = r'%s ($\bf{%s}$)' % (key, gs[:-2])

    return rngs_dct


from mpl_toolkits.axes_grid1.inset_locator import inset_axes

def plot_cnv_hit( cna_info, adata = None, title = None, title_fs = 13, label_fs = 12, tick_fs = 10, 
                  wspace = 0.1, dpi = 100, ylabel = 'Genomic region', bin_size = 0.22,
                  cmap = None, vmax = 1, known_cna_markers = None, verbose = False ):

    """
    ------------------------------------------------------------
    📌 Summarize **CNV gain support across samples and regions**
    ------------------------------------------------------------

    Produces a two-panel figure:
      (1) Heatmap of region-level CNV gain scores per sample
      (2) Bar plot of gain frequency across samples per region

    If `adata` and region definitions are provided, regions can optionally
    be annotated with known CNA marker genes (e.g., ERBB2, EGFR, KRAS),
    and column labels will be updated accordingly.

    Parameters
    ----------
    cna_info : dict or pd.DataFrame
        - If DataFrame → treated directly as sample × region score matrix.
        - If dict      → expected to contain:
              'cnv_peaks_pos' : DataFrame (sample × region)
              'spots'         : { region_name : np.array of spots }

    adata : AnnData or None (default=None)
        Required only if annotating regions with known CNA markers.
        Must be compatible with `find_genes_in_genomic_spots()`.

    title : str or None
        Figure title.

    title_fs, label_fs, tick_fs : int
        Font sizes for title, axis labels, and ticks.

    wspace : float (default=0.1)
        Horizontal spacing between the heatmap and bar-plot panels.

    dpi : int (default=100)
        Figure resolution.

    ylabel : str (default='Genomic region')
        Y-axis label for the heatmap panel.

    bin_size : float (default=0.22)
        Controls the figure size scaling based on number of samples/regions.

    cmap : str or None
        Colormap passed to seaborn.heatmap.
        If None → seaborn default.

    vmax : float (default=1)
        Upper limit for heatmap color scale.

    known_cna_markers : list or None
        If provided, region labels will include bolded known markers
        discovered within each region.

    verbose : bool (default=False)
        If True, prints details about known marker localization.

    ------------------------------------------------------------
    Returns
    -------
    axes : np.ndarray of matplotlib.axes
        [0] → heatmap axis, [1] → bar plot axis

    rngs_dct : dict or None
        Optional mapping from original region names to annotated labels:
            { region_key : "region_label ($\\bf{MARKER1,MARKER2}$)" }

    ------------------------------------------------------------
    Usage
    ------
    >>> axes, rngs = plot_cnv_hit(
            cna_info=res,
            adata=adata,
            title="Recurrent CNV gain regions across samples",
            known_cna_markers=['ERBB2','EGFR','KRAS']
        )

    >>> rngs
    # {'17q12': '17q12 ($\\bf{ERBB2,GRB7}$)', ...}
    """
    
    some_known_markers_list = ['ESR1', 'ERBB2', 'EGFR', 'KRAS', 'CDKN2A', 'TP53', 'SMAD4', 'GATA6', 
                      'NFASC', 'ACOT1', 'GSDMD', 'SOX2', 'BRAF', 'ALK', 'ROS1', 'RET', 'NTRK',
                      'INTS8', 'ECT2', 'LSM1', 'DDHD2', 'COPS5', 'EIF3E', 'TPD52']

    if isinstance( known_cna_markers, list ):
        some_known_markers_list = list(set(some_known_markers_list).union(known_cna_markers))
    
    df = None
    rngs_dct = None
    # plst = None
    spot_llst = None
    
    if isinstance( cna_info, pd.DataFrame ):
        df = cna_info
    elif isinstance( cna_info, dict ):
        if 'cnv_peaks_pos' in list(cna_info.keys()):
            df = cna_info['cnv_peaks_pos']
            if 'spots'  in list(cna_info.keys()):
                spot_llst = cna_info['spots']

    if (adata is not None) & (spot_llst is not None) & (df is not None):
        rngs_dct = get_amp_regions_for_known_markers(adata, spot_llst, 
                                                     some_known_markers_list, 
                                                     verbose = verbose)
        if (known_cna_markers is not None):
            if known_cna_markers:
                df.rename(columns = rngs_dct, inplace = True)

    nr, nc = 1, 2
    hspace = wspace
    Nr = (df.sum(axis = 0) > 0).sum()
    Ns = df.shape[0]
    fs = ( bin_size*Ns*1.2, bin_size*Nr )
    w = fs[1]
    width_ratios = [fs[0], 1.2]
    aa = (width_ratios[0]+width_ratios[1])/width_ratios[0]
    figsize = (w*aa*fs[0]/fs[1], w)
    
    fig, axes = plt.subplots(nrows=nr, ncols=nc, constrained_layout=False, dpi = dpi, 
                             gridspec_kw={'width_ratios': width_ratios}, figsize = figsize)
    fig.tight_layout() 
    wspace = wspace*12/Ns
    # hspace = 0.1
    
    if title is not None: 
        fig.suptitle(title, x = 0.5, y = 1 + 0.05*(25/Nr), fontsize = title_fs, ha = 'center')
    plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=wspace, hspace=hspace)
    
    ax = axes[0]
    cax = inset_axes(ax,
                     width="4%",  # width: 40% of parent_bbox width
                     height="20%",  # height: 10% of parent_bbox height
                     loc='lower left',
                     bbox_to_anchor=(-0.08, 0, 1, 1),
                     bbox_transform=ax.transAxes,
                     borderpad=0 )
    
    g = sns.heatmap( df.transpose(), # row_cluster = False, col_cluster = False,
                       annot = True,
                       annot_kws = {'size': 8}, fmt = '.1f',
                       cbar_ax = cax,
                       cbar_kws = dict(use_gridspec=True, orientation = 'vertical', 
                                       location = 'left', shrink = 0.3),
                       linewidth=0.5, vmax = vmax, ax = ax,
                       yticklabels=False, cmap = cmap)
    
    # g.set_title( 'Average z-score in the region ($z_{max}$ = 1)', fontsize = title_fs )
    ax.tick_params( axis = 'both', labelsize = tick_fs ) 
    a = ax.set_ylabel(ylabel, fontsize = label_fs)
    
    #'''
    ax = axes[1]
    bar_values = ((df[ reversed(list(df.columns.values)) ] > 0).mean(axis = 0))
    ax = bar_values.plot.barh(fontsize = 10, ax = ax)
    ax.set_xlim([0,1])
    ax.grid()
    # ax.set_title(title, fontsize = title_fs)
    ax.set_xlabel('Frequency', fontsize = label_fs)
    ndiv = 5
    ax.set_xticks( np.arange(ndiv+1)/ndiv, np.arange(ndiv+1)/ndiv, fontsize = tick_fs, rotation = 90 ) 
    ax.tick_params( axis = 'y', labelsize = tick_fs ) 
    ax.yaxis.tick_right()
    dd = np.round( bar_values.max() + 0.4, 1 )
    ax.set_xlim( [0, dd])
    label_lst = [' %3.2f' % a for a in list(bar_values.round(2))]
    a = ax.bar_label(ax.containers[0], labels=label_lst, rotation = 0, fontsize = tick_fs-2)

    return axes, rngs_dct

