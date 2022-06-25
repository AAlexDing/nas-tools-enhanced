import os
import re
import json
try:
    import requests
except ImportError:
    os.system('pip install requests')
    import requests

from utils.config import *
from utils.functions import *
from config import *
from time import sleep


# 马赛克破坏版后缀、流出版后缀、无码后缀、有码后缀、中文字幕关键字、中文字幕后缀、后缀拼接顺序
config = {'umr_style': '-umr', 'leak_style': '-leaked', 'wuma_style': '', 'youma_style': '',
          'cnword_char': '-C.,-C-,字幕', 'cnword_style': '-C', 'suffix_sort': 'mosaic,cd_part,cnword,definition'}
compareUMR = config.get('umr_style').upper()
compareLEAKED = config.get('leak_style').upper()



def removeDupName(srcFolder):
    '''
    清除ghstemp文件夹中的重复文件
    '''
    print('[!] 正在去除临时文件夹中的重复文件')
    filelist = getFileList(srcFolder)

    #按扩展名优先级预排序文件名
    sortedlist = []
    for sortext in MEDIAEXT:
        templist = []
        for file in filelist:
            fname,ext = os.path.splitext(file)
            if ext.lower() == sortext:
                templist.append(file)
        templist.sort()
        sortedlist.extend(templist)

    fnamelist = []

    #按照扩展名优先级去除相同名称文件
    for file in sortedlist:
        fname,ext = os.path.splitext(file)
        if fname in fnamelist:
                os.remove(file)
                print('[!] 已删除重复文件:%s'%file)
        else:
            fnamelist.append(fname)

    #尽量不要多分集的，按照-CD去除相同名称文件
    for file in sortedlist:
        fname,ext = os.path.splitext(file)
        if fname.upper().find('-CD') != -1:
            newfname = re.sub(r"(-CD|-cd)\d{1,2}","",fname)
            if newfname in fnamelist:
                os.remove(file)
                print('[!] 已删除重复文件:%s'%file)

