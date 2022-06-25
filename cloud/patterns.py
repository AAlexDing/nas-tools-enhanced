##################
##### 扩展名 ######
##################


# 扩展名按优先级排序
MEDIAEXT = ['.mkv','.mp4','.avi','.mov','.ts','.m2ts','.mpg','.wmv']
# 有可能出现在论坛名、压制组中的文件属性关键字，避免混淆识别，如：压制组BT4K 中的4K容易被识别为reslution字段
GROUPNAMESEG = ('4K','BD','HD','UHD','MP4','HDR','MKV','DC','SE','3D')
# 有可能出现在论坛名、压制组中的结尾，用于识别，提供给group字段
GROUPNAMEEND = '压制组|字幕组|原创组|小组|出品|论坛|龙网|HD'
COUNTRYZH = ['阿富汗','阿尔巴尼亚','阿尔及利亚','美属萨摩亚','安道尔','安哥拉','安圭拉岛','南极洲','安提瓜和巴布达','阿根廷','亚美尼亚','阿鲁巴岛','澳大利亚','奥地利','阿塞拜疆','巴哈马','巴林','孟加拉国','巴巴多斯','白俄罗斯','比利时','伯利兹','贝宁','百慕大','不丹','玻利维亚','波斯尼亚和黑塞哥维那','博茨瓦纳','巴西','英属印度洋领地','英属维尔京群岛','文莱','保加利亚','布基纳法索','缅甸','布隆迪','柬埔寨','喀麦隆','加拿大','佛得角','开曼群岛','中非共和国','乍得','智利','中国','圣诞岛','克利珀顿岛','科科斯（基林）群岛','哥伦比亚','科摩罗','刚果民主共和国','刚果共和国','库克群岛','珊瑚海群岛','哥斯达黎加','科特迪瓦','克罗地亚','古巴','塞浦路斯','捷克共和国','丹麦','吉布地','多米尼克','多明尼加共和国','厄瓜多尔','埃及','萨尔瓦多','赤道几内亚','厄立特里亚','爱沙尼亚','埃塞俄比亚','欧罗巴岛','福克兰群岛','法罗群岛','斐济','芬兰','法国','法属圭亚那','法属波利尼西亚','加蓬','冈比亚','乔治亚','德国','加纳','直布罗陀','格洛里厄斯群岛','希腊','格陵兰','格林纳达','瓜德罗普岛','关岛','危地马拉','根西岛','几内亚','几内亚比绍','圭亚那','海地','罗马教廷（梵蒂冈城）','洪都拉斯','匈牙利','冰岛','印度','印度尼西亚','伊朗','伊拉克','爱尔兰','马恩岛','以色列','意大利','牙买加','扬马延岛','日本','泽西岛','约旦','新胡安岛','哈萨克斯坦','肯尼亚','基里巴斯','科威特','吉尔吉斯斯坦','老挝','拉脱维亚','黎巴嫩','莱索托','利比里亚','利比亚','列支敦士登','立陶宛','卢森堡','马其顿','马达加斯加','马拉维','马来西亚','马尔代夫','马里','马耳他','马绍尔群岛','马提尼克岛','毛里塔尼亚','毛里求斯','马约特岛','墨西哥','密克罗尼西亚联邦','摩尔多瓦','摩纳哥','蒙古','蒙特塞拉特','摩洛哥','莫桑比克','纳米比亚','瑙鲁','纳瓦萨岛','尼泊尔','荷兰','荷属安的列斯','新喀里多尼亚','新西兰','尼加拉瓜','尼日尔','尼日利亚','纽埃','诺福克岛','朝鲜','北马里亚纳群岛','挪威','阿曼','巴基斯坦','帕劳','巴拿马','巴布亚新几内亚','西沙群岛','巴拉圭','秘鲁','菲律宾','皮特凯恩群岛','波兰','葡萄牙','波多黎各','卡塔尔','留尼汪','罗马尼亚','俄罗斯','卢旺达','圣赫勒拿岛','圣基茨和尼维斯','圣卢西亚岛','圣皮埃尔和密克隆群岛','圣文森特和格林纳丁斯','萨摩亚','圣马力诺','圣多美和普林西比','沙特阿拉伯','塞内加尔','塞尔维亚和黑山','塞舌尔群岛','塞拉利昂','新加坡','斯洛伐克','斯洛文尼亚','所罗门群岛','索马里','南非','韩国','西班牙','南沙群岛','斯里兰卡','苏丹','苏里南','斯瓦尔巴群岛','斯威士兰','瑞典','瑞士','叙利亚','塔吉克斯坦','坦桑尼亚','泰国','东帝汶','多哥','托克劳','汤加','特立尼达和多巴哥','特罗姆兰岛','突尼斯','土耳其','土库曼斯坦','特克斯和凯科斯群岛','图瓦卢','乌干达','乌克兰','阿拉伯联合酋长国','英国','美国','乌拉圭','乌兹别克斯坦','瓦努阿图','委内瑞拉','越南','维尔京群岛','威克岛','瓦利斯和富图纳群岛','西撒哈拉','也门','赞比亚','津巴布韦']



