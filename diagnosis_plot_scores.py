#!/usr/bin/env python
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')   # Force matplotlib to not use any Xwindows backend
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind
import sys
import os
from statsmodels.sandbox.stats.multicomp import multipletests


def zscore(X):
    return((X - X.mean(axis=0)) / X.std(axis=0))


def zscore_by_group(X, labels, group):
    """z-scores each column of X by the mean and standard deviation of group."""
    assert(X.shape[0] == len(labels))
    idx = np.where(labels == group)[0]
    X_group_mean = np.mean(X.loc[idx], axis=0)
    X_group_std = np.std(X.loc[idx], axis=0)
    return((X - X_group_mean) / X_group_std)


def init_df(input_df):
    db = pd.DataFrame()
    db['id'] = input_df['ID']
    db['diagnosis'] = input_df['Diagnosis']

    return(db)


def melt_df(db, cols):
    return(pd.melt(db, id_vars=['id', 'diagnosis'], value_vars=cols))


def test_cols(input_df, cols, z_by_healthy=False, remove_healthy=False):


    if remove_healthy:
        input_df = input_df.loc[input_df['Diagnosis'] != healthy_group]
        z_by_healthy = False

    idx_0 = np.where(input_df['Diagnosis'] == healthy_group)[0]
    idx_1 = np.where(input_df['Diagnosis'] == cases_group)[0]


    labels = input_df['Diagnosis']

    db = init_df(input_df)
    ts = np.zeros((len(cols), 2)) # ts, ps (per column)
    for i, col in enumerate(cols):

        if z_by_healthy:
            db[col] = zscore_by_group(input_df[col], labels, healthy_group)
        else:
            db[col] = zscore(input_df[col])

        # replace nulls with nanmean
        db[col].loc[db[col].isnull()] = np.nanmean(db[col])

        ttest = ttest_ind(db[col].iloc[idx_0], db[col].iloc[idx_1])
        ts[i, 0] = ttest[0] # tvals
        ts[i, 1] = ttest[1] # pvals

    # https://stats.stackexchange.com/questions/20825/sidak-or-bonferroni
    #`bonferroni` : one-step correction
    #`sidak` : one-step correction
    #`holm-sidak` : step down method using Sidak adjustments
    #`holm` : step-down method using Bonferroni adjustments
    #`simes-hochberg` : step-up method  (independent)
    #`hommel` : closed method based on Simes tests (non-negative)
    #`fdr_bh` : Benjamini/Hochberg  (non-negative)
    #`fdr_by` : Benjamini/Yekutieli (negative)
    #`fdr_tsbh` : two stage fdr correction (non-negative)
    #`fdr_tsbky` : two stage fdr correction (non-negative)

    corrected = multipletests(np.ravel(ts[:, 1]), alpha=0.05, method='fdr_bh')
    H1 = np.where(corrected[0])[0]

    print('{}/{} tests reject H0'.format(len(H1), len(cols)))
    db = melt_df(db, cols)

    return(db, ts, H1)


def format_stats(db, cols, ts, H1):
    lines = []
    for i, col in enumerate(cols):
        avg_grp_mean = np.mean((db['value'].loc[db['diagnosis'] == healthy_group].loc[db['variable'] == col]))
        bad_grp_mean = np.mean((db['value'].loc[db['diagnosis'] == cases_group].loc[db['variable'] == col]))
        n_avg_grp = len(db['value'].loc[db['diagnosis'] == healthy_group].loc[db['variable'] == col])
        n_bad_grp = len(db['value'].loc[db['diagnosis'] == cases_group].loc[db['variable'] == col])
        t = ts[i, 0]
        p = ts[i, 1]
        if i in H1:
            passed = 1
        else:
            passed = 0
        lines.append('{},{},{},{},{},{},{},{}\n'.format(
            col, avg_grp_mean, bad_grp_mean, n_avg_grp, n_bad_grp, t, p, passed))

    return(lines)


def star_sig_tests(names, H1):
    for i in range(len(names)):
        if i in H1:
            names[i] = names[i] + ' *'

    return(names)


# input data
input_df = pd.read_csv('xbrain_database_with_biotypes.csv')

flip = False
try:
    if sys.argv[1] == 'flip':
        flip = True
except:
    pass

if 'replication' in os.path.basename(os.path.abspath(os.curdir)):
    replication = True
else:
    replication = False

if replication:
    healthy_group = 'HC'
    cases_group = 'SZ'
else:
    healthy_group = 1
    cases_group = 4


# for each plot of interest (cognitive scores, outcome scores, symptom scores, health scores)
cog_cols = ['scog_er40_crt_columnqcrt_value_inv', 'Part1_TotalCorrect', 'Part2_TotalCorrect', 'Part3_TotalCorrect', 'RMET total', 'rad_total', 'np_domain_tscore_process_speed', 'np_domain_tscore_work_mem', 'np_domain_tscore_verbal_learning', 'np_domain_tscore_visual_learning', 'np_domain_tscore_reasoning_ps', 'np_domain_tscore_att_vigilance']

