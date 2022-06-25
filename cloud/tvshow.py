import os
from posixpath import relpath
import re
import shutil
import json
from time import sleep
from utils.config import lowerCaseWarning
from config import mediaInfoDict
CONFIGPATH = os.getcwd()
SEP = u'/'




class Formatter(object):
    '''
    云端文件整理-按Emby格式重命名媒体文件
    前置要求：需要按：片名 (年份)/Season X/媒体文件  或者 片名 (年份)/媒体文件 来进行预整理
    目的：增大tMM的自动识别能力（去除h265被认成集数的问题）
    '''
    def __init__(self, mediaRootPath,dstPath):
        self._mediaRootPath = mediaRootPath
        segments = self._mediaRootPath.split(SEP)
        self._dstPath = dstPath
        self.driveType = segments[-3]
        self.folderName = segments[-1]
        self._configFPath = os.path.join(CONFIGPATH,'REM_%s_%s.json'%(self.driveType,self.folderName))
        self._dirPath = []
        self._pairs = []
        self._dirPathsuc = []
        self._dirPathfld = []
        self.scheduler()

        #循环完成未修改的
        while True:
            if self._dirPathfld:
                self.scheduler(fld=True)
            else:
                break

    def _walkPath(self,rootPath):
        filelist = []
        for root,dirs,files in os.walk(rootPath): 
            for file in files:
                filelist.append(os.path.join(root,file))
        return (filelist)

    def _getEpisodeOrder(self,filename):
        '''
        获得文件名中的Episode序号
        '''
        #去除干扰项
        filename = filename.replace('4k','').replace('4K','').replace('AC3','')
        filename = re.sub(r"第.季","",filename)
        filename = re.sub(r"第.部","",filename)
        filename = re.sub(r"S(\d{1,2})","",filename)
        filename = re.sub(r"SE(\d{1,2})","",filename)
        #合集筛选 E01+E02
        dashe = re.search(r'(Ep|E|EP|e|ep)(\d+)(-|\+)(\d+)',filename)
        if dashe:
            partE = '%s-E%s' %(dashe.group(2).zfill(2),dashe.group(4).zfill(2))
            return partE
        else:
            #排除了合集，单集筛选
            e = re.search(r'(Ep|E|EP|e|ep)(\d+)',filename)
            if e:
                partE = e.group(2)
            else:
                #如果找不到那就匹配两位纯数字
                two = re.search(r'(\D+|^)(\d{1,2})(\D+)',filename)
                if two:
                    partE = two.group(2)
                else:
                    return None
            return partE.zfill(2)

    def _getAddtionalInfo(self,filename):
        #附加信息转义
        addInfoList = []
        addInfoList.append(self.driveType)
        filenameLower = filename.lower().replace("'",'')
        print(filenameLower)
        #分辨率;附加信息;编码格式;电影版本；电影来源；音轨格式；
        #仍需修改 DTS/DTSHD判断
        for name,kv in mediaInfoDict.items():
            for key,value in kv.items():
                if re.search(key,filenameLower):
                    if value not in addInfoList:
                            addInfoList.append(value)

        return (' - '+'.'.join(addInfoList))

    def _getNewFNamelist(self,filelist):
        '''
        获取文件列表更改后的文件名，返回一个文件名的list
        '''
        newfnamelist = []
        count = 0
        for file in filelist:
            ext = os.path.splitext(file)[-1]

            addInfo = self._getAddtionalInfo(file)

            segments = file.split(SEP)
            if segments[-2].find('Season') != -1: #如果找到Season 
                #按SXXEXX重命名
                s = re.search(r'Season (\d+)',segments[-2].replace('\xa0',' '))
                partS = s.group(1)
                partE = self._getEpisodeOrder(segments[-1])
                seriesName = segments[-3].split('(')[0].replace(' ','')
                if partE:
                    newfilename = '%s - S%sE%s%s%s' %(seriesName,partS.zfill(2),partE,addInfo,ext)
                    if segments[-1] == newfilename:
                        count += 1
                else:
                    newfilename = segments[-1]
            elif segments[-2].find('Special') != -1: #如果找到Special
                '''
                partE = self._getEpisodeOrder(segments[-1])
                seriesName = segments[-3].split('(')[0].replace(' ','')
                if partE:
                    newfilename = '%s - S%sE%s%s%s' %(seriesName,'00',partE.zfill(2),addInfo,ext)
                    if segments[-1] == newfilename:
                        count += 1
                else:
                '''
                newfilename = segments[-1]   
            else:
                #如果没有找到,那就按S01EXX重命名
                partE = self._getEpisodeOrder(segments[-1])
                seriesName = segments[-2].split('(')[0].replace(' ','')
                if partE:
                    newfilename = '%s - S01E%s%s%s' %(seriesName,partE.zfill(2),addInfo,ext)
                    if segments[-1] == newfilename:
                        count += 1
                else:
                    newfilename = segments[-1]
            newfnamelist.append(newfilename)
        if len(filelist) == count:
            return None
        else:
            return(newfnamelist)


    def _writeStatus(self,data):
        if os.path.exists(self._configFPath):
            shutil.copyfile(self._configFPath,self._configFPath + '.old')
        with open(self._configFPath, 'w',encoding='utf-8') as fw:
            json.dump(data,fw,ensure_ascii=False,sort_keys=True, indent=4, separators=(',', ':'))
        print('[√] 写入成功，保存到 '+self._configFPath)
        return

    def scheduler(self,fld = False):
        failed = []
        count = 0
        rem = []
        #检查是不是failed模式，否就正常读取，是就清除之前的数据
        if not fld:
            #获取记忆文件
            if os.path.exists(self._configFPath):
                with open(self._configFPath,'r',encoding='utf-8') as f:
                    rem = json.load(f)
            #先获取mediaRootPath下的所有剧集目录
            for fname in os.listdir(self._mediaRootPath):
                fullpath = os.path.join(self._mediaRootPath,fname)
                if os.path.isdir(fullpath):
                    self._dirPath.append(fullpath)
        else:
            self._dirPath = self._dirPathfld
            self._dirPathsuc = []
            self._dirPathfld = []
            self._pairs = []
            rem = []
        
        #再一个剧一个剧获取应该更改的文件名 
        for path in self._dirPath:
            print('[!] 即将处理：%s'%path)
            count += 1
            filelist = self._walkPath(path)
            newfnamelist = self._getNewFNamelist(filelist)
            dupnewfnamelist =[val for val in list(set(newfnamelist)) if newfnamelist.count(val)>1]
            dupMark = False
            change = ''
            readed = False
            if rem:
                for x in rem:
                    if path in x[0]:
                        change = x[1]
                        readed = True
                        break
            if newfnamelist:
                while True:
                    for i in range(0,len(filelist)):
                        if newfnamelist[i] in dupnewfnamelist:
                            dupMark = True
                            print('\033[31m[x] 源文件相对路径：%s，更改后文件名：%s (更改后文件名重复！)\033[0m ' % (filelist[i].replace(path,''),newfnamelist[i]))
                        else:
                            print('[!] 源文件相对路径：%s，更改后文件名：%s' % (filelist[i].replace(path,''),newfnamelist[i]))
                    if dupMark:
                        dupMark = False
                        print('[?] [%d/%d]当前文件夹为：%s ，存在重复的目标命名，放弃修改还是刷新？ n放弃/r刷新'% (count,len(self._dirPath),path) )
                    else:
                        print('[?] [%d/%d]当前文件夹为：%s ，是否进行重命名？ y是/n否/r刷新'% (count,len(self._dirPath),path) )
                    #确认是否要更改
                    if not change:
                        change = input()
                    if change == 'y' and not dupMark:
                        #是，执行更改
                        for i in range(0,len(filelist)):
                            pathdir,pathname = os.path.split(filelist[i])
                            newpath = os.path.join(pathdir,newfnamelist[i])
                            #print('%s到%s'%(filelist[i],newpath))
                            self._pairs.append([filelist[i],newpath])
                        print('[!] %s 文件夹已添加至修改队列'% path)
                        self._dirPathsuc.append(path)
                        break
                    elif change == 'n':
                        #否，记录一下未更改的
                        segments = path.split(SEP)
                        failed.append(segments[-1])
                        self._dirPathfld.append(path)
                        print ('[!] %s 文件夹放弃修改'% segments[-1])
                        break
                    elif change == 'r':
                        print ('[!] %s 文件夹需要重新整理'% path)
                        filelist = self._walkPath(path)
                        newfnamelist = self._getNewFNamelist(filelist)
                        change = ''
                    else:
                        print(lowerCaseWarning)
                if not readed:
                    rem.append([path,change])
                    self._writeStatus(rem)
            else:
                print('[!] 当前文件夹已整理，不再重复整理：%s '% path)

        print('[✔]所有文件已完成更名设置，现在开始更名')
        for pair in self._pairs:
            src,dst = pair
            print('[!] 重命名:源文件名：%s，更改后文件名：%s'%(src.replace(self._mediaRootPath,''),dst.replace(self._mediaRootPath,'')))
            os.rename(src,dst)
        

        #准备移动temp去主目录
        print('[✔]成功整理的剧目将会被移动')
        if self.driveType.find('CM') != -1:
            CMSleep = int(len(self._pairs)/60)
            print('[!] 检测到网盘类型为天翼云盘，等待辣鸡天翼反应%s秒'%CMSleep)
            sleep(CMSleep)

        for path in self._dirPathsuc:
            relPath = os.path.relpath(path,self._mediaRootPath)
            newpos = os.path.join(self._dstPath,relPath)
            
            if os.path.exists(newpos):
                # 如果存在此文件夹，则选择操作 替换/不替换/补充移动
                while True:
                    print('[!] 目标文件夹 %s 已存在，请选择操作 y替换/n不替换/m移动差异部分' % newpos)
                    existChoice = input()
                    if existChoice == 'y':
                        srcposFList = self._walkPath(path)
                        newposFList = self._walkPath(newpos)
                        srcposList = [x.replace(path,'') for x in srcposFList]
                        newposList = [x.replace(newpos,'') for x in newposFList]
                        print('[!] 旧文件夹文件为：%s'% '，'.join(newposList))
                        print('[!] 新文件夹文件为：%s'% '，'.join(srcposList))
                        while True:
                            print('[?] 是否确认替换？y/n')
                            replaceChoice = input()
                            if replaceChoice == 'y':
                                shutil.rmtree(newpos)
                                shutil.move(path,newpos)
                                break
                            elif replaceChoice == 'n':
                                print('[!] 取消对 %s 的操作，路径被扔回需要更正的文件列表中'%relPath)
                                segments = path.split(SEP)
                                failed.append(segments[-1])
                                self._dirPathfld.append(path)
                                break
                            else:
                                print(lowerCaseWarning)
                        break
                    elif existChoice == 'n':
                        print('[!] 不对 %s 进行操作'%relPath)
                        break
                    elif existChoice == 'm':
                        dir1 = path
                        dir2 = newpos
                        left = set()
                        right = set()

                        for cwd, dirs, files in os.walk(dir1):
                            for f in files:
                                # 转换为相对路径，以便后续与目标目录的比对
                                path = os.path.relpath(os.path.join(cwd, f), dir1) 
                                left.add(path)

                        for cwd, dirs, files in os.walk(dir2):
                            for f in files:
                                path = os.path.relpath(os.path.join(cwd, f), dir2) 
                                right.add(path)
                        common = left.intersection(right)
                        # 移除相同部分
                        left.difference_update(common)
                        fleft = [x.replace(path,'') for x in left]
                        print('[!] 需要移动的文件夹文件为：%s'% '，'.join(fleft))
                        while True:
                            print('[!] 是否确认移动？y/n')
                            moveConfirm = input()
                            if moveConfirm == 'y':
                                for rpath in left:
                                    fulloldpos = os.path.join(dir1,rpath)
                                    fullnewpos = os.path.join(dir2,rpath)
                                    newposParPath = os.path.split(fullnewpos)[0]
                                    if not os.path.exists(newposParPath):
                                        os.makedirs(newposParPath)
                                    shutil.move(fulloldpos,fullnewpos)
                                break
                            elif moveConfirm == 'n':
                                print('[!] 取消对 %s 的操作，路径被扔回需要更正的文件列表中'%relPath)
                                segments = path.split(SEP)
                                failed.append(segments[-1])
                                self._dirPathfld.append(path)
                                break
                            else:
                                print(lowerCaseWarning)
                        break
                    else:
                        print(lowerCaseWarning)

            else:
                print('[!] 正在移动剧集 %s 至 %s'% (relPath,self._dstPath))
                shutil.move(path,newpos)


        #更正
        if failed:
            print( ('[!] 目前仍需更正的文件夹为：%s') % '、'.join(failed))
            while True:
                print('[?] 是否更正完成？更正完毕后请输入y')
                corrected = input()
                if corrected == 'y':
                    break
                else:
                    print(lowerCaseWarning)
        return

def formatFolderNames(mediaRootPath,dstPath):
    Formatter(mediaRootPath,dstPath)


def compareTempFolder(tmpPath,srcPath):
    # 1.提取名称，比对相似度（包含文件名） 2.提取源文件属性关键字和目标文件/文件夹属性关键字
    formattedNames = os.listdir()
    return

