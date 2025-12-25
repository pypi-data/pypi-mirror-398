from joolbox import date_fn
from joolbox import num_fn


class GlobalImport:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        import inspect
        collector = inspect.getargvalues(inspect.getouterframes(inspect.currentframe())[1][0]).locals
        globals().update(collector)


def import_all():
    with GlobalImport():
        ## will fire a warning as its bad practice for python. 
        import numpy as np
        import pandas as pd
        import polars as pl
        from pandas import json_normalize
        from multiprocessing import Process
        try:
            import pencilbox as pb
        except ImportError:
            print("Module not found. Continuing without it.")
        import logging
        import seaborn as sns
        import matplotlib.pyplot as plt
        from datetime import datetime
        from datetime import timedelta
        from pytz import timezone
        import time
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.float_format', lambda x: '%.5f' % x)
        from sklearn.cluster import KMeans
        from scipy.stats import zscore
        from numpy import asarray
        from sklearn.preprocessing import MinMaxScaler
        # from IPython.display import display
        import os
        import json
        from typing import Callable
        from functools import partial
        from scipy.stats import linregress
        import math
        import matplotlib.ticker as mtick
        import papermill as pm
        import shutil
        import requests
        from tabulate import tabulate
        from babel.numbers import format_currency
        import io
        import ast


import_all()
dt = date_fn.Cdt()

def ims_buckets():
    ims = pd.read_csv(io.StringIO("""bucket	ids	op
b2b return	[23, 35]	+
b2b return bad	[24, 25, 66, 36, 37, 68]	NA
b2b sale	[22]	-
badstock sale	[133, 134, 135]	NA
crbs	[7, 9, 63, 67]	NA
crwi bad	[87, 88, 89]	NA
customer return	[3, 29]	+
customer sale	[2, 50]	-
dump	[11, 12, 64]	-
excess stock transfer	[17, 92, 124, 125]	-
fresh liquidation	[127]	-
grn	[1, 28]	+
in house picking	[57, 140]	NA
item not received	[131]	NA
negative manual update	[39, 40, 41, 42, 117, 119, 129, 130, 132]	-
positive manual update	[44, 45, 46, 47, 118, 141]	+
positive manual update for grn	[120]	NA
prn	[20, 21, 65]	NA
put away	[38]	NA
putaway from system	[58, 61]	NA
reinventorization	[121, 122]	+
rts inward at warehouse	[136, 137, 138]	NA
secondary sales	[52, 56, 69]	NA
system negative update	[113]	-
system positive update	[112]	+
vendor return	[126]	-
coins positive update	[142]	+
coins negative update	[143]	-
esto positive udpate	[141]	+"""), delimiter='\t')

    # def CPR(x):
    #     result = x['id'].tolist()
    #     return result
    # ims_ndf = ims.groupby(['bucket']).apply(CPR).reset_index()
    # ims_ndf.rename(columns={0: 'ids'}, inplace=True)
    # def treatments(x):
    #     val = ims[ims.bucket == x['bucket']]['consideration'].tolist()[0]
    #     return val
    # ims_ndf['op'] = ims_ndf.apply(lambda x: treatments(x), axis=1)
    # return ims_ndf
    ims.ids = ims.ids.apply(lambda x: ast.literal_eval(x))
    return ims

def bucketise_ims_df(df, update_type_col, consideration_col_list):
    ims_buckets_df = ims_buckets()
    def ntr(x):
        for index, row in ims_buckets_df.iterrows():
            if x[update_type_col] in row['ids']:
                return row['bucket']
        return 'NA'
    def opr(x):
        for index, row in ims_buckets_df.iterrows():
            if x[update_type_col] in row['ids']:
                return row['op']
        return 'NA'
    def run_op(x, col):
        if x['op'] == '+':
            return x[col]
        elif x['op'] == '-':
            return -1*x[col]
        else:
            return 0
    df['bucket'] = df.apply(lambda x: ntr(x), axis = 1)
    df['op'] = df.apply(lambda x: opr(x), axis = 1)
    for col in consideration_col_list:
        df[f'{col}_consideration'] = df.apply(lambda x: run_op(x, col), axis = 1)

    return df

def fmt_inr(value, compact=False):
    fmt_cur = num_fn.NumFmt(currency=True, decimals=2, compact=compact, absolute=False)
    if value == 0:
        return '0'
    else:
        return fmt_cur.fmt(value)

def fmt_val(value, compact=False):
    fmt_num = num_fn.NumFmt(currency=False, decimals=2, compact=compact, absolute=False)
    if value == 0:
        return '0'
    else:
        return fmt_num.fmt(value)

class StopExecution(Exception):
    def _render_traceback_(self):
        pass

class Store:
    def __init__(self):
        self.default_folder_id = '146i1OOUqlLwRt9uxuOJ_IY4MNhzOyHLi'


store = Store()

