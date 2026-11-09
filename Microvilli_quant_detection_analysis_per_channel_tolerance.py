# -*- coding: utf-8 -*-
"""
Created on Wed Aug  7 14:02:12 2024

@author: bio_polatasy
"""

import imageio
import numpy as np
import os
import csv
import matplotlib.pyplot as plt
from scipy.ndimage import fourier_shift, gaussian_laplace, median_filter
from scipy.fftpack import fftn, ifftn
from skimage import restoration
from skimage.feature import peak_local_max
from skimage.filters import gaussian
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from skimage.draw import disk



CONFIG = {
    'center_z': 42,                     # at which z layer do the microvillis look the best? 
    'start_layer': 39,                   # at which z layer does the substrate surface layer start/beginning of the pores 
    'sigma': 1.5,                       # radius of the microvilli for the detection
    'intensity_threshold':900,          # are those actually microivlli youre detecting? if not, raise threshold
    'percentile_threshold': 80,         # does your cell mask look good? is it really showing the cell
    'z_spacing': 0.15,                  # spacing between each layer in micrometer
    'rolling_ball_radius': 4 ,          # check rolling ball filter image. cut out spaces should be around the same size as MV
    'tolerance_factor_channel1': 1.5,  # Separate tolerance factor for Channel 1
    'tolerance_factor_channel2': 1.0       # background threshold for MV length CUT OFF. either 0.5, 1 or 2. depends on experiment
}


shift_correction_enabled = False  # Set to True when you want to enable shift correction

# Function to read a multi-layer TIFF stack
def read_tiff_stack(file_path):
    return imageio.volread(file_path)

