# -*- coding: utf-8 -*-

#
# Created by: PyQt5 UI code generator 5.9
#

from PyQt5.QtWidgets import QApplication , QMainWindow,QWidget,QPushButton,QVBoxLayout,QComboBox

from PyQt5 import QtCore, QtGui, QtWidgets

from CoreWidget import *
import wxtools
import os
import pickle
from pathlib import Path



class LogInThread(QtCore.QThread):
    trigger = QtCore.pyqtSignal(tuple)

    def setValue(self,father):
        self.father = father

    def run(self):
        bot = wxtools.myBot(cache_path=self.father.cache,qr_callback = self.father.qr_callback,login_callback=self.father.login_callback)
        bot.set_init()
        @bot.register(except_self=False)
        def get_message(msg,index_file = [1]):
            filename = None
            if msg.type in (PICTURE,VIDEO,ATTACHMENT):
                filename = bot.path /(str(index_file[0]) + msg.file_name)
                index_file[0]+=1
                msg.get_file(str(filename))
                filename = str(filename)
            self.trigger.emit((msg,'MSG',filename))

        if bot.is_first:
            bot.first_run()
        
        self.trigger.emit((bot, 'BOT'))
        # bot.auto_run()

class WelcomeFrame:
    def __init__(self,cache=False):
        self.cache = cache#存储登录信息路径的pkl文件 
        self.users_login=self.get_users_login()
        self.cache_select = None
    def get_users_login(self):
        users = [str(i.name).replace('.jpg','') for i in self.cache.parent.glob('*.jpg')]
        users = [i.split('_') for i in users]
        return users
    def setupUi(self, Form,ox,oy,w,h,father=None):
        self.father_view=father
        self.Form=Form
        self.size=(w,h)

        self.addLabel()
    def addLabel(self):
        w,h = self.size
        self.combox = QComboBox(self.Form)
        names = [name for _,name in self.users_login]
        self.combox.addItems(names)
        self.combox.activated[str].connect(self.comActivated)
        self.combox.move(int(w*3/8),int(h/2*1.3-w/8))
        

        self.LogIn_button = YTextButton(self.Form)
        self.LogIn_button.setTextIcon("登录",(12,234,12),(0,0,0),(int(w/2),int(w/6)))
        self.LogIn_button.clicked.connect(self.saved_log_in)
        self.LogIn_button.setGeometry(int(w/4), int(h/2*1.3),int(w/2),int(w/6))
        self.LogIn_button.show()

        self.reLogIn_button = YTextButton(self.Form)
        self.reLogIn_button.setTextIcon("登陆新账号",(12,234,12),(0,0,0),(int(w/4),int(w/12)))
        self.reLogIn_button.clicked.connect(self.new_log_in)
        self.reLogIn_button.setGeometry(int(w*3/8), int(h/2*1.3+w/5),int(w/4),int(w/12))
        self.reLogIn_button.show()


        self.QR_label = QLabel(self.Form)
        self.QR_label.setScaledContents(True)
        self.QR_label.setGeometry(int(w/6), int(w/3), int(w/6*4), int(w/6*4))
        self.QR_label.hide()

        if len(names) == 0:
            self.combox.hide()
        else:
            self.comActivated(names[0])
            self.combox.show()
    def comActivated(self,text):
        for yxsid,name in self.users_login:
            if text == name:
                yxsid_now = yxsid
                s = self.cache.with_name(yxsid+'_'+name+'.jpg')
                self.QR_label.setPixmap(QtGui.QPixmap(str(s)))
                self.QR_label.show()
                self.cache_select = self.cache.with_name(yxsid+'_wx.pkl')
                break
    def new_log_in(self):
        if Path(self.cache).is_file():
            os.remove(self.cache)
        self.get_QRcode()
    def saved_log_in(self):
        if self.cache_select is not None:
            self.cache.write_bytes(self.cache_select.read_bytes())
        self.get_QRcode()
    def qr_callback(self, uuid, status, qrcode):
        open('qrcode.png','wb').write(qrcode)
        s=QtGui.QImage('qrcode.png')
        self.QR_label.setPixmap(QtGui.QPixmap.fromImage(s))
        self.QR_label.show()
        os.remove('qrcode.png')

    def login_callback(self,*t):
        print('login callback')

    def bot_callback(self,callback_data):
        if len(callback_data) == 2:
            data, TYPE = callback_data
        else:
            data, TYPE, file_path= callback_data
        if TYPE == 'BOT':
            self.bot=data
            self.father_view.bot = self.bot
            self.father_view.Form.setBot(self.bot)
            self.hide()
            self.father_view.setupUi()
            self.father_view.show()
        elif TYPE == 'MSG':
            self.bot.get_message(data,file_path)
            return
        elif TYPE == 'FIRST':
            pass
        p = Path(self.cache)
        print(p.is_file(), '是否产生登录文件?')
        t = p.read_bytes()
        yxsid = self.bot.get_user_yxsid(self.bot.self)
        open(p.with_name(yxsid+'_wx.pkl'),'wb').write(t)
        img_name = p.with_name(yxsid+'_'+self.bot.self.name+'.jpg')
        self.bot.self.get_avatar(img_name)
    def get_QRcode(self):
        print('jump to user frame')
        self.loginthread=LogInThread()
        self.loginthread.setValue(self)
        self.loginthread.trigger.connect(self.bot_callback)
        self.loginthread.start()

    def goto_view(self,name):
        #跳转到conversation的内容界面
        self.father_view.goto_view('chat',name)

    def hide(self):
        self.LogIn_button.hide()
        self.QR_label.hide()

    