#############################
###### 从文件名提取属性 ######
#############################



# |亿万同人字幕组|橘里橘气译制组|悸花字幕组|小易甫字幕组|马特鲁字幕组|弯弯字幕组
preparePatterns = {'ZMZ\-.*\-MP4|mUHD\-FRDS|FFansBD|邵氏|美亚|星卫|mp4ba|自由译者联盟':('group','re!!!'),
                '(?:[\[〖『「《【]?[a-zA-Z&\u4e00-\u9fa5]+(?:译制组|压制组|字幕组|原创组|小组|出品|论坛|龙网)[\]】〗』」》·]?)':('group','re!!!'),
                '(?:(?:默认)?[国英葡法俄日韩德意西印泰希阿波土捷匈罗丹瑞挪芬菲越马荷台港粤中导]{1,10}(?:[双三四五六]语(?!字幕)|[双三四五六]音轨|语配音|语?音频|语.字)|[国英葡法俄日韩德意西印泰希阿波土捷匈罗丹瑞挪芬菲越马荷台港粤中导]]{3,10})':('audioLang','re!!!'),
                '(?:(?:特效|内封|官译|官方|外挂|默认|(?:[国英葡法俄日韩德意西印泰希阿波土捷匈罗丹瑞挪芬菲越马荷台港粤中简繁语体文字]+)){1,3}(?:[双三四五六]字|字幕|双语字幕)|简体中字|中字简体|中字|双语字幕|(?:特效|内封|官译|外挂)+[国英葡法俄日韩德意西印泰希阿波土捷匈罗丹瑞挪芬菲越马荷台港粤中简繁语文字]+)|(?:[国英葡法俄日韩德意西印泰希阿波土捷匈罗丹瑞挪芬菲越马荷台港粤中简繁语文字]+(?:特效|内封|官译|外挂)+)':('subLang','re!!!'),
                'BD\-MP4|WEB\-MP4':('excess',''),
                'BD4K':('source','BluRay'),
                'HD4K':('source','HDTV'),
                '无删减版':('release','UNCUT'),
                '未分级版':('release','UNRATED'),
                'pniao.com':('website','re!!!'),
                '蓝光':('source','re!!!'),
}

# patterns编写原则：
# 受 \b 拼接影响的正则，所以必须要以(?:)为外壳，并保持壳内不成group
# 'season', 'episode','cd' 等会同时匹配 raw，clean 修改时需要保持这个规则
# (?:MP3|DDP?5\.?1|AAC[.-]LC|AAC(?:\.?2\.0)?|(?:AC3|DD)(?:.?[52]\.[10])?|PCM|LPCM|FLAC|DTS(?:-(?:X|HD))?[\.\s\-]?(?:MA|HRA|ES)?(?:[\.\s\-]?[76521]\.[10])?|Atmos|TrueHD(?:\.[76521]\.[10])?)
# 原版group范围更小，少误伤 (?:- ?(?:[^-]+(?:-={[^-]+-?$)?))$|(?:(?:^|[\[〖『「《【]).+(?:译制组|压制组|字幕组|原创组|小组|出品|论坛|龙网|HD)\s?[\]】〗』」》·])|\b(?:.+(?:译制组|压制组|字幕组|原创组|小组|出品|)\b)
# GER|MAN  → german

