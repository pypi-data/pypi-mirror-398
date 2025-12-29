#导入依赖包
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"]="1" #隐藏pygame输出文本
import pygame
import math
import numpy as np
from PIL import Image

#常量定义
GENERAL="general" #缩放质量一般
EXQUISITE="exquisite" #缩放质量精美
HORIZONTALLY="horizontally" #水平翻转
VERTICALLY="vertically" #竖直翻转

#图片类
class Static(object):
    """
    The Static class is used to load images in emeral and perform a series of operations on them.
    """
    def __init__(self,path=None,imgfile=None):
        self._path=path #图片路径
        if (path!=None):
            self._img=pygame.image.load(path) #加载的图片
        else:
            self._img=imgfile #直接提供现有的pygame图片文件
    def proportional_scale(self,times,quality=GENERAL):
        """
        Used for proportionally scaling images.
        """
        after_x=self._img.get_width()*times
        after_y=self._img.get_height()*times
        if (quality==GENERAL):
            self._img=pygame.transform.scale(self._img,(after_x,after_y)) #重新调整图片大小
        elif (quality==EXQUISITE):
            self._img=pygame.transform.smoothscale(self._img,(after_x,after_y)) #重新调整图片大小
        return self #返回自身
    def scale(self,new_size,quality=GENERAL):
        """
        Resize the image.
        """
        if (quality==GENERAL):
            self._img=pygame.transform.scale(self._img,new_size) #重新调整图片大小
        elif (quality==EXQUISITE):
            self._img=pygame.transform.smoothscale(self._img,new_size) #重新调整图片大小
        return self #返回自身
    def rotate(self,radians):
        """
        Rotate the image along the positive direction of any angle.
        """
        self._img=pygame.transform.rotate(self._img,math.degrees(radians))
        return self #返回自身
    def flip(self,direction):
        """
        Flip the image horizontally or vertically.
        """
        if (direction==HORIZONTALLY):
            self._img=pygame.transform.flip(self._img,flip_x=True,flip_y=False)
        elif (direction==VERTICALLY):
            self._img=pygame.transform.flip(self._img,flip_x=False,flip_y=True)
        return self #返回自身
    def extract_edges(self):
        """
        Extract the edges of the image and remove everything except the edges.
        """
        self._img=pygame.transform.laplacian(self._img) #提取边缘
        return self #返回自身
    def solid_overlay(self,color):
        """
        Convert all opaque pixels in the image to the given RGB color.
        """
        img=self._img.convert_alpha()
        new_img=pygame.Surface(img.get_size(),pygame.SRCALPHA)
        #复制alpha通道
        pygame.surfarray.blit_array(new_img, 
                                pygame.surfarray.array3d(img)*0 +  # 清零RGB，然后设置新颜色
                                np.array([[[color[0],color[1],color[2]]]],dtype=np.uint8))
        alpha_array=pygame.surfarray.pixels_alpha(img) #设置alpha通道
        pygame.surfarray.pixels_alpha(new_img)[:]=alpha_array
        
        self._img=new_img #更新图像
        return self #返回自身
    def adjust_brightness(self,brightness):
        """
        Set the brightness of the image, with values ranging from -128 to 128. The default is 0 for the original image.
        """
        lightness=max(-255,min(255, brightness))
        img_converted=self._img.convert_alpha()

        #获取所有像素数据
        pixel_data=pygame.surfarray.array3d(img_converted) #RGB数据
        alpha_data=pygame.surfarray.array_alpha(img_converted) #Alpha数据
        new_pixels=np.clip(pixel_data.astype(np.int16)+lightness,0,255).astype(np.uint8)
        new_img=pygame.Surface(img_converted.get_size(),pygame.SRCALPHA)
        pygame.surfarray.blit_array(new_img,new_pixels)
        alpha_channel=pygame.surfarray.pixels_alpha(new_img)
        alpha_channel[:]=alpha_data
        del alpha_channel #释放锁

        self._img=new_img
        return self #返回自身
    def adjust_alpha(self,percent):
        """
        Set image transparency using a percentage.
        """
        percent=max(0,min(100,percent))
        alpha_value=int(percent*2.55) #计算实际alpha值
        img_converted=self._img.convert_alpha()
        new_img=pygame.Surface(img_converted.get_size(),pygame.SRCALPHA)
        new_img.blit(img_converted,(0,0))
        new_img.set_alpha(alpha_value)
        
        self._img=new_img #替换图片
        return self #返回自身
    def get_width(self):
        """
        Return the width of image.
        """
        return self._img.get_width()
    def get_height(self):
        """
        Return the height of image.
        """
        return self._img.get_height()
    def get_size(self):
        """
        Return the width and height of image by using a tuple which format (width,height).
        """
        return (self._img.get_width(),self._img.get_height())
    
