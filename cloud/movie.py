from email.mime import audio
import os
import re
import shutil


from utils.sqls import deleteMovieByID, getDetailInfosFromDB,insertMovie, insertUnknownMovie, isExistsMovie
try:
    from tmdbv3api import TMDb, Search, Movie, TV
except:
    os.system('pip install tmdbv3api')
    from tmdbv3api import TMDb, Search, Movie, TV
from time import sleep
from utils.config import *
from config import *
from utils.functions import *


class MovieFile(object):

    def __init__(self,srcfile,checkLater=True):
        self.checkLater = checkLater
        self.srcfile = srcfile
        self.fpath,self.fname = os.path.split(self.srcfile)
        self.fname,self.ext = os.path.splitext(self.fname)
        self.fname = re.sub('\(\d\)$','',self.fname)
        # 中文名-zhTitle、英文名-enTitle、分辨率-resolution、年份-year、季-season、集-episode、压制来源-source、视频编解码器-codec、音频编解码器-audio、
        # 动态范围类型-dynRes、地区-region、发行版本-release、流媒体源-stream、文件大小-size、3D-3d、音频通道数-audioLangNum、
        # 音频语言-audioLang、字幕语言subLang、帧率-fps、色彩深度-bit、CD分片-cd、来源网站-website、压制小组-group
        self.detailInfo = parse(self.fname)     # 从文件名获取
        self.advSub = False
        self.uniName = str()
        self.checkLaterConfirmed = True

        self._initConfig()


        if self.detailInfo.get('tmdbid'):
            self.tmdbID = int(self.detailInfo['tmdbid'])
        else:
            self.tmdbID = 0
        if self.detailInfo.get('imdbid'):
            self.imdbID = int(self.detailInfo['imdbid'])
        else:
            self.imdbID = 0
        if self.detailInfo.get('tvdbid'):
            self.tvdbID = int(self.detailInfo['tvdbid'])
        else:
            self.tvdbID = 0
            

        # 初始化
            
        try:
            self.processStatus = self._process()
            if not self.processStatus:
                self.uniName = ''
                self.detailInfo = {}

        except Exception as e:
            print('[x] 过程出现异常！错误原因：%s'%e)
            self.processStatus = False
            self.uniName = ''
            self.detailInfo = {}

    def _initConfig(self):
        config = Config()
        app = config.get_config('app')
        self.webhook_allow_ip = config.get_config('security').get('media_server_webhook_allow_ip')
        if app:
            if app.get('rmt_tmdbkey'):
                self.tmdb = TMDb()
                self.tmdb.cache = True
                self.tmdb.api_key = app.get('rmt_tmdbkey')
                self.tmdb.language = 'zh-CN'
                self.tmdb.proxies = config.get_proxies()
                self.tmdb.wait_on_rate_limit = False
                self.tmdb.debug = True
                self.search = Search()
                self.movie = Movie()
                self.tv = TV()

    def _romanToInt(self,roman):
        return roman.replace('XXVIII','28').replace('XXVII','27').replace('XXIII','23').replace('XVIII','18').replace('XXIX','29').replace('XXVI','26').replace('XXIV','24').replace('XVII','17').replace('XIII','13').replace('XXII','22').replace('VIII','8').replace('XXX','30').replace('XXV','25').replace('XXI','21').replace('XIX','19').replace('XVI','16').replace('XIV','14').replace('XII','12').replace('VII','7').replace('III','3').replace('II','2').replace('IV','4').replace('VI','6').replace('IX','9').replace('XI','11').replace('XV','15').replace('XX','20')
        

    def _preClean(self):
        # 去除release 里的 V234
        releaseContent = self.detailInfo.get('release')
        if releaseContent:
            for i in releaseContent:
                if re.match('^[Vv]\d+$',i):
                    self.detailInfo['release'].remove(i)
        if self.detailInfo.get('release') == []:
            del self.detailInfo['release']
        
        # 去除zhTitle里的国家名称
        zhTitleContent = self.detailInfo.get('zhTitle')
        if zhTitleContent:
            zhTitleSegments = zhTitleContent.split(' ')
            newzhTitleSegments = []
            for i in zhTitleSegments:
                if i not in COUNTRYZH:
                    newzhTitleSegments.append(i)
            self.detailInfo['zhTitle'] = re.sub('修复|源码|超清|高清|标清|官方|中字|港版|国语','',self._romanToInt(' '.join(newzhTitleSegments))).strip(' ')
        
        # 去除enTitle里的国家名称
        enTitleContent = self.detailInfo.get('enTitle')
        if enTitleContent:
            self.detailInfo['enTitle'] = self._romanToInt(enTitleContent).strip(' ')
        # 1080P 变成 1080p
        resolutionContent = self.detailInfo.get('resolution')
        if resolutionContent:
            self.detailInfo['resolution'] = resolutionContent.lower()

        return


    def _process(self):

        self._preClean()

        if self._confirmTitle():
            # 获得dbtag
            if not self._getMovieTMDBTag():
                return False
            if not self.tmdbID:
                self._getMovieIMDBTag()
            if not self.imdbID:
                self._getMovieTVDBTag()

            # 如果啥都没获得
            if not self.tmdbID and not self.imdbID and not self.tvdbID:
                print('[x] 完了芭比Q了找不到id')
                self.checkLaterConfirmed = False
                return False
            else:
                # 获得了tagid后,先存回detailInfo中
                if self.tmdbID:
                    self.detailInfo['tmdbid'] = self.tmdbID
                if self.imdbID:
                    self.detailInfo['imdbid'] = self.imdbID
                if self.tvdbID:
                    self.detailInfo['tvdbid'] = self.tvdbID
                
                # 根据当前内容生成符合规范的名称
                self._checkDetailInfo()
                self._generateUniName()


            self.checkLaterConfirmed = False
            return True



            


    def _confirmTitle(self):
        return True
        if self.detailInfo.get('excess'):
            if self.detailInfo['zhTitle']:
                print('    中文名：%s  英文名：%s 是否为正确的影片名称？ y是 或 输入正确名称'% (self.detailInfo['zhTitle'],self.detailInfo['enTitle']))
            else:
                print('    英文名：%s 是否为正确的影片名称？ y是 或 输入正确名称'% self.detailInfo['enTitle'])
            while True:
                if self.checkLater:
                    print('[!] 自动模式，稍后手动匹配！')
                    return False
                else:
                    guessChoice = input()
                if guessChoice == 'y' or guessChoice == '':
                    break
                else:
                    self.detailInfo['zhTitle'] = guessChoice
                    break
        return True

    def _getMovieTMDBTag(self):
        # 获取tmdb所有信息
        allMatch = list()

        searchKeywordList = []

        # 搜索字典建立
        if self.detailInfo.get('zhTitle'):
            searchKeywordList.append(self.detailInfo['zhTitle']) # 中文名
        if self.detailInfo.get('enTitle'):
            searchKeywordList.append(self.detailInfo['enTitle'].replace('sph-','').replace('blow-','').replace('rep-','')) # 搜索英文名
        if self.detailInfo.get('zhTitle'):
            segments = self.detailInfo['zhTitle'].split(' ') # 分割后选第一个
            if len(segments)>1:
                searchKeywordList.append(segments[0])
            searchKeywordList.append(self.detailInfo['zhTitle'].replace('之','')) # 去除数字
        retryNum = 3

        search = []
        
        for fullname in searchKeywordList:
            retryCount = 0
            while True:
                try:
                    search = self.movie.search(fullname)
                    break
                except:
                    if retryCount > retryNum:
                        break
                    else:
                        retryCount += 1
                        print('[!] 搜索失败，重试中...')
                        sleep(2)
            if search:
                break

        for res in search:
            try:
                if self.detailInfo.get('year'):
                    if res.release_date.find(str(self.detailInfo['year'])) != -1:
                        allMatch.append(res)
                        if (res.title == self.detailInfo['zhTitle']) or (res.original_title == self.detailInfo['enTitle']):
                            allMatch = [res]
                            break
                    else:
                        if (res.title == self.detailInfo['zhTitle']) or (res.original_title == self.detailInfo['enTitle']):
                            allMatch.append(res)
                else:
                    if res.title == fullname:
                        allMatch.append(res)
            except:
                pass
        
        if len(allMatch) == 0:
        
            # 补漏，如果只匹配到一个，且没选上，则确认一下对不对
            if len(search) == 1:
                while True:
                    releaseDate = search[0].get('release_date')
                    if not releaseDate:
                        releaseDate = 'Unknown' 
                    if self.detailInfo.get('tmdbid'):
                        if str(search[0].id) == str(self.detailInfo['tmdbid']):
                            allMatch = [search[0]]
                            break
                    print('[?] 只匹配到一个：id:%d - %s(%s) 是否确认？ y是/n否'% (search[0].id,search[0].title,releaseDate))
                    '''
                    if self.checkLater:
                        print('[!] 自动模式，稍后手动匹配！')
                        return False

                    oneChoice = input() 
                    '''
                    oneChoice = 'y'
                    if oneChoice == 'y' or oneChoice == '':
                        allMatch = [search[0]]
                        break
                    elif oneChoice == 'n':
                        break
                    else:
                        print('[!] 请重新输入正确选项')

            # 如果一个都没匹配到，那就判断下是否有两个以上，如果只有一个就放弃
            elif len(search) > 1:
                print('[x] 没有完全匹配的项，已推荐相似项')
                allMatch = search
            elif len(search) == 0:
                if self.detailInfo.get('tmdbid'):
                    print('[x] 没有自动查找到TMDBID，但读取到了文件名的TMDBID，是否使用？ y是/n否')
                    content = self.movie.details(self.detailInfo.get('tmdbid'))
                    releaseDate = content.get('release_date')
                    if not releaseDate:
                        releaseDate = '0000'
                    print('    id:%d - %s(%s)'% (content.id,content.title,content.release_date))
                    while True:
                        if self.checkLater:
                            print('[!] 自动模式，稍后手动匹配！')
                            return False
                        else:
                            oneChoice = input()
                        if oneChoice == 'y' or oneChoice == '':
                            allMatch = [content]
                            break
                        elif oneChoice == 'n':
                            break
                        else:
                            print('[!] 请重新输入正确选项')


        # 选择
        
        TMDbContent = None

        if len(allMatch) == 1:
            # 获得了tmdbid
            TMDbContent = allMatch[0]
            if self.tmdbID and TMDbContent.id != self.tmdbID:
                while True:
                    print('[x] 匹配到的id=%d 与 文件名id=%d不符，请选择正确的选项，1使用匹配到的id，2使用文件名id，或输入正确的tmdbid\n    1 - https://www.themoviedb.org/movie/%d\n    2 - https://www.themoviedb.org/movie/%d'%(TMDbContent.id,self.tmdbID,TMDbContent.id,self.tmdbID))

                    if self.checkLater:
                        print('[!] 自动模式，稍后手动匹配！')
                        return False

                    nomatchChoice = input()
                    try:
                        intnomatchChoice = int(nomatchChoice)
                        if intnomatchChoice == 1:
                            TMDbContent = allMatch[0]
                            break                    
                        elif intnomatchChoice > 1:
                            if not intnomatchChoice == 2:
                                self.tmdbID = intnomatchChoice
                            TMDbContent = self.movie.details(self.tmdbID)
                            break
                        else:
                            print('[x] 请输入正确的数字！')
                    except:
                        print('[x] 请输入正确的数字！')
        elif (len(allMatch) > 1) or (len(allMatch) == 0):# 多个tmdbid，确认
            
            # 如果文件名存在tmdbid且有相同的选项
            tmdbidMatch = False
            if self.tmdbID:
                for content in allMatch:
                    if content.id == self.tmdbID:
                        tmdbidMatch = True
            if allMatch:
                strmatch = list()
                for i in range(0,len(allMatch)):
                    releaseDate = allMatch[i].get('release_date')
                    if not releaseDate:
                        releaseDate = '0000'
                    if allMatch[i].title == allMatch[i].original_title:
                        strmatch.append('%d.id:%d - %s (%s) 详情链接：https://www.themoviedb.org/movie/%d'%(i+1,allMatch[i].id,allMatch[i].title,releaseDate,allMatch[i].id))
                    else:
                        strmatch.append('%d.id:%d - %s %s (%s) 详情链接：https://www.themoviedb.org/movie/%d'%(i+1,allMatch[i].id,allMatch[i].title,allMatch[i].original_title,releaseDate,allMatch[i].id))
                strmatch = '\n    '.join(strmatch)
                if tmdbidMatch:
                    print('[!] 查询到相似的结果：\n    %s\n    请选择正确结果！   文件名tmdbid为%d如果正确请回车，无结果选0，或-1退出，也可直接输入tmdbid'% (strmatch,self.tmdbID) )
                else:
                    print('[!] 查询到相似的结果：\n    %s\n    请选择正确结果！   无结果选0，或-1退出，也可直接输入tmdbid'% strmatch )
            else:
                print('[!] 未查询到相似的结果，请手动输入tmdbid 或 输入0进入imdb搜索模式 或-1退出 \n    TMDB搜索中文名：https://www.themoviedb.org/search?query=%s\n    TMDB搜索英文名：https://www.themoviedb.org/search?query=%s'%(self.detailInfo['zhTitle'].replace(' ','%20'),self.detailInfo['enTitle'].replace(' ','%20')))
            

            if self.checkLater:
                print('[!] 自动模式，稍后手动匹配！')
                return False

            while True:
                tmdbChoice = input()
                try:
                    intTMDBChoice = int(tmdbChoice)
                    if intTMDBChoice-1 in range(0,len(allMatch)):
                        TMDbContent = allMatch[intTMDBChoice-1]
                        break                    
                    elif intTMDBChoice == 0:
                        break
                    elif intTMDBChoice == -1:
                        self.checkLaterConfirmed = False
                        return False
                    elif intTMDBChoice > 15:
                        self.tmdbID = int(tmdbChoice)
                        TMDbContent = self.movie.details(self.tmdbID)
                        break
                    else:
                        print('[x] 请输入正确的数字！')
                except:
                    if tmdbChoice == '' and self.tmdbID:
                        TMDbContent = self.movie.details(self.tmdbID)
                        break
        

        # 刷新数据
        if TMDbContent:
            self.tmdbID = TMDbContent.id
            self.detailInfo['zhTitle'] = TMDbContent.title
            if TMDbContent.title != TMDbContent.original_title:
                self.detailInfo['enTitle'] = TMDbContent.original_title
            if TMDbContent.get('release_date'):
                year = re.findall(r"(?:19[0-9]|20[0123])[0-9]",TMDbContent.release_date)
            else:
                year = None
            if year:
                self.detailInfo['year'] =  int(year[0])
            else:
                print('[x] TMDB没有年份信息，手动输入年份')
                if self.checkLater:
                    print('[!] 自动模式，稍后手动匹配！')
                    return False
                self.detailInfo['year'] = int(input())
            print("[!] 匹配到的是:id:%d - %s (%s)"%(self.tmdbID,self.detailInfo['zhTitle'],self.detailInfo['year']))
            return True
        else:
            print("[!] 未匹配到任何结果，将移动到回收站")
            return False
        
        
    def _getMovieIMDBTag(self):
        return

    def _getMovieTVDBTag(self):
        pass
        return

    def _videoCodec(self,mediaInfo):
        return getVideoCodec(mediaInfo)

    def _audioCodec(self,mediaInfo):
        return getAudioCodec(mediaInfo)

    def _resolution(self,mediaInfo):
        return getResolution(mediaInfo)

    def _checkDetailInfo(self):
        '''
        检查是否存在足够的detailInfo(分辨率、视频编码、音频编码)
        '''
        enoughDetail = True
        for field in ('resolution','videoCodec','audioCodec','subLang','audioLang'):
            if self.detailInfo.get(field) == None:
                enoughDetail = False
                break

        # 如果没有足够的detailInfo，则获取
        if not enoughDetail:
            self.detailInfo = completeDetailInfoFromFile(self.detailInfo,self.srcfile)

        # doublecheck
        for field in ('resolution','videoCodec','audioCodec'):
            if self.detailInfo.get(field) == None:
                print('[x] pymediainfo有问题！！！！！！！')
                input()
                break

        return

    def validateTitle(self,title):
        rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
        new_title = re.sub(rstr, " ", title)  # 替换为下划线
        return new_title


    def _generateUniName(self):
        '''
        获取统一术语的文件名
        '''
        # 统一化文件名表达方式
        for field,fieldValue in self.detailInfo.items():
            if field in ('resolution','source','videoCodec','audioCodec','dynRes','release','stream','audioLang','subLang'):
                self._unifyField(field)
        if self.advSub: self.detailInfo['advSub'] = True

        # 拼接所有字段
        uniName = ""
        for fieldName in renameOrder:
            if self.detailInfo.get(fieldName):
                if fieldName in ('tmdbid','imdbid','tvdbid'):
                    uniName += '[%s=%s] '%(fieldName,str(self.detailInfo[fieldName]))
                elif fieldName in ('zhTitle'):
                    uniName += self.detailInfo[fieldName]+' '
                elif fieldName in ('year'):
                    uniName += '(%s) - '%str(self.detailInfo[fieldName])
                elif fieldName in ('fps','bit'):
                    uniName += '%s%s.'%(str(self.detailInfo[fieldName]),fieldName)
                elif fieldName in ('resolution', 'dynRes', 'videoCodec','stream'):
                    uniName += str(self.detailInfo[fieldName])+'.'
                elif fieldName in ('audioLang', 'subLang'):
                    segments = ''
                    for lang in self.detailInfo[fieldName]:
                        for k,v in LangDict.items():
                            if re.findall(k,lang):
                                segments += v
                                break
                    if fieldName == 'audioLang':
                        uniName += segments + '音频.'
                    elif fieldName == 'subLang':
                        if self.detailInfo.get('advSub') == True:
                            uniName += '特效' + segments + '字幕.'
                        else:
                            uniName += segments + '字幕.'
                elif fieldName in ('source','audioCodec'):
                    max1 = ''
                    order = eval('%sOrder'%fieldName)
                    for i in order:
                        for j in self.detailInfo[fieldName]:
                            if j.find(i) != -1:
                                max1 = j
                                break
                        if max1:
                            break
                    uniName += max1 + '.'
                elif fieldName in ('audioLangNum'):
                    uniName += str(self.detailInfo[fieldName])+'Audio.'
                elif fieldName in ('group'):
                    if self.detailInfo[fieldName].find('-') != -1:
                        uniName += self.detailInfo[fieldName]
                    else:
                        uniName += '-'+self.detailInfo[fieldName]
                else:
                    value = self.detailInfo[fieldName]
                    if type(value) == list:
                        value = '.'.join(value)
                    elif type(value) == int:
                        value = str(value)
                    uniName += value+'.'
        self.uniName = self.validateTitle(uniName.replace('.-','-').strip('.') + self.ext)
        return

    def _unifyField(self,field):
        '''
        统一各个字段的表达方式
        '''
        fieldContent = self.detailInfo.get(field)
        if mediaInfoDict.get(field) or field in ('audioLang','subLang'):
            if type(fieldContent) == list:
                # 整理音频和字幕  中转英
                if field in ('audioLang','subLang') :
                    if re.findall(u'[\u4e00-\u9fa5]',fieldContent[0]):
                        # 如果存在中文，遍历每个字
                        langs = []
                        for item in fieldContent:
                            for stra in item:
                                lang = ivLangDict.get(stra)
                                if lang:
                                    langs.append(lang)
                            if self.fname.find('特效') != -1:
                                self.advSub = True
                        self.detailInfo[field] = langs
                    else:
                        # 如果不存在中文，则检查是否在LangDict中
                        langs = []
                        for item in fieldContent:
                            for k,v in LangDict.items():
                                if re.findall(k,item):
                                    langs.append(v)
                                    break
                        self.detailInfo[field] = [ivLangDict.get(x) for x in langs if ivLangDict.get(x)]
                else:
                    unifiedContent = []
                    for content in fieldContent:
                        for key,value in mediaInfoDict.get(field).items():
                            if re.findall(key,content,re.I):
                                if field == 'audioCodec':
                                    channelNum = re.findall('[76521][\.\s][10]\.?[210]?',content)
                                    if channelNum:
                                        unifiedContent.append(value+'.'+channelNum[0])
                                        break
                                unifiedContent.append(value)
                                break
                        else:
                            if field == 'release':
                                unifiedContent.append(content)
                    self.detailInfo[field] = unifiedContent
            elif type(fieldContent) == str:
                for key,value in mediaInfoDict.get(field).items():
                    match = re.findall(key,fieldContent,re.I)
                    if match:
                        if value.find('re!!!') != -1:
                            value = value.replace('re!!!',match[0])
                        self.detailInfo[field] = value
                        break
            else:
                pass
        return


