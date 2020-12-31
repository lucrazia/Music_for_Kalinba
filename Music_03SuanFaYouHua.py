#需要pip安装pyaudio,建议直接本地下载whl来安装
import os
import wave
import pyaudio
from Music_map import *
import copy     #用于列表深复制

import numpy as np #矩阵计算用的？
#============================================
#混音函数
#============================================
#将声音混合；从而实现同时播放多个音频的效果
#需要传入：转换为矩阵后的2个音频数据，及其长度
def music_mix(yin1,yin2,len1,len2):

    #混音教程地址：https://blog.csdn.net/weixin_33704234/article/details/92299297
    #读取，之前保存了的音节数据
    data1 = yin1
    data2 = yin2
    len_of_1 = len1
    len_of_2 = len2
    #混音过程，首先将字符格式的数据转换为矩阵的
    wave_data_1 = np.frombuffer(data1, dtype=np.int16)
    wave_data_2 = np.frombuffer(data2, dtype=np.int16)
    # 对不同长度的音频用数据零对齐补位
    if len_of_1 < len_of_2:
        length = abs(len_of_2 - len_of_1)
        temp_array = np.zeros(length, dtype=np.int16)
        rwave_data_1 = np.concatenate((wave_data_1, temp_array))
        rwave_data_2 = wave_data_2

    elif len_of_1 > len_of_2:
        length = abs(len_of_2 - len_of_1)
        temp_array = np.zeros(length, dtype=np.int16)
        rwave_data_2 = np.concatenate((wave_data_2, temp_array))
        rwave_data_1 = wave_data_1

    else:
        rwave_data_1 = wave_data_1
        rwave_data_2 = wave_data_2

    #混音,必须长度一致。。。
    mix_wave_data = rwave_data_1+rwave_data_2
    return  mix_wave_data,len(mix_wave_data)

#============================================
#音频数据提取函数
#============================================
#将音频片段取出，若播放完毕则从musicList中移除音频
def pickUp_music(musicList,music,mList_i,index):
    data1 = music[mList_i][0][ music[mList_i][1][index] ]
    # print(mList_i+" : "+str(music[mList_i][1]))
    #每取出一次，下标+1
    music[mList_i][1][index] += 1
    #如果字典记录的下标大于音频数据列表长度，则退出;将音源字典的重复弹奏列表移除该下标元素
    if music[mList_i][1][index]>= len(music[mList_i][0]):
        #根据索引删除
        del music[mList_i][1][index]
        # 如果音源重复弹奏标记列表内容为空，则将音频播放列表的对应元素删除。
        if len(music[mList_i][1]) == 0:
            musicList.remove(mList_i)

    wave_data = np.frombuffer(data1, dtype=np.int16)
    len_of_d_w = len(wave_data)
    #返回音频片段的 矩阵数据 和 长度
    return wave_data,len_of_d_w


#============================================
#初始化
#============================================

filepath = "拇指琴各音节wav/对齐长度"  # 添加路径
filename = os.listdir(filepath)  # 得到文件夹下的所有文件名称

#音频拆分，每段长度（1024）316能整除
#chunk大了，可以明显感觉到串音如：chunk：7168 ，弹奏间隔：1
chunk = 129
#弹奏间隔   （7）
INTERVAL = 47

#格式，输出用。。
FORMAT = pyaudio.paInt16
RATE = 48000

# 获取音频字典，并存储到字典中
# 字典结构：{'wav文件名':[  音频数据拆分成列表，列表元素为音频数据字符------------------字典[wav名][0]
#                        [nchannels, sampwidth, framerate, nframes]-----字典[wav名][1][0,1,2,3]
#                     ]     }
music_one = {}
for i in range(0,len(filename)):
    #获取音节
    w = wave.open(filepath+'\\'+filename[i], 'rb')
    params = w.getparams()
    nchannels, sampwidth, framerate, nframes = params[:4]
    #这一步相当于去掉扩展名
    yinjie_name = filename[i].split('.')[0]
    #对音频进行拆分，每段长度为chunk，分段存储到列表中，方便后续混音操作
    music_str_dataList = []
    while True:
        data = w.readframes(chunk)
        if data == b'': break
        music_str_dataList.append(data)
    #音频字典：
    music_one[ yinjie_name ] =[ music_str_dataList,                      # 0简谱音频数据转为字符的列表
                                [],                                     # 1重复弹奏音节，标记列表。
                              [nchannels, sampwidth, framerate, nframes] # 2其他信息
                              ]
    w.close()