#动态图类
class Animation(object):
    """
    The Animation class allows you to provide a sequence of Images or the path of an animated file so that it can be played in the game, and it can be passed to a Sprite object.
    """
    def __init__(self,sequence=None,path=None):
        if (sequence!=None and path==None): #当序列不为空时
            self._seq=sequence #储存
        elif (sequence==None and path!=None): #当文件路径不为空时
            gif=Image.open(path)
            self._seq=[]
            for frame_index in range(gif.n_frames):
                gif.seek(frame_index)
                frame_rgba=gif.convert('RGBA')
                frame_size=frame_rgba.size
                frame_data=frame_rgba.tobytes()
                pygame_surface=pygame.image.fromstring(frame_data,frame_size,'RGBA')
                self._seq.append(Static(imgfile=pygame_surface)) #写入造型序列
    def get_length(self):
        """
        Return the length of the shape sequence.
        """
        return len(self._seq) #返回造型序列长度
    def get_frame(self,index):
        """
        Find and return the Static object based on the given index.
        """
        return self._seq[index] #返回Static对象
    def proportional_scale(self,times,quality=GENERAL):
        """
        Used for proportionally scaling images.
        """
        new_sequence=[] #新序列
        for item in self._seq:
            after_x=item.get_width()*times
            after_y=item.get_height()*times
            if (quality==GENERAL):
                new_img=pygame.transform.scale(item._img,(after_x,after_y)) #重新调整图片大小
            elif (quality==EXQUISITE):
                new_img=pygame.transform.smoothscale(item._img,(after_x,after_y)) #重新调整图片大小
            new_sequence.append(Static(imgfile=new_img)) #将新的图片写入列表末尾
        self._seq=new_sequence #覆盖原来的序列
        return self #返回自身
    def scale(self,new_size,quality=GENERAL):
        """
        Resize the image.
        """
        new_sequence=[] #新序列
        for item in self._seq: #遍历原来的序列
            if (quality==GENERAL):
                new_img=pygame.transform.scale(item._img,new_size) #重新调整图片大小
            elif (quality==EXQUISITE):
                new_img=pygame.transform.smoothscale(item._img,new_size) #重新调整图片大小
            new_sequence.append(Static(imgfile=new_img))
        self._seq=new_sequence #覆盖原来的序列
        return self #返回自身
    def rotate(self,radians):
        """
        Rotate the image along the positive direction of any angle.
        """
        new_sequence=[]
        for item in self._seq:
            new_img=pygame.transform.rotate(item._img,math.degrees(radians))
            new_sequence.append(Static(imgfile=new_img))
        self._seq=new_sequence
        return self #返回自身
    def flip(self,direction):
        """
        Flip the image horizontally or vertically.
        """
        new_sequence=[]
        for item in self._seq:
            if (direction==HORIZONTALLY):
                new_img=pygame.transform.flip(item._img,flip_x=True,flip_y=False)
            elif (direction==VERTICALLY):
                new_img=pygame.transform.flip(item._img,flip_x=False,flip_y=True)
            new_sequence.append(Static(imgfile=new_img))
        self._seq=new_sequence
        return self #返回自身
    def extract_edges(self):
        """
        Extract the edges of the image and remove everything except the edges.
        """
        new_sequence=[]
        for item in self._seq:
            new_img=pygame.transform.laplacian(item._img) #提取边缘
            new_sequence.append(Static(imgfile=new_img))
        self._seq=new_sequence
        return self #返回自身
    def solid_overlay(self,color):
        """
        Convert all opaque pixels in the image to the given RGB color.
        """
        new_sequence=[]
        for item in self._seq:
            img=item._img.convert_alpha()
            new_img=pygame.Surface(img.get_size(),pygame.SRCALPHA)
            #复制alpha通道
            pygame.surfarray.blit_array(new_img, 
                                    pygame.surfarray.array3d(img)*0 +  # 清零RGB，然后设置新颜色
                                    np.array([[[color[0],color[1],color[2]]]],dtype=np.uint8))
            alpha_array=pygame.surfarray.pixels_alpha(img) #设置alpha通道
            pygame.surfarray.pixels_alpha(new_img)[:]=alpha_array

            new_sequence.append(Static(imgfile=new_img))
        
        self._seq=new_sequence
        return self #返回自身
    def adjust_brightness(self,brightness):
        """
        Set the brightness of the image, with values ranging from -255 to 255. The default is 0 for the original image.
        """
        new_sequence=[]
        lightness=max(-255,min(255, brightness))
        for item in self._seq:
            img_converted=item._img.convert_alpha()

            #获取所有像素数据
            pixel_data=pygame.surfarray.array3d(img_converted) #RGB数据
            alpha_data=pygame.surfarray.array_alpha(img_converted) #Alpha数据
            new_pixels=np.clip(pixel_data.astype(np.int16)+lightness,0,255).astype(np.uint8)
            new_img=pygame.Surface(img_converted.get_size(),pygame.SRCALPHA)
            pygame.surfarray.blit_array(new_img,new_pixels)
            alpha_channel=pygame.surfarray.pixels_alpha(new_img)
            alpha_channel[:]=alpha_data
            del alpha_channel #释放锁
            new_sequence.append(Static(imgfile=new_img))

        self._seq=new_sequence
        return self #返回自身
    def adjust_alpha(self,percent):
        """
        Set image transparency using a percentage.
        """
        new_sequence=[]
        percent=max(0,min(100,percent))
        alpha_value=int(percent*2.55) #计算实际alpha值
        for item in self._seq:
            img_converted=item._img.convert_alpha()
            new_img=pygame.Surface(img_converted.get_size(),pygame.SRCALPHA)
            new_img.blit(img_converted,(0,0))
            new_img.set_alpha(alpha_value)
            new_sequence.append(Static(imgfile=new_img))
        
        self._seq=new_sequence
        return self #返回自身
    def average_size(self):
        """
        Calculate the average size of the image sequence.
        """
        width_values=[] #宽高值列表
        height_values=[]
        for item in self._seq:
            width_values.append(item.get_width())
            height_values.append(item.get_height())
        average_width=sum(width_values)/len(width_values) #计算平均值
        average_height=sum(height_values)/len(height_values)
        return (average_width,average_height) #返回平均值