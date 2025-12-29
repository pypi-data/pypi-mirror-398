#导入依赖包
from . import display
from . import image
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"]="1" #隐藏pygame输出文本
import pygame
import uuid

#精灵类
class Sprite(object):
    """
    The Sprite class is used to create an interactive image object on the screen.
    """
    def __init__(self,host:display.Room,img:image.Static|image.Animation,position=(0,0)):
        self._relhost=host
        self._host=host._window #主机名称
        if (type(img)==image.Static):
            self._image=img._img #引用的图像
        elif (type(img)==image.Animation):
            self._image=img._seq[0]._img #选取第一张图像作为默认图像
        self._texture_index=0 #造型索引
        self._host_img=img
        self._x,self._y=position[0],position[1] #精灵位置
        self._id=uuid.uuid4() #精灵id

        #将精灵信息写入主机
        self._host._entities.update({self._id:{"host":host,"image":self._image,"x":self._x,"y":self._y}})
    def next_texture(self):
        """
        Have the sprite switch to the next costume. If it is the last costume, switch back to the first costume.
        """
        if (type(self._host_img)==image.Animation):
            if (self._texture_index<len(self._host_img._seq)-1):
                self._texture_index+=1
                self._image=self._host_img._seq[self._texture_index]._img
            else:
                self._texture_index=0
                self._image=self._host_img._seq[0]._img
        #将精灵信息写入主机
        self._host._entities.update({self._id:{"host":self._relhost,"image":self._image,"x":self._x,"y":self._y}})
    def last_texture(self):
        """
        Have the sprite switch to the last costume. If it is the first costume, switch back to the last costume.
        """
        if (type(self._host_img)==image.Animation):
            if (self._texture_index>0):
                self._texture_index-=1
                self._image=self._host_img._seq[self._texture_index]._img
            else:
                self._texture_index=len(self._host_img._seq)-1
                self._image=self._host_img._seq[0]._img
        #将精灵信息写入主机
        self._host._entities.update({self._id:{"host":self._relhost,"image":self._image,"x":self._x,"y":self._y}})
    def set_texture(self,index):
        """
        Set the sprite costume by costume number.
        """
        if (type(self._host_img)==image.Animation):
            self._texture_index=index
            self._image=self._host_img._seq[self._texture_index]._img
        #将精灵信息写入主机
        self._host._entities.update({self._id:{"host":self._relhost,"image":self._image,"x":self._x,"y":self._y}})
    def texture_length(self):
        """
        Return the length of the costume list.
        """
        return len(self._host_img._seq) #返回造型列表长度
    def translate(self,position):
        """
        Move the sprite to a certain coordinate.
        """
        self._x,self._y=position[0],position[1]
        #将精灵信息写入主机
        self._host._entities.update({self._id:{"host":self._relhost,"image":self._image,"x":self._x,"y":self._y}})
    def x_addition(self,dx):
        """
        Increase the sprite's x coordinate by a certain increment.
        """
        self._x=self._x+dx #增加x坐标
        #将精灵信息写入主机
        self._host._entities.update({self._id:{"host":self._relhost,"image":self._image,"x":self._x,"y":self._y}})
    def y_addition(self,dy):
        """
        Increase the sprite's y coordinate by a certain increment.
        """
        self._y=self._y+dy #增加x坐标
        #将精灵信息写入主机
        self._host._entities.update({self._id:{"host":self._relhost,"image":self._image,"x":self._x,"y":self._y}})
    def set_x(self,x):
        """
        Set the sprite's x coordinate.
        """
        self._x=x #设置精灵的x坐标
        #将精灵信息写入主机
        self._host._entities.update({self._id:{"host":self._relhost,"image":self._image,"x":self._x,"y":self._y}})
    def set_y(self,y):
        """
        Set the sprite's y coordinate.
        """
        self._y=y #设置精灵的y坐标
        #将精灵信息写入主机
        self._host._entities.update({self._id:{"host":self._relhost,"image":self._image,"x":self._x,"y":self._y}})
    def get_location(self):
        """
        Return the sprite's coordinates as a tuple in the format (x, y).
        """
        return (self._x,self._y) #返回坐标值
    def check_collision_with_sprite(self,sprite):
        """
        Use precise pixel detection to determine whether two sprites have collided.
        """
        mask1=pygame.mask.from_surface(self._image) #分别计算两个图片的掩码
        mask2=pygame.mask.from_surface(sprite._image)
        offset_x=sprite._x-self._x #计算偏移量
        offset_y=sprite._y-self._y
        overlap=mask1.overlap(mask2,(offset_x,offset_y))
        return (overlap is not None) #返回布尔值，碰撞为True，不碰撞为False
    def get_id(self):
        """
        Return the ID of the sprite.
        """
        return self._id #返回精灵id
    def predict_collision(self,sprite,dx,dy):
        """
        Predict whether the sprite will collide with another sprite after adding increments dx and dy.
        """
        mask1=pygame.mask.from_surface(self._image) #分别计算两个图片的掩码
        mask2=pygame.mask.from_surface(sprite._image)
        offset_x=sprite._x-(self._x+dx) #计算偏移量
        offset_y=sprite._y-(self._y+dy)
        overlap=mask1.overlap(mask2,(offset_x,offset_y))
        return (overlap is not None) #返回布尔值，碰撞为True，不碰撞为False
    def set_id(self,id:str):
        """
        Set an ID for the sprite and replace the default ID.\n
        Warning: Assigning duplicate IDs to sprites may cause command conflicts and runtime errors.
        """
        self._id=id #替换默认id
    def set_image(self,img):
        """
        Assign a new image to the sprite.
        """
        self._image=img._img #替换原来的精灵图片
        self._host_img=img
    def is_last_texture(self):
        """
        Determine whether the current form of the sprite is the final form.
        """
        if (self._texture_index==len(self._host_img._seq)-1):return True #判断造型编号是否为最后一个
        else:return False
    def is_first_texture(self):
        """
        Determine whether the sprite's current appearance is the first appearance.
        """
        if (self._texture_index==0):return True #判断造型编号是否为0
        else:return False