# Find subpixel shift using phase correlation
def find_subpixel_shift(img1, img2):
    img1_ft = fftn(img1)
    img2_ft = fftn(img2)
    cross_power_spectrum = (img1_ft * np.conj(img2_ft)) / np.abs(img1_ft * np.conj(img2_ft))
    cross_correlation = np.abs(ifftn(cross_power_spectrum))
    maxima = np.unravel_index(np.argmax(cross_correlation), cross_correlation.shape)
    shifts = np.array(maxima, dtype=np.float64)
    shifts[shifts > np.array(img1.shape) // 2] -= np.array(img1.shape)[shifts > np.array(img1.shape) // 2]
    return shifts

# Apply subpixel shift with Fourier transform
def apply_shift(image, shift):
    return np.real(ifftn(fourier_shift(fftn(image), shift)))

# Normalize image
def normalize_image(image):
    return (image - np.min(image)) / (np.max(image) - np.min(image))

def detect_blobs(image, sigma=3.5, intensity_threshold=80, filter_size=5):
    blobs = []
    filtered_image = median_filter(image, size=filter_size)
    smoothed_image = gaussian(filtered_image, sigma=1.0)
    log_image = gaussian_laplace(smoothed_image, sigma=sigma)
    log_image = log_image ** 2
    log_image_normalized = normalize_image(log_image)
    
    imgmin = np.min(image)
    local_maxima = peak_local_max(log_image_normalized, exclude_border=False)
    
    for loc in local_maxima:
        y, x = loc
        if image[y, x] > imgmin + intensity_threshold:
            blobs.append((y, x, sigma))
    
    print(f"Blobs detected: {len(blobs)}")
    return blobs, log_image_normalized, filtered_image

def create_blob_mask(blobs, shape):
    mask = np.zeros(shape, dtype=bool)
    
    for blob in blobs:
        y, x, r = blob
        rr, cc = disk((int(y), int(x)), int(r))
        rr = np.clip(rr, 0, shape[0] - 1)
        cc = np.clip(cc, 0, shape[1] - 1)
        mask[rr, cc] = True
    
    return mask

def create_cell_mask(stack, start_layer, blob_mask):
    cell_mask = np.zeros_like(stack[0], dtype=bool)
    
    selem_radius = 2
    
    for z in range(start_layer, stack.shape[0]):
        layer = stack[z]
        threshold = np.percentile(layer, CONFIG['percentile_threshold'])
        layer_mask = (layer > threshold)
        
        refined_mask = layer_mask & ~blob_mask
        
        for blob in blobs:
            y, x, _ = blob
            rr, cc = disk((y, x), selem_radius)
            rr = np.clip(rr, 0, stack[0].shape[0] - 1)
            cc = np.clip(cc, 0, stack[0].shape[1] - 1)
            cell_mask[rr, cc] = False
        
        cell_mask |= refined_mask
    return cell_mask




def extract_profiles(blobs, stack, radii, background_data, start_layer, tolerance_factor=1.5):
    profiles = []
    valid_blobs = []

    background_means, background_std_devs = background_data

    for i, blob in enumerate(blobs):
        y, x, r = blob
        profile = []
        for z in range(start_layer, stack.shape[0]):
            region = stack[z, int(y - r):int(y + r + 1), int(x - r):int(x + r + 1)]
            intensity = np.mean(region)

            if z - start_layer < len(background_means) and not np.isnan(background_means[z - start_layer]):
                threshold = background_means[z - start_layer]
                tolerance = tolerance_factor * background_std_devs[z - start_layer]

            if np.abs(intensity - threshold) < tolerance:
                break
            profile.append(intensity)
        
        if len(profile) > 1:
            profiles.append(np.array(profile))
            valid_blobs.append(blob)
    
    print(f"Valid blobs after filtering: {len(valid_blobs)}")
    return profiles, valid_blobs







def apply_rolling_ball_filter(image, radius):
    try:
        background = restoration.rolling_ball(image, radius=radius)
        return image - background 
    except Exception as e:
        print(f"Error applying rolling ball filter: {e}")
        return image




def calculate_average_background(channel_stack, blob_mask, cell_mask, start_layer):
    backgrounds = []
    std_devs = []
    
    for z in range(start_layer, channel_stack.shape[0]):
        layer = channel_stack[z]
        combined_mask = cell_mask & ~blob_mask
        background_values = layer[combined_mask]
        
        if len(background_values) > 0:
            avg_background = np.mean(background_values)
            std_dev_background = np.std(background_values)
            backgrounds.append(avg_background)
            std_devs.append(std_dev_background)
        else:
            backgrounds.append(np.nan)
            std_devs.append(np.nan)
    
    return [backgrounds, std_devs]






def calculate_average_length(profiles):
    lengths = [len(profile) for profile in profiles]
    average_length = np.mean(lengths) if lengths else 0
    return average_length





def save_profiles_to_csv(profiles1, profiles2, z_spacing, filename='profiles.csv', save_path='.'):
    full_path = os.path.join(save_path, filename)
    with open(full_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Metadata'])
        csvwriter.writerow(['Z-spacing (µm)', CONFIG['z_spacing']])
        csvwriter.writerow([])  # Empty row
        csvwriter.writerow(['Blob', 'Profile Channel 1', 'Profile Channel 2'])
        for i, (profile1, profile2) in enumerate(zip(profiles1, profiles2)):
            csvwriter.writerow([f'Blob {i + 1}', profile1.tolist(), profile2.tolist()])

  # Toggle this flag to control shift correction

# Open file dialog to select the TIFF stack file
Tk().withdraw()
file_path = askopenfilename(title="Select the TIFF file", filetypes=[("TIFF files", "*.tif *.tiff")])

if file_path:
    # Read the TIFF stack
    tiff_stack = read_tiff_stack(file_path)
    print(f"TIFF stack shape: {tiff_stack.shape}")

    # Separate the stack into two color channels
    channel1_stack = tiff_stack[:, 0, :, :]  # Assuming first channel is at index 0
    channel2_stack = tiff_stack[:, 1, :, :]  # Assuming second channel is at index 1

    # Use configuration parameters
    center_z = CONFIG['center_z']
    start_layer = CONFIG['start_layer']

    if center_z is None or center_z < 0 or center_z >= tiff_stack.shape[0] or start_layer is None or start_layer < 0 or start_layer >= tiff_stack.shape[0]:
        print("Invalid z-layer index. Exiting.")
        exit()

    # Initialize the corrected stacks
    corrected_channel1_stack = None
    corrected_channel2_stack = None

    # Check if shift correction is enabled before applying it
    if shift_correction_enabled:
        # Calculate the shift using the center z-layer
        img1_center = normalize_image(channel1_stack[center_z])
        img2_center = normalize_image(channel2_stack[center_z])

        subpixel_shift = find_subpixel_shift(img1_center, img2_center)
        print(f"Center Z-layer {center_z}: Detected subpixel shift (y, x): {subpixel_shift}")

        # Apply the subpixel shift to the entire stack
        corrected_channel1_stack = np.array([apply_shift(image, subpixel_shift) for image in channel1_stack])
        corrected_channel2_stack = np.array([apply_shift(image, subpixel_shift) for image in channel2_stack])
    else:
        # If shift correction is not enabled, just apply the rolling ball filter without shifting
        corrected_channel1_stack = np.array([apply_rolling_ball_filter(image, radius=CONFIG['rolling_ball_radius']) for image in channel1_stack])
        corrected_channel2_stack = np.array([apply_rolling_ball_filter(image, radius=CONFIG['rolling_ball_radius']) for image in channel2_stack])


# Corrected stack for channel 2
    corrected_channel2_stack_raw = np.array([normalize_image(image) for image in corrected_channel2_stack])


    norm_corrected_channel1_stack = np.array([normalize_image(image) for image in corrected_channel1_stack])
    norm_corrected_channel2_stack = np.array([normalize_image(image) for image in corrected_channel2_stack_raw])

    # Detect blobs in the corrected center z-layer image for Channel 1
    blobs, log_image_normalized, filtered_image = detect_blobs(corrected_channel1_stack[center_z], sigma=CONFIG['sigma'], intensity_threshold=CONFIG['intensity_threshold'])
    
    if len(blobs) == 0:
        print("No blobs detected. Try adjusting the parameters.")
        exit()
    
    # Create blob mask for Channel 1
    blob_mask = create_blob_mask(blobs, corrected_channel1_stack[center_z].shape)
    
    # Create cell mask
    cell_mask = create_cell_mask(corrected_channel1_stack, start_layer, blob_mask)
    
    # Calculate average background for both channels
    background_thresholds_channel1 = calculate_average_background(corrected_channel1_stack, blob_mask, cell_mask, start_layer)
    background_thresholds_channel2 = calculate_average_background(corrected_channel2_stack, blob_mask, cell_mask, start_layer)
    
    # Unpack the result
    background_means, background_std_devs = background_thresholds_channel1
    background_means2, background_std_devs2 = background_thresholds_channel2
    
        # Extract profiles for each detected blob
    # Extract profiles for each detected blob
    profiles_channel1, valid_blobs_channel1 = extract_profiles(
        blobs, corrected_channel1_stack, CONFIG['sigma'], 
        (background_means, background_std_devs), start_layer, 
        tolerance_factor=CONFIG['tolerance_factor_channel1']
    )
    
    profiles_channel2, valid_blobs_channel2 = extract_profiles(
        blobs, corrected_channel2_stack, CONFIG['sigma'], 
        (background_means2, background_std_devs2), start_layer, 
        tolerance_factor=CONFIG['tolerance_factor_channel2']
    )



    """
    # Extract profiles for each detected blob
    profiles_channel1 = extract_profiles(blobs, corrected_channel1_stack, CONFIG['sigma'], (background_means, background_std_devs), start_layer)
    profiles_channel2 = extract_profiles(blobs, corrected_channel2_stack_raw, CONFIG['sigma'], (background_means2, background_std_devs2), start_layer)
    """
    # Calculate max intensity for each profile
 #  maxI_channel1 = calculate_maxI(profiles_channel1)
  #  maxI_channel2 = calculate_maxI(profiles_channel2)
    
    # Calculate average length of profiles
    avg_length_channel1 = calculate_average_length(profiles_channel1)
    avg_length_channel2 = calculate_average_length(profiles_channel2)
    
        # Example: use the center slice of channel 1 for visualization
    test_image = corrected_channel1_stack[center_z]

    

    # Apply rolling ball filter
    background = restoration.rolling_ball(test_image, radius=CONFIG['rolling_ball_radius'])
    filtered_image = test_image - background
    # Plot the blob detection results
    plt.figure(figsize=(12, 8))
    
    """
    plt.subplot(2, 3, 1)
    plt.imshow(log_image_normalized, cmap='gray')
    plt.title('Log Image Normalized')
    plt.scatter([b[1] for b in blobs], [b[0] for b in blobs], c='r', s=30, edgecolor='k')
    
    plt.subplot(2, 3, 2)
    plt.imshow(corrected_channel1_stack[center_z], cmap='gray')
    plt.title('Channel 1 Center Z-layer')
    plt.scatter([b[1] for b in blobs], [b[0] for b in blobs], c='r', s=30, edgecolor='k')
    """
    plt.subplot(1, 3, 1)
    plt.imshow(corrected_channel1_stack[center_z], cmap='gray')
    plt.title('Channel 1 Center Z-layer')
    plt.scatter([b[1] for b in blobs], [b[0] for b in blobs], c='r', s=30, edgecolor='k')
    
    
    plt.subplot(1, 3, 2)
    plt.title('Estimated Background')
    plt.imshow(background, cmap='gray')
    
    plt.subplot(1, 3, 3)
    plt.imshow(corrected_channel1_stack[center_z], cmap='gray')
    plt.imshow(cell_mask, cmap='Blues', alpha=0.5)  # Overlay cell mask in blue with transparency
    plt.title("Cell Mask Overlay")
    #plt.axis('off')
    '''
    plt.subplot(2, 3, 4)  # Add this subplot
    plt.imshow(apply_rolling_ball_filter(corrected_channel1_stack[center_z], radius=10), cmap='gray')
    plt.title('Channel 1 with Rolling Ball Filter')
    '''
    plt.tight_layout()
    plt.show()

    """
    # Plot original image and background
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 3, 1)
    plt.title('Original Image')
    plt.imshow(test_image, cmap='gray')
    
    plt.subplot(1, 3, 2)
    plt.title('Estimated Background')
    plt.imshow(background, cmap='gray')
    
    plt.subplot(1, 3, 3)
    plt.title('Filtered Image')
    plt.imshow(filtered_image, cmap='gray')
    
    plt.show()
    """


    
    # Convert background thresholds to numpy arrays for consistency
    background_thresholds_channel1 = np.array(background_thresholds_channel1)
    background_thresholds_channel2 = np.array(background_thresholds_channel2)
    
    # Plot individual intensity profiles for each blob across z-layers
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    
    
    # Determine the minimum number of valid blobs across both channels
    min_valid_blobs = min(len(profiles_channel1), len(profiles_channel2))
        # Plot individual intensity profiles for each blob across z-layers

    
    # Plot the profiles for Channel 1 and Channel 2
    if len(profiles_channel1) > 0:
        for i in range(len(profiles_channel1)):
            if len(profiles_channel1[i]) > 0:
                z_values1 = np.arange(len(profiles_channel1[i])) * CONFIG['z_spacing']
                axs[0, 0].plot(z_values1, profiles_channel1[i], color='blue', linestyle='--', alpha=0.7)
    else:
        print("No valid profiles found in profiles_channel1.")
    
    if len(profiles_channel2) > 0:
        for i in range(len(profiles_channel2)):
            if len(profiles_channel2[i]) > 0:
                z_values2 = np.arange(len(profiles_channel2[i])) * CONFIG['z_spacing']
                axs[0, 0].plot(z_values2, profiles_channel2[i], color='red', linestyle='-', alpha=0.7)
    else:
        print("No valid profiles found in profiles_channel2.")
    
    # Plot background thresholds
    if len(background_means) > 0:
        z_values_backgrounds = np.arange(len(background_means)) * CONFIG['z_spacing']
        axs[0, 0].plot(z_values_backgrounds, background_means, color='cyan', linestyle='--', label='Channel 1 Background')
        axs[0, 0].plot(z_values_backgrounds, background_means2, color='magenta', linestyle='-', label='Channel 2 Background')
    
        # Fill between standard deviations
        axs[0, 0].fill_between(z_values_backgrounds, 
                               np.array(background_means) - np.array(background_std_devs), 
                               np.array(background_means) + np.array(background_std_devs), 
                               color='cyan', alpha=0.1)
        
        axs[0, 0].fill_between(z_values_backgrounds, 
                               np.array(background_means2) - np.array(background_std_devs2), 
                               np.array(background_means2) + np.array(background_std_devs2), 
                               color='magenta', alpha=0.1)
    
    # Set plot titles and labels
    axs[0, 0].set_title("Intensity Profiles of Detected Blobs Across Z-layers")
    axs[0, 0].set_xlabel("Z (slices)")
    axs[0, 0].set_ylabel("Intensity")
    axs[0, 0].legend()
    axs[0, 0].grid(True)
    
    
    
    
    
    
    
    
    
        
            
    # Plot the histograms of the profile lengths
    profile_lengths_channel1 = [len(profile) for profile in profiles_channel1]
    profile_lengths_channel2 = [len(profile) for profile in profiles_channel2]
    
    # Convert lengths to desired scale
    length_channel1 = [length * CONFIG['z_spacing'] for length in profile_lengths_channel1]
    length_channel2 = [length * CONFIG['z_spacing'] for length in profile_lengths_channel2]
    
    # Plot histogram
    n_bins = 20  # Number of bins
    
    # Plot histogram for Channel 1
    n1, bins1, patches1 = axs[0, 1].hist(length_channel1, bins=n_bins, color='blue', alpha=0.5, label='Channel 1', edgecolor='black')
    
    # Plot histogram for Channel 2
    n2, bins2, patches2 = axs[0, 1].hist(length_channel2, bins=n_bins, color='red', alpha=0.5, label='Channel 2', edgecolor='black')
    
    # Add titles and labels
    axs[0, 1].set_title("Histogram of Profile Lengths")
    axs[0, 1].set_xlabel("Profile Length (slices)")
    axs[0, 1].set_ylabel("Frequency")
    axs[0, 1].legend()
    axs[0, 1].grid(True)
    
    # Adjust layout to fit plots nicely
    plt.tight_layout()


    
    
    
    
    
    
    
    
    # Plot detected blobs in the corrected image
    axs[1, 0].imshow(corrected_channel1_stack[center_z], cmap='gray')
    for blob in blobs:
        y, x, r = blob
        circle = plt.Circle((x, y), r, color='red', fill=False, linewidth=2)
        axs[1, 0].add_patch(circle)
    
        # Add file name text to the subplot showing the corrected image with detected blobs
    file_name = os.path.basename(file_path)  # Extract the file name from the file path
    axs[1, 0].text(0.05, 0.95, f'File: {file_name}', color='white', fontsize=12, 
                   verticalalignment='top', horizontalalignment='left', 
                   transform=axs[1, 0].transAxes)

    
    axs[1, 0].set_title("Detected Blobs in Corrected Image")
    axs[1, 0].axis('off')
    
    # Plot the average profile length bar plot
    avg_chan1_length = avg_length_channel1 * CONFIG['z_spacing']
    avg_chan2_length = avg_length_channel2 * CONFIG['z_spacing']
    axs[1, 1].bar(['Channel 1', 'Channel 2'], [avg_chan1_length, avg_chan2_length], color=['blue', 'red'])
    axs[1, 1].set_title('Average Profile Length')
    axs[1, 1].set_ylabel('Average Length')
    
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.3, wspace=0.3)
    plt.show()

    
        
    # Print average profile lengths
    print(f"Average profile length for Channel 1: {avg_chan1_length}")
    print(f"Average profile length for Channel 2: {avg_chan2_length}")
    
    
    
    # Extract the base name of the file without extension
    file_base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Generate the full filename for profiles
    profiles_filename = f"{file_base_name}_profiles.csv"
    
    # Save profiles to CSV
    save_profiles_to_csv(profiles_channel1, profiles_channel2, CONFIG['z_spacing'], filename=profiles_filename, save_path=os.path.dirname(file_path))

    # Optionally save results or further analyze them
else:
    print("No file selected. Exiting.")
