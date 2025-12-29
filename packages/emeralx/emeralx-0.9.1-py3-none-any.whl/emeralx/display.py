#导入依赖包
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"]="1" #隐藏pygame输出文本
import pygame
import pygame.freetype
from win32api import GetMonitorInfo,MonitorFromPoint
import ctypes
import uuid
from . import image
from . import canvas

#运行变量设置
monitor_info=GetMonitorInfo(MonitorFromPoint((0,0)))
monitor=monitor_info.get('Monitor')
work_area=monitor_info.get('Work')

#常量设置
ALL="all"

#计时器
clock=pygame.time.Clock()

#窗口类
class Window(object):
    """
    The Window class is used to create a window frame on the screen and listen for window events.
    """
    def __init__(self,width=work_area[2]*(2/3),height=work_area[3]*(2/3)):
        pygame.init()
        self._window=pygame.display.set_mode((width,height))
        pygame.display.set_caption("Emeral Window")
        path="\\".join(os.path.abspath(__file__).split("\\")[:-1])+"\\resources\\logo.png"
        self._icon=pygame.image.load(path).convert_alpha() #加载图标
        pygame.display.set_icon(self._icon)
        self._isRunning=True #循环变量
        self._capteffec=False #标题是否有效
        self._caption="Emeral Window"
        self._WIDTH,self._HEIGHT=width,height #窗口宽高
        self._MAX_WIDTH,self._MAX_HEIGHT,self._MIN_WIDTH,self._MIN_HEIGHT=None,None,None,None
        self._FPS=60 #帧率
        self._room:Room=None #显示的房间

        #实体字典
        self._entities=dict()

        #绘制图形字典
        self._objs=dict()

        #事件执行项
        self._events={
            "start_running":[], #开始运行事件类
            "each_frame_step":[], #每帧事件类
            "press_mouse_LEFT":[], #点击鼠标左键事件类
            "press_mouse_RIGHT":[], #点击鼠标右键事件类
            "press_mouse_MIDDLE":[], #点击鼠标中键事件类
            "release_mouse_LEFT":[], #松开鼠标左键事件类
            "release_mouse_RIGHT":[], #松开鼠标右键事件类
            "release_mouse_MIDDLE":[], #松开鼠标中键事件类
            "move_wheel_WHEELUP":[], #向上滚动鼠标滚轮事件类
            "move_wheel_WHEELDOWN":[], #向下滚动鼠标滚轮事件类
            "motion_mouse":[] #移动鼠标事件类
        }
        #加入点击按键事件类
        self._keylist={pygame.K_a:"A",pygame.K_b:"B",pygame.K_c:"C",pygame.K_d:"D",pygame.K_e:"E",pygame.K_f:"F",pygame.K_g:"G",
                       pygame.K_h:"H",pygame.K_i:"I",pygame.K_j:"J",pygame.K_k:"K",pygame.K_l:"L",pygame.K_m:"M",pygame.K_n:"N",
                       pygame.K_o:"O",pygame.K_p:"P",pygame.K_q:"Q",pygame.K_r:"R",pygame.K_s:"S",pygame.K_t:"T",pygame.K_u:"U",
                       pygame.K_v:"V",pygame.K_w:"W",pygame.K_x:"X",pygame.K_y:"Y",pygame.K_z:"Z",pygame.K_0:"0",pygame.K_1:"1",
                       pygame.K_2:"2",pygame.K_3:"3",pygame.K_4:"4",pygame.K_5:"5",pygame.K_6:"6",pygame.K_7:"7",pygame.K_8:"8",
                       pygame.K_9:"9",pygame.K_UP:"UP",pygame.K_DOWN:"DOWN",pygame.K_LEFT:"LEFT",pygame.K_RIGHT:"RIGHT",pygame.K_SPACE:"SPACE",
                       pygame.K_RETURN:"RETURN",pygame.K_ESCAPE:"ESCAPE",pygame.K_BACKSPACE:"BACKSPACE",pygame.K_TAB:"TAB",pygame.K_LSHIFT:"LSHIFT",
                       pygame.K_RSHIFT:"RSHIFT",pygame.K_LCTRL:"LCTRL",pygame.K_RCTRL:"RCTRL",pygame.K_LALT:"LALT",pygame.K_RALT:"RALT",
                       pygame.K_CAPSLOCK:"CAPSLOCK",pygame.K_INSERT:"INSERT",pygame.K_DELETE:"DELETE",pygame.K_HOME:"HOME",pygame.K_END:"END",
                       pygame.K_PAGEUP:"PAGEUP",pygame.K_PAGEDOWN:"PAGEDOWN",pygame.K_F1:"F1",pygame.K_F2:"F2",pygame.K_F3:"F3",pygame.K_F4:"F4",
                       pygame.K_F5:"F5",pygame.K_F6:"F6",pygame.K_F7:"F7",pygame.K_F8:"F8",pygame.K_F9:"F9",pygame.K_F10:"F10",pygame.K_F11:"F11",
                       pygame.K_F12:"F12"}
        for item in self._keylist.values():
            self._events.update({f"press_key_{item}":[]})

        #加入松开按键事件类
        for item in self._keylist.values():
            self._events.update({f"release_key_{item}":[]})

        #加入按下按键事件类
        for item in self._keylist.values():
            self._events.update({f"hold_key_{item}":[]})

        self._trigger_times=0
        self._last_pos=pygame.mouse.get_pos() #上一次鼠标位置
        self._dx,self._dy=0,0 #鼠标位置变化量
    def listen(self):
        """
        The listen method is used to fix a window and continuously listen for events occurring on the window.
        """
        while (self._isRunning):
            if all((self._MAX_WIDTH!=None,self._MAX_HEIGHT!=None,self._MIN_WIDTH!=None,self._MIN_HEIGHT!=None)):
                width,height=self._window.get_size()
                width=max(self._MIN_WIDTH,min(width,self._MAX_WIDTH)) #动态调整宽高
                height=max(self._MIN_HEIGHT,min(height,self._MAX_HEIGHT))
                self._window=pygame.display.set_mode((width,height),pygame.RESIZABLE)
                pygame.display.set_icon(self._icon)

            #窗口标题分类设置
            if (self._room!=None and self._capteffec==False):
                if (self._caption!=self._room._caption):
                    pygame.display.set_caption(self._room._caption)
                    self._caption=self._room._caption
            elif (self._room==None and self._capteffec==False):
                if (self._caption!="Emeral Window"):
                    pygame.display.set_caption("Emeral Window")
                    self._caption="Emeral Window"

            #设置窗口背景颜色
            if (self._room!=None):
                self._window.fill(self._room._background)

            #触发事件
            for item in self._events["start_running"]: #触发当开始运行时事件
                if (self._trigger_times==0):
                    item()
            for item in self._events["each_frame_step"]: #触发每帧运行事件
                item()
            for item in self._events["motion_mouse"]: #触发鼠标移动事件
                if (pygame.mouse.get_pos()!=self._last_pos):
                    item()
                    self._dx=pygame.mouse.get_pos()[0]-self._last_pos[0]
                    self._dy=pygame.mouse.get_pos()[1]-self._last_pos[1]
                    self._last_pos=pygame.mouse.get_pos()
            
            #键盘按下事件
            keys=pygame.key.get_pressed()
            for kname in self._keylist.keys():
                if (keys[kname]): #遍历执行相应函数
                    for item in self._events[f"hold_key_{self._keylist[kname]}"]:
                        item()

            for events in pygame.event.get():
                if (events.type==pygame.QUIT):
                    self._isRunning=False
                    break

                #这里的思路是，首先监听发生的是什么事件，如果发生了这个事件，就通过遍历self的
                #按键字典的键来判断按下的是什么键，在每个判断分支的下面，就是如果按下了这个键，
                #那么就寻找这个键所对应的事件类，循环遍历其中的行为并运行行为。
                if (events.type==pygame.KEYDOWN):
                    for kname in self._keylist.keys():
                        if (events.key==kname): #遍历执行相应函数
                            for item in self._events[f"press_key_{self._keylist[kname]}"]:
                                item()
                if (events.type==pygame.KEYUP):
                    for kname in self._keylist.keys():
                        if (events.key==kname): #遍历执行相应函数
                            for item in self._events[f"release_key_{self._keylist[kname]}"]:
                                item()
                if (events.type==pygame.MOUSEBUTTONDOWN): #鼠标按下事件
                    if (events.button==pygame.BUTTON_LEFT):
                        for item in self._events["press_mouse_LEFT"]:item()
                    if (events.button==pygame.BUTTON_RIGHT):
                        for item in self._events["press_mouse_RIGHT"]:item()
                    if (events.button==pygame.BUTTON_MIDDLE):
                        for item in self._events["press_mouse_MIDDLE"]:item()
                if (events.type==pygame.MOUSEBUTTONUP): #鼠标松开事件
                    if (events.button==pygame.BUTTON_LEFT):
                        for item in self._events["release_mouse_LEFT"]:item()
                    if (events.button==pygame.BUTTON_RIGHT):
                        for item in self._events["release_mouse_RIGHT"]:item()
                    if (events.button==pygame.BUTTON_MIDDLE):
                        for item in self._events["release_mouse_MIDDLE"]:item()
                if (events.type==pygame.MOUSEWHEEL): #滚动滚轮事件
                    if (events.y>0):
                        for item in self._events["move_wheel_WHEELUP"]:item()
                    if (events.y<0):
                        for item in self._events["move_wheel_WHEELDOWN"]:item()

            for item in self._entities.keys(): #遍历实体列表
                if (self._entities[item]["host"]==self._room):
                    if (self._room._camera!=None):
                        self._window.blit(self._entities[item]["image"],(self._entities[item]["x"]+self._WIDTH/2-self._entities[item]["image"].get_size()[0]/2-self._room._camera._x,self._entities[item]["y"]+self._HEIGHT/2-self._entities[item]["image"].get_size()[1]/2-self._room._camera._y))
                    else:
                        self._window.blit(self._entities[item]["image"],(self._entities[item]["x"]+self._WIDTH/2-self._entities[item]["image"].get_size()[0]/2,self._entities[item]["y"]+self._HEIGHT/2-self._entities[item]["image"].get_size()[1]/2))

            for item in self._objs.keys(): #遍历非实体列表
                if (self._objs[item][1]==self._room):
                    if (type(self._objs[item][0])==image.Static): #如果对象为图片，则blit可以成功，否则不能成功
                        if (self._room._camera!=None):
                            self._window.blit(self._objs[item][0]._img,(self._objs[item][2][0]+self._WIDTH/2-self._objs[item][0]._img.get_size()[0]/2-self._room._camera._x,self._objs[item][2][1]+self._HEIGHT/2-self._objs[item][0]._img.get_size()[1]/2-self._room._camera._y))
                        else:
                            self._window.blit(self._objs[item][0]._img,(self._objs[item][2][0]+self._WIDTH/2-self._objs[item][0]._img.get_size()[0]/2,self._objs[item][2][1]+self._HEIGHT/2-self._objs[item][0]._img.get_size()[1]/2))
                    elif (type(self._objs[item][0])==canvas.Line): #如果对象为线段
                        if (self._room._camera!=None):
                            pygame.draw.line(self._window,self._objs[item][0]._color,
                                             (self._objs[item][0]._start_pos[0]+self._WIDTH/2-self._room._camera._x,self._objs[item][0]._start_pos[1]+self._HEIGHT/2-self._room._camera._y),
                                             (self._objs[item][0]._end_pos[0]+self._WIDTH/2-self._room._camera._x,self._objs[item][0]._end_pos[1]+self._HEIGHT/2-self._room._camera._y),
                                             width=self._objs[item][0]._size)
                        else:
                            pygame.draw.line(self._window,self._objs[item][0]._color,
                                             (self._objs[item][0]._start_pos[0]+self._WIDTH/2,self._objs[item][0]._start_pos[1]+self._HEIGHT/2),
                                             (self._objs[item][0]._end_pos[0]+self._WIDTH/2,self._objs[item][0]._end_pos[1]+self._HEIGHT/2),
                                             width=self._objs[item][0]._size)
                    elif (type(self._objs[item][0])==canvas.Triangle): #如果对象为三角形
                        if (self._room._camera!=None):
                            pygame.draw.polygon(self._window,self._objs[item][0]._color,[
                                             (self._objs[item][0]._pos1[0]+self._WIDTH/2-self._room._camera._x,self._objs[item][0]._pos1[1]+self._HEIGHT/2-self._room._camera._y),
                                             (self._objs[item][0]._pos2[0]+self._WIDTH/2-self._room._camera._x,self._objs[item][0]._pos2[1]+self._HEIGHT/2-self._room._camera._y),
                                             (self._objs[item][0]._pos3[0]+self._WIDTH/2-self._room._camera._x,self._objs[item][0]._pos3[1]+self._HEIGHT/2-self._room._camera._y)],
                                             width=self._objs[item][0]._size)
                        else:
                            pygame.draw.polygon(self._window,self._objs[item][0]._color,[
                                             (self._objs[item][0]._pos1[0]+self._WIDTH/2,self._objs[item][0]._pos1[1]+self._HEIGHT/2),
                                             (self._objs[item][0]._pos2[0]+self._WIDTH/2,self._objs[item][0]._pos2[1]+self._HEIGHT/2),
                                             (self._objs[item][0]._pos3[0]+self._WIDTH/2,self._objs[item][0]._pos3[1]+self._HEIGHT/2)],
                                             width=self._objs[item][0]._size)
                    elif (type(self._objs[item][0])==canvas.Rect): #如果对象为矩形
                        if (self._room._camera!=None):
                            pygame.draw.polygon(self._window,self._objs[item][0]._color,[
                                             (self._objs[item][0]._cpos[0]-self._objs[item][0]._width/2+self._WIDTH/2-self._room._camera._x,self._objs[item][0]._cpos[1]+self._objs[item][0]._height/2+self._HEIGHT/2-self._room._camera._y),
                                             (self._objs[item][0]._cpos[0]+self._objs[item][0]._width/2+self._WIDTH/2-self._room._camera._x,self._objs[item][0]._cpos[1]+self._objs[item][0]._height/2+self._HEIGHT/2-self._room._camera._y),
                                             (self._objs[item][0]._cpos[0]+self._objs[item][0]._width/2+self._WIDTH/2-self._room._camera._x,self._objs[item][0]._cpos[1]-self._objs[item][0]._height/2+self._HEIGHT/2-self._room._camera._y),
                                             (self._objs[item][0]._cpos[0]-self._objs[item][0]._width/2+self._WIDTH/2-self._room._camera._x,self._objs[item][0]._cpos[1]-self._objs[item][0]._height/2+self._HEIGHT/2-self._room._camera._y)],
                                             width=self._objs[item][0]._size)
                        else:
                            pygame.draw.polygon(self._window,self._objs[item][0]._color,[
                                             (self._objs[item][0]._cpos[0]-self._objs[item][0]._width/2+self._WIDTH/2,self._objs[item][0]._cpos[1]+self._objs[item][0]._height/2+self._HEIGHT/2),
                                             (self._objs[item][0]._cpos[0]+self._objs[item][0]._width/2+self._WIDTH/2,self._objs[item][0]._cpos[1]+self._objs[item][0]._height/2+self._HEIGHT/2),
                                             (self._objs[item][0]._cpos[0]+self._objs[item][0]._width/2+self._WIDTH/2,self._objs[item][0]._cpos[1]-self._objs[item][0]._height/2+self._HEIGHT/2),
                                             (self._objs[item][0]._cpos[0]-self._objs[item][0]._width/2+self._WIDTH/2,self._objs[item][0]._cpos[1]-self._objs[item][0]._height/2+self._HEIGHT/2)],
                                             width=self._objs[item][0]._size)
                    elif (type(self._objs[item][0])==canvas.Circle): #如果对象为圆形
                        if (self._room._camera!=None):
                            pygame.draw.circle(self._window,self._objs[item][0]._color,
                                             (self._objs[item][0]._cpos[0]+self._WIDTH/2-self._room._camera._x,self._objs[item][0]._cpos[1]+self._HEIGHT/2-self._room._camera._y),
                                             radius=self._objs[item][0]._radius,
                                             width=self._objs[item][0]._size)
                        else:
                            pygame.draw.circle(self._window,self._objs[item][0]._color,
                                             (self._objs[item][0]._cpos[0]+self._WIDTH/2,self._objs[item][0]._cpos[1]+self._HEIGHT/2),
                                             radius=self._objs[item][0]._radius,
                                             width=self._objs[item][0]._size)
                    elif (type(self._objs[item][0])==canvas.Arc): #如果对象为圆弧
                        if (self._room._camera!=None):
                            pygame.draw.arc(self._window,self._objs[item][0]._color,
                                             (self._objs[item][0]._cpos[0]-self._objs[item][0]._radius+self._WIDTH/2-self._room._camera._x,self._objs[item][0]._cpos[1]-self._objs[item][0]._radius+self._HEIGHT/2-self._room._camera._y,self._objs[item][0]._radius*2,self._objs[item][0]._radius*2),
                                             start_angle=self._objs[item][0]._from_a,
                                             stop_angle=self._objs[item][0]._to_a,
                                             width=self._objs[item][0]._size)
                        else:
                            pygame.draw.arc(self._window,self._objs[item][0]._color,
                                             (self._objs[item][0]._cpos[0]-self._objs[item][0]._radius+self._WIDTH/2,self._objs[item][0]._cpos[1]-self._objs[item][0]._radius+self._HEIGHT/2,self._objs[item][0]._radius*2,self._objs[item][0]._radius*2),
                                             start_angle=self._objs[item][0]._from_a,
                                             stop_angle=self._objs[item][0]._to_a,
                                             width=self._objs[item][0]._size)
                    elif (type(self._objs[item][0])==canvas.Text): #如果对象为文字
                        font=pygame.freetype.Font(self._objs[item][0]._fontpath,self._objs[item][0]._size)
                        textSurface,textRect=font.render(self._objs[item][0]._text,self._objs[item][0]._color)
                        if (self._room._camera!=None):
                            self._window.blit(textSurface,(self._objs[item][0]._pos[0]-textRect.width/2+self._WIDTH/2-self._room._camera._x,self._objs[item][0]._pos[1]-textRect.height/2+self._HEIGHT/2-self._room._camera._y))
                        else:
                            self._window.blit(textSurface,(self._objs[item][0]._pos[0]-textRect.width/2+self._WIDTH/2,self._objs[item][0]._pos[1]-textRect.height/2+self._HEIGHT/2))

            pygame.display.update()
            #触发次数加一
            self._trigger_times+=1

            #设置帧率
            clock.tick(self._FPS)
    def set_caption(self,title):
        """
        The set_caption method is used to set a string title for the window.
        """
        if (self._capteffec==True):
            pygame.display.set_caption(title)
            self._caption=title
    def caption_effective(self,state=True):
        """
        Used to set whether the window title takes effect. When the state value is True, the window can set its own title; when the state value is False, the window cannot set its own title and uses the current room's title as the default value.
        """
        self._capteffec=state #设置标题是否有效变量
    def set_width(self,width):
        """
        Set the width of the window.
        """
        self._window=pygame.display.set_mode((width,self._HEIGHT))
        pygame.display.set_icon(self._icon)
        self._WIDTH=width
    def set_height(self,height):
        """
        Set the height of the window.
        """
        self._window=pygame.display.set_mode((self._WIDTH,height))
        pygame.display.set_icon(self._icon)
        self._HEIGHT=height
    def set_size(self,size):
        """
        Set the size of the window, the size parameter is passed as a tuple in the format (width, height).
        """
        self._window=pygame.display.set_mode((size[0],size[1])) #重新设置窗口尺寸
        pygame.display.set_icon(self._icon)
        self._WIDTH,self._HEIGHT=size[0],size[1]
    def set_icon(self,icon):
        """
        Set an icon for the window, replacing the original window icon.
        """
        self._icon=pygame.image.load(icon).convert_alpha()
        pygame.display.set_icon(self._icon)
    def set_fullscreen(self):
        """
        Set window to fullscreen.
        """
        self._window=pygame.display.set_mode((self._WIDTH,self._HEIGHT),pygame.FULLSCREEN) #窗口全屏
        pygame.display.set_icon(self._icon)
    def cancel_fullscreen(self):
        """
        Exit full screen mode.
        """
        self._window=pygame.display.set_mode((self._WIDTH,self._HEIGHT)) #取消全屏
        pygame.display.set_icon(self._icon)
    def set_minimize(self):
        """
        Set the window to minimize.
        """
        pygame.display.iconify() #设置为最小化窗口
    def set_resizable(self):
        """
        The window can be manually resized.
        """
        self._window=pygame.display.set_mode((self._WIDTH,self._HEIGHT),pygame.RESIZABLE) #设置窗口可调整大小
        pygame.display.set_icon(self._icon)
    def set_resizeless(self):
        """
        Set the window to be non-resizable.
        """
        self._window=pygame.display.set_mode((self._WIDTH,self._HEIGHT)) #设置窗口不可调节大小
    def restrict_size(self,max_width,max_height,min_width,min_height):
        """
        Limit the window's maximum and minimum size.
        """
        restriction=(max_width,max_height,min_width,min_height)
        self._MAX_WIDTH,self._MAX_HEIGHT,self._MIN_WIDTH,self._MIN_HEIGHT=restriction #解包获取限制尺寸
    def set_transparent(self):
        """
        Set the window to full transparency mode. If you do this, you can only see the contents of the window, not the borders.
        """
        hwnd=pygame.display.get_wm_info()["window"]
        ctypes.windll.user32.SetWindowLongA(hwnd,ctypes.c_long(-20),ctypes.c_long(524288|32))
        #设置窗口的位置和大小
        self._window=pygame.display.set_mode((self._WIDTH,self._HEIGHT),pygame.NOFRAME)
        pygame.display.set_icon(self._icon)
    def get_caption(self):
        """
        Return window title.
        """
        return self._caption #返回窗口标题
    def get_size(self):
        """
        Return the window size.
        """
        return (self._WIDTH,self._HEIGHT) #以元组的形式返回窗口尺寸
    def get_restriction(self):
        """
        Return a tuple consisting of the window's maximum width, maximum height, minimum width, and minimum height, in order.
        """
        #返回窗口的限制尺寸
        return (self._MAX_WIDTH,self._MAX_HEIGHT,self._MIN_WIDTH,self._MIN_HEIGHT)
    def set_fps(self,fps):
        """
        Set the frame rate of the window.
        """
        self._FPS=fps #设置窗口的帧率
    def get_fps(self):
        """
        Get the ideal frame rate of the current window.
        """
        return self._FPS #返回窗口的理想帧率
    def get_frame_time(self):
        """
        Ideal frame time for return window.
        """
        return 1000/self._FPS #获取窗口的理想帧时间
    def get_handle(self):
        """
        Get window handle.
        """
        return pygame.display.get_wm_info()['window'] #返回句柄
    
