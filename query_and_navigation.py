#coding:utf-8

## 2020/11/12 ##

import requests
import json
import folium
import math
import serial

from sys import argv, exit
from os import getcwd, remove, rename
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QInputDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

# 常量
TILES = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x=105&y=48&z=7'  # 可选的地图
JQUERY_SOUR = 'https://code.jquery.com/jquery-1.12.4.min.js'  # 需要被替换的jQuery库
NEW_JQUERY_SOUR = 'http://lib.sinaapp.com/js/jquery/1.9.1/jquery-1.9.1.min.js'  # 用于替换的jQuery库

LOCAL_FILE = r'file:///'  # 标识本地文件的URL头部
MY_FILE_ROOT = 'E:/OneDrive/VSCode_Python/projects/Baidu_API/json_data/'  # 本开发机上的根目录
POINT_JSON_DATA = 'point_json_data.txt'  # 存储地点查询所获得的原始json信息
POINT_QUERY_RES = 'point_query_res.txt'  # 存储从原始json信息中提取出的信息
QUERY_MAP_RES = 'query_map_res.html'  # 地点查询可视化，存储为html文件
NAVI_JSON_DATA = 'navi_json_data.txt'  # 存储导航操作所获得的原始json信息
NAVI_MAP_RES = 'navi_map_res.html'  # 导航操作可视化，存储为html文件
TEMP_MAP_RES = 'temp_map_res.html'  # 临时html文件，可忽略
COM_TEXT_RES = 'COM_text_res.txt'  # 存储从串口中读取的数据

METHOD = ('driving', 'riding', 'walking', 'transit')  # 出行方式
MY_AK = 'qFaGBCZLiXgUzUGmCzaEfRDS8H6GbPee'  # 开发者AK
MARKER_INTERVAL = 20  # 间隔一定量输出路径上点

# 用于坐标转换的一系列常数
PI = 3.1415926535897932384626
X_PI = 3.14159265358979324 * 3000.0 / 180
PARA_A = 6378245.0
EE = 0.0069342162296594323

# 测试数据
address_list_1 = ['光明', '深圳市']
lat_lng_list_1 = [['22.746051,113.955462', '22.544192,113.952027']]

# 全局变量
curr_query_res = None  # 存储查询获得的字符串化结果


