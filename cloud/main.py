'''
python3 /mnt/user/Database/WebDAV/05-Code/MVUtils/main.py

MVUtils

重命名(预刮削)-软链接-刮削三步

tvshow/movie/ghs三个类型

renamer

电影整理顺序为：
在网盘内预刮削nfo文件，不刮削poster，整理文件夹名称，预刮削时设置更改文件名的细节程度(分辨率，音源，版本)

电视剧整理顺序为：
转存文件后如果多季按Season分出文件夹
tMM简单刮削nfo,规范化文件夹名
对网盘文件用embyformat规范化文件命名
完成后把放在整理文件夹的所有文件移动到指定预设文件夹后，激活shadowSync同步

shadowSync

分为两层：real层和 shadow 层

real层是往shadow层单向同步的

real层是网盘的真实数据，由clouddrive挂载，包含真实文件和简单nfo，所有的文件增删改操作全部在此操作

shadow层保存完全版metadata ，由tMM自动刮削

大体上dowork之前还是按照dirsync来，到了copy / update 阶段有大更改

1.开始前还是进行ignore exclude include处理
只软链接媒体文件，只同步简单nfo

* 准备阶段：开启自动刷新后要确认clouddrive的autorefresh选项关闭，每次拉取文件名前测试clouddrive 可用性，大量拉取两遍核对列表，大量文件不相同的情况警告且仅转移不删除
* 增：real层增加视频文件/文件夹后，等待sync触发，检查与shadow列表不一致处，添加软链接
* 删：real删除文件夹，shadow连同metadata也一起删除
* 改：real改动文件/目录名,shadow按删除后再添加处理 ，shadow被删除的metadata需要重新刮削

tMM docker
设置某些文件夹作为自动刮削的目的文件夹，随时检查变动
'''

import os 
from singlesync import singleSync
from shadowsync import shadowSync

from ghs import updateCloudGHS,moveNativeSingleActor,zeroByte,deleteDislikeMedia,getEmbyPlaylist,getDislikePlaylistID
from tvshow import formatFolderNames,compareTempFolder
from movie import updateCloudMovie

from utils.config import DRIVETYPE,MEDIATYPE,tmpFolderName,cloudRootPath,dstRootPath,CDConfigPath,relAVDCFailedPath,lowerCaseWarning
import json


# 输入网盘编号
print("[+] 请选择需要更新的网盘：")
print('   '.join(['%d.%s'%(i+1,DRIVETYPE[i]) for i in range(0,len(DRIVETYPE))]))


while True:
    driveChoice = input()
    if int(driveChoice)-1 in range(0,len(DRIVETYPE)):
        driveChoiceStr = DRIVETYPE[int(driveChoice)-1]
        print("[+] 你选择的是:%s.%s"%(driveChoice,driveChoiceStr))
        break
    else:
        print('[x] 请输入正确的数字！')


# 输入视频库编号
print("[+] 请选择需要更新的视频库：")
print('   '.join(['%d.%s'%(i+1,MEDIATYPE[i]) for i in range(0,len(MEDIATYPE))]))

while True:
    mediaChoice = input()
    if int(mediaChoice)-1 in range(0,len(MEDIATYPE)):
        mediaChoiceStr = MEDIATYPE[int(mediaChoice)-1]
        print("[+] 你选择的是:%s.%s"%(mediaChoice,mediaChoiceStr))
        break
    else:
        print('[x] 请输入正确的数字！')

# 构造临时目录、源目录和目标目录路径
tmpPath = os.path.join(cloudRootPath,driveChoiceStr,tmpFolderName,mediaChoiceStr)
srcPath = os.path.join(cloudRootPath,driveChoiceStr,mediaChoiceStr)
dstPath = os.path.join(dstRootPath,driveChoiceStr,mediaChoiceStr)
tmpfailedFolder = os.path.join(dstPath,relAVDCFailedPath)

#预检查

#检查是否存在目录
tmpPathExist = os.path.exists(tmpPath)
if not tmpPathExist:
    print('[x] 临时目录 %s 不存在，请检查 CloudDrive 可用性' % tmpPath)


srcPathExist = os.path.exists(srcPath)
if not srcPathExist:
    print('[x] 源目录 %s 不存在，请检查 CloudDrive 可用性' % srcPath)


#检查是否关闭AutoRefreshFolder
if os.path.exists(CDConfigPath):
    with open(CDConfigPath,'r',encoding='utf-8') as f:
        conf = json.load(f)