if not replication:
    out_cols = ['bsfs_total', 'qls_factor_interpersonal', 'qls_factor_instrumental_role', 'qls_factor_intrapsychic', 'qls_factor_comm_obj_activities', 'qls_total', 'sans_total_sc', 'sans_dim_exp_avg', 'sans_dim_mot_avg', 'bprs_factor_total', 'cirsg_total', 'cirsg_severity_index', 'sas_total', 'CPZ_equiv']
    #out_cols = ['bsfs_sec1_total', 'bsfs_sec2_total', 'bsfs_sec3_total', 'bsfs_sec4_total', 'bsfs_sec5_total', 'bsfs_sec6_total', 'bsfs_sec7_total', 'qls_factor_interpersonal', 'qls_factor_instrumental_role', 'qls_factor_intrapsychic', 'qls_factor_comm_obj_activities', 'qls_total', 'sans_total_sc', 'sans_dim_exp_avg', 'sans_dim_mot_avg', 'bprs_factor_total', 'cirsg_total', 'cirsg_severity_index', 'sas_total', 'CPZ_equiv']
    #fxn_cols = ['bsfs_sec1_total', 'bsfs_sec2_total', 'bsfs_sec3_total', 'bsfs_sec4_total', 'bsfs_sec5_total', 'bsfs_sec6_total', 'bsfs_sec7_total', 'qls_factor_interpersonal', 'qls_factor_instrumental_role', 'qls_factor_intrapsychic', 'qls_factor_comm_obj_activities', 'qls_total']
    #smp_cols = ['sans_total_sc', 'sans_dim_exp_avg', 'sans_dim_mot_avg', 'bprs_factor_total']
    #hlt_cols = ['cirsg_total', 'cirsg_severity_index', 'sas_total', 'CPZ_equiv']

cog_names = ['ER40 RT (inv)', 'Tasit 1', 'Tasit 2', 'Tasit 3', 'RMET', 'RAD', 'Processing Speed', 'Working Memory', 'Verbal Learning', 'Visual Learning', 'Reasoning', 'Attention/Vigilance']

if not replication:
    out_names = ['Birchwood total', 'QLS interpersonal', 'QLS instrumental role', 'QLS intrapsychic', 'QLS common objectives', 'QLS total', 'SANS total', 'SANS diminished expression', 'SANS motivation', 'BPRS total', 'CIRSG total', 'CIRSG severity', 'SAS total', 'Medication load (CPZ equivilant)']
    #out_names = ['BSFS 1', 'BSFS 2', 'BSFS 3', 'BSFS 4', 'BSFS 5', 'BSFS 6', 'BSFS 7', 'QLS Interpersonal', 'QLS Instrumental Role', 'QLS intrapsychic', 'QLS Common Objectives', 'QLS Total', 'SANS Total', 'SANS Diminished Expression', 'SANS Motivation', 'BPRS', 'CIRSG Total', 'CIRSG Severity', 'SAS Total', 'Medication load (CPZ equivilant)']
    #fxn_names = ['BSFS 1', 'BSFS 2', 'BSFS 3', 'BSFS 4', 'BSFS 5', 'BSFS 6', 'BSFS 7', 'QLS Interpersonal', 'QLS Instrumental Role', 'QLS intrapsychic', 'QLS Common Objectives', 'QLS Total']
    #smp_names = ['SANS Total', 'SANS Diminished Expression', 'SANS Motivation', 'BPRS']
    #hlt_names = ['CIRSG Total', 'CIRSG Severity', 'SAS Total', 'Medication load (CPZ equivilant)']

idx_0 = np.where(input_df['Diagnosis'] == healthy_group)[0]
idx_1 = np.where(input_df['Diagnosis'] == cases_group)[0]

# calculate all info for plots
cog_db, cog_ts, cog_H1 = test_cols(input_df, cog_cols, z_by_healthy=True)

if not replication:
    out_db, out_ts, out_H1 = test_cols(input_df, out_cols, remove_healthy=True)
    #fxn_db, fxn_ts, fxn_H1 = test_cols(input_df, fxn_cols, remove_healthy=True)
    #smp_db, smp_ts, smp_H1 = test_cols(input_df, smp_cols, remove_healthy=True)
    #hlt_db, hlt_ts, hlt_H1 = test_cols(input_df, hlt_cols, remove_healthy=True)

# write out stats
f = open('diagnosis_score_stats.csv', 'wb')
f.write('stat_name,avg_grp_mean,poor_grp_mean,n_avg_grp,n_poor_grp,t,p,passed\n')
f.writelines(format_stats(cog_db, cog_cols, cog_ts, cog_H1))

if not replication:
    f.writelines(format_stats(out_db, out_cols, out_ts, out_H1))
    #f.writelines(format_stats(fxn_db, fxn_cols, fxn_ts, fxn_H1))
    #f.writelines(format_stats(smp_db, smp_cols, smp_ts, smp_H1))
    #f.writelines(format_stats(hlt_db, hlt_cols, hlt_ts, hlt_H1))