class UI_Form(object):
    """
    用于定义主窗体图形界面格式，
    定义了主窗体及其控件的属性
    """
    def setup_UI(self, Form):

        Form.setObjectName("Form")
        Form.resize(1000, 920)  # 设置主窗体规模大小，即长宽值

        # 设置窗体中的字体格式
        font = QtGui.QFont()
        font.setFamily('Arial')
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(20)
        Form.setFont(font)

        # 维护主窗体中各控件的位置表
        self.base_yaxis_1 = 40
        self.base_yaxis_2 = 480
        self.delta = 50
        self.layout = [
            (50, self.base_yaxis_1),  # 表征查询功能的标签
            (50, self.base_yaxis_2),  # 表征导航功能的标签
            (150, self.base_yaxis_1 + self.delta * 2, 150, 31),  # 地址输入栏
            (150, self.base_yaxis_1 + self.delta * 3, 150, 31),  # 地区输入栏
            (150, self.base_yaxis_2 + self.delta * 2, 150, 31),  # 出行方式输入栏
            (150, self.base_yaxis_2 + self.delta * 3, 150, 31),  # 起始地址输入栏
            (150, self.base_yaxis_2 + self.delta * 4, 150, 31),  # 目的地址输入栏
            (50, self.base_yaxis_1 + self.delta * 2, 80, 31),  # 地址按钮
            (50, self.base_yaxis_1 + self.delta * 3, 80, 31),  # 地区按钮
            (50, self.base_yaxis_1 + self.delta * 5, 80, 31),  # 地点查询按钮
            (150, self.base_yaxis_1 + self.delta * 5, 80, 31),  # 显示查询结果按钮
            (50, self.base_yaxis_2 + self.delta, 80, 31),  # 定位自身按钮
            (50, self.base_yaxis_2 + self.delta * 2, 80, 31),  # 出行方式按钮
            (50, self.base_yaxis_2 + self.delta * 3, 80, 31),  # 起始地址按钮
            (50, self.base_yaxis_2 + self.delta * 4, 80, 31),  # 目的地址按钮
            (50, self.base_yaxis_2 + self.delta * 6, 80, 31),  # 开始导航按钮
            (360, self.base_yaxis_1, 600, 400),  # 查询结果窗口
            (360, self.base_yaxis_2, 600, 400)  # 导航结果窗口
        ]

        self.it = iter(self.layout)

        # 标签控件

        # 查询功能表头
        coord_x, coord_y = next(self.it)
        self.QueryLabel = QtWidgets.QLabel(Form)
        self.QueryLabel.move(coord_x, coord_y)
        self.QueryLabel.setObjectName('QueryLabel')

        # 导航功能表头
        coord_x, coord_y = next(self.it)
        self.NaviLabel = QtWidgets.QLabel(Form)
        self.NaviLabel.move(coord_x, coord_y)
        self.NaviLabel.setObjectName('NaviLabel')

        # 文本框控件

        # 获取地址文本框
        coord_x, coord_y, length, height = next(self.it)
        self.GetAddrLineEdit = QtWidgets.QLineEdit(Form)
        self.GetAddrLineEdit.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.GetAddrLineEdit.setObjectName('GetAddrLineEdit')

        # 获取行政区划文本框
        coord_x, coord_y, length, height = next(self.it)
        self.GetRegionLineEdit = QtWidgets.QLineEdit(Form)
        self.GetRegionLineEdit.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.GetRegionLineEdit.setObjectName('GetRegionLineEdit')

        # 获取出行方式文本框
        coord_x, coord_y, length, height = next(self.it)
        self.GetMethodLineEdit = QtWidgets.QLineEdit(Form)
        self.GetMethodLineEdit.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.GetMethodLineEdit.setObjectName('GetMethodLineEdit')

        # 获取起始地点文本框
        coord_x, coord_y, length, height = next(self.it)
        self.GetOriginLineEdit = QtWidgets.QLineEdit(Form)
        self.GetOriginLineEdit.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.GetOriginLineEdit.setObjectName('GetOriginLineEdit')

        # 获取目的地点文本框
        coord_x, coord_y, length, height = next(self.it)
        self.GetDestLineEdit = QtWidgets.QLineEdit(Form)
        self.GetDestLineEdit.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.GetDestLineEdit.setObjectName('GetDestLineEdit')

        # 按钮控件

        # 获取地址按钮
        coord_x, coord_y, length, height = next(self.it)
        self.getAddrButton = QtWidgets.QPushButton(Form)
        self.getAddrButton.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.getAddrButton.setObjectName('getAddrButton')

        # 获取行政区划按钮
        coord_x, coord_y, length, height = next(self.it)
        self.getRegionButton = QtWidgets.QPushButton(Form)
        self.getRegionButton.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.getRegionButton.setObjectName('getRegionButton')

        # 开始查询目标地点按钮
        coord_x, coord_y, length, height = next(self.it)
        self.startQueryButton = QtWidgets.QPushButton(Form)
        self.startQueryButton.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.startQueryButton.setObjectName('startQueryButton')

        # 打印查询结果文本按钮
        coord_x, coord_y, length, height = next(self.it)
        self.printQueryButton = QtWidgets.QPushButton(Form)
        self.printQueryButton.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.startQueryButton.setObjectName('printQueryButton')

        # 定位自身位置按钮
        coord_x, coord_y, length, height = next(self.it)
        self.locateYourselfButton = QtWidgets.QPushButton(Form)
        self.locateYourselfButton.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.startQueryButton.setObjectName('locateYourselfButton')

        # 获取出行方式按钮
        coord_x, coord_y, length, height = next(self.it)
        self.getMethodButton = QtWidgets.QPushButton(Form)
        self.getMethodButton.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.getMethodButton.setObjectName('getMethodButton')

        # 获取起始地点按钮
        coord_x, coord_y, length, height = next(self.it)
        self.getOriginButton = QtWidgets.QPushButton(Form)
        self.getOriginButton.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.getOriginButton.setObjectName('getOriginButton')

        # 获取目的地点按钮
        coord_x, coord_y, length, height = next(self.it)
        self.getDestButton = QtWidgets.QPushButton(Form)
        self.getDestButton.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.getDestButton.setObjectName('getDestButton')

        # 开始规划路径按钮
        coord_x, coord_y, length, height = next(self.it)
        self.startNaviButton = QtWidgets.QPushButton(Form)
        self.startNaviButton.setGeometry(
            QtCore.QRect(coord_x, coord_y, length, height))
        self.startNaviButton.setObjectName('startNaviButton')

        self.retranslate_UI(Form)  # 统一设置控件文本
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslate_UI(self, Form):
        _translate = QtCore.QCoreApplication.translate

        # 依次设置各控件文本
        Form.setWindowTitle(_translate('Form', 'Query and Navigation'))

        self.QueryLabel.setText(_translate('Form', 'Query Function'))
        self.NaviLabel.setText(_translate('Form', 'Navi Function'))

        self.getAddrButton.setText(_translate('Form', 'Get Address'))
        self.getRegionButton.setText(_translate('Form', 'Get Region'))
        self.startQueryButton.setText(_translate('Form', 'Query'))
        self.printQueryButton.setText(_translate('Form', 'Show Text'))

        self.locateYourselfButton.setText(_translate('Form', 'Location'))
        self.getMethodButton.setText(_translate('Form', 'Get Method'))
        self.getOriginButton.setText(_translate('Form', 'Get Origin'))
        self.getDestButton.setText(_translate('Form', 'Get Dest'))
        self.startNaviButton.setText(_translate('Form', 'Navigation'))