patterns = [
    ('resolution', '([0-9]{3,4}[pi]|4k|[0-9]{3,4}[xX][0-9]{3,4}p?)'),
    ('year', '([\[\(]?((?:19[0-9]|20[012])[0-9])[\]\)]?)'),
    ('season', '(s?([0-9]{1,2}))[ex](?=[\d+])'),
    ('episode', '((?<=[0-9])[ex]p?([0-9]{2})(?:[^0-9]|$))'),
    ('source', '(?:(?:PPV\.)?(?:HR[-])?[HP]DTV(?:Rip|\-HR)?|VOD|(?:HD)?CAM|(?:PPV )?WEB-?DL(?: DVDRip)?|(?:Cam|WEB|TV|B[DR]|F?HD|(?:HQ)?DVD)-?(?:Rip|HR)|Blu.?Ray|DvDScr|telesync|UHD|UltraHD|(?:BD)?Remux)'),
    ('videoCodec', '(?:mpeg2|vc\-1|hevc|avc|xvid|divx|[hx]\.?26[2345])'),
    ('audioCodec', '(?:MP3|AAC[.\-]LC|(?:DD[P\+]?|A?AC|HE\-AAC|Opus|AC3|DD|PCM|LPCM|FLAC|DTS(?:(?:[-\s]?X|[-\s]?HD))?(?:[\.\s\-]{0,2}(?:M.?A|HRA|ES))?|TrueHD|Atmos)(?:[\.\s\-]{0,2}[76521][\.\s][10])?)'),
    ('dynRes','(?:SDR|HDR10Plus|HDR\-X|HDR|HLG|DV|DoVi|Dolby.Vision)'),
    ('region', 'R[0-9]'),
    ('release', '(?:(?:(?:The.)?(?:Special|Collector\'?s|Ultimate|Final|Limited|Director\\\\{0,2}\'?s|REMASTERED|EXTENDED|UNCUT|UNRATED|THEATRICAL|PROPER|SUBBED|ENSUBBED|IMAX|REPACK)+(?:.(?:Cut|Edition|Version)))|(?:(?:The.)?(?:REMASTERED|EXTENDED|UNCUT|UNRATED|THEATRICAL|PROPER|SUBBED|ENSUBBED|IMAX|REPACK|(?:[0-9]{2}TH.)?ANNIVERSARY)+(?:Collector\'?s)?(?:.(?:Cut|Edition|Version))?)|(?:GBR|HKG|CEE|EUR|USA|AUS|V2|Carlotta|RERip|Criterion.Collection|Criterion|Open.Matte|Masters.of.Cinema))'),
    ('stream', '(?:hbo.max|HMAX|NF|Netflix|AMZN|HULU|DSNP|iP)'),
    ('size', '(\d+(?:\.\d+)?(?:GB|MB))'),
    ('audioLangNum','(([0-9])Audios?|(?:Dual|Tri|Quad|Multi)[\- \.]?Audio)'),
    ('audioLang', '(?:(?:English|Russian|Portuguese|Spanish|French|German|Italian|Dutch|Turkish|Japanese|Korean|Thai|Vietnamese|Arabic|Polish|Mandarin|Cantonese|Chinese|INDONESIAN)[\.\-\s&_]?){2,}'),
    ('subLang', '(?:(?:GER|ENG|CHS|CHI|FRA|FRE|DEU|KOR|ITA|JPN|ARA|RUS|CHT|THA|PLK|POR|SPA|FRE|JAP|CAN)[\.\-\s&_]?){2,}|(?:(?:GB|JP)[\.\-\s&_]?){2,}'),
    ('fps', '(?:([0-9]{2})(?:fps|帧))'),
    ('bit', '((1?[0-9])bits?)'),
    ('cd','(?:cd([0-9]{1,2}))'),
    ('website', '([\[〖『「《【] ?(.+?\.(net|com|cn|org|info|de|tk|uk|ru|nl|xyz|eu|br|fr|au|it|us|ca|co|pl|es|in|cc|se|cd|be|site|jp|to|me|club|cf|vip|app|tv|dev|fan)) ?[\]】〗』」》@])'),# 修改版可能有未知错误，原版^(\[ ?([a-zA-Z0-9\.\s]+?) ?\])  在最前面 [720pMkv.Com] 和 [X战警.逆转未来.加长版] 区分
    ('group', '(?:(?:- ?(?:[^-]+(?:-={[^-]+-?$)?))$)')
]

