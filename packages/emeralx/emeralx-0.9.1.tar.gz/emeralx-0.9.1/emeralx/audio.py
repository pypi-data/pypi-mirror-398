#导入依赖包
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"]="1" #隐藏pygame输出文本
import pygame

#初始化pygame音频
pygame.mixer.init()

#可引用常量
LOOP=-1

#全局音量
_GLOBAL_VOLUME=1

#全局音量设置
def set_global_volume(volume):
    """
    Used to set the global volume, with a value ranging from 0 to 1.
    """
    global _GLOBAL_VOLUME
    _GLOBAL_VOLUME=volume #设置全局音量大小

#获取全局音量
def get_global_volume():
    """
    Get global volume.
    """
    return _GLOBAL_VOLUME #返回全局音量

#音效类
class Sound(object):
    """
    The Sound class is used to play short music clips on a computer and supports formats such as wav and ogg.
    """
    def __init__(self,path,times=1,volume=1):
        global _GLOBAL_VOLUME
        self._path=path #播放的音频文件的位置
        self._sound=pygame.mixer.Sound(self._path) #pygame音效类
        self._personal_volume=volume #个人音量
        self._volume=_GLOBAL_VOLUME*self._personal_volume #音量
        self._times=times #播放次数
    def play(self):
        """
        Play sound effect.
        """
        self._sound.play(loops=self._times) #播放音效
    def stop(self):
        """
        Stop playing sound effects.
        """
        self._sound.stop()
    def set_volume(self,volume):
        """
        Set own volume.
        """
        global _GLOBAL_VOLUME
        self._personal_volume=volume #设置个人音量
        self._volume=self._personal_volume*_GLOBAL_VOLUME
        self._sound.set_volume(self._volume) #音量设置
    def get_volume(self):
        """
        Return current volume level.
        """
        return self._personal_volume #返回个人音量
    def get_relative_volume(self):
        """
        Return relative volume of sound.
        """
        return self._volume #返回相对音量
    
#音乐类
class Music(object):
    """
    The Music class is used to play long music such as BGM.
    """
    def __init__(self,path,times=1,volume=1):
        global _GLOBAL_VOLUME #初始化全局音量
        self._path=path #文件路径
        self._personal_volume=volume #个人音量
        self._volume=self._personal_volume*_GLOBAL_VOLUME #相对音量
        self._times=times #播放次数
    def play(self,start_time=0,fade=0):
        """
        The method is used to play a music in computer.
        """
        pygame.mixer.music.load(self._path) #加载音乐
        pygame.mixer.music.play(loops=self._times,start=start_time,fade_ms=fade*1000) #播放音乐
    def stop(self):
        """
        Stop playing the music.
        """
        pygame.mixer.music.stop() #结束播放音乐
    def pause(self):
        """
        Pause the music.
        """
        pygame.mixer.music.pause() #暂停播放音乐
    def unpause(self):
        """
        Continue to play the music.
        """
        pygame.mixer.music.unpause() #继续播放音乐
    def set_volume(self,volume):
        """
        Set the volume of playing music.
        """
        global _GLOBAL_VOLUME
        now_progress=self.get_progress()
        self._personal_volume=volume #个人音量设置
        self._volume=self._personal_volume*_GLOBAL_VOLUME #设置相对音量
        pygame.mixer.music.set_volume(self._volume) #音量设置
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.play(loops=self._times,start=now_progress) #从当前进度以新音量播放
        except:
            pass
    def get_volume(self):
        """
        Return the personal volume of music.
        """
        return self._personal_volume #返回个人音量
    def get_relative_volume(self):
        """
        Return the relative volume of music.
        """
        return self._volume #返回相对音量
    def get_busy(self):
        """
        Check if the music is playing, if the state is playing then return True, else return False.
        """
        return pygame.mixer.music.get_busy() #返回播放状态
    def get_progress(self):
        """
        Get the position of music playing.
        """
        return pygame.mixer.music.get_pos()/1000 #播放进度的秒数