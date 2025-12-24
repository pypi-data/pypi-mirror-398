import zbToolLib as zb
from PIL import Image


def combineWonderImage(id1: int | str, id2: int | str, imgs_path: str, output_path: str):
    """
    合并家园伟大工程图片
    :param id1: 第一位id，是文件名中第一个数字，表示建筑类型
    :param id2: 第二位id，是文件名中第二个数字，表示建筑进度
    :param imgs_path: 家园伟大工程图片路径，图片名称需和源文件名一致，默认位于apk中/assets/assets/resource_packs/vanilla_login/textures/sfxs/home/ass_community
    :param output_path: 输出文件路径
    """
    wid = str(id1) + "-" + str(id2)
    name = "wonder_" + wid + "_"

    def getPos(img: str):
        img = zb.getFileName(img).replace(name, "").replace(".png", "").strip()
        l = img.rsplit("-", 1)
        return [int(i) for i in l]

    imgs = sorted([i for i in zb.walkFile(imgs_path, 1) if i.endswith(".png") and zb.getFileName(i).startswith(name)], key=lambda k: getPos(k))
    poses = [getPos(i) for i in imgs]
    max_x = max([i[0] for i in poses])
    min_x = min([i[0] for i in poses])
    max_y = max([i[1] for i in poses])
    min_y = min([i[1] for i in poses])
    x = max_x - min_x + 1
    y = max_y - min_y + 1
    img_size = 448

    big_image = Image.new("RGBA", (img_size * x, img_size * y))

    for i in imgs:
        img = Image.open(i)
        big_image.paste(img, (img_size * (getPos(i)[0] - min_x), img_size * (max_y - getPos(i)[1])))
    big_image.save(output_path)