class MainWindow(QMainWindow, UI_Form):
    """
    主窗体类，定义主窗体的具体功能实现
    """
    def __init__(self, file_root, parent=None):

        super(QMainWindow, self).__init__(parent)  # 父类初始化

        # 设置保存文件的根目录
        self.file_root = file_root  # 用于保存中间文件的文件夹的绝对路径
        self.cwd = getcwd()  # 获取当前所在目录路径
        choosen_file_root = ''.join([
            QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select Folder to Save Files", self.cwd), '/'
        ])  # 让用户自行选取想保存文件的路径
        if choosen_file_root != None:
            global MY_FILE_ROOT
            print(''.join(['File will be saved to path: ', choosen_file_root]))
            self.file_root = choosen_file_root
            MY_FILE_ROOT = choosen_file_root

        self.query_address = None  # 地址
        self.query_region = None  # 行政区划
        self.query_res = None  # 存储查询函数返回的查询结果

        self.navi_method = None  # 出行方式
        self.navi_origin = None  # 起始地址
        self.navi_dest = None  # 目的地址

        self.setup_UI(self)

        # 设置查询的回调函数
        self.getAddrButton.clicked.connect(self.getAddr)
        self.getRegionButton.clicked.connect(self.getRegion)
        self.startQueryButton.clicked.connect(self.startQuery)
        # 设置导航的回调函数
        self.getMethodButton.clicked.connect(self.getMethod)
        self.getOriginButton.clicked.connect(self.getOrigin)
        self.getDestButton.clicked.connect(self.getDest)
        self.startNaviButton.clicked.connect(self.startNavi)

        coord_x, coord_y, length, height = next(self.it)
        self.queryWebEngine = QWebEngineView(
            self)  # 新建QWebEngineView()对象显示查询结果地图
        self.queryWebEngine.setGeometry(coord_x, coord_y, length,
                                        height)  # 设置网页在窗口中显示的位置和大小

        coord_x, coord_y, length, height = next(self.it)
        self.naviWebEngine = QWebEngineView(
            self)  # 新建QWebEngineView()对象显示导航结果地图
        self.naviWebEngine.setGeometry(coord_x, coord_y, length,
                                       height)  # 设置网页在窗口中显示的位置和大小

    # 通过字符串询问窗口获取地址
    def getAddr(self):
        address, status_addr = QInputDialog.getText(self, 'Address',
                                                    'Enter address: ')
        if status_addr and address:
            self.GetAddrLineEdit.setText(str(address))
            self.query_address = address

    # 通过字符串询问窗口获取行政区划
    def getRegion(self):
        region, status_region = QInputDialog.getText(self, 'Region',
                                                     'Enter Region：')
        if status_region and region:
            self.GetRegionLineEdit.setText(str(region))
            self.query_region = region

    # 进行查询
    def startQuery(self):
        global curr_query_res  # 字符串化的查询结果保存在这个全局变量中
        
        # 获取当前文本框中的字符串
        self.query_address = self.GetAddrLineEdit.text()
        self.query_region = self.GetRegionLineEdit.text()
        if self.query_address and self.query_region:

            # 调用实用函数，传入用户输入的参数进行查询
            self.query_res = batch_address_lookup(self.query_address,
                                                  self.query_region,
                                                  self.file_root)
            # 将查询结果字符串化
            res_list = []
            for ii, item in enumerate(self.query_res[self.query_address]):
                # 一些格式化工作
                seq_str = ' '.join(['Point ', str(ii + 1)])
                addr_name = ' '.join(['Address: ', item[0]])
                coord_val = ' '.join(
                    ['Lat, Lng: ', ','.join([str(item[1]),
                                             str(item[2])])])
                line = '\n'.join([seq_str, addr_name, coord_val])
                res_list.append(line)
            self.query_res = '\n\n'.join(res_list)
            curr_query_res = self.query_res

            print('Loading query map...')

            self.queryWebEngine.load(
                QUrl(''.join([LOCAL_FILE, self.file_root,
                              QUERY_MAP_RES])))  # 在QWebEngineView中加载查询结果

    # 通过选项询问窗口获取出行方式
    def getMethod(self):
        items = METHOD
        item, status_method = QInputDialog.getItem(self, "Select input dialog",
                                                   'Method List:', items, 0,
                                                   False)
        if status_method and item:
            self.GetMethodLineEdit.setText(str(item))
            self.navi_method = item

    # 通过字符串询问窗口获取起始地址的经纬度坐标
    def getOrigin(self):
        origin, status_origin = QInputDialog.getText(self, 'Origin',
                                                     'Enter Origin：')
        if status_origin and origin:
            self.GetOriginLineEdit.setText(str(origin))
            self.navi_origin = origin

    # 通过字符串询问窗口获取目的地的经纬度坐标
    def getDest(self):
        dest, status_dest = QInputDialog.getText(self, 'Destination',
                                                 'Enter Destination：')
        if status_dest and dest:
            self.GetDestLineEdit.setText(str(dest))
            self.navi_dest = dest

    # 进行导航
    def startNavi(self):
        # 获取当前文本框中的字符串
        self.navi_method = self.GetMethodLineEdit.text()
        self.navi_origin = self.GetOriginLineEdit.text()
        self.navi_dest = self.GetDestLineEdit.text()

        if self.navi_method and self.navi_origin and self.navi_dest:
            # 调用实用函数，传入用户输入的参数进行查询
            path_project(self.navi_method, self.navi_origin, self.navi_dest,
                         self.file_root)

            print('Loading navigation map...')

            self.naviWebEngine.load(
                QUrl(''.join([LOCAL_FILE, self.file_root,
                              NAVI_MAP_RES])))  # 在QWebEngineView中加载导航的路径规划