def getNumber(filepath, escape_string=''):
    corp = ''
    filepath = filepath.upper().replace('1080P', '').replace('720P', '').replace('-C.', '.').replace('.PART', '-CD').replace('-PART', '-CD').replace(' ', '-').replace('FULL.', '.')
    filename = os.path.splitext(os.path.split(filepath)[1])[0]
    # 排除多余字符
    escape_string_list = re.split('[,，]', escape_string)
    for string in escape_string_list:
        filename = filename.replace(string.upper(), '')

    # 如果存在厂商关键字则增加
    if filename.find('HEYDOUGA') != -1:
        corp = 'HEYDOUGA-'
    elif filename.find('CARIB') != -1:
        corp = 'CARIB-'
    elif filename.find('1PON') != -1:
        corp = '1PON-'
    elif filename.find('PACO') != -1:
        corp = 'PACO-'
    elif filename.find('10MU') != -1:
        corp = '10MU-'
    elif filename.find('GACHI') != -1:
        if filename.find('GACHIP') != -1:
            corp = 'GACHIP-'
        elif filename.find('GACHIG') != -1:
            corp = 'GACHIG-'
        elif filename.find('GACHIPPV') != -1:
            corp = 'GACHIPPV-'
        else:
            corp = 'GACHI-'

    # 再次排除关键字
    filename = filename.replace('HEYDOUGA-', '').replace('HEYDOUGA', '').replace('CARIBBEANCOM', '').replace('CARIB', '').replace('1PONDO', '').replace('1PON', '').replace('PACOMA', '').replace('PACO', '').replace('10MUSUME', '').replace('-10MU', '').replace('FC2PPV', 'FC2-').replace('--', '-').replace('(', '').replace(')', '').replace('GACHIPPV', 'GACHI').replace('_HD_', '').replace('TOKYO-HOT', '').replace('_FULL', '').replace('[THZU.CC]', '').replace('「麻豆」', '')
    



    part = ''
    if re.search(r'-CD\d+', filename):
        part = re.findall(r'-CD\d+', filename)[0]
    filename = filename.replace(part, '')
    filename = str(re.sub(r"-\d{4}-\d{1,2}-\d{1,2}", "", filename))             # 去除文件名中时间
    filename = str(re.sub(r"\d{4}-\d{1,2}-\d{1,2}-", "", filename))             # 去除文件名中时间
    if re.search(r'[^.]+[.-]+\d{2}\.\d{2}\.\d{2}', filename):                   # 提取欧美番号 sexart.11.11.11
        file_number = re.search(r'[^.]+[.-]\d{2}\.\d{2}\.\d{2}', filename).group()
        return file_number.lower().replace('-', '.')
    elif re.search(r'XXX-AV-\d{4,}', filename):                                 # 提取xxx-av-11111
        file_number = re.search(r'XXX-AV-\d{4,}', filename).group()
        return file_number
    elif 'FC2' in filename:
        filename = filename.replace('PPV', '').replace('_', '-').replace('--', '-')
        if re.search(r'FC2-\d{5,}', filename):                                  # 提取类似fc2-111111番号
            file_number = re.search(r'FC2-\d{5,}', filename).group()
        elif re.search(r'FC2\d{5,}', filename):
            file_number = re.search(r'FC2\d{5,}', filename).group().replace('FC2', 'FC2-')
        else:
            file_number = filename
        return file_number
    elif 'HEYZO' in filename:
        filename = filename.replace('_', '-').replace('--', '-')
        if re.search(r'HEYZO-\d{3,}', filename):                                # 提取类似HEYZO-1111番号
            file_number = re.search(r'HEYZO-\d{3,}', filename).group()
        elif re.search(r'HEYZO\d{3,}', filename):
            file_number = re.search(r'HEYZO\d{3,}', filename).group().replace('HEYZO', 'HEYZO-')
        else:
            file_number = filename
        return file_number
    elif re.search(r'S2M[BD]?-\d{3,}', filename):                               # 提取S2MBD-002 或S2MBD-006
        file_number = re.search(r'S2M[BD]?-\d{3,}', filename).group()
        return file_number
    elif re.search(r'MX3DS?-\d{3,}', filename):                               # 提取S2MBD-002 或S2MBD-006
        file_number = re.search(r'MX3DS?-\d{3,}', filename).group()
        return file_number
    elif re.search(r'T28-\d{3,}', filename):                                    # 提取T28-223
        file_number = re.search(r'T28-\d{3,}', filename).group()
        return file_number
    elif re.search(r'TH101-\d{3,}-\d{5,}', filename):                           # 提取th101-140-112594
        file_number = re.search(r'TH101-\d{3,}-\d{5,}', filename).group().lower()
        return file_number
    elif '-' in filename or '_' in filename:                                    # 普通提取番号 主要处理包含减号-和_的番号
        if re.search(r'\d+[a-zA-Z]+-\d+', filename):                            # 提取类似259luxu-1456番号
            file_number = re.search(r'\d+[a-zA-Z]+-\d+', filename).group()
        elif re.search(r'[a-zA-Z]+-\d+', filename):                             # 提取类似mkbd-120番号
            file_number = re.search(r'[a-zA-Z]+-\d+', filename).group()
            suren_dic = {
                'LUXU': '259',                                                  # 200LUXU-2556
                'GANA': '200',                                                  # 200GANA-2556
                'MAAN': '300',                                                  # 300MAAN-673
                'MIUM': '300',                                                  # 300MIUM-745
                'NTK-': '300',                                                  # 300NTK-635
                'JAC-': '390',                                                  # 390JAC-034
                'DCV-': '277',                                                  # 277DCV-102
                'NTR-': '348',                                                  # 348NTR-001
                'ARA-': '261',                                                  # 261ARA-094
                'TEN-': '459',                                                  # 459TEN-024
                'GCB-': '485',                                                  # 485GCB-015
                'SEI-': '502',                                                  # 502SEI-001
                'KNB-': '336',                                                  # 336KNB-172
                'SUKE-': '428',                                                 # 428SUKE-086
                'HHH-': '451',                                                  # 451HHH-027
                'MLA-': '476',                                                  # 476MLA-043
                'KJO-': '326',                                                  # 326KJO-002
                'SIMM-': '345',                                                 # 345SIMM-662
                'MFC-': '435',                                                  # 435MFC-142
                'SHN-': '116',                                                  # 116SHN-045
                'NAMA-': '332',                                                 # 332NAMA-077
                'CUTE-': '229',                                                 # 229SCUTE-953
                'KIRAY-': '314',                                                # 314KIRAY-128
            }
            for key, value in suren_dic.items():
                if key in file_number:
                    if surenNumber:
                        file_number = value + file_number
                    else:
                        file_number = file_number
                    break
        elif re.search(r'[a-zA-Z]+-[a-zA-Z]\d+', filename):                     # 提取类似mkbd-s120番号
            file_number = re.search(r'[a-zA-Z]+-[a-zA-Z]\d+', filename).group()
        elif re.search(r'\d+-\d+', filename):                                   # 提取类似 111111-000 番号
            file_number = re.search(r'\d+-\d+', filename).group()
        elif re.search(r'\d+_\d+', filename):                                   # 提取类似 111111_000 番号
            file_number = re.search(r'\d+_\d+', filename).group()
        elif re.search(r'\d+-[a-zA-Z]+', filename):                             # 提取类似 111111-MMMM 番号
            file_number = re.search(r'\d+-[a-zA-Z]+', filename).group()
        elif re.findall(r'\d{3,}', filename) and re.findall(r'[A-Z]{2,}', filename):
            find_num = re.findall(r'\d{3,}', filename)[0]
            find_char = re.findall(r'[A-Z]{2,}', filename)[0]
            file_number = find_char + '-' + find_num
        else:
            file_number = filename

        return corp+file_number
    elif re.search(r'([A-Z]{3,})00(\d{3})', filename):                          # 提取ssni00644为ssni-644
        a = re.search(r'([A-Z]{3,})00(\d{3})', filename)
        file_number = a[1] + '-' + a[2]
        return file_number
    elif re.search(r'N\d{4}', filename):                                        # 提取N1111
        file_number = re.search(r'N\d{4}', filename).group()
        return file_number.lower()
    elif re.search(r'K\d{4}', filename):                                        # 提取K1111
        file_number = re.search(r'N\d{4}', filename).group()
        return file_number.lower()
    elif re.search(r'HEYZO_\d{4}', filename):                                   # 提取HEYZO_0666.640X480
        file_number = re.search(r'HEYZO_\d{4}', filename).group().replace('_', '-')
        return file_number
    else:                                                                       # 提取不含减号-的番号，FANZA CID 保留ssni00644，将MIDE139改成MIDE-139
        try:
            find_num = re.findall(r'\d{2,}', filename)[0]
            find_char = re.findall(r'[A-Z]{2,}', filename)[0]
            file_number = find_char + '-' + find_num
        except:
            try:
                file_number = re.findall(r'([^【】「」]{3,}\d+)', filename)[0]
            except:
                file_number = filename
        return file_number

