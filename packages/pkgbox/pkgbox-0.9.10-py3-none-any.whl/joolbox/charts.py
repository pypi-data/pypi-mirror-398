import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
import numpy as np
import pandas as pd
import matplotlib.ticker as mtick


def contribution_pie(df, x=None, y=None, ax=None, title=''):
    fig, ax = plt.subplots(1, 1, figsize=(15, 5))
    fig.suptitle(title)
    cdf = pd.pivot_table(df.round(2), index=[x], values=[y], columns=[], aggfunc=np.sum).reset_index()
    plt.pie(cdf[y], labels=cdf[x], autopct='%.0f%%')
    plt.show()

def contribution_bar(df, x=None, y=None, ax=None, showlabels=True):
    cdf = pd.pivot_table(df.round(2), index=[x], values=[y], columns=[], aggfunc=np.sum).reset_index()
    sns.barplot(data=cdf, x=x, y=y, ax=ax)
    if showlabels:
        ax.bar_label(ax.containers[0], color='C0')
    return ax


def pareto_chart(df_in, x='', y=None,
                 title='', figsize=(15, 5),
                 max_display_count=None,
                 show_right_axis=True,
                 showlabels=True, c0='C0', c1='C1', save_as_image=False):
    df_in = pd.pivot_table(df_in, index=[x], values=[y], columns=[], aggfunc=np.sum).reset_index()
    df = df_in.sort_values(y, ascending=False)
    df["cumpercentage"] = (df[y].cumsum()/df[y].sum())*100
    if max_display_count is not None:
        df = df.head(max_display_count)
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(title)
    ax.tick_params(axis="y", colors=c0)
    ax.set_xticks(ax.get_xticks().tolist())
    ax.set_xticklabels(labels=ax.get_xticklabels(), rotation=90)
    if show_right_axis:
        ax2 = ax.twinx()
        ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
        # ax2.line_label(ax2.containers[0], fmt='%.2f%%')
        ax2.tick_params(axis="y", colors=c1)
        sns.lineplot(x=x, y="cumpercentage", data=df, ax=ax2, color=c1, marker="D", ms=7)
    pareto_plot = sns.barplot(x=x, y=y, data=df, ax=ax, color=c0)
    if showlabels:
        ax.bar_label(ax.containers[0], color=c0)
        if show_right_axis:
            for item in df.groupby('cumpercentage'):
                for x1, y1 in item[1][[x, 'cumpercentage']].values:
                    # print(x1,y1,y1)
                    plt.text(x1, y1+2, "{0:.1f}%".format(y1), color=c1)
    if save_as_image:
        imgfig = pareto_plot.get_figure()
        imgfig.savefig(f"{title}.jpg", dpi=300, bbox_inches='tight')
    plt.show()

def lineplot(df, x=None, y=None, ax=None, hue=None, showlabels=False):
    if hue is None:
        cdf = pd.pivot_table(df.round(2), index=[x], values=[y], columns=[], aggfunc=np.sum).reset_index()
    else:
        cdf = pd.pivot_table(df.round(2), index=[x, hue], values=[y], columns=[], aggfunc=np.sum).reset_index()
    sns.lineplot(data=cdf, x=x, y=y, hue=hue, ax=ax)
    return ax

def df2img(data, col_width=2.0, row_height=0.625, header_height=1.4, font_size=14,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0, title='',
                     center_col_indexes = [], left_col_indexes = [], right_col_indexes = [],
                     ax=None, **kwargs):
    import six
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        plt.tight_layout()
        ax.axis('off')
        ax.set_title(title, fontsize=16)

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)

    mpl_table.auto_set_font_size(False)
    # mpl_table.set_fontsize(font_size)
    mpl_table.auto_set_column_width(col=list(range(len(data.columns))))
    mpl_table.set_fontsize(font_size)
    # cells = mpl_table.properties()["celld"]
    # for i in range(0, 15):
    #     cells[i, 0]._loc = 'center'
    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w',ha="center")
            cell.set_facecolor(header_color)
            cell.set_height(header_height)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors)])
            cell.set_height(row_height)
            if k[1] in center_col_indexes: 
                cell.set_text_props(color='black',ha="left")
            if k[1] in left_col_indexes: 
                cell.set_text_props(color='black',ha="left")
            else:
                cell.set_text_props(color='black',ha="right")
    fig.savefig(f"{title}.jpg", dpi=300, bbox_inches='tight')
    return f"{title}.jpg"

def df2img_custom(data, col_width=2.0, row_height=0.625, header_height=1.4, font_size=14,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0, title='',
                     center_col_indexes = [], left_col_indexes = [], right_col_indexes = [],
                     ax=None, **kwargs):
    import six
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        plt.tight_layout()
        ax.axis('off')
        ax.set_title(title, fontsize=16)

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)

    mpl_table.auto_set_font_size(False)
    # mpl_table.set_fontsize(font_size)
    mpl_table.auto_set_column_width(col=list(range(len(data.columns))))
    mpl_table.set_fontsize(font_size)
    # cells = mpl_table.properties()["celld"]
    # for i in range(0, 15):
    #     cells[i, 0]._loc = 'center'
    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w',ha="center")
            cell.set_facecolor(header_color)
            cell.set_height(header_height)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors)])
            cell.set_height(row_height)
            if k[1] in center_col_indexes: 
                cell.set_text_props(color='black',ha="left")
            if k[1] in left_col_indexes: 
                cell.set_text_props(color='black',ha="left")
            else:
                cell.set_text_props(color='black',ha="right")
    fig.savefig(f"{title}.jpg", dpi=300, bbox_inches='tight')
    return f"{title}.jpg"