def run_folder_replacements(folder_id):
    new_folder = folder_id
    if(folder_id == '146i1OOUqlLwRt9uxuOJ_IY4MNhzOyHLi'):  # Jobs
        new_folder = '1X6L0RjJXq49aSmJR1P3aSP6xJw8A3AqY'
    if(folder_id == '1B3dyuFtN3PxNcqlXQJr4CyT0DGPT9YLx'):  # Alerts
        new_folder = '11FN-qqMcfxbNbA1s8WEDDpHgtP9UDScs'
    if(folder_id == '15lgDtar1j-TNczQP_HRjfxyFtdbBnMTp'):  # DN
        new_folder = '1nOpXhp4qZY4Yw_2dlL_pjXT4hVaaz1F0'
    if(folder_id == '1NwSsS1Hg93ozZBsYbk44cdln3unxhKKl'):  # PnLV6
        new_folder = '1IVV87SqggheQImEwIaz7ryf7bzaiw8Gl'
    if(folder_id == '1rdJKFfYBXmt3NWiqObRMBBrnBNFKSILn'):  # Transfer Loss
        new_folder = '1_zJR2tO401rtq4e49_tR19JEUBWG33BM'
    if(folder_id == '148r9xNGkNMBGQxof2PFzly86ehPTXRiE'):  # Queries
        new_folder = '126Lt9d19Mtf1MMMNqZ7JzTujmdUWY9fV'
    if(folder_id == '1-SWHTrU4o951ZURJDxk-FDQb2hJ5CbeO'):  # SQL
        new_folder = '1pZTrwu8RHd4vQZVO3Qb9OdBdIKrSYayy'

    return new_folder


def set_default_folder_id(folder_id):
    store.default_folder_id = folder_id

def get_default_folder_id():
    return store.default_folder_id


def fn_read_gsheet(sheet_id, sheet_name):
    try:
        df_out = pb.from_sheets(sheet_id, sheet_name)
    except():
        df_out = pb.from_sheets(sheet_id, sheet_name, service_account="service_account")
    return df_out

def redcon():
    return pb.get_connection("redpen").connect()

def trinocon():
    return pb.get_connection('[Warehouse] Trino')


def prescon():
    return pb.get_connection("[Warehouse] Presto").connect()


def fn_execute_notebook(notebook, params={}, output_notebook=None, folder_id=None) -> str:
    '''This fn executes a jupyter notebook via command line while optionally
        taking in dictionary style parameters. Make sure notebook is having parameters tag on a cell
        when you want to pass parameters to notebook.
        Parameters which are not to auto inferred for type should start with suffix #raw_
    '''
    if folder_id is None:
        folder_id = get_default_folder_id()

    folder_id = run_folder_replacements(folder_id)

    def dicToparam(dic):
        def ml(dic):
            for k, v in dic.items():
                if k.startswith('#raw_'):
                    x = f'''-r {k.replace('#raw_', '')} "{v}"'''
                else:
                    x = f'''-p {k} "{v}"'''
                yield x
        return " ".join(list(ml(dic)))

    params = dicToparam(params)

    if output_notebook is None:
        command = f'''papermill "{notebook}" "{notebook}" {params}'''
    else:
        command = f'''papermill "{notebook}" "{output_notebook}" {params}'''

    os.system(command.strip())

    return command



def hello():
    print("Hello user. Current Package Version is {0.10.8}")


def fn_pl_sql(qkey, q=None, params={}, read_from_csv=False, save=False, con=None):
    if(con is None):
        con = trinocon()
    if(q is None):
        return pl.DataFrame()

    if (type(q) == dict and len(q) == 0):
        return pl.DataFrame()

    query = q[qkey]

    for key, val in params.items():
        query = query.replace(key, val)

    fpara = json.dumps(params).replace("{","_").replace("}","").replace(": ", "_").replace("\"","").replace(", ", "_")
    if (fpara == "_"):
        fpara = ""
    fpath = f"qdata/{qkey}{fpara}.csv"
    if(not read_from_csv) or (not os.path.exists(fpath)):
        if not os.path.exists('qdata'):
            if(save):
                os.makedirs('qdata')

        df = pl.read_database(query=query, connection=con)

        if(save):
            df.write_csv(fpath)

    #reading from file
    if(read_from_csv):
        df = pl.read_csv(fpath)

    return df


def fn_qsv(qkey, q=None, params={}, read_from_csv=False, save=False, con=None):
    if(con is None):
        con = trinocon()
    if(q is None):
        return pd.DataFrame()

    if (type(q) == dict and len(q) == 0):
        return pd.DataFrame()

    query = q[qkey]

    for key, val in params.items():
        query = query.replace(key, val)

    fpara = json.dumps(params).replace("{","_").replace("}","").replace(": ", "_").replace("\"","").replace(", ", "_")
    if (fpara == "_"):
        fpara = ""
    fpath = f"qdata/{qkey}{fpara}.csv"
    if(not read_from_csv) or (not os.path.exists(fpath)):
        if not os.path.exists('qdata'):
            if(save):
                os.makedirs('qdata')
        df = pd.read_sql(sql=query, con=con)
        if(save):
            df.to_csv(fpath, index = False)

    #reading from file
    if(read_from_csv):
        df = pd.read_csv(fpath, index_col=False, low_memory=False)

    return df

