from .update_checker import check_for_update
import sys
import threading

# Run update check automatically on import
threading.Thread(target=lambda: check_for_update("qdesc"), daemon=True).start()

 # replace with your current version

def desc(df):
    import pandas as pd
    import numpy as np
    from scipy.stats import anderson

    x = np.round(df.describe().T, 2)
    x = x.iloc[:, [0, 1, 2, 5, 3, 7]]
    x.rename(columns={'50%': 'median'}, inplace=True)

    mad_raw = {}
    mad_norm = {}

    for column in df.select_dtypes(include=[np.number]):
        clean_col = df[column].dropna()

        if len(clean_col) == 0:
            mad_raw[column] = np.nan
            mad_norm[column] = np.nan
            continue
        median = np.median(clean_col)
        abs_dev = np.abs(clean_col - median)
        raw = np.median(abs_dev)
        mad_raw[column] = raw
        mad_norm[column] = 1.4826 * raw  # normalized MAD
    mad_df = pd.DataFrame({
        'MAD_raw': mad_raw,
        'MAD_norm': mad_norm
    })
    results = {}
    for column in df.select_dtypes(include=[np.number]):
        clean_col = df[column].dropna()

        if len(clean_col) < 5:
            results[column] = {'AD_stat': np.nan, '5% crit_value': np.nan}
            continue

        result = anderson(clean_col)
        results[column] = {
            'AD_stat': result.statistic,
            '5% crit_value': result.critical_values[2]
        }
    anderson_df = pd.DataFrame.from_dict(results, orient='index')
    xl = x.iloc[:, :4]
    xr = x.iloc[:, 4:]
    x_df = np.round(pd.concat([xl, mad_df, xr, anderson_df], axis=1), 2)
    return x_df

def grp_desc(df, numeric_col, group_col):
    import pandas as pd
    import numpy as np
    from scipy.stats import median_abs_deviation, anderson
    results = []
    for group, group_df in df.groupby(group_col):
        data = group_df[numeric_col].dropna()
        if len(data) < 2:

            stats = {
                group_col: group,
                'count': len(data),
                'mean': np.nan,
                'std': np.nan,
                'median': np.nan,
                'mad': np.nan,
                'min': np.nan,
                'max': np.nan,
                'anderson_stat': np.nan,
                'crit_5%': np.nan
            }
        else:
            ad_result = anderson(data, dist='norm')
            stats = {
                group_col: group,
                'count': len(data),
                'mean': data.mean(),
                'std': data.std(),
                'median': data.median(),
                'mad_raw': median_abs_deviation(data),
                'mad_norm': median_abs_deviation(data)*1.4826,
                'min': data.min(),
                'max': data.max(),
                'AD_stat': ad_result.statistic,
                'crit_5%': ad_result.critical_values[2],  # 5% is the third value
            }
        results.append(stats)
    return np.round(pd.DataFrame(results),2)

def freqdist(df, column_name):
    import pandas as pd
    import numpy as np
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in DataFrame.")
    
    if df[column_name].dtype not in ['object', 'category']:
        raise ValueError(f"Column '{column_name}' is not a categorical column.")
    
    freq_dist = df[column_name].value_counts().reset_index()
    freq_dist.columns = [column_name, 'Count']
    freq_dist['Percentage'] = np.round((freq_dist['Count'] / len(df)) * 100,2)
    return freq_dist

def freqdist_a(df, ascending=False):
    import pandas as pd
    import numpy as np
    results = []  
    for column in df.select_dtypes(include=['object', 'category']).columns:
        frequency_table = df[column].value_counts()
        percentage_table = np.round(df[column].value_counts(normalize=True) * 100,2)

        distribution = pd.DataFrame({
            'Column': column,
            'Value': frequency_table.index,
            'Count': frequency_table.values,
            'Percentage': percentage_table.values
        })
        distribution = distribution.sort_values(by='Percentage', ascending=ascending)
        results.append(distribution)
    final_df = pd.concat(results, ignore_index=True)
    return final_df

def clean_sheet_name(name):
    import re
    # Remove invalid characters
    name = re.sub(r'[:\\/?*\[\]]', '', name)
    # Limit to 31 characters
    name = name.strip()[:31]
    return name