class PrintQueryTextWindow(QtWidgets.QWidget):
    """
    定义了子窗口的属性
    """
    def __init__(self, parent=None):

        super(QtWidgets.QWidget, self).__init__(parent)  # 父类初始化

        self.setWindowTitle('Query Text')  # 新窗口名称
        self.resize(400, 400)  # 新窗口规模

        self.textEditWin = QtWidgets.QTextEdit()  # 定义一个显示文字的文本框
        self.printTextButton = QtWidgets.QPushButton(
            'Show Text')  # 定义显示文字按钮，点击则显示地点查询结果

        # 纵向布局子窗口
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.textEditWin)
        layout.addWidget(self.printTextButton)
        self.setLayout(layout)

        # 将回调函数与按钮的点击关联
        self.printTextButton.clicked.connect(self.printText)

    def printText(self):
        global curr_query_res
        if curr_query_res != None:
            self.textEditWin.setPlainText(
                curr_query_res)  # 将全局变量中存储的字符串化查询结果显示在文本框中
        else:
            self.textEditWin.setPlainText('Please query firstly!')


class LocateYourselfTextWindow(QtWidgets.QWidget):
    """
    定义了子窗口的属性
    """
    def __init__(self, parent=None):

        super(QtWidgets.QWidget, self).__init__(parent)  # 父类初始化

        self.file_path = None

        self.setWindowTitle('Location')  # 新窗口名称
        self.resize(400, 400)  # 新窗口规模

        self.textEditWin = QtWidgets.QTextEdit()  # 定义一个显示文字的文本框

        self.readCOMButton = QtWidgets.QPushButton(
            'Start Reading COM (Ctrl+C to Terminate)')  # 定义串口读取按钮，点击后从串口读取数据
        self.printReceivedTextButton = QtWidgets.QPushButton(
            'Show Text Received')  # 定义显示查询结果按钮，点击后显示接收机接收到的报文信息
        self.printYourLocationButton = QtWidgets.QPushButton(
            'Get Your Location')  # 定义显示接收机所在经纬度按钮，点击后显示接收机所处的经纬度坐标

        # 纵向布局子窗口
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.textEditWin)
        layout.addWidget(self.readCOMButton)
        layout.addWidget(self.printReceivedTextButton)
        layout.addWidget(self.printYourLocationButton)
        self.setLayout(layout)

        # 将回调函数与按钮的点击关联
        self.readCOMButton.clicked.connect(self.readCOM)
        self.printReceivedTextButton.clicked.connect(self.printReceivedText)
        self.printYourLocationButton.clicked.connect(self.printYourLocation)

    # 从串口读取数据
    def readCOM(self):
        COM_str, status_COM_str = QInputDialog.getText(
            self, 'COM String',
            'Enter string of COM (Ex."COM1"):')  # 询问要读取哪个串口
        baud_rate, status_baud_rate = QInputDialog.getText(
            self, 'Baud Rate', 'Enter Baud Rate (Ex."38400"):')  # 询问读取的波特率
        if (COM_str and status_COM_str) and (baud_rate and status_baud_rate):
            description = None
            srl = serial.Serial(COM_str, baud_rate)
            if srl.isOpen():
                global MY_FILE_ROOT
                description = 'COM successfully opened!'
                self.file_path = ''.join([MY_FILE_ROOT,
                                          COM_TEXT_RES])  # 打开写入文件
                fp = open(self.file_path, 'w')
            else:
                description = 'COM open failed!\n'

            print('Reading, file saved to {}'.format(self.file_path))

            try:  # 进行串口的数据读取
                received_bytes = b''
                timer = 50
                while timer:
                    count = srl.inWaiting()
                    if count > 0:
                        data = srl.read(count)
                        if data != received_bytes:
                            print(data)
                            fp.write(data.decode('utf-8'))  # 读取的数据写入文件
                            received_bytes = data
                            timer -= 1
                description = ''.join([description, ' Successfully Read!'])
            except KeyboardInterrupt:  # 键盘输入中断读取
                description = ''.join([
                    'KeyboardInterrupt, ', description, ' Successfully Read!'
                ])
            finally:
                if srl != None:  # 读取成功
                    self.textEditWin.setPlainText(description)
                    fp.close()
                    srl.close()

    # 打印从接收机读取的源数据
    def printReceivedText(self):
        if self.file_path != None:
            with open(self.file_path, 'r') as fp:
                lines = fp.readlines()
                self.textEditWin.setPlainText(
                    ''.join(lines))  # 将从文件中读取的结果显示在文本框中
        else:
            self.textEditWin.setPlainText('Please reading COM firstly!')

    # 打印接收机所处经纬度
    def printYourLocation(self):
        if self.file_path != None:
            with open(self.file_path, 'r') as fp:
                lines = fp.readlines()

                # 从文件中提取经纬度信息
                lat, lng = None, None
                for line in lines:
                    if 'RMC' in line:
                        data_list = line.split(',')
                        if 'A' in data_list[2] and data_list[3] and data_list[5]:
                            lat, lng = data_list[3], data_list[5]
                    elif 'GGA' in line:
                        data_list = line.split(',')
                        if data_list[2] and data_list[4]:
                            lat, lng = data_list[2], data_list[4]
                    else:
                        continue
                    # 将度分制表示的经纬度转换为十进制
                    lat, lng = round(
                        float(lat[:2]) + float(lat[2:]) / 60.0,
                        6), round(float(lng[:3]) + float(lng[3:]) / 60.0, 6)
                self.textEditWin.setPlainText(''.join(
                    ['lat, lng: ', ','.join([str(lat), str(lng)])]))
        else:
            self.textEditWin.setPlainText('Please reading COM firstly!')


