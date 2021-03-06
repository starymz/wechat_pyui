# -*- coding: utf-8 -*-

# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QWidget, QSlider, QApplication,QMainWindow,
                             QHBoxLayout, QVBoxLayout,QLabel,QFrame)
from PyQt5.QtCore import Qt,QPoint,QRect
from PyQt5.QtGui import (QTextDocument,QPalette,QBrush,QColor,QFontMetrics,QPainter,
                        QPen,QImage,QPixmap,QMovie,QLinearGradient,QCursor,QPolygon)
import sys
from pathlib import Path
import re
import os
from PIL import Image
from os.path import getsize
from yxspkg import songziviewer as ysv
from wxpy import TEXT, PICTURE, MAP, CARD, NOTE, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS, SYSTEM
import video_player
import imageio
import webbrowser
import subprocess
from multiprocessing import Process
GLOBAL_DICT = {}
platform = sys.platform

SYSTEM_YXS = 'SYSTEM_YXS'
global_font=QtGui.QFont()
global_font.setFamily('SimHei')

data_path = Path(sys.path[0]) / 'wechat_data'
WECHAT_DATA_PATH = str(data_path)+'/'

#宏定义值
AUTO_PUSH=1
CRITERION = int(100/1280*640)
#用户头像大小
HEAD_PHOTO_LENGTH = 80/90*CRITERION
ME=5 
OTHER=6
emoji = dict()
class Emoji:
    def __init__(self,emoji_path):
        self.emoji_path = Path(emoji_path)
        self.name_list = self.emoji_path.name[:-4].split('_')
        
def read_emoji(path_emoji=None):
    if path_emoji is None:
        path_emoji = WECHAT_DATA_PATH+'/emoji'
    p=Path(path_emoji)
    emo = {j:str(i) for i in p.glob('*.png') for j in Emoji(i).name_list}
    emoji.update(emo)
read_emoji()
class YButton(QtWidgets.QPushButton):
    def __init__(self,d=None):
        super().__init__(d)
        self.setStyleSheet('border:none')
    def setButton(self,I,pw,ph,objectname,position=None,connect=None,callback = None):
        if I is not None:
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(I))
            self.setIcon(icon)
            self.setIconSize(QtCore.QSize(pw , ph))
        self.setObjectName(objectname)
        if position is not None:self.setGeometry(QtCore.QRect(*position))
        if connect is not None:self.clicked.connect(connect)
        if callback is not None:self.callback = callback
    def selfCallback(self):
        self.callback(self)

class YScrollArea(QtWidgets.QScrollArea):
    def __init__(self,*d,**k):
        super().__init__(*d,**k)
        self.setAcceptDrops(False)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.bottom = 0
        self.widgets = list()
        self.widgets_dict = dict()
        self.bar=self.verticalScrollBar()
        
    def mousePressEvent(self,e):
        print(e.x(),e.y(),'Ps')
    def mouseReleaseEvent(self,e):
        print(e.x(),e.y(),'Rs')
    def resizeEvent(self,d):
        width_w = self.width()
        height_w = self.main_widget.height()
        self.main_widget.resize(width_w,height_w)
        for i in self.widgets:
            i.adjust_position(width_w)

    def append_element(self,element,key = 0):#默认widgets_dict的key值为0
        
        h=element.height()
        mw,mh = self.main_widget.width(),self.main_widget.height()
        if h+self.bottom > mh:
            self.main_widget.resize(mw,self.bottom+h)
            self.main_widget.setMinimumSize(mw,self.bottom+h)
        element.move(0,self.bottom)
        self.bottom += h
        self.widgets.append(element)
        self.widgets_dict[key] = element
    def insert_elements(self,elements,keys = None):#在elements顶部插入 多个element
        if keys is None:
            keys = [0]*len(elements)
        mw, mh = self.main_widget.width(), self.main_widget.height()
        heights = [e.height() for e in elements]
        delta_h = sum(heights)
        if delta_h + self.bottom > mh:
            self.main_widget.resize(mw,self.bottom+delta_h)
            self.main_widget.setMinimumSize(mw, self.bottom+delta_h)
        self.bottom += delta_h
        [i.move(0, i.pos().y()+delta_h) for i in reversed(self.widgets)]
            
        for i,key in zip(reversed(elements),reversed(keys)):
            height = i.height()
            i.move(0,delta_h-height)
            delta_h -= height
            self.widgets.insert(0,i)
            self.widgets_dict[key] = i

    def setWidget(self,w): #设置并记录该滚动区域的widget
        super().setWidget(w)
        self.main_widget = w
    def reset(self):
        self.bottom = 0
        self.main_widget.resize(self.main_widget.width(), 1)
        self.main_widget.setMinimumSize(self.main_widget.width(), 2)
        [i.hide() for i in self.widgets]
        self.widgets = list()
    def slideBar(self,pos='bottom'):
        if pos == 'top':
            self.bar.setValue(0)
        else:
            self.bar.setValue(self.bottom)