def getTopPriorityValue(field,list):
    # 将多个选项转换为单个最强字符串
    if '%sOrder'%field in globals().keys():
        order = eval('%sOrder'%field)
        def byOrder(elem):
            i = order.get(elem)
            if i:
                return i
            else:
                return 0
        list.sort(key=byOrder)
        return list[-1]

def getMergedFieldValue(field,existingDetailInfos):
    values = []
    for existingDetailInfo in existingDetailInfos:
        value = existingDetailInfo.get(field)
        if type(value) == list:
            value = getTopPriorityValue(field,value)
            if value:
                # 如果有优先级设置的话加入到values列表中
                values.append(value)
            else:
                # 如果没有优先级设置的话，直接extend到values列表中
                values.extend(existingDetailInfo.get(field))
        else:
            values.append(value)

    return values

def filterExistingDetailInfos(existingDetailInfos,field,value):
    # 过滤属性相同的detailInfo
    filteredDetailInfos = []
    for existingDetailInfo in existingDetailInfos:
        if existingDetailInfo.get(field) == value:
            filteredDetailInfos.append(existingDetailInfo)
    return filteredDetailInfos


def scoreMovie(detailInfo):
    # 计算评分
    score = 0
    for field in ('source','audioCodec','videoCodec'):
        order = eval('%sOrder'%field)
        value = detailInfo.get(field)
        if value:
            if field == 'audioCodec':
                newvalue = []
                for i in value:
                    i = re.sub('[76521][\.\s][10]\.?[210]?','',i)
                    newvalue.append(i)
                value = newvalue
            if type(value) == list:
                value = getTopPriorityValue(field,value)
            subScore = order.get(value)
            if subScore:
                score += subScore
    audioLangNum = detailInfo.get('audioLangNum')
    if audioLangNum:
        score += audioLangNum*2

    if detailInfo.get('subLang'):
        if 'Chinese' in detailInfo.get('subLang'):
            score += 30
    
    fps = detailInfo.get('fps')
    if fps:
        score += int(fps)/20
    
    bit = detailInfo.get('bit')
    if bit == 10:
        score += 5

    return score