def fn_sql(sqlpath, params={}, read_from_csv=True, save=True, con=None):
    if(con is None):
        con = redcon()

    if not os.path.exists(sqlpath):
        raise Exception("sql path does not exist")
    
    with open(sqlpath, 'r') as f:
        query = f.read()

    for key, val in params.items():
        query = query.replace(key, val)

    fpara = json.dumps(params).replace("{","_").replace("}","").replace(": ", "_").replace("\"","").replace(", ", "_")
    if (fpara == "_"):
        fpara = ""
    fpath = f"qdata/{os.path.basename(sqlpath).split('.', 1)[0]}{fpara}.csv"
    if(not read_from_csv) or (not os.path.exists(fpath)):
        if not os.path.exists('qdata'):
            if(save):
                os.makedirs('qdata')
        df = pd.read_sql(sql=query, con=con)
        if(save):
            df.to_csv(fpath, index = False)

    #reading from file
    if(read_from_csv):
        df = pd.read_csv(fpath, index_col=False, low_memory=False)

    return df



def remove_outlier(df_in, col_name):
    q1 = df_in[col_name].quantile(0.25)
    q3 = df_in[col_name].quantile(0.75)
    iqr = q3-q1 #Interquartile range
    fence_low  = q1-1.5*iqr
    fence_high = q3+1.5*iqr
    df_out = df_in.loc[(df_in[col_name] > fence_low) & (df_in[col_name] < fence_high)]
    return df_out


def remove_outliers(df_in, col_name_list, iqr_multiple=1.5):
    for col_name in col_name_list:
        q1 = df_in[col_name].quantile(0.25)
        q3 = df_in[col_name].quantile(0.75)
        iqr = q3-q1 #Interquartile range
        fence_low  = q1-iqr_multiple*iqr
        fence_high = q3+iqr_multiple*iqr
        df_out = df_in.loc[(df_in[col_name] > fence_low) & (df_in[col_name] < fence_high)]
    return df_out


def get_ntile_rnk_output(df_in, col_name, cuts=100, cname='Ntile'):
    df_out = df_in.copy()
    df_out[cname] = pd.qcut(df_out[col_name].rank(method='first'), cuts, labels = range(1, cuts + 1))
    df_out[cname] = df_out[cname].astype(float)
    conditions = [
                (df_out[cname] >=0) & (df_out[cname] <= 6),
              (df_out[cname] >=7) & (df_out[cname] <= 14),
              (df_out[cname] >=15) & (df_out[cname] <= 23),
              (df_out[cname] >=24) & (df_out[cname] <= 36),
              (df_out[cname] >=37) & (df_out[cname] <= 55),
              (df_out[cname] >=56) & (df_out[cname] <= 75),
              (df_out[cname] >=76) & (df_out[cname] <= 86),
              (df_out[cname] >=87) & (df_out[cname] <= 94),
                (df_out[cname] >=95) & (df_out[cname] <= 100)
             ]
    choices = [0,1,2,3,4,5,6,7,8]
    df_out['rnk'] = np.select(conditions, choices)
    return df_out


def get_ntile_output(df_in, col_name, cuts=100, cname='Ntile'):
    df_out = df_in.copy()
    df_out[cname] = pd.qcut(df_out[col_name].rank(method='first'), cuts, labels = range(1, cuts + 1))
    df_out[cname] = df_out[cname].astype(float)
    return df_out


def make_flat_index(df_in):
    df_in.columns = ["_".join(map(str, a)).rstrip('_') for a in df_in.columns.to_flat_index()]
    return df_in

def pareto_test(df_in, col_name):
    df = get_ntile_output(df_in, col_name)
    gdf = pd.pivot_table(df, values = [col_name], index =['Ntile'],
                         columns =[], aggfunc = {col_name: [np.sum, 'count']}).reset_index()
    gdf.columns = ["_".join(a) for a in gdf.columns.to_flat_index()]
    gdf.rename({'Ntile_': 'Ntile'}, axis=1, inplace=True)
    col_name_sum = f"{col_name}_sum"
    col_name_count = f"{col_name}_count"
    
    gdf['top_x_perc'] = 100 - gdf['Ntile'] + 1
    gdf['contribution_perc'] = round((gdf[col_name_sum]/gdf[col_name_sum].sum())*100,1)
    gdf[col_name_sum] = gdf[col_name_sum].round(2)
    gdf['upto_contribution_perc'] = gdf.apply(lambda x: gdf[gdf['Ntile']>=x['Ntile']]['contribution_perc'].sum(),axis=1)
    gdf[f"upto_{col_name_sum}"] = gdf.apply(lambda x: gdf[gdf['Ntile']>=x['Ntile']][col_name_sum].sum(),axis=1)
    gdf[f"upto_{col_name_count}"] = gdf.apply(lambda x: gdf[gdf['Ntile']>=x['Ntile']][col_name_count].sum(),axis=1)
    
    cols = ['top_x_perc', 'upto_contribution_perc', f"upto_{col_name_sum}", f"upto_{col_name_count}", 'contribution_perc', col_name_sum, col_name_count, 'Ntile']
    gdf = gdf[cols]
    return gdf.sort_values('top_x_perc')