#滚动区域的Widget
class YWidget(QtWidgets.QWidget):
    def __init__(self,*d,**k):
        super().__init__(*d,**k)
    def mouseMoveEvent(self,e):
        # print(e.x(),e.y(),'M')
        pass
    def mousePressEvent(self,e):
        # print(e.x(),e.y(),'P')
        pass
    def mouseReleaseEvent(self,e):
        # print(e.x(),e.y(),'R')
        pass

class YTextButton(YButton):
    position_dict={'center':Qt.AlignCenter,'left':Qt.AlignLeft,'hcenter':Qt.AlignHCenter,'vcenter':Qt.AlignVCenter,'justify':Qt.AlignJustify}
    def setTextIcon(self,text,color_background,color_text,icon_size,position='center',font=None,font_percent_size=0.4):
        position_qt=self.position_dict[position.lower()]
        qp = QtGui.QPainter()
        icon=QtGui.QIcon()
        if font is None:
            font=global_font
            font.setPixelSize(icon_size[1]*font_percent_size)
        img=QtGui.QImage(icon_size[0],icon_size[1],QtGui.QImage.Format_RGB32)
        img.fill(QtGui.QColor(*color_background))
        qp.begin(img)
        qp.setPen(QtGui.QColor(*color_text))
        qp.setFont(font)
        qp.drawText(img.rect(), position_qt,text)
        qp.end()
        qimg=QtGui.QPixmap.fromImage(img)
        icon.addPixmap(qimg)
        self.setIcon(icon)
        self.setIconSize(QtCore.QSize(*icon_size))


