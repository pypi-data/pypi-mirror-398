import cv2
import numpy as np
from numba import jit
def removeSmallPatches(binary_mask, min_pixels=50, min_area=40):
    binary_mask = (binary_mask > 0).astype(np.uint8)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binary_mask, connectivity=8
    )    
    output_mask = np.zeros_like(binary_mask)    
    for i in range(1, num_labels):
        pixel_count = stats[i, cv2.CC_STAT_AREA]        
        if pixel_count < min_pixels:
            continue
        component_mask = (labels == i).astype(np.uint8)
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)        
        if contours:
            contour = contours[0]
            area = cv2.contourArea(contour)            
            if area < min_area:
                continue        
        output_mask[labels == i] = 255    
    return output_mask

"""
mask = removeSmallPatches(b, min_pixels=50, min_area=40)
data = np.where(mask, data, 0)
filtered_data = np.full([256,256],0)
filtered_data[mask] = e[mask]
"""

import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
def process_block_optimized(args):
    block, coords, min_pixels, min_area = args
    y, x, y_end, x_end = coords    
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(block, 8)
    result = np.zeros_like(block)    
    valid_labels = []
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_pixels:
            valid_labels.append(i)   
    for i in valid_labels:
        component_mask = (labels == i).astype(np.uint8)
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)        
        if contours and cv2.contourArea(contours[0]) >= min_area:
            result[labels == i] = 255    
    return result, coords
def removeSmallPatches_fast(binary_mask, min_pixels=100, min_area=40, num_workers=3):
    binary_mask = (binary_mask > 0).astype(np.uint8)
    h, w = binary_mask.shape
    output = np.zeros_like(binary_mask)
    block_size = 2000    
    blocks = []
    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            y_end, x_end = min(y+block_size, h), min(x+block_size, w)
            block = binary_mask[y:y_end, x:x_end]
            blocks.append((block, (y, x, y_end, x_end), min_pixels, min_area))    
    with ThreadPoolExecutor(num_workers) as executor:
        for result, (y, x, y_end, x_end) in executor.map(process_block_optimized, blocks):
            output[y:y_end, x:x_end] = result    
    return output

"""
mask = removeSmallPatches(b, min_pixels=50, min_area=40)
data = np.where(mask, data, 0)
filtered_data = np.full([256,256],0)
filtered_data[mask] = e[mask]
"""

import cv2
import numpy as np
from numba import jit, prange
from concurrent.futures import ThreadPoolExecutor
def removeSmallPatches_optimized(binary_mask, min_pixels=50, min_area=40):
    binary_mask = (binary_mask > 0).astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
    output_mask = np.zeros_like(binary_mask)
    valid_labels = [i for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] >= min_pixels]
    for i in valid_labels:
        contour_mask = (labels == i).astype(np.uint8)
        contours, _ = cv2.findContours(contour_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours and cv2.contourArea(contours[0]) >= min_area:
            output_mask[labels == i] = 255
    
    return output_mask

@jit(nopython=True, parallel=True, nogil=True)
def numba_filter_components(labels, stats, min_pixels, min_area):
    height, width = labels.shape
    output = np.zeros((height, width), dtype=np.uint8)
    for i in prange(1, stats.shape[0]):
        if stats[i, 4] >= min_pixels:  # stats[i, 4] 对应 cv2.CC_STAT_AREA
            for y in range(height):
                for x in range(width):
                    if labels[y, x] == i:
                        output[y, x] = 255    
    return output
def removeSmallPatches_numba(binary_mask, min_pixels=50, min_area=40):
    binary_mask = (binary_mask > 0).astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
    output_mask = numba_filter_components(labels, stats, min_pixels, min_area)
    if min_area > 0:
        num_labels2, labels2, stats2, _ = cv2.connectedComponentsWithStats(output_mask, connectivity=8)
        final_output = np.zeros_like(output_mask)        
        for i in range(1, num_labels2):
            contour_mask = (labels2 == i).astype(np.uint8)
            contours, _ = cv2.findContours(contour_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)            
            if contours and cv2.contourArea(contours[0]) >= min_area:
                final_output[labels2 == i] = 255        
        return final_output    
    return output_mask
def process_block_optimized_v2(args):
    block, coords, min_pixels, min_area = args
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(block, connectivity=8)
    result = np.zeros_like(block)
    valid_labels = []
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_pixels:
            valid_labels.append(i)
    for i in valid_labels:
        component_indices = (labels == i)
        if component_indices.any():
            component_mask = component_indices.astype(np.uint8)
            contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)            
            if contours and cv2.contourArea(contours[0]) >= min_area:
                result[component_indices] = 255    
    return result, coords
