import math
import os.path
import time
from pathlib import Path
import pandas
import yaml
from PIL import Image
from natsort import natsorted
import shutil

from huojiweiguoba import lbw_datetime


def get_aspect_ratio(width, height):
    gcd = math.gcd(width, height)
    aspect_ratio = (width // gcd, height // gcd)
    return aspect_ratio


def load_yaml(file):
    with open(file, 'r', encoding='utf-8') as f:
        # return yaml.load(f, Loader=yaml.FullLoader)
        return yaml.safe_load(f)


class ReadListingInfo:
    '''读取上新文件夹信息'''

    def __init__(self, listing_folder_path, structure, yaml_rule):
        self.yaml_rule = yaml_rule
        self.structure = structure
        self.listing_folder_path = listing_folder_path  # 上新文件夹路径

        self.listing_shop_folder_path = Path(listing_folder_path).parent.resolve().__str__()  # 店铺文件夹
        self.listing_shop_folder_name = Path(listing_folder_path).parent.name  # 店铺文件夹名
        self.listing_shop_log_file = (Path(listing_folder_path).parent / "上架日志.txt").resolve().__str__()  # 店铺日志

        self.listing_folder_name = Path(listing_folder_path).name  # 上新文件夹名

        # shop
        self.shop_id = None  # 店铺ID
        self.shop_name = None  # 店铺名

        # task
        self.template_name = None  # 模板名
        self.title = None  # 标题

        # 载入文件夹
        for x in structure['folder']:
            self.__setattr__(x['attr_name'], None)

        # 载入文件
        for x in structure['file']:
            self.__setattr__(x['attr_name'], None)

    def record_log(self, bid: str):
        text = f"[{lbw_datetime.get_local_now_date()}] 上架成功 宝贝ID:{bid} {self.listing_folder_name}\n"
        with open(self.listing_shop_log_file, 'a') as f:
            f.write(text)

    def end_action(self, text):
        text = f"[{lbw_datetime.get_local_now_date()}] {text}"
        end_file_path = (Path(self.listing_folder_path) / "日志.txt").resolve().__str__()
        with open(end_file_path, 'w') as f:
            f.write(text)

    def load_folder(self):
        # 从文件夹规则中载入对应图片
        for x in self.structure['folder']:
            # 文件夹路径
            path = Path(self.listing_folder_path) / x['name']
            # 查看是否必须拥有+文件夹是否存在
            if x['required'] and not Path(path).is_dir():
                raise ValueError(f"缺少【{x['name']}】文件夹")
            # 获取文件夹中得所有对应类型图片
            files = [f for f in path.glob("*") if f.suffix.lower()[1:] in x['file_type']]
            # 文件夹存在则校验
            if Path(path).is_dir():
                # 是否需要自然排序
                if x['sort']:
                    files = natsorted(files, key=lambda y: y.stem.lower())
                # 校验图片张数
                if len(files) < x['file_num_limit']['min'] or len(files) > x['file_num_limit']['max']:
                    raise ValueError(
                        f"【{path.name}】文件夹：图片数量应该为{x['file_num_limit']['min']}-{x['file_num_limit']['max']}张")
                # 校验其他
                for f in files:
                    # 获取图片高和宽
                    img = Image.open(f)
                    w, h = img.size
                    size = os.path.getsize(f) / (1024 * 1024)  # 单位MB
                    # 校验图片大小
                    if size < x['file_size_limit']['min'] or size > x['file_size_limit']['max']:
                        raise ValueError(
                            f"【{path.name}】文件夹：【{Path(f).name}】大小应该为{x['file_size_limit']['min']}-{x['file_size_limit']['max']}MB")
                    # 校验图片尺寸
                    if w < x['file_pixel_limit']['width_min'] or w > x['file_pixel_limit']['width_max']:
                        raise ValueError(
                            f"【{path.name}】文件夹：【{Path(f).name}】 宽区间应该为{x['file_pixel_limit']['width_min']}px-{x['file_pixel_limit']['width_max']}px")
                    if h < x['file_pixel_limit']['height_min'] or h > x['file_pixel_limit']['height_max']:
                        raise ValueError(
                            f"【{path.name}】文件夹：【{Path(f).name}】 高区间应该为{x['file_pixel_limit']['height_min']}px-{x['file_pixel_limit']['height_max']}px")
                    # 校验图片比例
                    if x['file_pixel_limit']['width_height_ratio']:
                        ratio = f"{get_aspect_ratio(w, h)[0]}:{get_aspect_ratio(w, h)[1]}"
                        if ratio != x['file_pixel_limit']['width_height_ratio']:
                            raise ValueError(
                                f"【{path.name}】文件夹：【{Path(f).name}】 比例应该为{x['file_pixel_limit']['width_height_ratio']},目前为{ratio}")
            # 图片新增到对应对象中
            self.__setattr__(x['attr_name'], {i.stem: {"local_path": i.__str__()} for i in files})

    def load_file(self):
        # 从文件规则中载入对应
        for x in self.structure['file']:
            # 文件路径
            path = Path(self.listing_folder_path) / (x['name'] + f".{x['file_type']}")
            # 查看是否必须拥有+文件是否存在
            if x['required'] and not Path(path).is_file():
                raise ValueError(f"缺少【{x['name']}】文件")
            # 判断文件类型
            if x['file_type'] == "xlsx":
                file_items = {}
                # 循环Sheet
                for sheet in x['sheets']:
                    sheet_df = pandas.read_excel(path, sheet_name=sheet['sheet_name'])
                    # 检查需求列是否都存在
                    for i in sheet['fields'].split(","):
                        assert i in sheet_df.columns, f"【{x['name']}】文件,Sheet：{sheet['sheet_name']}中缺少【{i}】列"
                    # 将所有nan转换为None
                    sheet_df = sheet_df.fillna(value="")
                    # 所有列转为字符串
                    sheet_df = sheet_df.astype(str)
                    sheet_items = sheet_df.to_dict('records')
                    file_items[sheet['sheet_name']] = sheet_items
            elif x['file_type'] == "mp4":
                if Path(path).is_file():
                    file_items = {"local_path": path.__str__()}
                else:
                    file_items = {}
            else:
                raise ValueError(f"文件类型应该为[xlsx,mp4]，目前为{x['file_type']},联系管理员增加其他类型文件读取")
            # 文件新增到对应对象中
            self.__setattr__(x['attr_name'], file_items)

    def move_listing_folder(self):
        move_path = self.listing_folder_path.replace(self.yaml_rule['listing_path'],
                                                     self.yaml_rule['listing_backups_path'])
        if not Path(move_path).parent.exists():
            Path(move_path).mkdir(parents=True)
        # 查看目标文件夹是否存在
        if Path(move_path).exists():
            shutil.rmtree(move_path)
        # 移动文件夹
        shutil.move(self.listing_folder_path, move_path)
        # 查看原文件夹是否还在 还在需要删除
        try:
            if Path(self.listing_folder_path).exists():
                shutil.rmtree(self.listing_folder_path)
        except Exception as e:
            raise ValueError(f"已完成上架提交,文件夹被占用删除失败,请手动删除此文件夹!{str(e)}")

    def load_shop_task(self):
        '''加载店铺信息+任务信息'''
        assert "_" in self.listing_shop_folder_name, f"店铺文件夹名[{self.listing_shop_folder_name}] 不符合标准,正确写法[店铺ID_店铺名]"
        assert "_" in self.listing_folder_name, f"上新文件夹名[{self.listing_folder_name}] 不符合标准,正确写法[模板名_标题_]"
        self.shop_id = self.listing_shop_folder_name.split("_")[0]
        self.shop_name = self.listing_shop_folder_name.split("_")[1]
        self.template_name = self.listing_folder_name.split("_")[0]
        self.title = self.listing_folder_name.split("_")[1]


def get_folder_listing_task(plat_name, yaml_path, wait_time=10):
    FOLDER_RULE = load_yaml(yaml_path)
    listing_path = Path(FOLDER_RULE['listing_path'])
    listing_plat_path = Path(FOLDER_RULE['listing_path']) / plat_name
    assert listing_path.is_dir(), f"找不到上新源文件夹：{listing_path}"
    assert listing_plat_path.is_dir(), f"找不到上新平台文件夹：{listing_plat_path}"
    assert plat_name in FOLDER_RULE[
        'structure'].keys(), f"非法平台：{plat_name},可用平台[{','.join(FOLDER_RULE['structure'].keys())}]"

    # 遍历文件夹
    while True:
        # 获取文件夹下的所有店铺文件夹
        shops_dir = [f for f in listing_plat_path.iterdir() if f.is_dir()]
        # 循环店铺
        for shop in shops_dir:
            # 获取店铺中得所有上架文件夹
            listing_dir = [f for f in shop.iterdir() if f.is_dir()]
            # 循环上架文件夹
            for listing in listing_dir:
                if "日志.txt" not in [x.name.__str__() for x in listing.iterdir() if x.is_file()]:
                    # 等待文件夹文件加载完成时间
                    print(f"=========================等待{wait_time}秒开始=========================")
                    print(f"当前上架文件夹：{listing}")
                    time.sleep(wait_time)
                    # 获取上架文件夹中得所有上架文件
                    rli = ReadListingInfo(listing.__str__(), FOLDER_RULE['structure'][plat_name], FOLDER_RULE)
                    yield rli
        time.sleep(wait_time)

# if __name__ == "__main__":
#     for task in get_folder_listing_task("拼多多",r"C:\Users\86251\Desktop\listing\folder_rule.yaml",2):
#         task.load_folder()
#         task.load_file()
#         task.load_shop_task()
#         print(task.__dict__)
