#导入依赖包
import math
import os

#线类
class Line(object):
    """
    The line class is used to create a line object, which can be referenced by the Room class to draw on the window.
    """
    def __init__(self,start_pos,end_pos,color=(255,255,255),size=1):
        self._start_pos=start_pos #起始坐标
        self._end_pos=end_pos #终止坐标
        self._color=color #直线颜色
        self._size=size #直线宽度
    def get_length(self):
        """
        Used to obtain the length of a straight line.
        """
        #计算直线长度
        return math.sqrt(pow(self._start_pos[0]-self._end_pos[0],2)+pow(self._start_pos[1]-self._end_pos[1],2))
    def get_slope(self):
        """
        Used to obtain the slope of a straight line.
        """
        #计算直线的斜率
        return (self._start_pos[1]-self._end_pos[1])/(self._start_pos[0]-self._end_pos[0])
    def get_midpoint(self):
        """
        Used to obtain the midpoint coordinates of a line segment.
        """
        #计算中点坐标
        return ((self._start_pos[0]+self._end_pos[0])/2,(self._start_pos[1]+self._end_pos[1])/2)
    
#三角形类
class Triangle(object):
    """
    The Triangle class is used to define a triangle object, which can be referenced by a Room object.
    """
    def __init__(self,pos1,pos2,pos3,color=(255,255,255),size=1):
        self._pos1=pos1 #第一个点坐标
        self._pos2=pos2 #第二个点坐标
        self._pos3=pos3 #第三个点坐标
        self._color=color #线条颜色
        self._size=size #线条粗细，0代表填充，1及以上代表不填充的轮廓粗细
    def get_perimeter(self):
        """
        Used to calculate the perimeter of a triangle.
        """
        length1=math.sqrt(pow(self._pos1[0]-self._pos2[0],2)+pow(self._pos1[1]-self._pos2[1],2))
        length2=math.sqrt(pow(self._pos2[0]-self._pos3[0],2)+pow(self._pos2[1]-self._pos3[1],2))
        length3=math.sqrt(pow(self._pos3[0]-self._pos1[0],2)+pow(self._pos3[1]-self._pos1[1],2))
        return length1+length2+length3 #分别算出各点之间的距离，再相加返回
    def get_area(self):
        """
        Used to obtain the area of a triangle.
        """
        return 0.5*math.fabs((self._pos2[0]-self._pos1[0])*(self._pos3[1]-self._pos1[1])-(self._pos3[0]-self._pos1[0])*(self._pos2[1]-self._pos1[1]))
    def get_barycenter(self):
        """
        Return the barycentric coordinates of the triangle.
        """
        x=(1/3)*(self._pos1[0]+self._pos2[0]+self._pos3[0])
        y=(1/3)*(self._pos1[1]+self._pos2[1]+self._pos3[1])
        return (x,y) #返回重心坐标
    def get_parameter(self):
        """
        Return the parameters of the triangle in the form of a tuple, formatted as (length1, length2, length3, angle1, angle2, angle3). length1, length2, and length3 refer to the distances between point 1 and point 2, point 2 and point 3, and point 3 and point 1, respectively. The remaining three parameters are the radian values of the angles opposite length1, length2, and length3, respectively.
        """
        length1=math.sqrt(pow(self._pos1[0]-self._pos2[0],2)+pow(self._pos1[1]-self._pos2[1],2))
        length2=math.sqrt(pow(self._pos2[0]-self._pos3[0],2)+pow(self._pos2[1]-self._pos3[1],2))
        length3=math.sqrt(pow(self._pos3[0]-self._pos1[0],2)+pow(self._pos3[1]-self._pos1[1],2))
        cos1=-(pow(length3,2)-pow(length1,2)-pow(length2,2))/(length1*length2*2) #用余弦定理计算角度的cos值
        cos2=-(pow(length1,2)-pow(length2,2)-pow(length3,2))/(length2*length3*2)
        cos3=-(pow(length2,2)-pow(length3,2)-pow(length1,2))/(length3*length1*2)
        try:
            return (length1,length2,length3,math.acos(cos2),math.acos(cos3),math.acos(cos1)) #返回三角形参数
        except:
            return (0,0,0,0,0,0) #非三角形时返回0向量
        
#矩形类
class Rect(object):
    """
    The Rect class is used to define a rect object, which can be referenced by a Room object.
    """
    def __init__(self,cpos,width,height,color=(255,255,255),size=1):
        self._cpos=cpos #中心点坐标
        self._width=width #宽度
        self._height=height #高度
        self._color=color #颜色
        self._size=size #边线宽度
    def get_perimeter(self):
        """
        Get the perimeter of a rectangle.
        """
        return (self._width)*2+(self._height)*2
    def get_area(self):
        """
        Get the area of a rectangle.
        """
        return self._width*self._height
    def get_rect(self):
        """
        Get the coordinates of the four sides of the rectangle object.
        """
        left=self._cpos[0]-self._width/2
        right=self._cpos[0]+self._width/2
        up=self._cpos[1]+self._height/2
        down=self._cpos[1]-self._height/2
        return (left,right,up,down)
    
#圆类
class Circle(object):
    """
    Create a circle object for drawing on the screen.
    """
    def __init__(self,cpos,radius,color=(255,255,255),size=1):
        self._cpos=cpos #圆心坐标
        self._radius=radius #半径
        self._color=color #颜色
        self._size=size #边线尺寸
    def get_area(self):
        """
        Get the area of a circular object.
        """
        return math.pi*pow(self._radius,2) #计算圆面积并返回
    def get_perimeter(self):
        """
        Get the circumference of a circular object.
        """
        return 2*math.pi*self._radius #计算圆周长并返回

#圆弧类
class Arc(object):
    """
    Create a arc object for drawing on the screen.
    """
    def __init__(self,cpos,radius,from_a,to_a,color=(255,255,255),size=1):
        self._cpos=cpos #中心点
        self._radius=radius #半径
        self._from_a=from_a #初始角
        self._to_a=to_a #结束角
        self._color=color #颜色值
        self._size=size #边缘线宽度
    def get_perimeter(self):
        """
        Get the circumference of the arc object.
        """
        return 2*math.pi*self._radius*((self._to_a-self._from_a)/(2*math.pi)) #计算圆弧周长并返回

#文字类
class Text(object):
    """
    Create a text object for drawing on the screen.
    """
    def __init__(self,text,pos,fontpath="\\".join(os.path.abspath(__file__).split("\\")[:-1])+"\\resources\\default.ttf",color=(255,255,255),size=24):
        self._text=text #文字内容
        self._pos=pos #文字坐标
        self._fontpath=fontpath #字体路径
        self._color=color #字体颜色
        self._size=size #字号