def removeSmallPatches_fast_v2(binary_mask, min_pixels=100, min_area=40, num_workers=4):
    binary_mask = (binary_mask > 0).astype(np.uint8)
    h, w = binary_mask.shape
    optimal_block_size = max(500, min(2000, (h * w) // (num_workers * 10000)))    
    output = np.zeros_like(binary_mask)
    blocks = []
    for y in range(0, h, optimal_block_size):
        for x in range(0, w, optimal_block_size):
            y_end, x_end = min(y + optimal_block_size, h), min(x + optimal_block_size, w)
            block = binary_mask[y:y_end, x:x_end].copy() 
            blocks.append((block, (y, x, y_end, x_end), min_pixels, min_area))    
    actual_workers = min(num_workers, len(blocks))    
    with ThreadPoolExecutor(max_workers=actual_workers) as executor:
        for result, (y, x, y_end, x_end) in executor.map(process_block_optimized_v2, blocks):
            output[y:y_end, x:x_end] = result    
    return output
def get_optimal_function(binary_mask, min_pixels=50, min_area=40):
    h, w = binary_mask.shape
    total_pixels = h * w    
    if total_pixels < 1000000:  # 小于100万像素
        return removeSmallPatches_optimized    
    if min_area <= 0:
        return removeSmallPatches_numba    
    return removeSmallPatches_fast_v2
def auto_remove_small_patches(binary_mask, min_pixels=50, min_area=40):
    optimal_func = get_optimal_function(binary_mask, min_pixels, min_area)
    return optimal_func(binary_mask, min_pixels, min_area)
""" 
try:
    result = auto_remove_small_patches(binary_mask, min_pixels=50, min_area=40)
except Exception as e:
    from original_module import removeSmallPatches
    result = removeSmallPatches(binary_mask, min_pixels=50, min_area=40)
 removeSmallPatches_numba optimum performance min_area <= 0
 removeSmallPatches_fast_v2 area
"""
@jit(nopython=True, parallel=True, nogil=True)
def QC_simple_numba(mat, dbzTH = 10.0, areaTH=20):
    # Create a copy of the matrix
    mat1 = np.copy(mat)
    rows, cols = mat1.shape
    
    # Create binary mask based on threshold
    mask = np.zeros((rows, cols), dtype=np.uint8)
    for i in range(rows):
        for j in range(cols):
            if mat1[i, j] > dbzTH:
                mask[i, j] = 1    
    # Simple 8-connectivity region labeling (flood fill algorithm)
    labels = np.zeros((rows, cols), dtype=np.int32)
    current_label = 1
    region_areas = []    
    for i in range(rows):
        for j in range(cols):
            # If current pixel is foreground and not yet labeled
            if mask[i, j] == 1 and labels[i, j] == 0:
                # Start flood fill
                stack = [(i, j)]
                labels[i, j] = current_label
                area = 0
                
                while stack:
                    x, y = stack.pop()
                    area += 1
                    
                    # Check 8 surrounding pixels
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nx, ny = x + dx, y + dy
                            # Check bounds and conditions
                            if (0 <= nx < rows and 0 <= ny < cols and 
                                mask[nx, ny] == 1 and labels[nx, ny] == 0):
                                labels[nx, ny] = current_label
                                stack.append((nx, ny))
                
                region_areas.append(area)
                current_label += 1
    
    # Apply area threshold filtering
    for i in range(rows):
        for j in range(cols):
            if labels[i, j] > 0 and region_areas[labels[i, j] - 1] < areaTH:
                mat1[i, j] = 0    
    return mat1
def QC_ref_numba(mat, dbzTH = 10, areaTH=20):
    for i in range(len(mat)):      
        mat[i] = QC_simple_numba(mat[i], dbzTH, areaTH)
    return mat 
"""
CR = subset["CR"].data[0].copy()
CR[CR < 6] = 0
CR = QC_ref_numba(CR[None], areaTH=15)[0]
"""