def transform_lat(x, y):
    """
    纬度转换函数，用于转换纬度
    """
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(
        abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) +
            20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * PI) +
            40.0 * math.sin(y / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * PI) +
            320 * math.sin(y * PI / 30.0)) * 2.0 / 3.0
    return ret


def transform_lng(x, y):
    """
    经度转换函数，用于转换经度
    """
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(
        abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) +
            20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * PI) +
            40.0 * math.sin(x / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * PI) +
            300 * math.sin(x * PI / 30.0 * PI)) * 2.0 / 3.0
    return ret


def transform(lat, lng):
    """
    经纬度转换函数，被函数GCJ02_to_GPS84()所调用，用于转换经纬度
    """
    delta_lat = transform_lat(lng - 105.0, lat - 35.0)
    delta_lng = transform_lng(lng - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * PI
    magic = math.sin(rad_lat)
    magic = 1 - EE * magic * magic
    sqrt_magic = math.sqrt(magic)
    delta_lat = (delta_lat * 180.0) / ((PARA_A * (1 - EE)) /
                                       (magic * sqrt_magic) * PI)
    delta_lng = (delta_lng * 180.0) / (PARA_A / sqrt_magic *
                                       math.cos(rad_lat) * PI)
    new_lat = lat + delta_lat
    new_lng = lng + delta_lng
    return new_lat, new_lng


def BD09_to_GCJ02(lat, lng):
    """
    经纬度转换函数，将BD09坐标转换为GCJ02坐标
    """
    y, x = lat - 0.006, lng - 0.0065
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * X_PI)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * X_PI)
    new_lng = z * math.cos(theta)
    new_lat = z * math.sin(theta)
    return new_lat, new_lng