def isUncensored(number):
    if re.match(r'^\d{4,}', number) or re.match(r'n\d{4}', number) or 'HEYZO' in number.upper() or re.search(r'[^.]+\.\d{2}\.\d{2}\.\d{2}', number):
        return True
    else:
        return False

def getFileInfo(file_path, appoint_number='',escape_string = ''):
    file_path = file_path.replace('\\', '/')
    movie_number = ''
    has_sub = False
    c_word = ''
    cd_part = ''
    destroyed = ''
    leak = ''
    wuma = ''
    youma = ''
    mosaic = ''
    definition = ''

    # 获取文件名
    folder_path, file_full_name = os.path.split(file_path)                  # 获取去掉文件名的路径、完整文件名（含扩展名）
    file_name, file_ext = os.path.splitext(file_full_name)                   # 获取文件名（不含扩展名）、扩展名(含有.)
    
    # 获得视频分辨率
    for key,value in resolutionDict.items():
        if re.search(key,file_name.lower()):
            definition = value
    if not definition and getDefinitionFromFile:
        mediaInfo = MediaInfo.parse(file_path)
        definition = getResolution(mediaInfo)

    try:
        # 获取番号
        if appoint_number:                                                  # 如果指定了番号，则使用指定番号
            movie_number = appoint_number
        else:
            movie_number = getNumber(file_path, escape_string)

        # 判断是否分集及分集序号
        file_name1 = file_name.lower().replace('_', '-').replace('.', '-') + '.' # .作为结尾

        # xxxxx 1.mp4 或者 xxxxx-1.mp4
        if re.search(r'[- ]\d{1}\.', file_name1):
            a = re.search(r'[- ](\d{1})\.', file_name1)
            file_name1 = file_name1.replace(a[0], '-cd' + str(a[1]))

        # .part2, -a.mp4
        file_name1 = file_name1.replace('-part', '-cd').replace('-a.', '-cd1').replace('-b.', '-cd2').replace('-d.', '-cd4').replace('-e.', '-cd5').replace('-f.', '-cd6').replace('-g.', '-cd7').replace('-h.', '-cd8').replace('-i.', '-cd9')

        # hd1.mp4
        file_name1 = file_name1.replace('-hd1.', '-cd1').replace('-hd2.', '-cd2').replace('-hd3.', '-cd3').replace('-hd4.', '-cd4').replace('-hd5.', '-cd5').replace('-hd6.', '-cd6').replace('-hd7.', '-cd7').replace('-hd8.', '-cd8')

        # a.vr.mp4
        file_name1 = file_name1.replace('a-vr.', '-cd1.').replace('b-vr.', '-cd2.').replace('c-vr.', '-cd3.').replace('d-vr.', '-cd4.').replace('e-vr.', '-cd5.').replace('f-vr.', '-cd6.').replace('g-vr.', '-cd7.').replace('h-vr.', '-cd8.')

        if 'cd' in file_name1:
            part_list = re.search(r'[-_]cd\d+', file_name1)
            if part_list:
                cd_part = part_list[0].replace('_', '-')
        else:
            part_list = re.search(r'[-_]\d{1}\.', file_name1)
            if part_list:
                cd_part = '-cd' + str(re.search(r'\d', part_list[0])[0])

        # 判断是否是马赛克破坏版
        umr_style = str(config.get('umr_style'))
        if '-uncensored.' in file_path.lower() or 'umr.' in file_path.lower() or '破解' in file_path or '克破' in file_path or (umr_style and umr_style in file_path):
            destroyed = umr_style
            mosaic = '无码破解'

        # 判断是否流出
        leak_style = str(config.get('leak_style'))
        if '流出' in file_path or 'leaked' in file_path.lower() or (leak_style and leak_style in file_path):
            destroyed = ''
            leak = leak_style
            mosaic = '无码流出'

        # 判断是否无码
        wuma_style = str(config.get('wuma_style'))
        if not mosaic:
            if isUncensored(movie_number) or '无码' in file_path or '無碼' in file_path or '無修正' in file_path or 'uncensored' in file_path.lower():
                wuma = wuma_style
                mosaic = '无码'

        # 判断是否有码
        youma_style = str(config.get('youma_style'))
        if not mosaic:
            if '有码' in file_path or '有碼' in file_path:
                youma = youma_style
                mosaic = '有码'

        # 判断是否国产
        if not mosaic:
            if '国产' in file_path or '麻豆' in file_path:
                mosaic = '国产'

        # 查找本地字幕文件
        cnword_list = config.get('cnword_char').replace('，', ',').split(',')
        cnword_style = str(config.get('cnword_style'))

        # 判断路径名是否有中文字幕字符
        if not has_sub:
            file_temp_path = file_path.upper().replace('CD', '').replace('CARIB', '') # 去掉cd/carib，避免-c误判
            cnword_list.append('-C-')
            for each in cnword_list:
                file_temp_name,file_temp_ext = os.path.splitext(file_path)
                if each.upper() in file_temp_path or file_temp_name.endswith('ch'):
                    if '無字幕' not in file_path and '无字幕' not in file_path:
                        c_word = cnword_style                                         # 中文字幕影片后缀
                        has_sub = True
                        break

        # 判断文件名是否包含待命名的中文字幕样式
        if not has_sub and cnword_style:
            file_temp_name = str(movie_number) + cd_part + cnword_style
            if file_temp_name.upper() in file_path.upper():
                c_word = cnword_style
                has_sub = True

        # 后缀拼接顺序
        file_show_name = movie_number
        suffix_sort_list = config.get('suffix_sort').split(',')
        for each in suffix_sort_list:
            if each == 'mosaic':
                file_show_name += destroyed + leak + wuma + youma
            elif each == 'cd_part':
                file_show_name += cd_part
            elif each == 'cnword':
                file_show_name += c_word
            elif each == 'definition':
                if definition:
                    file_show_name += '-'+definition
        file_show_name += file_ext
        
    except Exception as e:
        print(str(e))
        

    return (movie_number,folder_path, file_show_name)