#聊天时显示对话文字内容的bubble
class YSentenceBubble(QtWidgets.QWidget):
    me_color=160,232,88
    other_color=255,255,254
    other_rect_pos=(120/90*CRITERION,12/90*CRITERION)
    border_text=8/90*CRITERION #bubble和文字边框之间的距离
    font_size=int(30/90*CRITERION) #字体大小css  单文px

    max_width=450/90*CRITERION
    
    def __init__(self,d):
        super().__init__(d)
        self.Yw=d.Yw
        s='|'.join(emoji.keys())
        s=s.replace('[',r'\[')
        s=s.replace(']',r'\]')
        self.emoji_re = re.compile('({})'.format(s))
        self.html_table = str.maketrans(
            {'<':'&lt;','>':'&gt;','\n':'<br/>',' ':'&nbsp;'}
        )
        self.min_height=d.min_height
    def paintEvent(self,e):
        qp = QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()
 
    def drawWidget(self, qp):

        qp.setBrush(QBrush(self.color))
        qp.setPen(QPen(self.color))
        qp.drawPolygon(self.bubble_ploygon)

        qp.setPen(QPen(QColor(220,220,220)))
        qp.drawPolygon(self.bubble_ploygon)

    
    def setBubble(self,identity=ME):
        self.identity = identity
        if identity is ME:
            self.color=QColor(*self.me_color)
            Width=self.Ysize[0]+self.border_text + HEAD_PHOTO_LENGTH/6
            rect_pos=self.Yw-(self.other_rect_pos[0]+Width),self.other_rect_pos[1]
        else:
            self.color=QColor(*self.other_color)
            rect_pos=self.other_rect_pos[0]-self.border_text,self.other_rect_pos[1]
        
        self.move(*rect_pos)

    def setMessage(self,text,identity=ME):
        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setObjectName("textEdit")
        pl=QPalette()
        pl.setBrush(pl.Base,QBrush(QColor(255,0,0,0)))
        self.textEdit.setPalette(pl)
        self.textEdit.setStyleSheet("border:none;")
        self.textEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit.setReadOnly(True)
        
        self.d = self.textEdit.document() 
        self.d.setTextWidth(self.max_width) 
        def sub_func(t): 
            ft = '< img src="{src}" height="{height}"/>' 
            b = t.group() 
            return ft.format(src= emoji[b], height = int(self.font_size)) 
        tt = self.emoji_re.sub(sub_func, text.translate(self.html_table)) 
        text = '<p style="font-size:{height}px;font-family:SimHei">{text}</p >'.format(text = tt, height=self.font_size) 
        self.textEdit.setHtml(text)



        width = self.d.idealWidth()   #获取对话框的宽度
        if platform.startswith('linux'):
            width += int(self.font_size/4)
        self.Ysize=width,self.d.size().height()

        self.setBubble(identity)
        Width, Height = self.Ysize
        Height0 = max(HEAD_PHOTO_LENGTH-2*self.border_text,Height)
        pw,ph = Width+self.border_text*2, Height0+self.border_text*2
        ruler = HEAD_PHOTO_LENGTH
        if identity is ME:
            self.bubble_ploygon = QPolygon([
                QPoint(0, 0),
                QPoint(pw,0),
                QPoint(pw,ruler/3),
                QPoint(pw+ruler/6,ruler/2),
                QPoint(pw,ruler/3*2),
                QPoint(pw,ph),
                QPoint(0,ph)])
            text_pos_x = self.border_text
        else:
            t = ruler/6
            self.bubble_ploygon = QPolygon([
                QPoint(t, 0),
                QPoint(pw+t,0),
                QPoint(pw+t,ph),
                QPoint(t,ph),
                QPoint(t,ruler/3*2),
                QPoint(0,ruler/2),
                QPoint(t,ruler/3)])
            text_pos_x = self.border_text+ruler/5
        self.textEdit.setGeometry(
            text_pos_x, (Height0-Height)/2+self.border_text, Width, Height)

        self.window_height = Height0+self.border_text*4


class YSystemBubble(QtWidgets.QWidget):#显示系统提示消息
    radius = 5/90*CRITERION

    font_size = int(30/90*CRITERION)  # 字体大小css  单文px

    def __init__(self, d):
        super().__init__(d)
        self.Yw = d.Yw
        s = '|'.join(emoji.keys())
        s = s.replace('[', r'\[')
        s = s.replace(']', r'\]')
        self.emoji_re = re.compile('({})'.format(s))
        self.color = QColor(205,205,205)
        self.max_width = 7*CRITERION

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def drawWidget(self, qp):

        Width, Height = self.Ysize
        self.rect = QRect(0, 0, Width, Height)
        self.textEdit.setGeometry(0, 0, Width, Height)
        qp.setBrush(QBrush(self.color))
        qp.setPen(QPen(self.color))
        qp.drawRoundedRect(self.rect, self.radius, self.radius)

    def setMessage(self, text, identity=ME):
        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setObjectName("textEdit")
        pl = QPalette()
        pl.setBrush(pl.Base, QBrush(QColor(255, 0, 0, 0)))
        self.textEdit.setPalette(pl)
        self.textEdit.setStyleSheet("border:none;")
        self.textEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit.setReadOnly(True)

        self.d = self.textEdit.document()
        self.d.setTextWidth(self.max_width)

        def sub_func(t):
            ft = '< img src="{src}" height="{height}" />' #替换emoji
            b = t.group()
            return ft.format(src=emoji[b], height=self.font_size)
        tt = self.emoji_re.sub(sub_func, text)
        #font-family:\'Times New Roman\', Times, serif
        text = '<p style="font-size:{height}px;color:white;font-family:SimHei">{text}</p >'.format(
            text=tt.replace('\n', '<br />'), height=self.font_size)
        self.textEdit.setHtml(text)

        width = self.d.idealWidth()  # 获取对话框的宽度
        if platform.startswith('linux'):
            width += int(self.font_size/4)
        self.Ysize = width, self.d.size().height()
        self.resize(*self.Ysize)