def df2img_custom2(data, col_width=2.0, row_height=0.625, header_height=1.4, font_size=14,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0, title='',
                     center_col_indexes = [], left_col_indexes = [], right_col_indexes = [],
                      bold_rows=[],
                     ax=None, **kwargs):
    import six
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        plt.tight_layout()
        ax.axis('off')
        ax.set_title(title, fontsize=16)

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)

    mpl_table.auto_set_font_size(False)
    # mpl_table.set_fontsize(font_size)
    mpl_table.auto_set_column_width(col=list(range(len(data.columns))))
    mpl_table.set_fontsize(font_size)
    # cells = mpl_table.properties()["celld"]
    # for i in range(0, 15):
    #     cells[i, 0]._loc = 'center'
    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w',ha="center")
            cell.set_facecolor(header_color)
            cell.set_height(header_height)
        elif k[0] in bold_rows:
            if k[1] == 0:
                cell.set_text_props(weight='bold', color='black',ha="left")
            else:
                if k[1] in center_col_indexes: 
                    cell.set_text_props(weight='bold', color='black',ha="left")
                if k[1] in left_col_indexes: 
                    cell.set_text_props(weight='bold', color='black',ha="left")
                else:
                    cell.set_text_props(weight='bold', color='black',ha="right")

            # cell.set_facecolor(header_color)
            cell.set_facecolor(row_colors[k[0]%len(row_colors)])
            cell.set_height(row_height)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors)])
            cell.set_height(row_height)
            if k[1] in center_col_indexes: 
                cell.set_text_props(color='black',ha="left")
            if k[1] in left_col_indexes: 
                cell.set_text_props(color='black',ha="left")
            else:
                cell.set_text_props(color='black',ha="right")
    fig.savefig(f"{title}.jpg", dpi=300, bbox_inches='tight')
    return f"{title}.jpg"

def pareto_bar(df, x, y, max_display_count=None, figsize=(6, 10), title=None, save_as_image=False, palette = ["#918BC3", "#e6ffff", "#e6ffff", "#918BC3"], color='C1'): 
    df_in = pd.pivot_table(df, index=[x], values=[y], columns=[], aggfunc=np.sum).reset_index()
    df = df_in.sort_values(y, ascending=False)
    df["cumpercentage"] = (df[y].cumsum()/df[y].sum())*100
    df["percentage"] = (df[y]/df[y].sum())*100
    
    df["cumpercentage"] = df["cumpercentage"].astype('int')
    df["percentage"] = df["percentage"].astype('int')
    
    df[y] = df[y].astype('int64')
    
    if max_display_count is not None:
        df = df.head(max_display_count)

    sns.set_theme(style="white")
    f, ax = plt.subplots(figsize=figsize)
    sns.despine(left=True, bottom=True)
    sns.set_palette(palette=palette)
    pareto_plot = sns.barplot(x=y, y=x, data=df,label=y, color=color, ax=ax)
    rects = ax.patches
    ax.set(xlabel=None)
    ax.set(ylabel=None)
    ax.set_xticks([])
    ax.set_yticks([])
    # labels = [f"label{i}" for i in range(len(rects))]
    labels1 = [f"{r[x]}" for i,r in df.iterrows()]
    labels2 = [f"{fmt_inr(r[y])}" for i,r in df.iterrows()]
    labels3 = [f"{r['percentage']}%" for i,r in df.iterrows()]
    
    plot_height = rects[0].get_y() - 0.5
    
    plt.rcParams['text.usetex'] = False #r'$\underline{x}$'
    
    if title is not None:
        ax.text(100000, plot_height - 0.5, title, ha="left", va="top", weight="bold")
        
    ax.text(10000, plot_height , x, ha="left", va="top", weight="bold")
    ax.text(120000, plot_height, y, ha="left", va="top", weight="bold")
    ax.text(180000, plot_height, 'Percentage Contribution', ha="left", va="top", weight="bold")
    
    
    for rect, label in zip(rects, labels1):
        width = rect.get_width()
        # print(width)
        ax.text(10000, rect.get_y() + rect.get_height()/2 , label, ha="left", va="top")
        # height = rect.get_height()
        # ax.text(rect.get_x() + rect.get_width() / 2, height + 5, label, ha="center", va="bottom")
    
    for rect, label in zip(rects, labels2):
        width = rect.get_width()
        ax.text(120000, rect.get_y() + rect.get_height()/2 , label, ha="left", va="top")
    
    for rect, label in zip(rects, labels3):
        width = rect.get_width()
        ax.text(180000, rect.get_y() + rect.get_height()/2 , label, ha="left", va="top")
    
    if save_as_image:
        imgfig = pareto_plot.get_figure()
        imgfig.savefig(f"{title}.jpg", dpi=300, bbox_inches='tight')
        return f'{title}.jpg'
        
    plt.show()
    