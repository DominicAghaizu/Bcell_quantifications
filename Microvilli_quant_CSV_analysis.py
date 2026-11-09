import numpy as np
import glob
import csv
import re
import os
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import linregress
import matplotlib.patches as mpatches  # To create custom legend handles



config = {
    'condition_folders': {
        'Moesin': 'E:\HU postdoc\Science\Data\B-cell imaging\B cell revision imaging\-spin\MV Analysis Asyas script\Phal, Moesin',
        'CD45': 'E:\HU postdoc\Science\Data\B-cell imaging\B cell revision imaging\-spin\MV Analysis Asyas script\Phal, CD45',
        'Moesin': 'E:\HU postdoc\Science\Data\B-cell imaging\B cell revision imaging\-spin\MV Analysis Asyas script\Phal, Moesin',
        'CD45': 'E:\HU postdoc\Science\Data\B-cell imaging\B cell revision imaging\-spin\MV Analysis Asyas script\Phal, CD45',
    },
    'plot_params': {
        'figsize': (16, 8),
        'title': 'Violin plot of profile lengths by condition and channel',
        'xlabel': 'Condition',
        'ylabel': 'Length (µm)',
        'legend_title': 'Channel',
        'channel_labels': {
            'Channel1': 'Actin',
            'Channel2': 'PhosphoProtein'
        },
        'violin_params': {
            'split': True,
            'inner': 'quartile'
        },
        'boxplot_params': {
            'width': 0.3
        },
        'font_params': {
            'title_size': 16,
            'label_size': 16,
            'legend_size': 16,  # Font size of legend items
            'legend_caption_size': 16,  # Font size of legend caption/title
            'annotation_size': 16,
            'tick_size': 15
        },
        'colors': {
            'Actin': 'lightblue',
            'PhosphoProtein': 'lightpink'
        }
    }
}

def clean_and_parse(profile_str):
    profile_str = profile_str.strip('[]')
    profile_str = re.sub(r'[,\s]+', ',', profile_str)
    try:
        result = [float(x) for x in profile_str.split(',') if x]
        return result
    except ValueError as e:
        print(f"Error parsing profile string: {profile_str}")
        print(e)
        return []

def load_profiles_from_csv(filename):
    profiles1 = []
    profiles2 = []
    z_spacing = None

    with open(filename, 'r', encoding='ISO-8859-1') as csvfile:
        csvreader = csv.reader(csvfile)
        
        for row in csvreader:
            if row and row[0].startswith('Z-spacing'):
                z_spacing = float(row[1])
                break
        
        next(csvreader, None)
        next(csvreader, None)
        
        current_profile1 = []
        current_profile2 = []

        for row in csvreader:
            if not row:
                continue
            
            try:
                if row[0].startswith('Blob'):
                    if current_profile1 or current_profile2:
                        profiles1.append(current_profile1)
                        profiles2.append(current_profile2)
                    
                    current_profile1 = []
                    current_profile2 = []
                    
                    profile1_str = row[1].strip()
                    profile2_str = row[2].strip()

                    current_profile1 = clean_and_parse(profile1_str)
                    current_profile2 = clean_and_parse(profile2_str)
                
            except (ValueError, IndexError, SyntaxError) as e:
                print(f"Error processing row: {row}")
                print(e)
        
        if current_profile1 or current_profile2:
            profiles1.append(current_profile1)
            profiles2.append(current_profile2)
    
    return profiles1, profiles2, z_spacing

def calculate_profile_lengths(profiles, z_spacing):
    return [len(profile) * z_spacing for profile in profiles]

# Create dictionaries to store data for each condition
conditions_data = {}
summary_info = []