def describe_basis(df_in, col_name, col_seq):
    df_result = pd.DataFrame()
    if(col_name not in col_seq):
            col_seq.append(col_name)
    for val in sorted(list(df_in[col_name].unique())):
        df_work = df_in[col_seq]
        df2 = df_work[df_work[col_name]==val]
#         df2 = remove_outliers(df2, col_seq)
        df_out = df2.describe()
#         df_out['index1'] = df_out.index
        df_out.reset_index(level=0, inplace=True)
        df_out[col_name] = val
        df_out.sort_values(by=col_name, inplace = True)
        cols = df_out.columns
        df_out[cols[1:]] = df_out[cols[1:]].apply(pd.to_numeric, errors='coerce')
#         df_out = df_out.astype('float64')
        df_result = df_result.append(df_out, ignore_index=True)
    return df_result.pivot_table(index=col_name, columns=["index"], values=df_result.columns.difference(["index", col_name]))

def df_to_zip(df_dic, zipname="data", zipfolder="data", output_type='csv', clean_up = False):
    if os.path.exists(zipfolder):
        shutil.rmtree(zipfolder)
    os.makedirs(zipfolder, exist_ok=True)
    for fname, df in df_dic.items():
        if(output_type == 'csv'):
            filename = f"{zipfolder}/{fname}.csv"
            df.to_csv(filename, index=False)
        else:
            filename = f"{zipfolder}/{fname}.xlsx"
            df.to_excel(filename, index=False)
    zipname = f"{zipname}"
    shutil.make_archive(zipname, "zip", zipfolder)
    if clean_up:
        shutil.rmtree(zipfolder)
    return f"{zipname}.zip"

def df2zip(df_dic, zipname="data", zipfolder="data", clean_up=False):
    return df_to_zip(df_dic, zipname = zipname, zipfolder = zipfolder, clean_up=clean_up)


def delete(filepath, path_type='file'):
    # Deleting the file
    if(path_type == 'file'):
        if os.path.exists(filepath):
            os.remove(filepath)
            print("File deleted successfully")
        else:
            print("The file does not exist")
    else:
        if os.path.exists(filepath):
            shutil.rmtree(filepath)


def df_to_excel_zip(df_dic, zipname="data", zipfolder="data", clean_up=False):
    return df_to_zip(df_dic, zipname = zipname, zipfolder = zipfolder, output_type='excel', clean_up=clean_up)

def upload_to_fingertips(url, filename):
    response = requests.post(url, files={'attachments': open(filename, 'rb')}, headers={'api-key': 'yoph45k2brv5bdfskb34hj5b2n3baw4'})
    return f"{response.status_code} - {response.content}"

class MyKmeanWay:
#     Within-Cluster-Sum-of-Squares
    def __init__(self, data, mparas=None, no_of_clusters=3):
        self.data = data
        self.mparas = mparas
        self.no_of_clusters = no_of_clusters
        if(mparas==None):
            self.selected_data = data
        else:
            self.selected_data = data[mparas]
    
    def get_kmeans_data(self, no_of_clusters: int=None):
        if(no_of_clusters==None):
            no_of_clusters=self.no_of_clusters
        self.kmeans = KMeans(no_of_clusters)
        identified_clusters = self.kmeans.fit_predict(self.selected_data)
        data_with_clusters = self.data.copy()
        data_with_clusters['Clusters'] = identified_clusters 
        return data_with_clusters
        
    def set_no_of_clusters(self, no_of_clusters):
        self.no_of_clusters = no_of_clusters
        
    def show_elbow(self):
        wcss=[]
        for i in range(1,10):
            kmeans = KMeans(i)
            kmeans.fit(self.selected_data.apply(zscore))
            wcss_iter = kmeans.inertia_
            wcss.append(wcss_iter)
        number_clusters = range(1,10)
        ax = sns.lineplot(x=number_clusters, y=wcss)
        ax.set_title('The Elbow title')
        ax.set_xlabel('Number of clusters')
        ax.set_ylabel('WCSS')
        plt.show()


