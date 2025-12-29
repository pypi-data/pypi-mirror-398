#导入依赖包
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"]="1" #隐藏pygame输出文本
import pygame
from . import display

#硬件常量
keyA=(pygame.K_a,"A")
keyB=(pygame.K_b,"B")
keyC=(pygame.K_c,"C")
keyD=(pygame.K_d,"D")
keyE=(pygame.K_e,"E")
keyF=(pygame.K_f,"F")
keyG=(pygame.K_g,"G")
keyH=(pygame.K_h,"H")
keyI=(pygame.K_i,"I")
keyJ=(pygame.K_j,"J")
keyK=(pygame.K_k,"K")
keyL=(pygame.K_l,"L")
keyM=(pygame.K_m,"M")
keyN=(pygame.K_n,"N")
keyO=(pygame.K_o,"O")
keyP=(pygame.K_p,"P")
keyQ=(pygame.K_q,"Q")
keyR=(pygame.K_r,"R")
keyS=(pygame.K_s,"S")
keyT=(pygame.K_t,"T")
keyU=(pygame.K_u,"U")
keyV=(pygame.K_v,"V")
keyW=(pygame.K_w,"W")
keyX=(pygame.K_x,"X")
keyY=(pygame.K_y,"Y")
keyZ=(pygame.K_z,"Z")

key0=(pygame.K_0,"0")
key1=(pygame.K_1,"1")
key2=(pygame.K_2,"2")
key3=(pygame.K_3,"3")
key4=(pygame.K_4,"4")
key5=(pygame.K_5,"5")
key6=(pygame.K_6,"6")
key7=(pygame.K_7,"7")
key8=(pygame.K_8,"8")
key9=(pygame.K_9,"9")

keyUP=(pygame.K_UP,"UP")
keyDOWN=(pygame.K_DOWN,"DOWN")
keyLEFT=(pygame.K_LEFT,"LEFT")
keyRIGHT=(pygame.K_RIGHT,"RIGHT")
keySPACE=(pygame.K_SPACE,"SPACE")
keyRETURN=(pygame.K_RETURN,"RETURN")
keyESCAPE=(pygame.K_ESCAPE,"ESCAPE")
keyBACKSPACE=(pygame.K_BACKSPACE,"BACKSPACE")
keyTAB=(pygame.K_TAB,"TAB")
keyLSHIFT=(pygame.K_LSHIFT,"LSHIFT")
keyRSHIFT=(pygame.K_RSHIFT,"RSHIFT")
keyLCTRL=(pygame.K_LCTRL,"LCTRL")
keyRCTRL=(pygame.K_RCTRL,"RCTRL")
keyLALT=(pygame.K_LALT,"LALT")
keyRALT=(pygame.K_RALT,"RALT")
keyCAPSLOCK=(pygame.K_CAPSLOCK,"CAPSLOCK")
keyINSERT=(pygame.K_INSERT,"INSERT")
keyDELETE=(pygame.K_DELETE,"DELETE")
keyHOME=(pygame.K_HOME,"HOME")
keyEND=(pygame.K_END,"END")
keyPAGEUP=(pygame.K_PAGEUP,"PAGEUP")
keyPAGEDOWN=(pygame.K_PAGEDOWN,"PAGEDOWN")

keyF1=(pygame.K_F1,"F1")
keyF2=(pygame.K_F2,"F2")
keyF3=(pygame.K_F3,"F3")
keyF4=(pygame.K_F4,"F4")
keyF5=(pygame.K_F5,"F5")
keyF6=(pygame.K_F6,"F6")
keyF7=(pygame.K_F7,"F7")
keyF8=(pygame.K_F8,"F8")
keyF9=(pygame.K_F9,"F9")
keyF10=(pygame.K_F10,"F10")
keyF11=(pygame.K_F11,"F11")
keyF12=(pygame.K_F12,"F12")

mouseLEFT=(pygame.BUTTON_LEFT,"LEFT")
mouseRIGHT=(pygame.BUTTON_RIGHT,"RIGHT")
mouseMIDDLE=(pygame.BUTTON_MIDDLE,"MIDDLE")

wheelUP=(pygame.BUTTON_WHEELUP,"WHEELUP")
wheelDOWN=(pygame.BUTTON_WHEELDOWN,"WHEELDOWN")

#事件类型函数
def IS_START_RUNNING(): #当开始运行瞬间
    return ("start_running",None)

def EACH_FRAME_STEP(): #运行时的每一帧
    return ("frame_step",None)

def IS_PRESS_KEY(key): #当键盘按下一瞬间
    return ("press_key",key)

def IS_HOLD_KEY(key): #当键盘一直按下
    return ("hold_key",key)

def IS_RELEASE_KEY(key): #当键盘松开
    return ("release_key",key)

def IS_CLICK_MOUSE(button): #当鼠标按下
    return ("press_mouse",button)

def IS_RELEASE_MOUSE(button): #当鼠标松开
    return ("release_mouse",button)

def IS_MOVE_WHEEL(direction): #当滚动滚轮
    return ("move_wheel",direction)

def IS_MOTION_MOUSE(): #当鼠标移动
    return ("motion_mouse",None)

#事件触发类
class When(object):
    """
    The When class allows you to provide an event and continuously check whether the event has occurred.
    """
    def __init__(self,host:display.Window,condition:str|bool):
        self._host=host #事件触发主体，一般是窗口类
        self._condition=condition #触发条件
    def do(self,command):
        """
        Trigger the specified command when the conditions are met.
        """
        if (self._condition==("start_running",None)): #仅触发一次
            self._host._events["start_running"].append(command)
        elif (self._condition==("frame_step",None)): #每一帧都会触发
            self._host._events["each_frame_step"].append(command)
        elif (self._condition[0]=="press_key"): #当键盘上按键被按下的一瞬间触发一次
            self._host._events[f"press_key_{self._condition[1][1]}"].append(command)
        elif (self._condition[0]=="hold_key"): #当键盘上的按键按下时一直触发，直到松开
            self._host._events[f"hold_key_{self._condition[1][1]}"].append(command)
        elif (self._condition[0]=="release_key"): #当键盘上的按键松开时触发
            self._host._events[f"release_key_{self._condition[1][1]}"].append(command)
        elif (self._condition[0]=="press_mouse"): #当点击鼠标时触发
            self._host._events[f"press_mouse_{self._condition[1][1]}"].append(command)
        elif (self._condition[0]=="release_mouse"): #当松开鼠标时触发
            self._host._events[f"release_mouse_{self._condition[1][1]}"].append(command)
        elif (self._condition[0]=="move_wheel"): #当滚动滚轮时触发
            self._host._events[f"move_wheel_{self._condition[1][1]}"].append(command)
        elif (self._condition[0]=="motion_mouse"): #当移动鼠标时触发
            self._host._events["motion_mouse"].append(command)
    def get_mouse_position(self):
        """
        Get the mouse's relative position in the window.
        """
        x,y=pygame.mouse.get_pos() #实时获取鼠标位置
        return (x-self._host.get_size()[0]/2,y-self._host.get_size()[1]/2)
    def get_delta_position(self):
        """
        Get the change in position of the mouse compared to the previous frame.
        """
        return (self._host._dx,self._host._dy) #获取鼠标位置的变化量