def checkFilenameFormat(folder):
    '''
    检查文件名格式
    '''
    if getDefinitionFromFile:
        print('[!] 正在检查 %s 文件夹文件名格式（开启读取文件分辨率模式）'%(folder))
    else:
        print('[!] 正在检查 %s 文件夹文件名格式'%(folder))
    dupMark = False
    change = ''
    tempfilelist = getFileList(folder)
    fileShowNameList = []
    for filepath in tempfilelist:
        number,folderPath,fileShowName = getFileInfo(filepath)
        fileShowNameList.append(fileShowName)
    dupnewfnamelist =[val for val in list(set(fileShowNameList)) if fileShowNameList.count(val)>1]

    if tempfilelist:
        while True:
            for i in range(0,len(fileShowNameList)):
                if fileShowNameList[i] in dupnewfnamelist:
                    dupMark = True
                    print('\033[31m[x] 原文件名：%s，新文件名：%s (新文件名有重复！)\033[0m ' % (os.path.split(tempfilelist[i])[1],fileShowNameList[i]))
                else:
                    if not os.path.split(tempfilelist[i])[1] == fileShowNameList[i]:
                        print('[!] 原文件名：%s，新文件名：%s' % (os.path.split(tempfilelist[i])[1],fileShowNameList[i]))
            if dupMark:
                dupMark = False
                print('[?] 存在重复的目标命名，放弃修改还是刷新？ n放弃/r刷新')
            else:
                print('[?] 是否进行重命名？ y是/n否/r刷新' )
            #确认是否要更改
            if not change:
                change = input()
            if change == 'y' and not dupMark:
                #是，执行更改
                for i in range(0,len(tempfilelist)):
                    pathdir,pathname = os.path.split(tempfilelist[i])
                    newpath = os.path.join(pathdir,fileShowNameList[i])
                    #print('%s到%s'%(filelist[i],newpath))
                    src = tempfilelist[i]
                    dst = newpath
                    print('[!] 重命名:原文件名：%s，新文件名：%s'%(src.replace(folder,''),dst.replace(folder,'')))
                    os.rename(src,dst)
                break
            elif change == 'n':
                #否，记录一下未更改的
                print ('[!] 放弃重命名')
                break
            elif change == 'r':
                print ('[!] 请重新整理 %s'%folder)
                tempfilelist = getFileList(folder)
                fileShowNameList = []
                for filepath in tempfilelist:
                    number,folderPath,fileShowName = getFileInfo(filepath)
                    fileShowNameList.append(fileShowName)
                change = ''
            else:
                print(lowerCaseWarning)

    return