def GCJ02_to_GPS84(lat, lng):
    """
    经纬度转换函数，将GCJ02坐标转换为GPS84坐标
    """
    coord = transform(lat, lng)
    new_lng = lng * 2 - coord[1]
    new_lat = lat * 2 - coord[0]
    return new_lat, new_lng


def BD09_to_GPS84(lat, lng):
    """
    经纬度转换函数，将BD09坐标转换为GPS84坐标
    """
    tmp_gcj02 = BD09_to_GCJ02(lat, lng)
    tmp_gps84 = GCJ02_to_GPS84(tmp_gcj02[0], tmp_gcj02[1])
    new_lng = round(tmp_gps84[1], 6)
    new_lat = round(tmp_gps84[0], 6)
    return new_lat, new_lng


def replace_jQuery_source(file_root, filename, tar_jQuery_source,
                          new_jQuery_source):
    """
    由于原始html中文件中的jQuery库，所以要将其换为可用源
    """
    sour_file_path = ''.join([file_root, filename])
    new_file_path = ''.join([file_root, TEMP_MAP_RES])
    # 打开源文件和临时文件
    with open(sour_file_path, 'r',
              encoding='utf-8') as fr, open(new_file_path,
                                            'w',
                                            encoding='utf-8') as fw:
        for line in fr:
            if tar_jQuery_source in line:  # 发现目标行
                new_line = line.replace(tar_jQuery_source,
                                        new_jQuery_source)  # 通过更改字符串实现换源操作
                fw.write(new_line)
            else:
                fw.write(line)
    remove(sour_file_path)  # 删除源文件
    rename(new_file_path, sour_file_path)  # 临时文件改为源文件名