def freqdist_to_excel(df, output_path, sort_by='Percentage', ascending=False, top_n=None):
    import pandas as pd
    import numpy as np
    used_names = set()
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        for column in df.select_dtypes(include=['object', 'category']).columns:
            frequency_table = df[column].value_counts()
            percentage_table = df[column].value_counts(normalize=True) * 100

            distribution = pd.DataFrame({
                'Value': frequency_table.index,
                'Count': frequency_table.values,
                'Percentage': percentage_table.values
            })
            distribution = distribution.sort_values(by=sort_by, ascending=ascending)
            if top_n is not None:
                distribution = distribution.head(top_n)
            # Generate safe sheet name
            base_name = clean_sheet_name(column)
            sheet_name = base_name
            count = 1
            while sheet_name.lower() in used_names:
                sheet_name = f"{base_name[:28]}_{count}"  # stay within 31 char limit
                count += 1
            used_names.add(sheet_name.lower())
            distribution.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"Frequency distributions written to {output_path}")

def normcheck_dashboard(df, significance_level=0.05, figsize=(18, 5)):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    import statsmodels.api as sm
    from scipy.stats import anderson
    import math
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        print("No numeric columns to analyze.")
        return
    for col in numeric_cols:
        data = df[col].dropna()
        print(f"\n--- Variable: {col} ---")
        if len(data) < 8:
            print("Not enough data to perform Anderson-Darling test or meaningful plots.")
            continue
        # Anderson-Darling Test
        test_result = anderson(data, dist='norm')
        stat = test_result.statistic
        sig_levels = test_result.significance_level
        crit_values = test_result.critical_values
        level_diff = [abs(sl - (significance_level * 100)) for sl in sig_levels]
        closest_index = level_diff.index(min(level_diff))
        used_sig = sig_levels[closest_index]
        crit_val = crit_values[closest_index]
        decision = "Fail to Reject Null" if stat <= crit_val else "Reject Null"
        # Print Summary
        print(f"  Anderson-Darling Statistic : {stat:.4f}")
        print(f"  Critical Value (@ {used_sig}%) : {crit_val:.4f}")
        print(f"  Decision : {decision}")
        # Plots (QQ, Histogram, Boxplot)
        fig, axes = plt.subplots(1, 3, figsize=figsize)
        # QQ Plot
        sm.qqplot(data, line='s', ax=axes[0])
        axes[0].set_title(f"QQ Plot - {col}")
        # Histogram (No KDE)
        sns.histplot(data, bins=30, kde=False, color='gray', alpha=0.3, ax=axes[1])
        axes[1].set_title(f"Histogram - {col}")
        # Boxplot
        sns.boxplot(x=data, ax=axes[2], color='lightblue')
        axes[2].set_title(f"Boxplot - {col}")
        axes[2].set_xlabel(col)
        plt.suptitle(f"Normality Assessment - {col}", fontsize=14, y=1.05)
        plt.tight_layout()
        plt.show()

COLOR_PALETTES = {
    "teal": {
        "neutral": "#8EC1C7",
        "highlight": "#2F6F73",
        "figure_bg": "#E9F4F6",
        "axes_bg": "#D4F1F4",
        "title_color": "#1B4F56",
        "x_color": "#1B4F56",
        "y_color": "#1B4F56"
    },
    "rose": {
        "neutral": "#f29db4",
        "highlight": "#D97199",
        "figure_bg": "#f7f7f7",
        "axes_bg": "#F4E5E3",
        "title_color": "#710019",
        "x_color": "#710019",
        "y_color": "#710019"
    },
    "dark_blue": {
        "neutral": "#5B7DB1",
        "highlight": "#2E4C6D",
        "figure_bg": "#EAEFF5",
        "axes_bg": "#D9EDF8",
        "title_color": "#2E4C6D",
        "x_color": "#2E4C6D",
        "y_color": "#2E4C6D"
    },
    "earth": {
        "neutral": "#A68A64",
        "highlight": "#5C4033",
        "figure_bg": "#EFE6D8",
        "axes_bg": "#F7F1E8",
        "title_color": "#5C4033",
        "x_color": "#5C4033",
        "y_color": "#5C4033"
    },
    "mono": {
        "neutral": "#9E9E9E",
        "highlight": "#212121",
        "figure_bg": "#F5F5F5",
        "axes_bg": "#FFFFFF",
        "title_color": "#212121",
        "x_color": "#212121",
        "y_color": "#212121"
    },
    "dawn": {
        "neutral": "#EBC490",
        "highlight": "#AA6A40",
        "figure_bg": "#F5F5F5",
        "axes_bg": "#F2E8D0",
        "title_color": "#AA6A40",
        "x_color": "#AA6A40",
        "y_color": "#AA6A40"
    },
    "stern": {
        "neutral": "#c7ced6",
        "highlight": "#7E7C7F",
        "figure_bg": "#F5F5F5",
        "axes_bg": "#F4EEDC",
        "title_color": "#7E7C7F",
        "x_color": "#7E7C7F",
        "y_color": "#7E7C7F"
    }
}