class NewMediaFile(object):

    def __init__(self, srcfile,dstFolder):
        self.srcfile = srcfile
        self.relsrcfile = srcfile.replace(cloudRootPath,'')
        self.dstFolder = dstFolder
        self.size = os.path.getsize(srcfile)
        self.fullname = os.path.split(srcfile)[1]
        self.fname = os.path.splitext(self.fullname)[0]
        self.ext = os.path.splitext(self.fullname)[1].lower()

        # 获取目标系列文件夹名称，如果不存在就放在others中
        self.seriesName = self.getSeriesName()
        self.dstSeriesFolder = os.path.join(self.dstFolder,self.seriesName)
        if not os.path.exists(self.dstSeriesFolder):
            self.dstSeriesFolder = os.path.join(self.dstFolder,'others')

        # 遍历得到系列已有的文件
        self.seriesFileList = getFileList(self.dstSeriesFolder)

        # 获得纯番号
        self.number = getNumber(self.fullname)
        self.dstFileExist = False
        self.existingFiles = self._getSeriesFolderFileList()
        self.dstFilePath = os.path.join(self.dstSeriesFolder,self.fullname)



    def getSeriesName(self):
        '''
        获取系列文件夹名称
        '''
        if re.search(r'N\d{4}', self.fname):                                        # 提取N1111
            seriesName = 'TokyoHot N'
        elif re.search(r'K\d{4}', self.fname):                                        # 提取K1111
            seriesName = 'TokyoHot K'
        elif re.search(r'GACHI', self.fname):                                      
            seriesName = 'GACHI'
        else:
            seriesName = self.fname.split('-')[0]
        
        return seriesName

    def _getSeriesFolderFileList(self):
        '''
        搜索现有文件中是否存在相同番号
        '''
        existingFiles = []
        for sfile in self.seriesFileList:
            sfNumber = getNumber(sfile)
            if self.number == sfNumber:
                existingFiles.append(sfile)
                self.dstFileExist =True
        return existingFiles
    

    def calScore(self,fpath):
        '''
        目前条件/权重：  条件优先级：版本>分级>分辨率>格式
            1.格式 '.MP4'+10,'.MKV'+9,'.AVI'+8,'.RMVB'+7,'.RM'+6,'.MOV'+5,'.WMV'+4,'.MPG'+3,'.VOB'+2,'.MPEG'+1,'.TS' 
            2.-CD  -90                                                          # 最好不要分集
            3.分辨率 8K-10  4K+10 1080P +20 720p +10   542p 0 低于542p -100     # 最好
            4.版本 马赛克破坏版+20、流出版 +100     字幕 +20                            # 流出版优先级最高 马赛克破坏版和字幕版相同权重
        '''
        fname = os.path.split(fpath)[1]
        score = 0
        # 按分值表打分
        kws = {'\.MP4$':10,'\.MKV$':9,'\.AVI$':8,'\.RMVB$':7,'\.RM$':6,'\.MOV$':5,'\.WMV$':4,'\.MPG$':3,'\.VOB$':2,'\.MPEG$':1,'-CD':-90,'8K':-10,'4K':10,'1440P|1080P|960P':20,'720P':10,'480P|360P|144P':-100,compareUMR:20,compareLEAKED:100}
        for key,value in kws.items():
            if re.search(key,fname.upper()):
                score += value
        
        # 如果没有分辨率标记的文件名，就读取文件属性
        if not re.search('8K|4K|(\d{3,4}P)',fname) and getDefinitionFromFile:
            mediaInfo = MediaInfo.parse(fpath)
            vsize = getResolution(mediaInfo)
            for key,value in kws.items():
                if re.search(key,vsize):
                    score += value
        #如果有字幕 20分
        if fname.upper().replace('-CD','').find(config.get('cnword_style')) != -1:
            score += 20
        return score


    def compareMove(self):
        '''
        目标文件夹存在相同文件，按 格式优先级、-CD优先级、版本比对移动
        '''
        moveList = []
        deleteList = []
        existingFilenames = [x.replace(self.dstFolder,'') for x in self.existingFiles]

        if self.dstFileExist:
            dstSize = min([os.path.getsize(efile) for efile in self.existingFiles])
            if dstSize < zeroByteThreshold:
                print('[!] %s - 旧的 %s 为0Byte化文件禁止更新，删除新文件 %s'%(self.number,'、'.join(existingFilenames),self.fullname))
                deleteList.append(self.srcfile)
                return(moveList,deleteList)

            print('[!] 目标文件夹存在相同文件名的文件:%s'%('、'.join(self.existingFiles)))


            # 双边打分
            srcScore = self.calScore(self.srcfile)
            dstScores = []
            for efile in self.existingFiles:
                dstScores.append(self.calScore(efile))
            dstScore = min(dstScores) #多文件取最小值

            # 比较分数
            if srcScore > dstScore:                 # 新分数更高
                replaceOld = True
            elif srcScore < dstScore:               # 旧分数更高
                replaceOld = False
            else:                                   # 相同分数，比较大小
                cdCase = len(self.existingFiles) > 1
                if cdCase:      # 如果都是多集
                    if deleteLogger.get(self.number): # 先看看有没有删除记录
                        if deleteLogger.get(self.number) == 'dst':
                            replaceOld = True
                        else:
                            replaceOld = False
                    else:  # 没有删除记录就比对大小
                        esizes = [os.path.getsize(file) for file in self.existingFiles]
                        avgESize = sum(esizes)/len(esizes)
                        replaceOld = self.size > avgESize
                        if replaceOld:
                            deleteLogger[self.number] = 'dst'
                        else:
                            deleteLogger[self.number] = 'src'
                else:           # 如果都不是多集
                    esize = os.path.getsize(self.existingFiles[0])
                    replaceOld =  self.size > esize
            
            
            # 加入删除和移动队列
            if replaceOld:
                print( '[!] %s - 新的优先级更大，将删除原有 %s，移动新文件 %s 至 %s' %(self.number,'、'.join(existingFilenames),self.fullname,self.dstSeriesFolder))
                deleteList.extend(self.existingFiles)
                moveList.append((self.srcfile,self.dstFilePath))
            else:
                print('[!] %s - 旧的优先级更大，将保留原有 %s 删除新文件 %s'%(self.number,'、'.join(existingFilenames),self.fullname))
                deleteList.append(self.srcfile)
        
        else:
            print('[!] %s - 未找到相同番号，将移动 %s 到 %s 处'%(self.number,self.relsrcfile,self.dstFilePath.replace(cloudRootPath,'')))
            moveList.append((self.srcfile,self.dstFilePath))

        
        return(moveList,deleteList)