for condition_name, folder in config['condition_folders'].items():
    if not os.path.exists(folder):
        print(f"Folder not found for condition '{condition_name}', skipping...")
        continue
    
    grouped_lengths = {'lengths1': [], 'lengths2': [], 'counts1': 0, 'counts2': 0, 'num_cells': 0}
    
    csv_files = glob.glob(os.path.join(folder, '*.csv'))
    num_cells = len(csv_files)
    grouped_lengths['num_cells'] = num_cells
    
    for filename in csv_files:
        profiles1, profiles2, z_spacing = load_profiles_from_csv(filename)
        lengths1 = calculate_profile_lengths(profiles1, z_spacing)
        lengths2 = calculate_profile_lengths(profiles2, z_spacing)
    
        adjusted_lengths2 = [min(l2, l1) for l1, l2 in zip(lengths1, lengths2)]
    
        grouped_lengths['lengths1'].extend(lengths1)
        grouped_lengths['lengths2'].extend(adjusted_lengths2)
        grouped_lengths['counts1'] += len(lengths1)
        grouped_lengths['counts2'] += len(lengths2)
    
    num_mvs = grouped_lengths['counts1']
    mvs_per_cell = grouped_lengths['counts1'] / num_cells if num_cells > 0 else 0
    
    conditions_data[condition_name] = grouped_lengths

    # Scatter plot preparation
    actin_lengths = grouped_lengths['lengths1']
    phospho_lengths = grouped_lengths['lengths2']

    min_length = min(len(actin_lengths), len(phospho_lengths))
    actin_lengths = actin_lengths[:min_length]
    phospho_lengths = phospho_lengths[:min_length]

    ratios = np.array(phospho_lengths) / np.array(actin_lengths)
    
    # Create plot for each condition
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.scatter(actin_lengths, ratios, color='purple', alpha=0.6)
    plt.title(f'Ratio of PhosphoProtein/Actin vs. Actin Length for {condition_name}')
    plt.xlabel('Actin Length (µm)')
    plt.ylabel('Ratio (PhosphoProtein / Actin)')
    plt.grid(True)
    
    plt.subplot(1, 2, 2)
    length_categories = pd.qcut(actin_lengths, q=3, labels=['Short', 'Medium', 'Long'])
    sns.scatterplot(x=phospho_lengths, y=actin_lengths, hue=length_categories, palette='viridis', alpha=0.9, edgecolor='w')
    
    slope, intercept, r_value, p_value, std_err = linregress(phospho_lengths, actin_lengths)
    plt.plot(phospho_lengths, intercept + slope * np.array(phospho_lengths), color='red', label=f'Regression Line (R²={r_value**2:.2f})')
    
    plt.title(f'Plot for {condition_name} (PhosphoProtein vs Actin)')
    plt.xlabel('PhosphoProtein Length (µm)')
    plt.ylabel('Actin Length (µm)')
    plt.legend(title='Length Category')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    plt.close()

    # Add Contour Plot
    plt.figure(figsize=(10, 6))
    sns.kdeplot(x=phospho_lengths, y=actin_lengths, cmap="bone", fill=True)
    plt.title(f'Contour Plot for {condition_name} (PhosphoProtein vs Actin)')
    plt.xlabel('PhosphoProtein Length (µm)')
    plt.ylabel('Actin Length (µm)')
    plt.grid(True)
    plt.show()

    # Add average lengths to summary_info
    avg_actin_length = np.mean(grouped_lengths['lengths1']) if grouped_lengths['lengths1'] else 0
    avg_phospho_length = np.mean(grouped_lengths['lengths2']) if grouped_lengths['lengths2'] else 0
    
    summary_info.append(
        f"Condition: {condition_name}\n"
        f"Number of cells: {num_cells}\n"
        f"Total number of MVs: {num_mvs}\n"
        f"Average number of MVs per cell: {mvs_per_cell:.2f}\n"
        f"Regression Line (R²={r_value**2:.2f})\n"
        f" p-Value ~~ {p_value:.4f}\n"
        f"Average Actin Length: {avg_actin_length:.2f} µm\n"
        f"Average PhosphoProtein Length: {avg_phospho_length:.2f} µm"
    )





'''

you can comment out the next part up until line "num_summary_plots"


'''



# Extract data for both pLCK 10min and pLCK 5min
#plck_10min_data = conditions_data['pLCK 10min']
#plck_5min_data = conditions_data['pLCK 5min']

# Get lengths for both Actin and PhosphoProtein
#plck_10min_actin_lengths = plck_10min_data['lengths1']
#plck_10min_phospho_lengths = plck_10min_data['lengths2']

#plck_5min_actin_lengths = plck_5min_data['lengths1']
#plck_5min_phospho_lengths = plck_5min_data['lengths2']

# Create a combined contour plot for both conditions
plt.figure(figsize=(10, 6))

# Contour plot for pLCK 10min
#sns.kdeplot(x=plck_10min_phospho_lengths, y=plck_10min_actin_lengths, cmap="viridis", fill=True, label='pLCK 10min', alpha=0.5)

# Contour plot for pLCK 5min
#sns.kdeplot(x=plck_5min_phospho_lengths, y=plck_5min_actin_lengths, cmap="bone", fill=True, label='pLCK 5min', alpha=0.5)