def removeMovieFile(cloudRootPath,mediaType,existingDetailInfo):
    driveType = existingDetailInfo.get('driveType')
    print('\033[0;31;40m[x]\033[0m 找到了更好的版本，删除 %s 的旧版本文件：%s'%(existingDetailInfo.get('driveType'),existingDetailInfo.get('filename')))
    if not os.path.exists(os.path.join(cloudRootPath,driveType)):
        input('[!] %s 根目录检测到不存在，按请挂载后按回车键继续...'%driveType)
    os.remove(os.path.join(cloudRootPath,existingDetailInfo.get('driveType'),mediaType,existingDetailInfo.get('filename')))
    deleteMovieByID(existingDetailInfo.get('id'))
    return

def compareDetailInfo(srcDetailInfo,existingDetailInfos):
    '''
    比较两个资源的详细信息
    '''
    # 预检查，减少计算量

    srcFilename = srcDetailInfo.get('origfilename')
    for existingDetailInfo in existingDetailInfos:
        #多网盘之间要考虑，可以移动到DAILYCHeck
        # 再检查原文件名是否相同
        if srcDetailInfo.get('origfilename') == existingDetailInfo.get('origfilename'):
            return False,[]
    
    if not existingDetailInfos:
        return True,[]

    # 开始根据优先级比较详细信息：主要是 resolution、subLang/advSub(中文字幕、特效)、SDR/HDR、release（特殊版本）
    #                          其他次要的就用打分器解决
    # 比较策略：匹配顺序： 1.resolution 看看有没有相同1080pi/2160p/720p的，如果有，则对比，如果没有，则留下 ，后处理：如果出现范围外的，则删除
    #                           同分辨率的情况下，检查HDR状态，如果有SDR版本，就检查HDR版本
    #           多版本存在的字段：resolution:1080/2160p/4320p/720p
    #                           dynRes:HDR/SDR/DOVI
    #                           release:有一个算一个
    #                           subLang:Chinese
    #                           advSub:必须拿


    isKeep = False
    removeDIList = []
    # 先比较resolution
    srcRes = srcDetailInfo.get('resolution')
    existResList = getMergedFieldValue('resolution',existingDetailInfos)
    if srcRes in existResList:
        existSameRes = True
    else:
        # 前面已经确认相同tmdbid了，如果新入库的是在720p/1080p/2160p/4320p
        # 范围内的，则查看现存的是否有低于720p的，删除它
        if srcRes in ("720p","1080p","2160p","4320p","1080i"):
            existSameRes = False
            print('\033[0;32;40m[√]\033[0m 多版本：resolution，将保留 %s 文件'%srcFilename)
            # 如果现存有低于720p的，则删除它
            deleteList = []
            for exist in existingDetailInfos:  
                if exist.get('resolution') and exist.get('resolution') not in ("720p","1080p","2160p","4320p","1080i"):
                    deleteList.append(exist)
            return True,deleteList
        else:
            existSameRes = True
    

    if existSameRes:
        # 如果有相同分辨率的，则对比release
        sameResDIList = filterExistingDetailInfos(existingDetailInfos,'resolution',srcRes)
        srcRelease = srcDetailInfo.get('release')

        existReleaseList = getMergedFieldValue('release',sameResDIList)
        if srcRelease in existReleaseList:
            existSameRelease = True
        else:
            existSameRelease = False
            print('\033[0;32;40m[√]\033[0m 多版本：release，将保留 %s 文件'%srcFilename)
            return True,[]

    

    if existSameRelease:
        # 如果有相同分辨率和release的，则对比HDR
        sameReleaseDIList = filterExistingDetailInfos(sameResDIList,'release',srcRelease)
        srcDynRes = srcDetailInfo.get('dynRes')
        if srcDynRes:
            existHDRList = getMergedFieldValue('dynRes',sameReleaseDIList)
            if srcDynRes in existHDRList:
                existSameDynRes = True
            else:
                if srcDynRes == 'SDR':
                    # 如果是SDR版本，之前也确认了没有重复的，就留下
                    print('\033[0;32;40m[√]\033[0m 多版本：SDR，将保留 %s 文件'%srcFilename)
                    return True,[]
                else:
                    # 如果不是SDR，那就是HDR10+>HLG>HDR10>DV排序后对比
                    #过滤一遍现存SDR
                    existHDRList = [x for x in  existHDRList if x != 'SDR']
                    existHDRList.append(srcDynRes)
                    filteredHDRDIList = [x for x in sameReleaseDIList if x.get('dynRes') != 'SDR']
                    if getTopPriorityValue('dynRes',existHDRList) == srcDynRes:
                        # 排序后最强的是src，那就留下
                        existSameDynRes = False
                        return True,filteredHDRDIList
                    else:
                        #排序后最强的不是src，那就判断advSub
                        existSameDynRes = True
        else:
            existSameDynRes = True
    
    if existSameDynRes:
        # 如果有相同分辨率和release和HDR的，则对比advSub
        sameDynResDIList = filterExistingDetailInfos(sameReleaseDIList,'dynRes',srcDynRes)
        srcAdvSub= srcDetailInfo.get('advSub')
        if srcAdvSub:
            existAdvSubList = getMergedFieldValue('advSub',sameDynResDIList)
            if srcAdvSub in existAdvSubList:
                existSameAdvSub = True
            else:
                existSameAdvSub = False
                return True,[]
        else:
            existSameAdvSub = True
    
    
    if existSameAdvSub:
        # 如果有相同分辨率和release和HDR和advSub的，则打分
        sameAdvSubDIList = filterExistingDetailInfos(sameDynResDIList,'advSub',srcAdvSub)
        srcScore = scoreMovie(srcDetailInfo)
        for detailInfo in sameAdvSubDIList:
            eScore = scoreMovie(detailInfo)
            if srcScore > eScore:
                # 如果src的分数更高，那就保留删除existing
                removeDIList.append(detailInfo)
                isKeep = True
            else:
                # 如果src的分数更低或相同，那就删除src
                isKeep = False
    
    return isKeep,removeDIList
    
    