recyclePatterns = {'翡翠台|CCTV[0-9]{1,2}':('source','HDTV'),
                '([0-9]{3,4}[pi])':('resolution','re!!!'),
                '720':('resolution','re!!!p'),
                r'(?:(?:BD|HD)(?=[0-9]{3,4}[pi]))|(?:[^\b]DVD)|(?:DVD[$\b])':('source','re!!!Rip'),
                '(?:ENGLISH|RUSSIAN|PORTUGUESE|SPANISH|FRENCH|DANiSH|GERMAN|ITALIAN|DUTCH|TURKISH|JAPANESE|KOREAN|THAI|VIETNAMESE|ARABIC|POLISH|MANDARIN|CANTONESE|CHINESE|INDONESIAN)':('audioLang','re!!!'),
                r'\b(?:GER|ENG|CHS|CHI|FRA|FRE|DEU|KOR|ITA|JPN|ARA|RUS|CHT|THA|PLK|POR|SPA|FRE|JAP)\b':('subLang','re!!!'),
                '(?:LiMiTED|LIMITED|iNTERNAL|INTERNAL|MULTi)':('release','re!!!!'),
                r'\b(?:BD|HD|WEB)\b':('source','re!!!Rip'),
                '(?:SDR|HDR10Plus|HDR\-X|HDR|DoVi)':('dynRes','re!!!'),
                r'\b(?:DC|SE|EE|CC)\b':('release','re!!!')
                
                }


types = {
    'season': 'integer',
    'episode': 'integer',
    'year': 'integer',
    'audioLangNum':'integer',
    'cd':'integer',
    'fps': 'integer',
    'bit': 'integer',
    'source':'list',
    'audioCodec':'list',
    'release':'list',
    'audioLang':'list',
    'subLang':'list'
}


###########################
###### 属性术语统一化 ######
###########################



resolutionDict = {'4K': '2160p','[0-9]{3,4}[xX]([0-9]{3,4})':'re!!!p'}
sourceDict = {'uhd|ultrahd':'UHD','blu.?ray':'BluRay','(?:bd)?.?remux':'Remux','br.?rip':'BRRip','bdrip':'BDRip','web-?dl':'WEBDL','web-?rip':'WEBRip','fhd.?rip':'FHDRip','hd(?:tv)?.?rip':'HDRip','hdtv':'HDTV','dvd-?rip|(?:hq)?dvd|video_ts':'DVDRip','dvdscr':'DVDSCR','pdtv':'PDTV','VOD':'VOD','(?:HD)?CAM(?:Rip)?':'CAM'}
videoCodecDict = {'[xh]264|avc':'AVC','[xh]265|hevc':'HEVC','xvid':'XviD','divx':'DivX','vc\-?1':'VC1','mpeg2':'MPEG2','h263':'H263','h262':'H262'}
audioCodecDict = {'pcm':'PCM','lpcm':'LPCM','flac':'FLAC','atmos':'Atmos','dts-x|dtsx':'DTS-X','dts-?hd.?ma':'DTS-HD.MA','truehd|true\shd':'TrueHD',
                    'dts\-?hd.?hra':'DTS-HD.HRA','dts\-?hd.?es':'DTS\-HD.ES','dts\-?es':'DTS-ES','dts':'DTS',
                    'dd\+|ddp':'DDP','e.?ac.?3':'EAC3','HE\-AAC':'HE-AAC','dd|ac3':'DD','aac':'AAC','mp3':'MP3','opus':'Opus','vorbis':'Vorbis','dolby':'Dolby'}
dynResDict = {'sdr':'SDR','hdr10Plus|hdr10\+':'HDR10Plus','hdr10':'HDR10','hdr':'HDR','hlg':'HLG','DV|DoVi|dolby.vision':'DoVi'}
#流媒体源：HBO MAX(HMAX)/NETFLEX(NF)/APPLE PLUS(iP)/AMAZON PREMIER/HULU/Disney+(DSNP)
streamDict = {'hbo[\s\.]?max|hmax':'HMAX','nf|netflix':'Netflix','AMZN':'AMZN','DSNP|DisneyPlus':'DSNP','iP|ApplePlus':'ApplePlus','hulu':'HULU'}

#发行版本：CC标准收藏版  有其他版本就删除的： DUPE/R-RATE   保留多版本：UNRATED/R5/UNCUT + THEATRICAL/PROPER/SUBBED/RECODE + IMAX + LIMITED + EXTENDED + DC/DIRECTOR'S CUT + SPECIAL/REMASTERED/COLLECTORS/ULTIMATE/FINAL
releaseDict = {'uncut|unrated':'UNRATED','theatrical|proper|subbed|recode|repack|rerip':'PROPER','imax':'IMAX','limited':'LIMITED','extended':'EXTENDED',"director.s":"Director's.Cut","(?:special|remastered|collector.s|ultimate|final)":"Special.Edition"}

