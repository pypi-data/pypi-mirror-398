import json

import zbToolLib as zb
from PIL import Image


def convertAll(path: str):
    """
    重命名ccui_packs目录下的所有文件后缀名
    :param path: ccui_packs路径
    """
    l = zb.walkFile(path)
    for i in l:
        if i.endswith(".1"):
            zb.movePath(i, zb.joinPath(zb.getFileDir(i), zb.getFileName(i, False) + ".png"), True)
        if i.endswith(".2"):
            zb.movePath(i, zb.joinPath(zb.getFileDir(i), zb.getFileName(i, False) + ".ktx"), True)
        elif i.endswith(".3"):
            zb.movePath(i, zb.joinPath(zb.getFileDir(i), zb.getFileName(i, False) + ".plist"), True)
    convertAllBplist(path)


def splitImage(img_file: str, json_file: str, output_path: str):
    """
    分割ccui_packs目录下的图片
    :param img_file: 精灵图图片文件
    :param json_file: 存储图片分割信息的Json文件
    :param output_path: 输出目录
    """
    big_image = Image.open(img_file)

    with open(json_file, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    for frame_name, frame_data in json_data["frames"].items():

        x, y, w, h = [int(eval(value)) for value in frame_data["frame"][1:-1].replace("{", "").replace("}", "").split(",")]
        x2, y2, w2, h2 = [int(eval(value)) for value in frame_data["sourceColorRect"][1:-1].replace("{", "").replace("}", "").split(",")]
        w3, h3 = [int(eval(value)) for value in frame_data["sourceSize"][1:-1].replace("{", "").replace("}", "").split(",")]
        offset_x, offset_y = [int(eval(value)) for value in frame_data["offset"][1:-1].split(",")]

        if frame_data["rotated"]:
            w, h = h, w
            w2, h2 = h2, w2
        small_image = big_image.crop((x, y, x + w, y + h))

        # 裁剪小图
        if frame_data["rotated"]:
            small_image = small_image.rotate(90, expand=True)

        b = Image.new("RGBA", (w3, h3))

        b.alpha_composite(small_image, (x2, y2))
        zb.createDir(zb.getFileDir(zb.joinPath(output_path, frame_name)))
        b.save(zb.joinPath(output_path, frame_name), format="png")


def readBplist(data: bytes):
    """
    读取bplist数据，返回dict数据
    :param data: bplist数据
    :return: dict数据
    """
    from .bplist import BPList
    return BPList(data).parse()


def convertAllBplist(path: str):
    """
    转换ccui_packs目录下的bplist文件
    :param path: ccui_packs路径
    """
    l = zb.walkFile(path)
    for i in l:
        try:
            with open(i, "rb") as file:
                data = file.read()
            b = readBplist(data)

            with open(zb.joinPath(zb.getFileDir(i), zb.getFileName(i, False) + ".json"), "w", encoding="utf-8") as file:
                file.write(json.dumps(b, indent=4, ensure_ascii=False))
            zb.deleteFile(i)
        except:
            pass
