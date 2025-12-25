import numpy as np
import random
# import albumentations as A
# import cv2

# def resize_array(array, size):
#     # 定义变换管道
#     transform = A.Compose([
#         A.SmallestMaxSize(max_size=size, interpolation=cv2.INTER_AREA)
#     ])
#     transformed_array = transform(image=array)["image"]
#     return transformed_array

def crop_array(array, crop_side_len):
    cropper = A.RandomCrop(height=crop_side_len, width=crop_side_len)
    cropped_array = cropper(image=array)["image"]
    return cropped_array

def crop_cna_pair(min_side_len, low_res_data, high_res_data):
    crop_side_len = min_side_len
    top = random.randint(0, low_res_data.shape[-2] - crop_side_len)
    left = random.randint(0, low_res_data.shape[-1] - crop_side_len)
    super_factor = high_res_data.shape[-2] / low_res_data.shape[-2] # Assuming the ratio in height dimensio
    cropped_low_res = low_res_data[top:top + crop_side_len, left:left + crop_side_len]
    cropped_high_res = high_res_data[int(top * super_factor):int((top + crop_side_len) * super_factor),
                                     int(left * super_factor):int((left + crop_side_len) * super_factor)]
    return cropped_low_res, cropped_high_res
def random_crop_pair(min_side_len, low_res_data, high_res_data):
    crop_side_len = min_side_len
    top = random.randint(0, low_res_data.shape[-2] - crop_side_len)
    left = random.randint(0, low_res_data.shape[-1] - crop_side_len)
    super_factor = high_res_data.shape[-2] / low_res_data.shape[-2] # Assuming the ratio in height dimension
    cropped_low_res = low_res_data[top:top + crop_side_len, left:left + crop_side_len]
    cropped_high_res = high_res_data[int(top * super_factor):int((top + crop_side_len) * super_factor),
                                     int(left * super_factor):int((left + crop_side_len) * super_factor)]
    return cropped_low_res, cropped_high_res

import random

def random_crop_triplet(min_side_len, low_res_data, high_res_data1, high_res_data2):
    top = random.randint(0, low_res_data.shape[-2] - min_side_len)
    left = random.randint(0, low_res_data.shape[-1] - min_side_len)
    cropped_low_res = low_res_data[..., top:top + min_side_len, left:left + min_side_len]
    factor1_h = high_res_data1.shape[-2] / low_res_data.shape[-2]
    factor1_w = high_res_data1.shape[-1] / low_res_data.shape[-1]
    cropped_high_res1 = high_res_data1[...,
                                       int(top * factor1_h):int((top + min_side_len) * factor1_h),
                                       int(left * factor1_w):int((left + min_side_len) * factor1_w)]
    factor2_h = high_res_data2.shape[-2] / low_res_data.shape[-2]
    factor2_w = high_res_data2.shape[-1] / low_res_data.shape[-1]
    cropped_high_res2 = high_res_data2[...,
                                       int(top * factor2_h):int((top + min_side_len) * factor2_h),
                                       int(left * factor2_w):int((left + min_side_len) * factor2_w)]
    return cropped_low_res, cropped_high_res1, cropped_high_res2

def random_crop_single(cropsize, input_data):
    # 确定裁剪的边长
    crop_side_len = cropsize

    # 随机选择左上角裁剪点
    top = random.randint(0, input_data.shape[0] - crop_side_len)
    left = random.randint(0, input_data.shape[1] - crop_side_len)

    # 裁剪输入数据
    cropped_data = input_data[top:top + crop_side_len, left:left + crop_side_len]

    return cropped_data


if __name__ == "__main__":
    low_res_data = np.load("./SAT_202507010900_49.42_117.82_100.npy")
    high_res_data = np.load("./CR_202507010900_49.42_117.82_100.npy")
    high_res_data1 = np.load("./mask_202507010900_49.42_117.82_100.npy")
    d1,d2,d3 =  random_crop_triplet(128, low_res_data, high_res_data[0], high_res_data1[0])
    transformed_low_res_data = resize_array(low_res_data, 240)
    transformed_high_res_data = resize_array(high_res_data, 960)
    np.save("transformed_low_res_data.npy", transformed_low_res_data)
    np.save("transformed_high_res_data.npy", transformed_high_res_data)

