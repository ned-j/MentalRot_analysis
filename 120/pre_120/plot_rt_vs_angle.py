import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load the correct-only long file generated earlier
long_path = 'MentalRotation_CORRECT_ONLY_LONG.csv'
long_df = pd.read_csv(long_path)

# Ensure columns exist
assert {'ID','Angle','ReactionTime_s'}.issubset(long_df.columns)

# Create per-participant RT vs Angle plots
sns.set(style='whitegrid')
plots = []

for pid, sdf in long_df.groupby('ID'):
    plt.figure(figsize=(7,5))
    # jitter x a bit to avoid overplotting if many identical angles
    jitter = (np.random.rand(len(sdf)) - 0.5) * 1.2
    plt.scatter(sdf['Angle'] + jitter, sdf['ReactionTime_s']*1000, alpha=0.6, label='Trials', color='#1f77b4')
    # overlay mean ± SEM per angle
    agg = sdf.groupby('Angle').agg(mean_ms=('ReactionTime_s', lambda x: x.mean()*1000),
                                   sem_ms=('ReactionTime_s', lambda x: x.sem()*1000)).reset_index()
    plt.errorbar(agg['Angle'], agg['mean_ms'], yerr=agg['sem_ms'], fmt='-o', color='#d62728', capsize=3, label='Mean ± SEM')
    plt.title(f'Reaction Time vs. Angle — {pid}')
    plt.xlabel('Angle (deg)')
    plt.ylabel('Reaction Time (ms)')
    plt.legend()
    plt.tight_layout()
    fname = f'rt_vs_angle_{pid}.png'
    plt.savefig(fname, dpi=160)
    plt.close()
    plots.append(fname)

# Group level: average across participants per angle
grp = (long_df.groupby(['Angle','ID'])['ReactionTime_s']
       .mean()
       .reset_index())

agg_grp = (grp.groupby('Angle')
           .agg(mean_ms=('ReactionTime_s', lambda x: x.mean()*1000),
                sem_ms=('ReactionTime_s', lambda x: x.sem()*1000),
                n_participants=('ID','nunique'))
           .reset_index())

plt.figure(figsize=(7,5))
plt.errorbar(agg_grp['Angle'], agg_grp['mean_ms'], yerr=agg_grp['sem_ms'], fmt='-o', color='#2ca02c', capsize=4)
plt.title('Group Reaction Time vs. Angle (Correct Trials)')
plt.xlabel('Angle (deg)')
plt.ylabel('Reaction Time (ms)')
plt.tight_layout()

group_plot = 'rt_vs_angle_GROUP.png'
plt.savefig(group_plot, dpi=160)
plt.close()

plots, group_plot, long_df['ID'].unique().tolist(), agg_grp.head(10).to_dict(orient='records')
