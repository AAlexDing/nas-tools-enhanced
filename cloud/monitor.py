
'''本地文件监控  （实时检测）
	类似sync的文件监控
	仅对本地软链接进行监控
	软链接文件变动入数据库
		启动时对照表和软链接
		表： SYMLINK_MANAGER
		结构：symlink_path 软链接路径   real_path  网盘实际路径 status  0正常 1软链接被删除 2真实文件被删除(检查网盘离线情况) 3未知情况  
	文件对比时本地直接读取数据库内容
	本地被删以后页面确认是否删除网盘

云端文件监控  （定时1h）
	设置监控目录，隔一定时间更改CD状态检查目录新增
	检测到新文件出现启动入库刮削

本地云端一致性检测  （定时1d）
	

入库刮削流程 （触发）
	入库
		tv - tmdb查询 - 获取第一集详细信息 - 入表 CLOUD_TV
		movie - tmdb查询 - 正常 - 入表 CLOUD_MOVIE
		adult - 番号提取/状态 - CLOUD_ADULT
	同步	
		根据上面的操作，记录更新文件的状态：新增/删除/更新
		查库决定是否同步内容
	刮削
		tv/movie - nas-tools 自带
		adult - MDC刮削
	异常处理
		错误表状态：未识别/不确定正确名称、刮削失败
'''
import os
import threading
from time import sleep
from unicodedata import category
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from config import Config
from utils.functions import get_dir_symlink_files, is_path_in_path,singleton
from utils.sqls import batch_insert_cloud_folder_info, batch_insert_symlink_info, delete_cloud_folder_info, delete_symlink_info, get_cloud_folder_info_by_path, get_cloud_folder_info_formatted, get_symlink_info_by_realpath, get_symlink_info_formatted, insert_cloud_folder_info, insert_symlink_info, update_cloud_folder_info, update_symlink_info
from utils.types import SyncType, OsType
from cloud.clouddrive import CloudDrive
from cloud.syncer import Syncer
import log
from watchdog.events import FileSystemEventHandler

lock = threading.Lock()



class FileMonitorHandler(FileSystemEventHandler):
    """
    目录监控响应类
    """
    def __init__(self, monpath, sync, **kwargs):
        super(FileMonitorHandler, self).__init__(**kwargs)
        self._watch_path = monpath
        self.sync = sync

    def on_created(self, event):
        self.sync.file_change_handler(event, "创建", event.src_path)

    def on_moved(self, event):
        self.sync.file_change_handler(event, "移动", event.dest_path)

    def on_modified(self, event):
        self.sync.file_change_handler(event, "修改", event.src_path)

    def on_deleted(self, event):
        self.sync.file_change_handler(event, "删除", event.src_path)

