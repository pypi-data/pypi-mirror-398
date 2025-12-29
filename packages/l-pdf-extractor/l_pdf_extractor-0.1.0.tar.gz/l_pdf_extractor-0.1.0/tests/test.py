from io import BytesIO
import os
from pathlib import Path
import time
import cv2
import fitz
from fitz import Document,Page
import numpy as np
os.environ["PPSTRUCTURE_HOME"] = "./model"
os.environ["FLAGS_allocator_strategy"] = "auto_growth"  # 关键！必须在 import paddle 前设置

# 可选：限制最大显存（单位 MB）
os.environ["FLAGS_fraction_of_gpu_memory_to_use"] = "0.7"  # 最多用 50% 显存
from paddleocr import PPStructureV3
# os.environ["CUDA_VISIBLE_DEVICES"] = "1"
#DISABLE_MODEL_SOURCE_CHECK` to `True`
def is_integer(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False
def extract_pdf(file_input:bytes):
    """
    Extract text from PDF file
    """
    mission_begin = time.perf_counter()
    pipeline = PPStructureV3(
        lang="ch",#en
        #use_doc_orientation_classify=True,#通过 use_doc_orientation_classify 指定是否使用文档方向分类模型
        use_doc_unwarping=False, # 通过 use_doc_unwarping 指定是否使用文本图像矫正模块
        use_textline_orientation=True, # 通过 use_textline_orientation 指定是否使用文本行方向分类模型
        device="cpu",
    )
    doc: Document = fitz.open(stream=BytesIO(file_input))
    all_markdown = ""
    final_result = {}
    index = 1

    for page in doc:
        begin = time.perf_counter()
        page: Page = page
        pix_layout = page.get_pixmap(dpi=120)
        img = np.frombuffer(pix_layout.samples, dtype=np.uint8).reshape(pix_layout.h, pix_layout.w, pix_layout.n).copy()
        crop_img = None
        if pix_layout.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        try:
            crop_width = int(pix_layout.width *(300/120))
            crop_height = int(pix_layout.height *(300/120))
            result = pipeline.predict(img)
            if len(result)>0:
                final_result[index] = {}
            latex = result[0].latex
            for lat in latex["images"]:
                from PIL import Image
                save_path = "./"+lat["path"]
                box = [int(str) for str in lat["path"].replace('.','_').split('_') if is_integer(str)]
                box = [int(val *(300/120)) for val in box]
                box = [box[0]-15 if box[0]>15 else 0,
                       box[1]-15 if box[1]>15 else 0,
                       box[2]+15 if box[2]+15 <crop_width else crop_width,
                       box[3]+15 if box[3]+15 <crop_height else crop_height]
                if crop_img is None:
                    crop_layout = page.get_pixmap(dpi=300)
                    crop_img = np.frombuffer(crop_layout.samples, dtype=np.uint8).reshape(crop_layout.h, crop_layout.w, crop_layout.n).copy()
                    if pix_layout.n == 4:
                        crop_img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                corp_figure = Image.fromarray(crop_img[box[1]:box[3], box[0]:box[2]])

                path = os.path.basename(lat["path"])
                # lat["img"].save(save_path)
                corp_figure.save(save_path)
                if "images" not in final_result[index]:
                    final_result[index]["images"] = []
                final_result[index]["images"].append({"path": path,"img": corp_figure})
            final_result[index]["markdown"] = result[0].markdown["markdown_texts"]
            all_markdown += result[0].markdown["markdown_texts"]
            all_markdown += f"\n----------{index}----------\n\n"
        except Exception as e:
            print(e)
        index += 1
        print(f"Page {index} done in {time.perf_counter() - begin}s")
    if all_markdown is not None:
        with open("./tests/esp32_datasheet_en.md", "w",encoding="utf-8") as f:
            f.write(all_markdown)
    print(f"Total time: {time.perf_counter() - mission_begin}s")
    return final_result


if __name__ == "__main__":
    with open("./tests/esp32_datasheet_en.pdf", "rb") as f:
        result = extract_pdf(f.read())
    for index, item in result.items():
        print(item["markdown"])
    # print(result)
    