mediaInfoDict = {'source':sourceDict,'resolution':resolutionDict,'dynRes':dynResDict,'videoCodec':videoCodecDict,'audioCodec':audioCodecDict,'stream':streamDict,'release':releaseDict}


LangDict = {'English|ENG|^en$': '英', 'Russian|RUS': '俄', 'French|FRE': '法', 'Spanish|SPA': '西', 'German|^GER$|^DEU$': '德', 'Italian|^ITA$': '意', 'Portuguese|POR': '葡', 'Korean|KOR': '韩', 'Chinese|^CHT$|^CHS$|^CHI$|^GB$|^zh$': '中', 'Mandarin|\bMAN\b':'国','Cantonese|\bCAN\b':'粤','Japanese|JAP|JPN|JP': '日', 'Hebrew': '希', 'Arabic|ARA': '阿', 'Polish': '波', 'Turkish': '土', 'Czech': '捷', 'Hungarian': '匈', 'Romanian': '罗', 'Danish': '丹', 'Swedish': '瑞', 'Norwegian': '挪', 'Finnish': '芬', 'Filipino': '菲', 'Indonesian': '印', 'Thai|THA': '泰', 'Vietnamese': '越', 'Malay': '马','Dutch':'荷','Director':'导'}
ivLangDict = {'英':'English','俄':'Russian','法':'French','西':'Spanish','德':'German','意':'Italian','葡':'Portuguese','韩':'Korean','中':'Chinese','国':'Mandarin','台':'Chinese','简':'Chinese','繁':'Chinese','港':'Cantonese','粤':'Cantonese','日':'Japanese','希':'Hebrew','阿':'Arabic','波':'Polish','土':'Turkish','捷':'Czech','匈':'Hungarian','罗':'Romanian','丹':'Danish','瑞':'Swedish','挪':'Norwegian','芬':'Finnish','菲':'Filipino','印':'Indonesian','泰':'Thai','越':'Vietnamese','马':'Malay','荷':'Dutch','导':'Director'}


####################
###### 优先级 ######
####################

# [tmdbid=<tmdbid>]<zhTitle>(<year>) - <driveType>.<resolution>.<special>.<release>.<source>.<dynRes>.<videoCodec>.<audioCodec>.<audioLang>.<subLang>-<group>.<extension>
renameOrder = ['tmdbid', 'imdbid','tvdbid','zhTitle', 'year', 'resolution','release','audioLang','subLang','fps', 'bit','dynRes','source','region','stream', 'videoCodec', 'audioCodec','audioLangNum', 'group']

#片源：UHDBluRay>Bluray>Remux>BDrip/BRRip>WEB-DL>WEBRip>HDTV>HDTVRip/HDRip>DVD/video_ts/DVDRip>DVDSCR
sourceOrder = {'BluRay':9,'Remux':8,'BDRip':7,'BRRip':7,'DVDRip':6,'FHDRip':5,'HDRip':4,'HDTV':4,'WEBDL':3,'WEBRip':3,'DVDSCR':2,'PDTV':0,'VOD':0,'CAM':0,'UHD':0}

#音频编码：PCM/LPCM/FLAC>Atmos>DTS-X>DTSHD-MA/TRUEHD>DTSHD-HRA/DTS-ES>DTS>DD+>EAC3>AC3/DD>AAC (可多次匹配，不分先后，全匹配完后处理)
audioCodecOrder = {'PCM':20,'LPCM':20,'FLAC':20,'Atmos':15,'DTS-X':15,'DTS-HD.MA':12,'TrueHD':12,'DTS-HD.HRA':10,'DTS-HD.ES':10,'DTS-ES':9,'DTS':8,'DDP':7,'EAC3':6,'Opus':5,'Vorbis':5,'HE-AAC':4,'DD':3,'AAC':2,'MP3':0}

#视频编码：x264>H264>H265>XVID
videoCodecOrder = {'HEVC':30,'AVC':20,'XviD':6,'DivX':4,'VC1':3,'H263':2,'H262':1,'MPEG2':0}


#视频动态范围：HDR10+>HLG>HDR10>SDR>DV DV/HDR/SDR版本预留 DV无法播放，优先级最低
dynResOrder = {'SDR':10,'HDR':9,'HDR10Plus':8,'HLG':7,'HDR10':6,'DoVi':0}

#网盘类型：阿里云盘>天翼云盘>115
driveTypeOrder = {'阿里云盘':300,'阿里云盘2':300,'CM':100,'CM2':100,'115':9}