#设置图片和动图的显示框
class YPictureBubble(QLabel):
    def __init__(self,widget):
        super().__init__(widget)
        self.parent_widget = widget
        self.setScaledContents(True)
    def setPicture(self,image_name):
        self.filename = image_name
        max_width = 300
        is_gif = False
        if image_name[-3:].lower() == 'gif':
            self.gif = QMovie(image_name)
            if self.gif.isValid():
                is_gif = True
                self.setMovie(self.gif)
                self.gif.start()
                g = self.gif.currentImage()
                w,h = (g.width(),g.height())
        if not is_gif:
            im = Image.open(image_name)
            w,h = im.size

            self.setPixmap(im.toqpixmap())
        
        if w>=h and w>max_width:
            ratio = max_width/w
        elif h>w and h>max_width:
            ratio = max_width/h
        else:
            ratio = 1
        w,h = int(w*ratio),int(h*ratio)
        self.resize(w,h)

class YTalkWidget(QtWidgets.QWidget):
    obj_name={ME:'me',OTHER:'other'}
    other_rect_topleft=(120/90*CRITERION,12/90*CRITERION)
    max_size=250/90*CRITERION
    min_size=104/90*CRITERION
    font = QtGui.QFont()
    font.setFamily('SimHei')
    font.setPixelSize(0.25*CRITERION)
    def __init__(self,d=None,Bot = None):
        super().__init__(d)
        self.Yw=d.width()
        self.bot = Bot
        self.pos_me=(self.Yw-110/90*CRITERION,12/90*CRITERION)
        self.pos_other=(30/90*CRITERION,12/90*CRITERION)
        self.pic_qsize=QtCore.QSize(HEAD_PHOTO_LENGTH,HEAD_PHOTO_LENGTH)
        self.min_height=104/90*CRITERION
        self.lable_geometry = None #显示消息widget的geometry
        self.message_label = None
    def setContent(self,value,Format,icon_name,identity,user_name=None):
        self.Format = Format 
        self.value = value
        if Format == NOTE:
            Format = SYSTEM_YXS
            identity = None
        self.identity=identity
        self.Format = Format
        if identity in (ME,OTHER):
            self.setPic(icon_name,self.obj_name[identity])
        if Format == TEXT:
            h=self.setMessage(value)
            h = max(h,self.min_size)
        elif Format == PICTURE:#显示表情或者图片
            h=self.setMessage_Picture(value)
            h = max(h,self.min_size)
        elif Format == SYSTEM_YXS:
            h=self.setMessage_System(value)
        elif Format == VIDEO:
            video_path = Path(value)
            path_video_cache = self.bot.thumbnail_path / ('thumbnail_'+video_path.name)
            path_video_cache = path_video_cache.with_suffix('.jpg')

            if not path_video_cache.is_file():
                reader = imageio.get_reader(value)
                img = reader.get_next_data()
                reader.close()
                img = Image.fromarray(img)
                w,h = img.size 
                if w>h:
                    rate = w/150
                else:
                    rate = h/150
                img.thumbnail((w//rate,h//rate))
                img.save(path_video_cache)
            h = self.setMessage_Picture(str(path_video_cache),is_video=True)
        elif Format == ATTACHMENT:
            h = self.setMessage_Attachment(value)
        elif Format == SHARING:
            h = self.setMessage_Attachment(value,is_sharing = True)
        elif Format == RECORDING:
            h = self.setMessage_Attachment(value)
        else:
            h = self.setMessage('不支持的消息类型，请在手机中查看：{}\n{}'.format(Format,value))
        if user_name and identity is OTHER:
            dh = 13
            h += dh
            pos = self.message_label.pos()
            x,y = pos.x(), pos.y()
            self.name_label = QLabel(user_name,self)
            self.name_label.setFont(self.font)
            self.message_label.move(x,y+dh)
            
            self.name_label.move(x,y)
        
        self.resize(self.Yw,h)
    def mouseDoubleClickEvent(self,e): 
        if e.buttons() == Qt.LeftButton and self.lable_geometry:
            g = self.lable_geometry
            x,y,w,h = g.x(),g.y(),g.width(),g.height()
            m_x, m_y = e.x(),e.y()
            if not (x < m_x <x+w and y<m_y<y+h):
                return #点击不在区域内
            print('open a file')
            if self.Format in (PICTURE,VIDEO):
                if not Path(self.value).exists():
                    value = str(self.bot.path.parent.with_name('wechat_data') / 'icon' / 'error.jpg')
                else:
                    value = self.value
            if self.Format == PICTURE:
                self._display = ysv.ImageViewer(name=value)
            elif self.Format == VIDEO:
                if platform.startswith('linux'):
                    p = Process(target = subprocess.call,args=(['ffplay',value],))
                    p.start()
                else:
                    self._play = video_player.Player([value])
                    self._play.show()
                    self._play.resize(700,600)
                    self._play.player.play()
            elif self.Format == SHARING:
                url = self.value.split()[0]
                webbrowser.open(url)
            elif self.Format == RECORDING:
                self.play_audio = video_player.play_audio(self.value)
                self.play_audio.start()
        else:
            pass
    def setMessage_System(self,value):
        self.system_bubble = YSystemBubble(self)
        self.message_label = self.system_bubble
        self.system_bubble.setMessage(value,None)
        w = (self.Yw - self.system_bubble.width()) // 2
        self.system_bubble.move(w,2)
        return self.system_bubble.Ysize[1]+4
    def adjust_position(self,width_w):#当窗口大小变化时调整对话内容的位置
        y=self.pos().y()
        sel_width = self.width()
        if self.identity is ME:
            pos_width=width_w-sel_width
        elif self.identity is None:
            pos_width = (width_w - sel_width)//2
        else:
            pos_width = 0
        self.move(pos_width, y)
    def setMessage(self,e): # 绘制用户文字信息
        self.message_bubble = YSentenceBubble(self)
        self.message_label = self.message_bubble
        self.message_bubble.setMessage(e,self.identity)
        h = self.message_bubble.window_height
        self.message_bubble.resize(self.Yw,h)
        return h+2

    def setPic(self,icon_name,oname): #绘制用户头像
        self.figure_button=YButton(self)
        self.figure_button.setIcon(icon_name)
        self.figure_button.setIconSize(self.pic_qsize)
        self.figure_button.setObjectName(oname)
        if self.identity is ME:
            pos=self.pos_me
        else:
            pos=self.pos_other
        self.figure_button.setGeometry(*pos,HEAD_PHOTO_LENGTH,HEAD_PHOTO_LENGTH)
    def setMessage_Sharing(self,value):
        return self.setMessage_Attachment(value,True)
    def setMessage_Attachment(self,value,is_sharing = False):#定义显示附件的组件
        self.attachment_bubble = QLabel(self)
        self.message_label = self.attachment_bubble
        
        self.attachment_bubble.setFrameShape(QFrame.Box)
        self.attachment_bubble.setStyleSheet('QLabel{border-width:1px;border-style:solid;border-color:rgb(150,180,140);background-color:rgb(250,250,250)}')

        self.attachment_bubble.resize(int(5.5*CRITERION),int(1.5*CRITERION))
        if self.identity is ME:
            pos = self.pos_me[0]-self.attachment_bubble.width()-5,self.pos_me[1]
        else:
            pic_width = self.pic_qsize.width()
            pos = self.pos_other[0]+5+pic_width,self.pos_other[1]
        self.attachment_bubble.move(*pos)
        if is_sharing:
            icon_path = self.bot.path.parent.with_name('wechat_data') / 'icon' / 'icon_sharing.jpg'
        else:
            icon_path = self.bot.path.parent.with_name('wechat_data') / 'icon' / 'icon_file_red.jpg'
        self.file_icon = QLabel(self.attachment_bubble)
        self.file_icon.setScaledContents(True)
        pixmap = Image.open(icon_path).toqpixmap()
        self.file_icon.setPixmap(pixmap)

        width = self.attachment_bubble.width()
        size = 50
        self.file_icon.setGeometry(width-size*1.3,0.2*CRITERION,size,size)

        bias = int(0.2*CRITERION)

        if not is_sharing:
            if Path(value).is_file():
                file_size = getsize(value)
            else:
                file_size = 0
            if file_size < 1024:
                fsize = '\n{}B'.format(file_size)
            elif file_size < 1024*1024:
                fsize = '\n{:.2f}KB'.format(file_size/1024)
            else:
                fsize = '\n{:.2f}KB'.format(file_size/1024/1024)
            text = Path(self.value).name+fsize
        else:
            n = value.find(' ')
            text = value[n+1:]
        self.text_label = QLabel(text ,self.attachment_bubble)
        self.text_label.setStyleSheet("border:none;")
        self.text_label.setGeometry(bias,bias,width - size * 2.3 - bias, CRITERION)
        self.lable_geometry = self.attachment_bubble.geometry()
        return self.attachment_bubble.height()+10
    def setMessage_Picture(self,value,is_video=False):
        def get_thumbnail(value):
            p = Path(value)
            name_thum = 'thum_'+p.name
            path_thum = self.bot.thumbnail_path / name_thum

            if path_thum.exists():
                return str(path_thum)
            else:
                if not p.exists():
                    return str(self.bot.path.parent.with_name('wechat_data') / 'icon' / 'error.jpg')
                if getsize(value)<1024*100 or value.split('.')[-1].lower() == 'gif':
                    return value
                try:
                    img = Image.open(p)
                
                    w,h = img.size
                    if w>h:
                        rate = w/150
                    else:
                        rate = h/150
                    img.thumbnail((w//rate,h//rate))
                    img.save(path_thum)

                except Exception as e:
                    print('Error:\n{}\nread image{}'.format(e,p))
                    path_thum = self.bot.path.parent.with_name('wechat_data') / 'icon' / 'error.jpg'
                return str(path_thum)
        value = get_thumbnail(value)
        self.picture_bubble = YPictureBubble(self)#定义显示图片的组件
        self.message_label = self.picture_bubble
        self.picture_bubble.setPicture(value)
        if self.identity is ME:
            pos = self.pos_me[0]-self.picture_bubble.width()-5,self.pos_me[1]
        else:
            pic_width = self.pic_qsize.width()
            pos = self.pos_other[0]+5+pic_width,self.pos_other[1]
        self.picture_bubble.move(*pos)
        w,h = self.picture_bubble.width(),self.picture_bubble.height()
        if is_video:
            self.display_label = QLabel(self.picture_bubble)
            self.display_label.setStyleSheet('QWidget{background-color:rgba(0,0,0,0)}')
            self.display_label.setScaledContents(True)
            display_path = self.bot.path.parent.with_name('wechat_data') / 'icon' /'video.png'
            pixmap = Image.open(display_path).toqpixmap()
            # pixmap.fill(Qt.transparent)
            self.display_label.setPixmap(pixmap)
            size = 50
            self.display_label.setGeometry((w-size)//2,(h-size)//2,size,size)
        self.lable_geometry = self.picture_bubble.geometry()
        return h



class YDesignButton(QtWidgets.QPushButton):
    def __init__(self,d):
        super().__init__(d)
        self.Yw=d.width()
        self.Yh=100/90
        self.color_background=(255,255,255)
        self.color_film=(220,220,220)
    def setDesigning(self,*d,color_background=(255,255,255),pos=(0,0),size=(2*CRITERION,CRITERION),sep=False):
        self.d=d
        self.p=pos
        self.s=size
        self.sep = sep
        qp = QtGui.QPainter()
        img=QtGui.QImage(*size,QtGui.QImage.Format_RGB32)
        img.fill(QtGui.QColor(*color_background))
        qp.begin(img)
        for i,v in d:
            if i is TEXT:
                self.YdrawText(*v,qp)
            elif i is PICTURE:
                self.YdrawImage(*v,qp)
            else:
                pass
        if sep is True:
            qp.setPen(QColor(200,200,200))
            # print(pos,'pos')
            qp.drawLine(0.05*self.Yw,0,self.Yw*0.95,0)
        qp.end()
        qimg=QtGui.QPixmap.fromImage(img)
        icon=QtGui.QIcon()
        icon.addPixmap(qimg)
        self.setIcon(icon)
        self.setIconSize(QtCore.QSize(*size))
        # self.setGeometry(QtCore.QRect(*pos,*size))
        self.resize(*size)

    def YdrawText(self,text,pos,size,color,qp):
        qp.setPen(QtGui.QColor(*color))
        global_font.setPixelSize(size)
        qp.setFont(global_font)
        qp.drawText(pos[0],pos[1],1000,1000,QtCore.Qt.AlignLeft,text)
    def YdrawImage(self,filename,pic_rect,qp):
        image=QtGui.QImage(str(filename))
        qp.drawImage(QtCore.QRectF(*pic_rect),image)
    def mousePressEvent(self,e):
        self.setDesigning(*self.d,color_background=self.color_film,pos=self.p ,size=self.s,sep = self.sep)
    def mouseReleaseEvent(self,e):
        self.setDesigning(*self.d,color_background=self.color_background,pos=self.p ,size=self.s,sep = self.sep)
        self.father_surface.goto_view(self.Yname)
    def setName(self,name,father):
        self.Yname=name
        self.father_surface=father

class FunctionButton(YDesignButton):
    def __init__(self,d):
        super().__init__(d)
        self.Yw=d.width()
        self.Yh=100/90
    def adjust_position(self,*d):
        pass
    def setContent(self,picture,name,pos=(0,0),sep=False,size_rate = 0.8):
        #picture:功能按钮的图片
        #name:功能按钮显示出来的名字

        w=self.Yw
        h=self.Yh*CRITERION
        color_background=self.color_background

        color_text_name=(63,63,63)
        picture_rect=(33/90*CRITERION,18/90*CRITERION,63/90*CRITERION,63/90*CRITERION)
        name_size=30/90*CRITERION
        pos_name=(124/90*CRITERION,34/90*CRITERION)
        arg1=PICTURE,(picture,picture_rect)
        arg2=TEXT,(name,pos_name,name_size,color_text_name)
        self.setDesigning(arg1,arg2,pos=pos,size=(w,h),sep=sep)
#微信信息输入框
class YInputText(QtWidgets.QTextEdit):
    
    def __init__(self,d):
        super().__init__(d)
        self.max_length=2*CRITERION
        pl=QPalette()
        pl.setBrush(pl.Base,QBrush(QColor(255,0,0,0)))
        self.setPalette(pl)
        self.setStyleSheet("border:none;")
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.statusConnect = lambda x:None
        self.d=self.document()
        self.font=QtGui.QFont()
        self.font.setFamily('SimHei')
        self.font.setPixelSize(0.35*CRITERION)
        self.setFont(self.font)
        self.cursor = self.textCursor()

    def press_enter_connect(self,func):
        self.press_enter = func
        
    def focusInEvent(self,e):
        super().focusInEvent(e)
        self.statusConnect('FOCUS')
        self.statusConnect((self.d.size().height(),self.height(),self.d.isEmpty()))
    def focusOutEvent(self,e):
        super().focusOutEvent(e)
        self.statusConnect('NOFOCUS')
    def setStatusConnect(self,p):
        self.statusConnect=p
    def keyReleaseEvent(self,e):
        self.statusConnect((self.d.size().height(),self.height(),self.d.isEmpty()))
    def keyPressEvent(self,e): #输入框按键事件
        value = e.key()
        if value == Qt.Key_Return:
            self.press_enter()
            return
        super().keyPressEvent(e)
    def paintEvent(self,d):
        super().paintEvent(d)
        self.statusConnect((self.d.size().height(),self.height(),self.d.isEmpty()))

class RedCircle(QWidget):
    color = QColor(255,0,0)
    text_color = QColor(255,255,255)
    font=QtGui.QFont()
    font.setFamily('SimHei')
    font.setBold(True)
    def __init__(self,father,text = None):
        super().__init__(father)
        self.text = text
    def paintEvent(self,e):
        qp = QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()
 
    def drawWidget(self, qp):
        Width,Height=self.width(),self.height()
        qp.setBrush(QBrush(self.color))
        qp.setPen(QPen(self.color))
        d = int(Width*0.9)
        rect = QRect(0,0,d,d)
        qp.drawEllipse(rect)
        if self.text:
            qp.setPen(QPen(self.text_color))
            self.font.setPixelSize(d*0.75)
            qp.setFont(self.font)
            qp.drawText(rect,QtCore.Qt.AlignCenter,self.text)


class EmotionWidget(QWidget):
    def __init__(self,Form,w,h,callback):
        super().__init__(Form)
        self.resize(w,h)
        self.ok_start = False

        self.setStyleSheet('QWidget{border-width:1px;border-style:solid;border-color:rgb(150,180,140);background-color:rgb(160,232,88)}')
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        self.current_use = False
        row_num = 8
        list_emoji = list(set(emoji.values()))
        list_emoji.sort()
        layout = QVBoxLayout()
        for i in range(len(list_emoji)//row_num):
            hlayout = QHBoxLayout()
            for j in range(row_num):
                t = YButton()
                em_path = list_emoji[i*row_num+j]
                t.setButton(em_path,40,40,em_path,None,t.selfCallback,callback)
                hlayout.addWidget(t)
            hlayout.addStretch()
            layout.addLayout(hlayout)
        if len(list_emoji)%row_num != 0:
            hlayout = QHBoxLayout()
            for e in list_emoji[-(len(list_emoji)%row_num):]:
                t = YButton()
                t.setButton(e,40,40,str(e),None,t.selfCallback,callback)
                hlayout.addWidget(t)
            hlayout.addStretch()
            layout.addLayout(hlayout)
        layout.addStretch()
        self.setLayout(layout)
        self.ok_start = True


    def changeEvent(self,e):
        if self.ok_start is False:
            return
        if self.current_use is True:
            self.current_use = False
            self.hide()
        else:
            pos = QCursor.pos()
            x,y = pos.x(),pos.y()
            w,h = self.width(), self.height()
            x= max(0,x-w//2)
            y = y-h-20
            self.move(x,y)
            self.current_use = True