def purvis_col(
    df,
    category_col='Category',
    value_col='Value',
    top_n=1,
    mode='top',  # 'top' or 'bottom'
    palette='teal',
    title='Insert title Here',
    xlabel='Indicate xlabel',
    ylabel='Indicate ylabel',
    figsize=(8, 5),
    label_offset=0.15
):
    import matplotlib.pyplot as plt
    if palette not in COLOR_PALETTES:
        raise ValueError(
            f"Palette '{palette}' not found. "
            f"Available: {list(COLOR_PALETTES.keys())}"
        )
    if mode not in ('top', 'bottom'):
        raise ValueError("mode must be either 'top' or 'bottom'")

    if top_n < 1 or top_n > len(df):
        raise ValueError("top_n must be between 1 and number of columns")

    colorset = COLOR_PALETTES[palette]

    # 🔹 Select indices based on mode
    if mode == 'top':
        indices = df[value_col].nlargest(top_n).index
        ref_value = df[value_col].max()
    else:
        indices = df[value_col].nsmallest(top_n).index
        ref_value = df[value_col].max()  # still use max for ylim

    # Bar colors
    colors = [colorset["neutral"]] * len(df)
    for idx in indices:
        colors[idx] = colorset["highlight"]

    # Figure setup
    plt.figure(figsize=figsize)
    plt.gcf().patch.set_facecolor(colorset["figure_bg"])
    ax = plt.gca()
    ax.set_facecolor(colorset["axes_bg"])

    bars = plt.bar(df[category_col], df[value_col], color=colors)

    # Titles and labels
    plt.title(title, fontsize=16, weight='bold', color=colorset["title_color"])
    plt.xlabel(xlabel, color=colorset["x_color"])
    plt.ylabel(ylabel, color=colorset["y_color"])

    # Label highlighted bars
    for idx in indices:
        bar = bars[idx]
        value = df.loc[idx, value_col]
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            value + (ref_value * 0.02),
            str(value),
            ha='center',
            va='bottom',
            fontsize=14,
            fontweight='bold'
        )
    # Y-axis padding
    plt.ylim(0, ref_value * (1 + label_offset))
    plt.tight_layout()
    plt.show()


def purvis_bar(
    df,
    category_col='Category',
    value_col='Value',
    top_n=1,
    mode='top',  # NEW: 'top' or 'bottom'
    palette='rose',
    title='Unit Tardiness during Annual Operations',
    xlabel='Tardiness',
    figsize=(9, 6),
    label_offset=0.03
):
    import matplotlib.pyplot as plt
    if palette not in COLOR_PALETTES:
        raise ValueError(
            f"Palette '{palette}' not found. "
            f"Available: {list(COLOR_PALETTES.keys())}"
        )
    if mode not in ('top', 'bottom'):
        raise ValueError("mode must be either 'top' or 'bottom'")

    if top_n < 1 or top_n > len(df):
        raise ValueError("top_n must be between 1 and number of bars")

    colorset = COLOR_PALETTES[palette]

    # 🔹 Select indices based on mode
    if mode == 'top':
        indices = df[value_col].nlargest(top_n).index
    else:
        indices = df[value_col].nsmallest(top_n).index

    max_value = df[value_col].max()

    # Bar colors
    colors = [colorset["neutral"]] * len(df)
    for idx in indices:
        colors[idx] = colorset["highlight"]

    # Figure setup
    plt.figure(figsize=figsize)
    plt.gcf().patch.set_facecolor(colorset["figure_bg"])
    ax = plt.gca()
    ax.set_facecolor(colorset["axes_bg"])

    # Plot horizontal bars
    bars = plt.barh(df[category_col], df[value_col], color=colors)

    # Titles and labels
    plt.title(title, fontsize=16, weight='bold', color=colorset["title_color"])
    plt.xlabel(xlabel, color=colorset["x_color"])

    # Label highlighted bars
    for idx in indices:
        bar = bars[idx]
        value = df.loc[idx, value_col]
        plt.text(
            value + (max_value * label_offset),
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va='center',
            fontsize=11,
            fontweight='bold'
        )
    # X-axis padding
    plt.xlim(0, max_value * (1 + label_offset * 5))
    plt.tight_layout()
    plt.show()

