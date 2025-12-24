#marearts_anpr.py
import cv2
from PIL import Image
import time 
import numpy as np

def marearts_anpr_from_pil(anpr_d, anpr_r, pil_img):
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert(mode="RGB")
    img = np.array(pil_img)
    return marearts_anpr_from_cv2(anpr_d, anpr_r, img)

def marearts_anpr_from_image_file(anpr_d, anpr_r, image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Failed to load image")
    return marearts_anpr_from_cv2(anpr_d, anpr_r, img)

def marearts_anpr_from_cv2(anpr_d, anpr_r, img):
    start_time = time.time()
    detections = anpr_d.detector(img)
    ltrb_time = time.time() - start_time

    if len(detections) == 0:
        return {
            "results": [],
            "ltrb_proc_sec": round(ltrb_time, 2),
            "ocr_proc_sec": 0.0
        }

    # Check if V14 detector and OCR (has batch support)
    # is_v14_detector = hasattr(anpr_d, '__class__') and 'v14' in anpr_d.__class__.__name__.lower()
    is_v14_ocr = hasattr(anpr_r, '__class__') and 'v14' in anpr_r.__class__.__name__.lower()

    results = []
    ocr_time = 0

    if is_v14_ocr:
        # V14: Batch processing - collect all crops first
        crop_images = []
        box_data = []

        for box_info in detections:
            if 'bbox' in box_info:
                l, t, r, b = box_info['bbox']
            else:
                l, t, r, b = box_info['box']

            crop_img = img[int(t):int(b), int(l):int(r)]

            if crop_img.size == 0:
                continue

            crop_images.append(crop_img)
            box_data.append({
                'ltrb': [int(l), int(t), int(r), int(b)],
                'ltrb_conf': int(box_info['score'] * 100)
            })

        if len(crop_images) > 0:
            # Batch OCR inference
            start_time = time.time()
            ocr_results = anpr_r.predict(crop_images)
            ocr_time = time.time() - start_time

            # Combine results
            for i, ocr_result in enumerate(ocr_results):
                results.append({
                    "ocr": ocr_result[0],
                    "ocr_conf": ocr_result[1],
                    "ltrb": box_data[i]['ltrb'],
                    "ltrb_conf": box_data[i]['ltrb_conf']
                })
    else:
        # Legacy: Loop processing (one-by-one)
        for box_info in detections:
            if 'bbox' in box_info:
                l, t, r, b = box_info['bbox']
            else:
                l, t, r, b = box_info['box']

            crop_img = img[int(t):int(b), int(l):int(r)]

            if crop_img.size == 0:
                continue

            pil_img = Image.fromarray(crop_img)
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert(mode="RGB")

            start_time = time.time()
            ocr_result = anpr_r.predict(pil_img)
            ocr_time += time.time() - start_time

            results.append({
                "ocr": ocr_result[0],
                "ocr_conf": ocr_result[1],
                "ltrb": [int(l), int(t), int(r), int(b)],
                "ltrb_conf": int(box_info['score'] * 100)
            })

    return {
        "results": results,
        "ltrb_proc_sec": round(ltrb_time, 2),
        "ocr_proc_sec": round(ocr_time, 2)
    }