import importlib
import logging


class GeoUtils:
    @staticmethod
    def translate(x, y, method="bd2wgs"):
        """
        GCJ-02 高德坐标 gcj
        BD-09  百度坐标 bd
        WGS-84 GPS坐标 wgs
        :param x: lat
        :param y: lon
        :param method: 转换方法（wgs2gcj、wgs2bd、gcj2wgs、gcj2bd、bd2wgs、bd2gcj）
        :return: 转换结果
        """
        try:
            tf = importlib.import_module("coord_convert.transform")
        except ImportError:
            raise Exception(f"coord-convert is not exist,run:pip install coord-convert==0.2.1")
        try:
            x, y = getattr(tf, method)(float(x), float(y))
        except Exception as e:
            logging.warning(f"坐标转换失败：{str(e)}")
        return float(x), float(y)