def purvis_line(
    df,
    x_col='Month',
    y_col='Sales',
    title='Monthly Sales',
    xlabel=None,
    ylabel=None,
    mode='top',             # 'top','bottom','both'
    top_n=3,                # number of labels to display
    light_grid=True,
    line_width=2,
    marker_shape='o',
    palette=None,
    figsize=(10,6),
    annotations=None
):
    import matplotlib.pyplot as plt
    import pandas as pd
    # Handle palette
    if isinstance(palette, str):
        if palette not in COLOR_PALETTES:
            raise ValueError(f"Palette '{palette}' not found in PALETTES dictionary.")
        palette = COLOR_PALETTES[palette]
    elif palette is None:
        palette = {
            "neutral": "#7CB7AF",
            "highlight": "#16796F",
            "figure_bg": "white",
            "axes_bg": "white",
            "title_color": "#16796F",
            "x_color": "#16796F",
            "y_color": "#16796F"
        }
    xlabel = xlabel or x_col
    ylabel = ylabel or y_col
    n_points = len(df)
    max_value = df[y_col].max()
    fig, ax = plt.subplots(figsize=figsize)
    # Backgrounds
    fig.patch.set_facecolor(palette.get("figure_bg","white"))
    ax.set_facecolor(palette.get("axes_bg","white"))
    # Numeric positions for categorical x-axis
    x_pos = list(range(n_points))
    # Plot line
    ax.plot(
        x_pos,
        df[y_col],
        marker=marker_shape,
        linewidth=line_width,
        markersize=6,
        color=palette["highlight"],
        alpha=0.85
    )
    # Fill under line
    ax.fill_between(
        x_pos,
        df[y_col],
        color=palette["neutral"],
        alpha=0.6
    )
    # Determine indices to label
    label_indices = []
    if top_n > 0:
        if mode == 'top':
            label_indices = df[y_col].nlargest(top_n).index.tolist()
        elif mode == 'bottom':
            label_indices = df[y_col].nsmallest(top_n).index.tolist()
        elif mode == 'both':
            top_indices = df[y_col].nlargest(top_n).index.tolist()
            bottom_indices = df[y_col].nsmallest(top_n).index.tolist()
            # Merge unique indices to avoid duplicates if overlap
            label_indices = list(set(top_indices + bottom_indices))
        else:
            raise ValueError("mode must be 'top', 'bottom', or 'both'")
    # Draw data labels
    for i in range(n_points):
        if i in label_indices:
            ax.text(
                x_pos[i],
                df[y_col].iloc[i] + max_value*0.03,
                str(df[y_col].iloc[i]),
                ha='center',
                va='bottom',
                fontsize=10,
                fontweight='bold',
                color=palette["highlight"]
            )
    # Custom annotations
    if annotations:
        for ann in annotations:
            wrapped_text = "\n".join(ann["text"].split())
            idx = df.index[df[x_col] == ann["x"]][0]
            ax.annotate(
                wrapped_text,
                xy=(x_pos[idx], df[y_col].iloc[idx] + max_value*0.03),
                xytext=(0, max_value*0.05),
                textcoords="offset points",
                ha='center',
                fontsize=7,
                fontweight='bold',
                color=palette["highlight"]
            )
    # Titles & labels
    ax.set_title(title, fontsize=16, fontweight='bold', color=palette["title_color"])
    ax.set_xlabel(xlabel, fontsize=12, color=palette["x_color"])
    ax.set_ylabel(ylabel, fontsize=12, color=palette["y_color"])
    # X-axis ticks
    ax.set_xticks(x_pos)
    ax.set_xticklabels(df[x_col])
    ax.tick_params(axis='x', colors=palette["x_color"])
    ax.tick_params(axis='y', colors=palette["y_color"])
    # Grid
    ax.grid(alpha=0.15 if light_grid else 0.4, color=palette["highlight"])
    # Y-axis padding
    ax.set_ylim(0, max_value*1.15)
    plt.tight_layout()
    plt.show()