class RfmWay:
    def __init__(self, df_in, rfm_cols, rfm_cuts, adjustment=0, adjustment_cols=None):
        self.df_in = df_in
        self.rfm_cols = rfm_cols
        self.rfm_cuts = rfm_cuts
        self.df_result = df_in
        self.rnks = []
        for col, cuts in zip(rfm_cols, rfm_cuts):
#             print(f"cuts: {cuts}")
            self.rnks.append(f'rnk_{col}')
            self.df_result = self.__get_ntile_output(self.df_result, col, cname=f'rnk_{col}', cuts = cuts)
            self.df_result['rnk'] = self.df_result[self.rnks].sum(axis=1) - adjustment
            if(adjustment_cols is not None):
                self.df_result['rnk'] = self.df_result['rnk'] - self.df_result[adjustment_cols].sum(axis=1)
#                 self.df_result['rnk'] = np.where(self.df_result['rnk']<0,0,self.df_result['rnk'])
            self.df_result['rnk'] = np.where(self.df_result['rnk']<0,0,self.df_result['rnk'])
    
    def set_new_adjustment(adjustment, adjustment_cols=None):
        self.df_result['rnk'] = self.df_result[self.rnks].sum(axis=1) - adjustment
        if(adjustment_cols is not None):
            self.df_result['rnk'] = self.df_result['rnk'] - self.df_result[adjustment_cols].sum(axis=1)
            self.df_result['rnk'] = np.where(self.df_result['rnk']<0,0,self.df_result['rnk'])
            
        
    def describe(self, col_seq):
        return self.__describe_basis(self.df_result, "rnk", col_seq)
    
#     def set_df_result(self, df_in):
#         self.df_result = df_in.copy()
    
    @staticmethod
    def __describe_basis(df_in, col_name, col_seq):
        df_result = pd.DataFrame()
        if(col_name not in col_seq):
            col_seq.append(col_name)
        for val in sorted(list(df_in[col_name].unique())):
            df_work = df_in[col_seq]
            df2 = df_work[df_work[col_name]==val]
    #         df2 = remove_outliers(df2, col_seq)
            df_out = df2.describe()
    #         df_out['index1'] = df_out.index
            df_out.reset_index(level=0, inplace=True)
            df_out[col_name] = val
            df_out.sort_values(by=col_name, inplace = True)
            cols = df_out.columns
            df_out[cols[1:]] = df_out[cols[1:]].apply(pd.to_numeric, errors='coerce')
    #         df_out = df_out.astype('float64')
            df_result = df_result.append(df_out, ignore_index=True)
        return df_result.pivot_table(index=col_name, columns=["index"], values=df_result.columns.difference(["index", col_name]))
   
    @staticmethod
    def __get_ntile_output(df_in, col_name, cuts=100, cname='Ntile'):
        df_out = df_in.copy()
        df_out[cname] = pd.qcut(df_out[col_name].rank(method='first'), cuts, labels = range(1, cuts + 1))
        df_out[cname] = df_out[cname].astype(float)
        return df_out
    
    @staticmethod
    def __remove_outliers(df_in, col_name_list, iqr_multiple=1.5):
        for col_name in col_name_list:
            q1 = df_in[col_name].quantile(0.25)
            q3 = df_in[col_name].quantile(0.75)
            iqr = q3-q1 #Interquartile range
            fence_low  = q1-iqr_multiple*iqr
            fence_high = q3+iqr_multiple*iqr
            df_out = df_in.loc[(df_in[col_name] > fence_low) & (df_in[col_name] < fence_high)]
        return df_out
    
    def rnk_plot(self, axes=None):
        sns.histplot(ax=axes, data=self.df_result, x=self.df_result['rnk'])
        
    def rnk_share_plot(self, axes=None):
        sns.histplot(ax=axes, data=self.df_result, x=self.df_result['rnk'])
        
    
    def line_plot(self, col_seq, col_name="rnk", fig_size=(20,10), title=None):
        
        wdf = self.describe(col_seq)
        if(col_name in col_seq):
            col_seq.remove(col_name)
        
        no_of_fig_cols = 4
        ln = len(col_seq)
        fig, axes = plt.subplots(int(ln/no_of_fig_cols)+1, min(ln,no_of_fig_cols), figsize=fig_size)

#         print(col_seq)
        for index, col in enumerate(col_seq):
            ax0 = int(index/no_of_fig_cols)
            ay0 = index - int(index/no_of_fig_cols)*no_of_fig_cols
            tdf = wdf.loc[:,col]
            tdf = tdf[tdf.columns.difference(["count", "max", "25%", "75%", "min"])]
#             fdf.reset_index(level=0, inplace=True)
            fdf = tdf.stack().reset_index().rename(columns={0: "values"})
            if(int(ln/no_of_fig_cols+1)<=1):
                sns.lineplot(ax=axes[index], x=fdf[col_name], hue="Index", data=fdf).set_title(col)
            else:
                sns.lineplot(ax=axes[ax0, ay0], data=fdf, x=col_name, y="values", hue="index").set_title(col)