# Add plot details
plt.title('Contour Plot for pLCK 10min and pLCK 5min (PhosphoProtein vs Actin)', fontsize=16)
plt.xlabel('PhosphoProtein Length (µm)', fontsize=14)
plt.ylabel('Actin Length (µm)', fontsize=14)
plt.grid(True)



# Create custom legend handles
pLCK_10min_patch = mpatches.Patch(color="purple", label='pLCK 10min')
pLCK_5min_patch = mpatches.Patch(color="grey", label='pLCK 5min')

# Manually add the legend with custom handles
plt.legend(handles=[pLCK_10min_patch, pLCK_5min_patch], title='Conditions', loc='upper right')

# Add a legend
#plt.legend(['pLCK 10min', 'pLCK 5min'])

# Show the plot
plt.show()





# Summary plot for all conditions
num_summary_plots = len(summary_info)
nrows = 2
ncols = 2
fig, axs = plt.subplots(nrows, ncols, figsize=(11, 4))
fig.subplots_adjust(hspace=0.2, wspace=0.00)  # Adjust the spacing between subplots

# Flatten the axes array for easier indexing
axs = axs.flatten()

for i in range(nrows * ncols):
    if i < num_summary_plots:
        axs[i].text(0.5, 0.5, summary_info[i], fontsize=12, ha='center', va='center', 
                    bbox=dict(facecolor='white', edgecolor='lightblue', boxstyle='square,pad=1'))
        axs[i].axis('off')
    else:
        axs[i].axis('off')  # Turn off unused subplots

plt.tight_layout(rect=[0, 0.1, 0, 0.8])  
#plt.savefig('summary_results.png')
plt.show()

# Prepare data for violin and box plots
plot_data = []
for condition, data in conditions_data.items():
    lengths1 = data['lengths1']
    lengths2 = data['lengths2']
    
    # Add lengths to the plot data
    plot_data.extend({'Condition': condition, 'Channel': 'Channel1', 'Length': length} for length in lengths1)
    plot_data.extend({'Condition': condition, 'Channel': 'Channel2', 'Length': length} for length in lengths2)

df = pd.DataFrame(plot_data)

# Map the channel names to custom labels
df['Channel'] = df['Channel'].map(config['plot_params']['channel_labels'])

# Create a figure with two subplots
fig, axs = plt.subplots(1, 2, figsize=config['plot_params']['figsize'], sharey=True)

# Violin plot
sns.violinplot(x='Condition', y='Length', hue='Channel', data=df, ax=axs[0],
               **config['plot_params']['violin_params'], palette=config['plot_params']['colors'])
axs[0].set_title(config['plot_params']['title'], fontsize=config['plot_params']['font_params']['title_size'])
axs[0].set_xlabel(config['plot_params']['xlabel'], fontsize=config['plot_params']['font_params']['label_size'])
axs[0].set_ylabel(config['plot_params']['ylabel'], fontsize=config['plot_params']['font_params']['label_size'])
axs[0].legend(title=config['plot_params']['legend_title'], title_fontsize=config['plot_params']['font_params']['legend_caption_size'],
              fontsize=config['plot_params']['font_params']['legend_size'])
axs[0].grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)  # Add light grid to the first subplot

# Box plot
sns.boxplot(x='Condition', y='Length', hue='Channel', data=df, ax=axs[1], palette=config['plot_params']['colors'],
            width=config['plot_params']['boxplot_params']['width'])
axs[1].set_title(config['plot_params']['title'], fontsize=config['plot_params']['font_params']['title_size'])
axs[1].set_xlabel(config['plot_params']['xlabel'], fontsize=config['plot_params']['font_params']['label_size'])
axs[1].set_ylabel(config['plot_params']['ylabel'], fontsize=config['plot_params']['font_params']['label_size'])
axs[1].legend(title=config['plot_params']['legend_title'], title_fontsize=config['plot_params']['font_params']['legend_caption_size'],
              fontsize=config['plot_params']['font_params']['legend_size'])
axs[1].grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)  # Add light grid to the second subplot

plt.tight_layout()
plt.show()

# Function to calculate average lengths
def calculate_average_lengths(df):
    # Group the data by condition and channel, and calculate the mean length
    averages = df.groupby(['Condition', 'Channel'])['Length'].mean().reset_index()
    
    # Pivot the table to get a more readable format
    pivot_averages = averages.pivot(index='Condition', columns='Channel', values='Length').reset_index()
    
    return pivot_averages

# Calculate and print average lengths
average_lengths_df = calculate_average_lengths(df)
print(average_lengths_df)