#这里的音频信息基本上都是一样的，先随便弄一套出来。
nchannels, sampwidth, framerate1, nframes = music_one['1'][2]

print('音频数据段数：\t'+str(len(music_one['_'][0])))
print('chunk:\t\t\t'+str(chunk) +' 字节')
print('弹奏间隔:\t\t\t'+str(INTERVAL)+' 个chunk')
print('帧数:\t\t\t'+str(nframes)+' 帧')
print(music_one['1'][2])

#测试各音节基本信息
# for i in music_one:
#     print(i,end='\t: ')
#     print(music_one[i][2])

#主函数，传入波形列表；填充波形数据。
def Music_main(wave_list,music_map):
    count = 0                   #count 是对每一次循环的计数；
    map_i = 0                   #map_i 是谱子的下标，作为谱子music_map的下标
    interval = INTERVAL         #弹奏间隔的控制
    musicList = []              #musicList 是即将播放的各个音节列表
    while True:
        wave_data_old = b''
        len_of_d_w_old = 0
        #每计数到n就加入下一个音频
        if count % interval == 0:
            #如果谱子下标大于谱子长度，就跳过加音频的操作
            if map_i >= len(music_map):
                pass
                #抽取音频片段的函数会慢慢消耗musicList，消耗完了，就播放完毕
                if len(musicList)==0:
                    # print('播放完毕')
                    break
            else:
                # print('加入下一处音频')
                #如果重复弹同一个音,重音列表就新增元素;但不需要加入musicList
                if music_map[map_i] in musicList:

                    music_one[  music_map[map_i]  ][1].append(0)
                    map_i += 1
                else:

                    #没有重复弹，也要在重音列表中新增元素，需要加入musicList
                    music_one[  music_map[map_i]  ][1].append(0)
                    musicList.append(  music_map[map_i]  )
                    map_i += 1

        count += 1

        #musicList的长度，在遍历过程中会发生变化，所以"深复制"一下，不直接遍历原列表
        musicList_beifen = copy.deepcopy(musicList)

        #根据音节列表循环，不断更新old的数据
        #最终得到当前chunk组的音节输出
        for mList_i in musicList_beifen:
            #repeated_index重复标志
            for repeated_index in range(  0 , len( music_one[mList_i][1] )  ):
                #降序的下标
                des_repeated_index = len( music_one[mList_i][1] ) - repeated_index - 1
                #将音频片段取出，若播放完毕则从musicList中移除音频,   传入的是从大到小的下标,所以不会出现下标越界
                wave_data, len_of_d_w = pickUp_music( musicList , music_one , mList_i , des_repeated_index )
                #与前面的部分进行混音，并保存给old
                wave_data_old,len_of_d_w_old =music_mix(
                                                    wave_data_old,
                                                    wave_data,
                                                    len_of_d_w_old,
                                                    len_of_d_w
                                                    )
        if wave_data_old is b'':
            pass
        else:
            wave_list.append(wave_data_old.tobytes())
            # print('====================================加入'+str(count))

#============================================
#音频播放部分：
#============================================
#目标波形列表
wave_list = []

#可选谱面：music_map，Genshin_main，Genshin_accompaniment,Monvzhilv
#将music_map：主调波形数据处理好，存到wave_list中。
choice = Monvzhilv
Music_main(wave_list,choice)
#python音乐播放器相关定义。
play = pyaudio.PyAudio()


#============================================
#录音，生成wav文件
#============================================

def record(re_frames, WAVE_OUTPUT_FILENAME):
    print("开始录音")
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(nchannels)
    wf.setsampwidth(play.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(re_frames)
    wf.close()
    print("关闭录音")

#定义w为bytes类型，用于合并wave数据
w = b''
for w1 in wave_list:
    w = w + w1

output_name = 'output_3'

record(w, 'save/%s.wav'%(output_name))