def updateCloudGHS(srcFolder,dstFolder):
    '''
    从ghstemp中入库至ghs中
    '''
    change = ''
    global moveListSum,deleteListSum,deleteLogger
    # 检查所有文件名是否符合规范
    checkFilenameFormat(srcFolder)
    # 先把temp中重复的删除
    removeDupName(srcFolder)
    # 搜索temp中需要入库的文件
    updatelist = getFileList(srcFolder)
    if updatelist:
        print('[!] 找到%d个需要入库项'%len(updatelist))
        # 新媒体入库
        moveListSum = []
        deleteListSum = []
        deleteLogger = {}
        for srcfile in updatelist:
            moveList,deleteList = NewMediaFile(srcfile,dstFolder).compareMove()
            moveListSum.extend(moveList)
            deleteListSum.extend(deleteList)

        print('[?] 是否确认移动？ y是/r刷新')
        while True:
            if not change:
                change = input()
            if change == 'y':
                #是，执行更改
                for rmfile in set(deleteListSum):
                    print('[x] 正在删除 %s'%rmfile)
                    os.remove(rmfile)
                for mvfile in set(moveListSum):
                    print('[!] 正在移动 %s 到 %s' % (mvfile[0].replace(cloudRootPath,''),mvfile[1].replace(cloudRootPath,'')))
                    os.rename(mvfile[0],mvfile[1])
                break
            elif change == 'r':
                print ('[!] %s 文件夹需要重新整理'% srcFolder)

                updatelist = getFileList(srcFolder)
                print('[!] 找到%d个需要更新项'%len(updatelist))
                # 新媒体入库
                moveListSum = []
                deleteListSum = []
                deleteLogger = {}
                for srcfile in updatelist:
                    moveList,deleteList = NewMediaFile(srcfile,dstFolder).compareMove()
                    moveListSum.extend(moveList)
                    deleteListSum.extend(deleteList)
            else:
                print(lowerCaseWarning)
    else:
        print('[!] 没有需要入库的内容')

#清理单体演员