def batch_address_lookup(address, region, file_root):
    """
    查询地址所对应的信息
    参数：
        address: 需要查询的地点列表，其中包含了待查询的一组地名
        region: 指定查询的目标行政区划，如“深圳市”、“广东省”等
        file_root: 存储相关文件的路径
    返回值：
        res_dict: 含有查询地点结果及其经纬度信息的字典
    """

    url = 'http://aPI.map.baidu.com/place/v2/search?query={}&region={}&output=json&ak={}'.format(
        address, region, MY_AK)  # 构造查询URL
    res = requests.get(url)
    json_data = json.loads(res.text)  # json数据转为python字典

    print('Querying')

    res_dict = {}
    if json_data['status'] == 0:  # 查询成功
        with open(''.join([file_root, POINT_JSON_DATA]), 'w',
                  encoding='utf-8') as fp:
            json.dump(json_data, fp, indent=4,
                      ensure_ascii=False)  # 将原始json数据写入文件

        # 从获取到的json数据中提取目标信息，即地点名称、地点经纬度
        res_dict[address] = []
        for result in json_data['results']:
            result.setdefault('address', '-')
            name = result['name']
            addr = result['address']
            detail_addr = ' '.join([addr, name])
            lat = result['location']['lat']
            lng = result['location']['lng']
            res_dict[address].append([detail_addr, lat, lng])
    else:  # 查询失败
        raise Exception('Return value error, query failed!')

    coord_list = []
    for item in res_dict[address]:
        lat, lng = item[1], item[2]
        lat, lng = BD09_to_GPS84(float(lat), float(lng))
        coord_list.append([lat, lng])

    center = coord_list[0]
    tar_map = folium.Map(
        center,
        zoom_start=10,
        control_scale=True,
        title='Point Query Route',
    )  # 构造地图
    tar_map.add_child(folium.LatLngPopup())  # 根据鼠标光标的点击实时显示经纬度
    tooltip = 'Click me for more information'
    for ii, coord in enumerate(coord_list):
        folium.map.Marker(location=coord,
                          popup=''.join(
                              ['Point',
                               str(ii + 1), res_dict[address][ii][0]]),
                          tooltip=tooltip,
                          icon=folium.Icon(color='blue')).add_to(tar_map)

    tar_map.save(''.join([file_root, QUERY_MAP_RES]))

    replace_jQuery_source(file_root, QUERY_MAP_RES, JQUERY_SOUR,
                          NEW_JQUERY_SOUR)

    with open(''.join([file_root, POINT_QUERY_RES]), 'w',
              encoding='utf-8') as fp:
        json.dump(res_dict, fp, indent=4,
                  ensure_ascii=False)  # 将提取所得的目标信息字典写入文件
        return res_dict