#                 sns.boxplot(ax=axes[ax0, ay0], x=fdf[col_name], hue="Index", data=fdf).set_title(col)

        fig.tight_layout()
        if(title is not None):
            fig.suptitle(title, size=16)
            fig.subplots_adjust(top=0.88)

        plt.show()

    @staticmethod
    def __show_values_on_bars(axs):
        def _show_on_single_plot(ax):        
            for p in ax.patches:
                _x = p.get_x() + p.get_width() / 2
                _y = p.get_y() + p.get_height()
                value = '{:.2f}'.format(p.get_height())
                ax.text(_x, _y, value, ha="center", va='top',rotation=90) 

        if isinstance(axs, np.ndarray):
            for idx, ax in np.ndenumerate(axs):
                _show_on_single_plot(ax)
        else:
            _show_on_single_plot(axs)

    def count_plot(self, title="Absolute", fig_size = (5,5)):
        wdf = self.describe(self.rfm_cols)

        tdf = wdf.loc[:,self.rfm_cols[0]]
        tdf = tdf.stack().reset_index().rename(columns={0: "values"})
        tdf = tdf[tdf["index"]=="count"]

        fig, axes = plt.subplots(1,1, figsize=fig_size)
        sns.barplot(x = 'rnk',
            y = 'values',
            data = tdf)
#         plt.xticks(rotation=70)
        plt.tight_layout()
        self.__show_values_on_bars(axes)
        if(title is not None):
            fig.suptitle(title, size=16)
            fig.subplots_adjust(top=0.88) 
        plt.show()

    def count_plot_perc(self, title="%Age", fig_size = (5,5)):
        wdf = self.describe(self.rfm_cols)
        tdf = wdf.loc[:,self.rfm_cols[0]]
        tdf["count%"] = (tdf["count"]/tdf["count"].sum())*100
        tdf = tdf.stack().reset_index().rename(columns={0: "values"})
        tdf = tdf[tdf["index"]=="count%"]
        fig, axes = plt.subplots(1,1, figsize=fig_size)
        sns.barplot(x = 'rnk',
            y = 'values',
            data = tdf)
#         plt.xticks(rotation=70)
        plt.tight_layout()
        self.__show_values_on_bars(axes) 
        if(title is not None):
            fig.suptitle(title, size=16)
            fig.subplots_adjust(top=0.88)
        plt.show()

    def box_plot(self, col_seq=None, col_name="rnk", fig_size=(10,5)):
        if(col_name not in col_seq):
            col_seq.append(col_name)

        if(col_seq is None):
            col_seq = self.df_result.columns

        ndf = self.df_result[col_seq]
#         ndf = pd.DataFrame()
#         for val in sorted(list(wdf[col_name].unique())):
#             df2 = wdf[wdf[col_name]==val]
#             df2 = self.__remove_outliers(df2, col_seq, iqr_multiple=1.5)
#             ndf = ndf.append(df2, ignore_index=True)

#         print(list(ndf.columns))
#         ndf[col_name] = ndf[col_name].astype('category')
        no_of_fig_cols = 4
        ln = len(col_seq) - 1
        fig_size_x = 4
        fig_size_y = 2 #(ln/no_of_fig_cols+1)*5
        fig, axes = plt.subplots(int(ln/no_of_fig_cols)+1, min(ln,no_of_fig_cols), figsize=fig_size)
        ls = [item for item in col_seq if item not in [col_name]]
        for index, col in enumerate(ls):
            ax0 = int(index/no_of_fig_cols)
            ay0 = index - int(index/no_of_fig_cols)*no_of_fig_cols
            max(0,(index - no_of_fig_cols*(ln/no_of_fig_cols)))
#             print(f"{ax0},{ay0}")
            if(int(ln/no_of_fig_cols+1)<=1):
                sns.boxplot(ax=axes[index], data=ndf, x=col_name, y=col, showfliers = False).set_title(col)
            else:
                sns.boxplot(ax=axes[ax0, ay0], data=ndf, x=col_name, y=col, showfliers = False).set_title(col)
        fig.tight_layout()
        plt.show()


fn_q = partial(fn_qsv, read_from_csv = False)
fn_q_nosave = partial(fn_qsv, read_from_csv = False, save=False)


def zip_file(filename, folder):
    from zipfile import ZipFile, ZipInfo
    # zif = ZipInfo.from_file(filename=filename)
    # print(type(zif))
    with ZipFile(f"{filename}.zip",'w') as zip:
        zip.write(f"{folder}/{filename}")
        # zip.write(os.path.join(os.getcwd(), filename))

def render_mpl_table(data, col_width=3.0, row_height=0.625, font_size=14,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, **kwargs):
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)

    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(font_size)

    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
    return ax