#房间类
class Room(object):
    """
    The Room class is used as a carrier for creating an entity such as a sprite or canvas on a window. You can create multiple rooms at the same time and use the Window class to switch between them.
    """
    def __init__(self,window:Window,caption="Untitled"):
        self._window=window
        self._caption=caption
        self._background=(0,0,0)

        #主要思路：创建精灵或实体时生成一份字典json，将字典json实时发送给Room对象，由Room处理后，
        #发送给Window对象进行绘制。Sprite等类主要负责对json中信息的修改等。
        
        self._entitys=[] #实体列表，用于存放实体
        self._camera=None #房间的主相机
    def switch(self):
        """
        Switch the room on the window to itself.
        """
        self._window._room=self #设置自身为显示状态
    def close(self):
        """
        Close the room, which means canceling the display of the room on the window.
        """
        self._window._room=None #取消自身在窗口上的显示状态
    def set_caption(self,title):
        """
        Set a title for the room.
        """
        self._caption=title #设置房间标题
    def set_background(self,color):
        """
        Set the background color for the room.
        """
        self._background=color #设置背景颜色
    def place(self,obj,location=(0,0)):
        """
        Place a picture or graphic at a certain location in the room
        """
        id=uuid.uuid4() #获取id
        self._window._objs.update({id:(obj,self,location)}) #将图形的信息与位置存入主机
        return id
    def clear(self,id=ALL):
        """
        Clear the specified non-physical objects in the room.
        """
        if (id!="all"):
            if (self._window._objs[id][1]==self):
                del self._window._objs[id] #清除指定非实体对象
        else:
            for item in self._window._objs.keys():
                if (self._window._objs[item][1]==self):
                    del self._window._objs[item] #删除所有房间归属为自身的非实体对象
                    break

#相机类
class Camera(object):
    """
    The camera class is used for shooting, viewing angles, and following movement in a room.
    """
    def __init__(self,room:Room):
        self._room=room
        self._x,self._y=0,0 #相机的x坐标与y坐标
    def switch(self):
        """
        Switch the camera to the main camera of the room.
        """
        self._room._camera=self #切换为自身
    def translate(self,location):
        """
        Translate the camera to change its position.
        """
        self._x,self._y=location #解包获取相机的横纵坐标
    def translate_to_sprite(self,sprite):
        """
        Pan the camera to the position of the sprite.
        """
        self._x,self._y=sprite._x,sprite._y #将相机移动到精灵位置