def path_project(method, origin, dest, file_root):
    """
    根据传入的信息在地图上绘制出行轨迹，实现路径规划
    参数：
        method: 出行方式，可为'driving', 'riding', 'walking', 'transit'的其中之一
        origin: 起始地点的经纬度字符串，如'40.01116,116.339303'
        dest: 目标地点的经纬度字符串，格式与origin类似
        file_root: 存储相关文件的路径
    返回值：
        无返回值
    """

    url = 'http://aPI.map.baidu.com/directionlite/v1/{}?origin={}&destination={}&ak={}'.format(
        method, origin, dest, MY_AK)  # 构造查询URL
    res = requests.get(url)
    json_data = json.loads(res.text)

    print('Navigating!')

    route_coord_list = []  # 用于存储路径上的经纬度坐标点
    if json_data['status'] == 0:  # 查询成功
        with open(''.join([file_root, NAVI_JSON_DATA]), 'w',
                  encoding='utf-8') as fp:
            json.dump(json_data, fp, indent=4,
                      ensure_ascii=False)  # 将原始json数据写入文件

        # 从json构造的字典中提取目标信息
        for result in json_data['result']['routes'][0]['steps']:
            path = result['path']
            path = path.split(';')  # 获取子路径中的一组经纬度字符串，并以列表储存
            # 将经纬度字符串转为浮点数
            for coord in path:
                coord = coord.split(',')  # 分离出经度字符串和纬度字符串
                coord[0], coord[1] = coord[1], coord[0]
                route_coord_list.append([float(ii) for ii in coord])  # 转型

        # 将列表中的所有由BD09坐标表示的经纬度转为通用的由GPS84坐标表示的经纬度
        for ii in range(len(route_coord_list)):
            tmp_coord = BD09_to_GPS84(route_coord_list[ii][0],
                                      route_coord_list[ii][1])

        center = list((route_coord_list[int(len(route_coord_list) / 2)][0],
                       route_coord_list[int(len(route_coord_list) /
                                            2)][1]))  # 取位于列表中段的坐标作为地图中心
        tar_map = folium.Map(center,
                             zoom_start=10,
                             control_scale=True,
                             title='Navigation Route')  # 构造地图

        route = folium.PolyLine(route_coord_list,
                                weight=2,
                                color='blue',
                                opacity=0.5).add_to(tar_map)  # 根据路径点绘制路径

        tar_map.add_child(folium.LatLngPopup())  # 根据鼠标光标实施显示经纬度

        # 在绘制的路径上添加标注点
        tooltip = 'Click me for more information'
        color_board = ['blue', 'red', 'green']
        seq_point = 1
        for ii, coord in enumerate(route_coord_list):
            curr_color = None

            if ii == 0:
                curr_color = color_board[0]
            elif ii == len(route_coord_list) - 1:
                curr_color = color_board[1]
            elif ii % MARKER_INTERVAL == 0:
                curr_color = color_board[2]

            if curr_color != None:
                folium.map.Marker(
                    location=coord,
                    popup=''.join(['Point ', str(seq_point)]),
                    tooltip=tooltip,
                    icon=folium.Icon(color=curr_color)).add_to(tar_map)
                seq_point += 1

        tar_map.save(''.join([file_root, NAVI_MAP_RES]))  # 以HTML格式保存路径地图

        replace_jQuery_source(file_root, NAVI_MAP_RES, JQUERY_SOUR,
                              NEW_JQUERY_SOUR)

    else:  # 查询失败
        raise Exception('Return value error, query failed!')


if __name__ == "__main__":

    app = QApplication(argv)

    main_win = MainWindow(MY_FILE_ROOT)  # 主窗口
    main_win.show()

    query_text_win = PrintQueryTextWindow()  # 查询结果子窗口
    main_win.printQueryButton.clicked.connect(query_text_win.show)

    locate_yourself_text_win = LocateYourselfTextWindow()  # 定位信息子窗口
    main_win.locateYourselfButton.clicked.connect(
        locate_yourself_text_win.show)

    exit(app.exec_())