def moveNativeSingleActor(nativePath,minVideo=5):
    '''
    本地文件整理-移动作品数量为X的女优目录到其他
    前置要求：AVDC整理后所有都移动到nativePath，nativePath指向本地AV库
    目的：将单次素人移动到其他，方便查询多片的女优
    '''
    depth = len(nativePath.strip('/').split('/'))+2

    folderlist = []
    filteredList = []

    for root,dirs,files in os.walk(nativePath): 
        for dir in dirs:
            folderlist.append(os.path.join(root,dir))


    for folder in folderlist:
        segments = folder.split('/')
        if segments[depth-1] == 'temp':
            continue
        if len(segments) == depth:
            #Depth对，把这个文件夹放到list
            filteredList.append(folder)
       
    for folder in filteredList:
        flist = os.listdir(folder)
        fileCount = 0
        folderCount = 0
        segments = folder.split('/')
        folderName = segments[depth-1]
        for i in range(0,len(flist)):
            path = os.path.join(folder,flist[i])
            if os.path.isdir(path):
                folderCount += 1
            if os.path.isfile(path):
                fileCount += 1
        if (folderCount < minVideo) and (fileCount == 0) and (folderName != '其他'):
            print('[!] 找到人名：%s，包含%d个文件夹，%d个文件'%(folderName,folderCount,fileCount))
            for i in range(0,len(flist)):
                srcPath = os.path.join(folder,flist[i])
                dstPath = os.path.join(nativePath,'其他')
                if not os.path.exists(dstPath):
                    os.makedirs(dstPath)
                print(srcPath+' to '+dstPath)
                os.system('mv "%s" "%s"'%(srcPath,dstPath))
        if (fileCount > 0) and (folderCount < 2):
            print('[!] 找到非人名文件夹%s'%folder)
            srcPath = folder
            dstPath = os.path.join(nativePath,'其他')
            print(srcPath+' to '+dstPath)
            os.system('mv "%s" "%s"'%(srcPath,dstPath))

    for folder in filteredList:
        try:
            flistCount = len(os.listdir(folder))
            if flistCount == 0:
                print('[!] 删除空文件夹%s'% folder)
                os.removedirs(folder)
        except:
            pass

#0byte化
def zeroByte(failedFolder,driveChoiceStr):
    failedCloudGHSFolderName = 'ghsfailed'
    failedCloudGHSFolder = os.path.join(cloudRootPath,driveChoiceStr,failedCloudGHSFolderName)
    # 遍历、过滤链接文件
    print('[!] 正在遍历本地 %s 文件夹下文件'%(failedFolder))
    failedList = []
    allFailedList = getFileList(failedFolder)
    for filepath in allFailedList:
        if os.path.islink(filepath):
            failedList.append(filepath)
    print('[!] 共找到 %d 个文件'%(len(failedList)))
    
    # 初始化fake115-go位置
    fake115BinPath = os.path.join(workDir,'fake115')
    cookiesPath = os.path.join(workDir,'cookies.txt')
    cid = 2279771448526503641 #ghsfailed的cid
    cid = str(cid)

    # 检查前置条件
    checkChoice = 'y'
    while True:
        if checkChoice == 'y':
            if os.path.exists(fake115BinPath) and os.path.exists(cookiesPath):
                break
            else:
                print('[x] 请检查 fake115 和 cookies.txt 是否放置于 %s，检查无误后输入y' % workDir)
                checkChoice = input()

    # 先用Size对应文件路径，移动云端至failed文件夹
    sizeDict = {}
    for filepath in failedList:
        realPath = os.path.realpath(filepath)
        realSize = os.path.getsize(realPath)
        realFName = os.path.split(realPath)[1]
        os.unlink(filepath)
        dstPath = os.path.join(failedCloudGHSFolder,realFName)
        print('[!] 正在移动云端文件 %s 至云端 %s 文件夹下'%(realFName,failedCloudGHSFolderName))
        os.rename(realPath,dstPath)
        sizeDict[realFName] = [realPath,str(realSize)]
    
    # 等待反应一会
    fileCount = len(sizeDict)
    wait115Time = fileCount / 30
    if wait115Time < 2:
        wait115Time = 2
    print('[!] 等待辣鸡115反应 %d 秒'%wait115Time)
    sleep(wait115Time)

    # 获取failed文件夹json
    jsonChoice = 'y'
    jsonfile = ''
    while True:
        if jsonChoice == 'y':
            print('[!] 正在导出cid为 %s 的 %s 文件夹下所有文件的115SHA1'%(cid,failedCloudGHSFolderName))
            os.system('%s %s'%(fake115BinPath,cid))
            for f in getFileList(workDir):
                if os.path.splitext(f)[1] == '.json':
                    jsonfile = f
            if jsonfile:
                print('[!] 获取115SHA1成功')
                break
            else:
                jsonChoice = 'n'
        elif jsonChoice == 'n':
            print('[!] 未获取到115SHA1，请检查cookie是否有效，cid是否为%s，检查完毕后输入y，修改cid输入c'%(cid))
            jsonChoice = input()
        elif jsonChoice == 'c':
            print('[!] 当前cid为%d，请输入新cid'%(cid))
            cid = input()
            jsonChoice = 'y'
        else:
            print(lowerCaseWarning)

    # 解析json文件中信息，比对
    if os.path.exists(jsonfile):
        with open(jsonfile,'r',encoding='utf-8') as f:
            sha1file = json.load(f)
    links = sha1file.get("files")

    if not len(sizeDict) == len(links):
        print('[x] 移动的文件数量和获取到的SHA1数量不一致！')

    for link in links:
        Lfname,Lsize,totalHash,blockHash = link.split('|')
        info = sizeDict.get(Lfname)
        if info: # 如果匹配到同名的
            if not info[1] == Lsize: # 文件大小警告
                print('[x] 文件 %s 的 实际大小%s 与 导出大小%s 不一致！'%(Lfname,info[1],Lsize))
            # 写入带SHA1LINK的小文件，以便以后恢复
            print('[✔] 正在将 %s 0Byte化'%info[0])
            with open(info[0], 'a',encoding='UTF-8') as f2:
                f2.write(link)
        else:
            print('[x] 导出的文件 %s 未找到对应0B位置！'%Lfname)
    
    os.remove(jsonfile)

    print('[?] 是否删除 %s 文件夹中的文件？y是/n否'%failedCloudGHSFolder)
    while True:
        deleteChoice = input()
        if deleteChoice == 'y':
            for dfile in getFileList(failedCloudGHSFolder):
                print('[!] 删除云端文件 %s'%dfile)
                os.remove(dfile)
            break
        elif deleteChoice == 'n':
            break
        else:
            print(lowerCaseWarning)
        
    return