def bring_columns_to_front(columns: list, data: pd.DataFrame=None) -> pd.DataFrame:
    '''Brings the provided column list to front of the df in the specified order'''
    if data is None:
        print("data parameter is mandatory")
        return None
    df = data[columns + [col for col in data.columns if col not in columns]]
    return df

def fn_delta_df(df1, df2):
    df_delta = pd.merge(df1, df2, how='outer', indicator='Exist')
    df_delta = df_delta.loc[df_delta['Exist'] != 'both']
    return df_delta


class PdTable:
    dtypelist = []
    def __init__(self, in_df, table_name,
                 primary_key: list=None,
                 sort_key: list=None,
                 table_description="Table",
                 col_order=None,
                 front_cols=None,
                 load_type="upsert", 
                 schema="consumer",
                 add_create_timestamp=True
                 ):
        df = in_df.copy()
        df.columns = [x.lower() for x in df.columns]
        df.columns = df.columns.str.replace(' ','_')
        df.columns = df.columns.str.replace('.','_')
        df.columns = df.columns.str.replace('/','_')
        df.columns = df.columns.str.replace('(','')
        df.columns = df.columns.str.replace(')','')
        df.columns = df.columns.str.replace('%','perc')
        df.columns = df.columns.str.replace('&','n')
        df.columns = df.columns.str.replace('*','x')
        if add_create_timestamp:
            df["record_created_at_ist"] = date_fn.Cdt().now()
            df["record_created_at_ist"] = pd.to_datetime(df["record_created_at_ist"])
        if front_cols is not None:
            df = df[ front_cols + [ col for col in df.columns if col not in front_cols]]
        if col_order is not None:
            df = df[col_order]
        self.df = df
        self.table_description = table_description
        self.load_type = load_type
        self.table_name = table_name
        self.schema = schema
        self.primary_key = primary_key
        self.sort_key = sort_key
        # df_pnl.set_index(["outlet_id"]).index.is_unique
        
    def upload(self):
        kwargs = self.kwargs()
        # print(kwargs)
        pb.to_redshift(self.df, **kwargs)
        
    def set_column_dtype(self, name, type, description):
        self.dtypelist.append({"name": name, 
                   "type": type,
                   "description": description})


    def column_dtypes(self):
        dtypes = []
        for col in self.df.columns.tolist():
            dic = {"name": col, 
                   "type": self.__get_type(col),
                   "description": col}
            for dtp in self.dtypelist:
                if dtp['name'] == col:
                    dic = dtp
            dtypes.append(dic)
        return dtypes
    
    def kwargs(self):
        kwargs = {
        "schema_name": self.schema,
        "table_name": self.table_name,
        "column_dtypes": self.column_dtypes(),
        "primary_key": self.primary_key,
        "sortkey": self.sort_key,
        "force_upsert_without_increment_check": True,
        "load_type": self.load_type,
        "table_description":self.table_description
        }
        return kwargs

    def __get_type(self, col):
        typea = self.df[col].dtype
        if typea == "float64":
            return "float"
        elif typea == "int64":
            return "bigint"
        elif typea == "datetime64[ns]":
            return "datetime"
        else:
            return "character varying(500)"


class AdvDF:
    def __init__(self, df, index_cols=None):
        self.df = df
        self.index_cols = index_cols
        # df_pnl.set_index(["outlet_id"]).index.is_unique

    def numeric_cols(self):
        dtypes = []
        for col in self.df.columns.tolist():
            if self.__is_value(col):
                dtypes.append(col)
        return dtypes

    def non_numeric_cols(self):
        dtypes = []
        for col in self.df.columns.tolist():
            if not self.__is_value(col):
                dtypes.append(col)
        return dtypes

    def value_cols(self):
        if self.index_cols is not None:
            return [a for a in self.numeric_cols() if a not in self.index_cols]
        return self.numeric_cols()

    def suggested_index_cols(self):
        first_list = self.non_numeric_cols()
        second_list = []
        if self.index_cols is not None:
            second_list = self.index_cols
        return first_list + list(set(second_list) - set(first_list))

    def pivot(self, drop_cols=None):
        value_cols = self.value_cols()
        index_cols = self.suggested_index_cols()
        if drop_cols is not None:
            value_cols = [a for a in value_cols if a not in drop_cols]
            index_cols = [a for a in index_cols if a not in drop_cols]
        pvt = pd.pivot_table(
            self.df.fillna(0),
            values=value_cols,
            index=index_cols,
            columns=None,
            aggfunc = 'sum',
            fill_value=None,
            margins=False,
            dropna=True,
            margins_name='All',
            observed=False,
            sort=True,
        ).reset_index()
        return pvt

    def __is_value(self, col):
        typea = self.df[col].dtype
        if typea == "float64":
            return True
        elif typea == "int64":
            return True
        elif typea == "datetime64[ns]":
            return False
        else:
            return False