@singleton
class CloudLocalMonitor(object):
    """
    本地文件监控
    """
    __observer = []
    __mon_sys = OsType.LINUX
    __drive_type = []
    __media_type = []
    __category = []
    __cloud_root_path = None
    __native_root_path = None
    mon_dir_config = {}
    def __init__(self):
        self.init_config()

    def init_config(self):
        config = Config()
        cloud = config.get_config('cloud')
        sync = config.get_config('sync')
        if cloud:
            if sync.get('nas_sys') == "windows":
                self.__mon_sys = OsType.WINDOWS
            # 获取本地监控根目录
            self.__cloud_root_path = cloud.get('cloud_root_path')
            self.__native_root_path = cloud.get('native_root_path')
            # 获取所有分类
            cate = cloud.get('category')
            self.__media_type = dict(cate)
            if cate:
                temp_cate = []
                for x in cate.values():
                    if x: temp_cate.extend(x)
                self.__category = temp_cate
        
            self.init_mon_dirs()
                
    def init_mon_dirs(self):
        '''
        初始化本地监控目录
        '''
        # 获取所有网盘
        self.CloudDriveClient = CloudDrive()
        self.__drive_type = [driveInfo.get('rootFolderPath').replace('/','') for driveInfo in self.CloudDriveClient.get_all_space_info() if driveInfo.get('totalSpace') != 0]
        
        # 生成所有路径
        if self.__drive_type and self.__category:
            for driveType in self.__drive_type:
                for cate in self.__category:
                    native = os.path.join(self.__native_root_path,driveType,cate)
                    cloud  = os.path.join(self.__cloud_root_path,driveType,cate)
                    if os.path.exists(cloud):
                        self.mon_dir_config[native] = {'driveType':driveType,'category':cate,'cloud':cloud}
        
        # 本地没有对应文件夹的生成文件夹
        for path in self.mon_dir_config.keys():
            if not os.path.exists(path):
                os.makedirs(path)
                log.info("【CLMON】本地目录不存在，正在创建：%s" % path)
        
    
    def file_change_handler(self, event, text, event_path):
        """
        处理文件变化
        :param event: 事件
        :param text: 事件描述
        :param event_path: 事件文件路径
        """
        if not event.is_directory:
            # 不是监控目录下的文件不处理
            is_monitor_file = False
            for tpath in self.mon_dir_config.keys():
                if is_path_in_path(tpath, event_path):
                    is_monitor_file = True
                    break
            if not is_monitor_file:
                return

            if os.path.islink(event_path):
                # 获取链接文件的真实路径
                real_path = os.path.realpath(event_path)
                # 获取driveType 和 category
                segments = event_path.split(os.sep)
                driveType = ''
                category = ''
                for segment in segments:
                    if segment in self.__category:
                        category = segment
                    if segment in self.__drive_type:
                        driveType = segment
                    if driveType and category:
                        break
                # 获取symlink的相对路径
                if driveType and category:
                    native = os.path.join(self.__native_root_path,driveType,category)
                    cloud  = os.path.join(self.__cloud_root_path,driveType,category)
                    rel_symlink_path = os.path.relpath(event_path,native)
                    rel_real_path = os.path.relpath(real_path,cloud)
                if driveType and category:
                    
                    if text == '创建':
                        insert_symlink_info(driveType, category, rel_symlink_path, rel_real_path,'Y')
                    elif text == '移动':
                        # 移动给的是目标路径
                        ret = get_symlink_info_by_realpath(real_path)
                        if ret:
                            id = ret[0][0]
                            update_symlink_info(id, symlinkPath = rel_symlink_path, realPath = rel_real_path)
                        else:
                            insert_symlink_info(driveType, category, rel_symlink_path, rel_real_path,'Y')
                    elif text == '修改':
                        symlink_infos = get_symlink_info_formatted(symlinkPath=rel_symlink_path)
                        if symlink_infos:
                            if symlink_infos[0]['realPath'] != rel_real_path:
                                update_symlink_info(symlink_infos[0]['id'], realPath = rel_real_path)
                    elif text == '删除':
                        symlink_infos = get_symlink_info_formatted(symlinkPath=rel_symlink_path)
                        if symlink_infos:
                            update_symlink_info(id = symlink_infos[0]['id'],state='N')
                            # WEBUI确认是否0Byte化云端，然后再delete_symlink_info(symlink_infos[0]['id'])
                    else:
                        log.error("【CLMON】未知事件：%s" % text)
                else:
                    log.error("【CLMON】识别不到网盘类型和类别：%s" % event_path)


    def run_service(self):
        """
        启动监控服务
        """
        self.__observer = []
        for monpath in self.mon_dir_config.keys():
            if monpath and os.path.exists(monpath):
                try:
                    if self.__mon_sys == OsType.LINUX:
                        # linux
                        observer = Observer()
                    else:
                        # 其他
                        observer = PollingObserver()
                    self.__observer.append(observer)
                    observer.schedule(FileMonitorHandler(monpath, self), path=monpath, recursive=True)
                    observer.setDaemon(True)
                    observer.start()
                    log.info("【CLMON】%s 的监控服务启动..." % monpath)
                except Exception as e:
                    log.error("【CLMON】%s 启动目录监控失败：%s" % (monpath, str(e)))

    def stop_service(self):
        """
        关闭监控服务
        """
        if self.__observer:
            for observer in self.__observer:
                observer.stop()
        self.__observer = []


    def check_all_files(self):
        self.check_native_files()
        self.check_cloud_files()

    def check_native_files(self):
        """
        全量检查本地目录与数据库内容一致性，WEB界面点击一致性检测时获发
        """
        batch_insert = []
        for monpath,values in self.mon_dir_config.items():
            log.info("【CLMON】本地数据库一致性检查，开始检查目录：%s" % monpath)

            driveType = values.get('driveType')
            category = values.get('category')
            cloud_root_path = values.get('cloud')

            # 从数据库获取所有symlink文件信息
            db_symlink_infos = get_symlink_info_formatted(driveType=driveType,category=category)
            
            # 获取所有软链接文件
            if monpath and os.path.exists(monpath):
                symlink_path_list = get_dir_symlink_files(monpath)
                for symlink_path in symlink_path_list:
                    # 获取相对路径
                    rel_symlink_path = os.path.relpath(symlink_path,monpath)
                    real_path = os.readlink(symlink_path)
                    rel_real_path = os.path.relpath(real_path,cloud_root_path)
                    if db_symlink_infos.get(rel_symlink_path):
                        # 如果数据库中存在该软链接文件，则对比更新数据库中的记录
                        info = db_symlink_infos.get(rel_symlink_path)
                        if info.get('realPath') != rel_real_path:
                            # 更新数据库中的记录
                            update_symlink_info(info.get('id'),rel_real_path)
                        # 删除缓存中的记录
                        del(db_symlink_infos[rel_symlink_path])
                    else:
                        # 如果数据库中不存在该软链接文件，则创建数据库记录
                        batch_insert.append((driveType,category,rel_symlink_path,rel_real_path,'Y'))
            
            # db_symlink_infos剩下的内容在数据库中全部删除
            for info in db_symlink_infos.values():
                delete_symlink_info(info.get('id'))
        
        batch_insert_symlink_info(batch_insert)
        log.info("【CLMON】本地数据库一致性检查完成")


    def check_cloud_files(self):
        """
        检查云端目录变动，如果有变动的文件夹，则更新数据库中的记录(增删改)，WEB界面点击一致性检测时获发
            1.check_folders = []
            2.检查云端目录下的一二级文件夹，对比db:CLOUD_FOLDER_MANAGER，看看有没有文件夹的创建修改和删除（只有115可到文件夹粒度）
                创建、删除：文件夹路径入checkfolders、db新增条目
                修改：获取 db 中的文件夹大小信息，对比现有文件夹大小，如果有变动，则文件夹路径入checkfolders、更新db记录
            
            4.根据checkfolders的路径 获取 db：SYMLINK_MANAGER 的realPath 与 网盘中真实的文件路径
            5.根据shadowsync的方法对 db更新，对文件进行标记删除、创建软链接
        """
        self.CloudDriveClient.set_vars('AutoRefreshFolder',True)
        self.CloudDriveClient.set_vars('FolderRefreshTimeInSeconds',1)
        if self.CloudDriveClient.get_vars('AutoRefreshFolder'):
            
            ###test###
            '''
            testinfo = get_cloud_folder_info_formatted(driveType='阿里云盘2',category='',path='/')
            if testinfo:
                delete_cloud_folder_info(testinfo['/']['id'])
            '''
            ###test###


            sleep(1)
            check_folders = []
            changed_drives = []

            for cdinfo in self.CloudDriveClient.get_all_space_info():
                driveType = cdinfo.get('rootFolderPath')[1:]
                dbinfo = get_cloud_folder_info_formatted(driveType=driveType,category='',path='/')
                cdsize = cdinfo.get('usedSpace')
                if cdsize != 0:
                    if dbinfo:
                        if len(dbinfo) == 1:
                            dbinfo = dbinfo['/']
                            # 如果存在该类型的云盘，则对比
                            dbsize = dbinfo.get('size')
                            if cdsize != dbsize:
                                changed_drives.append(driveType)
                                update_cloud_folder_info(dbinfo.get('id'),size=cdsize)
                        else:
                            log.error('【CLMON】 %s 有一条以上记录，请检查数据库' % driveType)
                    else:
                        # 如果不存在该类型的云盘，则新建
                        changed_drives.append(driveType)
                        insert_cloud_folder_info(driveType,'','/',cdsize)

        

            for monpath,values in self.mon_dir_config.items():
                driveType = values.get('driveType')
                category = values.get('category')
                cloud_folder_path = values.get('cloud')
                log.info("【CLMON】云端数据库一致性检查，开始检查目录：%s" % cloud_folder_path)
                temp_folder_list = []
                batch_temp_folder_list = []
                batch_insert_list = []
                if driveType == '115':
                    # 检查一级文件夹是否改变
                    first_level_folder_changed = False


                    level1_info = get_cloud_folder_info_formatted(driveType=driveType ,category=category,path = '/')
                    level1_clouddetail = self.CloudDriveClient.get_file_detail_properties(os.path.join(driveType,category))
                    if level1_clouddetail:
                        if level1_info:
                            level1_info = [x for x in level1_info.values()][0]
                            # 数据库查到了，则比较大小
                            level1_dbsize = level1_info['size']
                            level1_cloudsize = level1_clouddetail.get('totalSize')
                            if level1_dbsize != level1_cloudsize:
                                first_level_folder_changed = True
                        else:
                            # 数据库没查到，则新增
                            level1_cloudsize = level1_clouddetail.get('totalSize')
                            first_level_folder_changed = True
                            
                    else:
                        log.error("【CLMON】获取云端文件夹大小失败：%s" % cloud_folder_path)
                        continue
                    
                    if first_level_folder_changed:
                        # 获取云端目录下的二级文件夹
                        left =[os.path.normpath(x) for x in os.listdir(cloud_folder_path) if os.path.isdir(os.path.join(cloud_folder_path,x))]
                        # 获取db记载的二级文件夹
                        dbinfo = get_cloud_folder_info_formatted(category=category)
                        right = [os.path.normpath(x) for x in dbinfo.keys() if x != '/']
                        left = set(left)
                        right = set(right)

                        # 对比common、新增left、删除right
                        common = left.intersection(right)
                        left.difference_update(common)
                        right.difference_update(common)

                        # 相同的就对比大小，如果有变动，则更新db记录
                        if common:
                            for rel_folder in common:
                                dbpath = rel_folder
                                cdpath = os.path.join(driveType,category,dbpath)
                                info  = get_cloud_folder_info_formatted(driveType=driveType,category=category,path=dbpath)
                                clouddetail = self.CloudDriveClient.get_file_detail_properties(cdpath)
                                if clouddetail:
                                    if info:
                                        info = [x for x in info.values()][0]
                                        dbsize = info['size']
                                        cloudsize = clouddetail.get('totalSize')
                                        if dbsize != cloudsize:
                                            temp_folder_list.append((driveType,category,rel_folder))
                                            update_cloud_folder_info(info['id'],size=cloudsize)
                                    else:
                                        log.error('【CLMON】 %s 出现了未知错误，请检查数据库' % driveType)
                                else:
                                    log.error("【CLMON】获取云端文件夹大小失败：%s" % cdpath)
                                    continue
                        # 新增的就新增db记录
                        if left:
                            for rel_folder in left:
                                dbpath = rel_folder
                                cdpath = os.path.join(driveType,category,dbpath)
                                clouddetail = self.CloudDriveClient.get_file_detail_properties(cdpath)
                                if clouddetail:
                                    cloudsize = clouddetail.get('totalSize')
                                    #容后批量插入
                                    batch_insert_list.append((driveType,category,dbpath,cloudsize))
                                    batch_temp_folder_list.append((driveType,category,rel_folder))
                                else:
                                    log.error("【CLMON】获取云端文件夹大小失败：%s" % cdpath)
                                    continue
                        # 删除的就删除db记录
                        if right:
                            for rel_folder in right:
                                dbpath = rel_folder
                                cdpath = os.path.join(driveType,category,dbpath)
                                if not delete_cloud_folder_info(dbinfo[rel_folder]['id']):
                                    log.error("【CLMON】删除云端文件夹记录失败：%s" % rel_folder)
                                else:
                                    temp_folder_list.append((driveType,category,rel_folder))
                        
                        # 如果都没有的话一级文件夹提交
                        if not temp_folder_list or not batch_temp_folder_list:
                            if level1_clouddetail:
                                if level1_info:
                                    if level1_dbsize != level1_cloudsize:
                                        update_cloud_folder_info(level1_info['id'],size=level1_cloudsize)
                                        temp_folder_list.append((driveType,category,'/'))
                                else:
                                    # 数据库没查到，则新增
                                    level1_cloudsize = level1_clouddetail.get('totalSize')
                                    insert_cloud_folder_info(driveType,category,'/',level1_cloudsize)
                                    if level1_cloudsize != 0:
                                        temp_folder_list.append((driveType,category,'/'))
                                    
                            else:
                                log.error("【CLMON】获取云端文件夹大小失败：%s" % cloud_folder_path)
                                continue
                        else:
                            # 如果二级文件夹有新增或删除的，则只修改数据库中一级文件夹信息，不提交同步
                            insert_cloud_folder_info(driveType,category,'/',level1_cloudsize)
                else:
                    if driveType in changed_drives:
                        temp_folder_list.append((driveType,category,'/'))
                check_folders.extend(temp_folder_list)
                if batch_insert_list:
                    if batch_insert_cloud_folder_info(batch_insert_list):
                        check_folders.extend(batch_temp_folder_list)
                    else:
                        log.error("【CLMON】批量插入云端文件夹记录失败：%s" % batch_insert_list)

            # 检查mediaType
            for driveType,category,rel_folder in check_folders:
                
                mediaType = ''
                # 匹配mediaType
                for key,value in self.__media_type.items():
                    if category in value:
                        mediaType = key
                
                if mediaType:
                    if  mediaType in('movie','adult'):
                        self.shadowSync(driveType,category,rel_folder,'sync',create=True,verbose = True,purge = True,single=True)
                    else:
                        self.shadowSync(driveType,category,rel_folder,'sync',create=True,verbose = True,purge = True,single=False)
                
            self.CloudDriveClient.set_vars('AutoRefreshFolder',False)
            if not self.CloudDriveClient.get_vars('AutoRefreshFolder'):
                return True
        else:
            log.error("【CLMON】云端设置刷新文件夹失败")
        
        log.info("【CLMON】云端数据库一致性检查完成")



    def shadowSync(self,drive_type,category,rel_folder,action, **options):

        copier = Syncer(drive_type,category,rel_folder, action, **options)
        copier.do_work()

        # print report at the end
        copier.report()

        return set(copier._changed).union(copier._added).union(copier._deleted)