ARFClosed = not conf['AutoRefreshFolder']
if not ARFClosed:
    print('[x] 请关闭 CloudDrive 中的 AutoRefreshFolder 选项后重试')

#预检查完毕
preCheckOK = srcPathExist and tmpPathExist and ARFClosed


# 根据不同类型分流+后期
if preCheckOK:
    if mediaChoiceStr == 'ghs':
        #GHS的整理流程:1.按番号放到ghstemp中 2.由updateCloudGHS分类放置在ghs中 3.singleSync同步 4.AVDCx刮削 5.单体演员整理 6.（可选）failed变为0字节
        print('[?] 请确认:已经将视频文件放置在 %s/%s 文件夹中，下一步将进行入库和同步操作，确认请输入 y' %(tmpFolderName,mediaChoiceStr))
        while True:
            ghstempConfirm = input()
            if ghstempConfirm == 'y':
                print('[!] 正在进行云端入库')
                updateCloudGHS(tmpPath,srcPath)
                print('[!] 正在进行云端→本地同步')
                singleSync(srcPath,dstPath,'sync',create=True,verbose = True,purge = True)
                ignorePath = os.path.join(dstPath,'temp','.ignore')
                if not os.path.exists(ignorePath):
                    os.makedirs(ignorePath)
                break
            else:
                print(lowerCaseWarning)

        print('[?] 请用AVDCx刮削，刮削完毕后，是否进行单体演员整理？ y/n')
        while True:
            singleActorChoice = input()
            if singleActorChoice == 'y':
                moveNativeSingleActor(dstPath)
                break
            elif singleActorChoice == 'n':
                break
            else:
                print(lowerCaseWarning)

        dislikePlaylistID = getDislikePlaylistID()
        if len(getEmbyPlaylist(dislikePlaylistID)) > 1:
            print('[?] 是否删除Emby中标记为不喜欢的影片？ y/n')
            while True:
                DDMChoice = input()
                if DDMChoice == 'y':
                    deleteDislikeMedia(dislikePlaylistID,tmpfailedFolder)
                    break
                elif DDMChoice == 'n':
                    break
                else:
                    print(lowerCaseWarning)

        print('[!] 失败的和被删除的文件是否进行 0Byte 处理？(默认n) y/n')
        zeroByteChoice = input()
        if zeroByteChoice == 'y':
            zeroByte(tmpfailedFolder,driveChoiceStr)


    elif mediaChoiceStr == '电影':
        #电影的整理流程：1.
        updateCloudMovie(cloudRootPath,driveChoiceStr,tmpFolderName,mediaChoiceStr,checkLater=True)
        singleSync(srcPath,dstPath,'sync',create=True,verbose = True,purge = True)



    else:
        #电视剧类的整理流程：0.temp文件夹比对现有文件夹去重 1.tMM_simple对云端temp进行预整理，更改剧集文件夹名 2.用embyfolderformat对文件名进行整理 3.shadowSync同步 4.tMM对shadow进行细刮削
        print('[!] 比对 %s/%s 文件夹与库中是否有重复的剧集'%(tmpFolderName,mediaChoiceStr))
        compareTempFolder(tmpPath,srcPath)

        print('[?] 请确认:已经用tMM_simple预整理，并放置在 %s/%s 文件夹中，下一步将进行入库和同步操作，确认请输入 y' %(tmpFolderName,mediaChoiceStr))
        while True:
            tvshowtempConfirm = input()
            if tvshowtempConfirm == 'y':
                print('[!] 正在进行云端整理入库')
                formatFolderNames(tmpPath,srcPath)
                print('[!] 正在进行云端→本地同步')
                while True:
                    print('[?] 是否同步字幕文件? y/n')
                    subtitlesSync = input()
                    if subtitlesSync == 'y':
                        shadowSync(srcPath,dstPath,'sync',create=True,verbose = True,purge = True)
                        break
                    elif subtitlesSync == 'n':
                        shadowSync(srcPath,dstPath,'sync',create=True,verbose = True,purge = True,exclude = ['.+\.ass$','.+\.ssa$','.+\.vtt$','.+\.srt$'])
                        break
                    else:
                        print(lowerCaseWarning)
                break
            else:
                print(lowerCaseWarning)
        print('[!] 下一步请用tMM对shadow进行精细刮削或交给Emby刮削')