def embyConn(api,method):
    url = '%s/emby/%sX-Emby-Token=%s'%(embyHost,api,embyAPIToken)
    if method == 'get':
        r = requests.get(url)
        return(json.loads(r.text))
    elif method == 'delete':
        r = requests.delete(url) 
    else:
        print('[x] 不支持的操作！')

def getDislikePlaylistID():
    '''
    获取playlistID
    '''
    djson = embyConn('Users/%s/Items?Recursive=true&IncludeItemTypes=Playlist&'%(embyUserID),'get')
    items = djson.get('Items')
    if items:
        for item in items:
            if re.search('del|删除',item.get("Name")):
                return item.get("Id")

def getEmbyPlaylist(dislikePlaylistID):
    '''
    查询playlist PlaylistService
    return:dict
    '''
    return embyConn('Playlists/%s/Items?'%str(dislikePlaylistID),'get').get("Items")

def getEmbyMovieFolders(movieID):
    folders = []
    infojson = embyConn('Users/%s/Items/%s?'%(embyUserID,movieID),'get')
    mediaSources = infojson.get("MediaSources")
    for mediaSource in mediaSources:
        folders.append(os.path.split(mediaSource.get("Path"))[0])
    return set(folders)


def getEmbyMovieFoldersold(movieID):
    '''
    获取影片所在文件夹    LibraryService        /Items/{Id}/DeleteInfo
    '''
    return embyConn('Items/%s/DeleteInfo?'%str(movieID),'get').get('Paths')

def deleteEmbyPlaylistItem(dislikePlaylistID,entryID):
    '''
    从playlist中移除某个影片
    '''
    return embyConn('Playlists/%s/Items?EntryIds=%s&'%(str(dislikePlaylistID),str(entryID)),'delete')

def deleteEmbyMovie(movieID):
    '''
    删除影片  LibraryService   /Items
    '''
    return embyConn('Items/%s?'%(str(movieID)),'delete')


def deleteDislikeMedia(dislikePlaylistID,tmpfailedFolder):
    '''
    不喜欢的片放置在playlist中 自动删除
    API REF: http://swagger.emby.media/?staticview=true#/ 或者 F12调试获得
    '''
    playlistjson = getEmbyPlaylist(dislikePlaylistID)
    print('[✔] 已获取 %d 个不喜爱的影片'%(len(playlistjson)-1))
    excludeMovieID = 5294 # 保留一个维持playlist
    for item in playlistjson:
        itemID = item.get('Id')
        itemEntryID = item.get('PlaylistItemId')
        itemName = item.get("Name")
        if itemID and itemEntryID and itemID != (str(excludeMovieID)):
            movieDirs = getEmbyMovieFolders(itemID)
            for movieDir in movieDirs:
                # 遍历目录下所有的软链接文件然后移动到failed文件夹，乘顺风车
                flist = getFileList(movieDir)
                for f in flist:
                    if os.path.islink(f):
                        dstPath = os.path.join(tmpfailedFolder,os.path.split(f)[1])
                        os.rename(f,dstPath)
            # 删除playlistitem,删除movie
            deleteEmbyPlaylistItem(dislikePlaylistID,itemEntryID)
            deleteEmbyMovie(itemID)
            print('[!] 已删除影片：ID %s：%s'%(itemID,itemName))
    return