def updateCloudMovie(cloudRootPath,driveType,tmpFolderName,mediaType,checkLater=True):

    srcFolder = os.path.join(cloudRootPath,driveType,tmpFolderName,mediaType)
    dstFolder = os.path.join(cloudRootPath,driveType,mediaType)


    if not os.path.exists(dstFolder):
        os.mkdir(dstFolder)

    # 回收站
    recycleBinPath = os.path.join(srcFolder,'recycleBin')
    if not os.path.exists(recycleBinPath):
        os.mkdir(recycleBinPath)

    # 去除recycleBin的文件
    updatelistPreCheck = getFileList(srcFolder)
    updatelist = []
    for file in updatelistPreCheck:
        precheckext = os.path.splitext(file)[1].lower()
        if file.find('recycleBin') == -1 and precheckext in MEDIAEXT:
            updatelist.append(file)

    while True:
        checkLaterList = []    
        if updatelist:
            print('[!] 找到%d个需要入库项'%len(updatelist))
            lenupdatelist = len(updatelist)
            count = 0
            # 新媒体入库
            for srcfile in updatelist:
                count += 1
                srcpath,srcfname = os.path.split(srcfile)
                print('[?] [%d/%d] 正在处理文件 %s'% (count,lenupdatelist,srcfname))
                srcmovie = MovieFile(srcfile,checkLater)
                # 检查是否稍后手动匹配
                if not srcmovie.checkLaterConfirmed:
                    srcDetailInfo = srcmovie.detailInfo
                    srcUniName = srcmovie.uniName
                    srcDetailInfo['filename'] = srcUniName
                    srcDetailInfo['origfilename'] = srcfname
                    srcDetailInfo['driveType'] = driveType

                    if srcDetailInfo.get('season'):
                        continue
                    if srcDetailInfo.get('episodeName'):
                        del srcDetailInfo['episodeName']
                    if srcDetailInfo.get('episode'):
                        continue

                    if srcDetailInfo.get('excess'):
                        del(srcDetailInfo['excess'])
                    
                    if srcmovie.processStatus:
                        # 根据tagid检查是否已经存在
                        isExist = False
                        for tagType in ('tmdbid','imdbid','tvdbid'):
                            if srcDetailInfo.get(tagType):
                                isExist = isExistsMovie(tagType,srcDetailInfo[tagType])
                                if isExist:
                                    confirmedTagType = tagType
                                    confirmedTagID = srcDetailInfo[tagType]
                                    break
                        
                        # 如果存在就对比，看是否留下，如果不存在，就直接改名留下
                        if isExist:
                            dbMediaInfos = getDetailInfosFromDB(confirmedTagType,confirmedTagID)
                            isKeep,removeDIList =  compareDetailInfo(srcDetailInfo,dbMediaInfos)
                            for rmdetailInfo in removeDIList:
                                removeMovieFile(cloudRootPath,mediaType,rmdetailInfo)
                        else:
                            isKeep = True
                        dstfile = os.path.join(dstFolder,srcUniName)
                        if os.path.exists(dstfile):
                            isKeep = False
                        
                        # 如果留下，就改名、写入数据库,如果不留下，就移动到废品文件夹
                        if isKeep:
                            print('\033[0;32;40m[√]\033[0m 文件入库中：%s'%srcUniName)
                            shutil.move(srcfile,dstfile)
                            insertMovie(srcDetailInfo)
                        else:
                            print('[!] 文件废弃：%s'%srcUniName)
                            if not os.path.exists(os.path.join(recycleBinPath,srcfname)):
                                shutil.move(srcfile,recycleBinPath)
                            else:
                                os.remove(srcfile)
                    else:
                        print('\033[0;31;40m[x]\033[0m %s 已添加错误记录到数据库，并移动文件至回收站'%srcfile)
                        # 写入数据库
                        insertUnknownMovie(srcfile)
                        shutil.move(srcfile,recycleBinPath)
                else:
                    if not srcmovie.processStatus:
                        checkLaterList.append(srcfile)
                    else:
                        print('\033[0;31;40m[x]\033[0m %s文件已被放弃，已添加错误记录到数据库'%srcfile)
                        # 写入数据库
                        insertUnknownMovie(srcfile)
                        shutil.move(srcfile,recycleBinPath)
            
            #后续逻辑部分：如果第一次循环则按checkLater设置处理，第二次以后无论如何关闭checkLater
            if checkLater:
                print('[!] 手动匹配模式')
                checkLater = False

            # 更新待检查列表，如果无检查对象就break
            updatelist = checkLaterList
            if not updatelist:
                print('[√] 已完成所有入库项')
                break

        else:
            print('[x] 无需要入库项')
            break

            
            
    return