def merge_images_vertical(file1, file2, output_file):
    """Merge two images into one, displayed side by side
    :param file1: path to first image file
    :param file2: path to second image file
    :return: the merged Image object
    """
    from PIL import Image
    image1 = Image.open(file1)
    image2 = Image.open(file2)

    (width1, height1) = image1.size
    (width2, height2) = image2.size

    # result_width = width1 + width2
    # result_height = max(height1, height2)
    result_width = max(width1, width2)
    result_height = height1 + height2

    result = Image.new('RGB', (result_width, result_height), color=(255, 255, 255, 0))
    result.paste(im=image1, box=(0, 0))
    result.paste(im=image2, box=(0, height1))
    result.save(output_file)
    return result

def merge_images_horizontal(file1, file2, output_file):
    """Merge two images into one, displayed side by side
    :param file1: path to first image file
    :param file2: path to second image file
    :return: the merged Image object
    """
    from PIL import Image
    image1 = Image.open(file1)
    image2 = Image.open(file2)

    (width1, height1) = image1.size
    (width2, height2) = image2.size

    result_width = width1 + width2
    result_height = max(height1, height2)
    # result_width = max(width1, width2)
    # result_height = height1 + height2

    result = Image.new('RGB', (result_width, result_height), color=(255, 255, 255, 0))
    result.paste(im=image1, box=(0, 0))
    result.paste(im=image2, box=(width1, 0))
    result.save(output_file)
    return result

def upload2s3(filename: str, cloud_folder_path=f"pencilbox/wastage_bucket", expiry_in_seconds=3600*24*2):
    import boto3
    from botocore.exceptions import ClientError
    bucket_name = "grofers-prod-dse-sgp"
    def create_presigned_url(filename, object_name, expiration=expiry_in_seconds):
        # Generate a presigned URL for the S3 object
        s3_client = boto3.client('s3',**pb.get_secret("dse/iam_users/application-pencilbox-s3-access"))
        try:
            response = s3_client.generate_presigned_url('get_object',Params={'Bucket': bucket_name,'Key': object_name},ExpiresIn=expiration)
        except ClientError as e:
            return None
        # The response contains the presigned URL
        return response
    cloud_filepath = f"{cloud_folder_path}/{filename}"
    pb.to_s3(f"{filename}", bucket_name, cloud_filepath)
    File_Path_Link = create_presigned_url(bucket_name, object_name=cloud_filepath, expiration=expiry_in_seconds)
    return File_Path_Link


class Workflow:
    def __init__(self):
        self.workflow = [
        (self.__sample_function, [1, 2], {"c": 3}),  # first_task
        (self.__sample_function, [4, 5], {"c": 6}),  # second_task
        [
            (self.__sample_function, [7, 8], {"c": 9}),  # third_task
            (self.__sample_function, [10, 11], {"c": 12}) # fourth_task
        ]
        ]
       

    def __execute_function(self, func, *args, **kwargs):
        func(*args, **kwargs)

#     def __execute_in_parallel(self, functions):
#         processes = []
#         for func, args, kwargs in functions:
#             process = Process(target=self.__execute_function, args=(func, *args), kwargs=kwargs)
#             processes.append(process)
#             process.start()

#         for process in processes:
#             process.join()

    def __execute_in_parallel(self, functions):
        processes = []
        for item in functions:
            func = item[0]  # The function to execute
            if len(item) == 2 and not isinstance(item[1], (list, dict)):
                # If there is one argument and it's not a list or dict, treat it as a single argument
                args = [item[1]]
            elif len(item) > 1:
                args = item[1]  # A list of arguments
            else:
                args = []

            kwargs = item[2] if len(item) > 2 else {}  # Default to empty dict if kwargs are not provided

            process = Process(target=self.__execute_function, args=(func, *args), kwargs=kwargs)
            processes.append(process)
            process.start()

        for process in processes:
            process.join()


    def execute(self, workflow=None):
        if workflow is None:
            workflow = self.workflow
        for task in workflow:
            if isinstance(task, list):
                # Parallel execution
                self.__execute_in_parallel(task)
            elif callable(task):
                # Function with no arguments
                self.__execute_function(task)
            elif isinstance(task, tuple) and len(task) == 2:
                func, second_element = task
                if isinstance(second_element, dict):
                    # Function with only keyword arguments
                    self.__execute_function(func, **second_element)
                elif isinstance(second_element, list):
                    # Function with only positional arguments (list)
                    self.___execute_function(func, *second_element)
                else:
                    # Function with a single positional argument
                    self.__execute_function(func, second_element)
            else:
                # Function with both positional and keyword arguments
                func, args, kwargs = task
                self.__execute_function(func, *args, **kwargs)

    # Example usage
    @staticmethod
    def __sample_function(a, b, c=0):
        print(f"Function called with a={a}, b={b}, c={c}")