f.close()

# star names of significant effects
cog_names = star_sig_tests(cog_names, cog_H1)

if not replication:
    out_names = star_sig_tests(out_names, out_H1)
    #fxn_names = star_sig_tests(fxn_names, fxn_H1)
    #smp_names = star_sig_tests(smp_names, smp_H1)
    #hlt_names = star_sig_tests(hlt_names, hlt_H1)

# plot
sns.set_style('white')

if not replication:
    fig, (ax1, ax2) = plt.subplots(figsize=(12, 10), nrows=2)
else:
    fig, ax1 = plt.subplots(figsize=(12,5), nrows=1, ncols=1)

plt.subplots_adjust(left=0.125, bottom=0.15, right=0.9, top=0.85, wspace=0.25, hspace=0.7)
lwidth = 0.1 # outlines

plt.suptitle("Healthy Controls vs Schizophrenia Spectrum Disorders", y=1.09, fontsize=20)
sns.boxplot(x="variable", y="value", hue="diagnosis", linewidth=lwidth,  data=cog_db, palette="RdBu", fliersize=2.5, ax=ax1)

if not replication:
    sns.boxplot(x="variable", y="value", hue="diagnosis", linewidth=lwidth,  data=out_db, palette="RdBu", fliersize=2.5, ax=ax2)
    #sns.violinplot(x="biotype", y="value", hue="diagnosis", linewidth=lwidth, data=cog_db, ax=ax[0][1])
    #sns.swarmplot(x="biotype", y="value", hue="diagnosis", data=cog_db.loc[cog_db['biotype'] == 1], palette="RdBu", ax=ax[0][2])
    #sns.boxplot(x="variable", y="value", hue="biotype", linewidth=lwidth, data=fxn_db, palette="RdBu", fliersize=2.5, whis=3, ax=ax[0][1])
    #sns.boxplot(x="variable", y="value", hue="biotype", linewidth=lwidth, data=smp_db, palette="RdBu", fliersize=2.5, whis=3, ax=ax[1][0])
    #sns.boxplot(x="variable", y="value", hue="biotype", linewidth=lwidth, data=hlt_db, palette="RdBu", fliersize=2.5, whis=3, ax=ax[1][1])

ax1.set_title("Cognitive scores")
ax1.set_xticklabels(cog_names, rotation=45, ha='right')
ax1.set_ylim([-6, 4])
ax1.hlines(0, ax1.xaxis.get_majorticklocs()[0], ax1.xaxis.get_majorticklocs()[-1])

if not replication:
    ax2.set_title("Outcome scores")
    ax2.set_xticklabels(out_names, rotation=45, ha='right')
    ax2.set_ylim([-2.5, 2.5])
    ax2.hlines(0, ax2.xaxis.get_majorticklocs()[0], ax2.xaxis.get_majorticklocs()[-1])

    #ax[0][1].set_title("Diagnosis distribution per biotype")
    #ax[0][1].set_xticklabels(['Average', 'Poor'], rotation=45, ha='right')
    #ax[0][1].set_ylim([-6, 4])
    #ax[0][1].hlines(0,  ax[0][1].xaxis.get_majorticklocs()[0], ax[0][1].xaxis.get_majorticklocs()[-1])

    # reserved?
    #ax[0][2].set_title("Poor-perfoming biotype diagnosis distribution", y=y_title_margin)
    #ax[0][2].set_xticklabels(ax[0][2].get_xticks(), rotation=45, ha='right')
    #ax[0][2].set_ylim([-4, 4])
    #ax[0][2].hlines(0,  ax[0][2].xaxis.get_majorticklocs()[0], ax[0][2].xaxis.get_majorticklocs()[-1])

    #ax[0][1].set_title("Social function scores")
    #ax[0][1].set_xticklabels(fxn_names, rotation=45, ha='right')
    #ax[0][1].set_ylim([-2.5, 2.5])
    #ax[0][1].hlines(0, ax[0][1].xaxis.get_majorticklocs()[0], ax[0][1].xaxis.get_majorticklocs()[-1])

    #ax[1][0].set_title("Symptom scores")
    #ax[1][0].set_xticklabels(smp_names, rotation=45, ha='right')
    #ax[1][0].set_ylim([-2.5, 2.5])
    #ax[1][0].hlines(0, ax[1][0].xaxis.get_majorticklocs()[0], ax[1][0].xaxis.get_majorticklocs()[-1])

    #ax[1][1].set_title("Health scores")
    #ax[1][1].set_xticklabels(hlt_names, rotation=45, ha='right')
    #ax[1][1].set_ylim([-2.5, 2.5])
    #ax[1][1].hlines(0, ax[1][1].xaxis.get_majorticklocs()[0], ax[1][1].xaxis.get_majorticklocs()[-1])

fig.savefig('diagnosis_scores.pdf')

