"""
shadowSync

分为两层：real层和 shadow，real层是往shadow层单向同步的
real层是网盘的真实数据，由clouddrive挂载，包含真实文件和简单nfo，所有的文件增删改操作全部在此操作
shadow层保存完全版metadata ，由tMM自动刮削

* 准备阶段：开启自动刷新后要确认clouddrive的autorefresh选项关闭，每次拉取文件名前测试clouddrive 可用性，大量拉取两遍核对列表，大量文件不相同的情况警告且仅转移不删除
* 增：real层增加视频文件/文件夹后，等待sync触发，检查与shadow列表不一致处，只软链接媒体文件，只同步简单nfo
* 删：real删除文件夹，shadow连同metadata也一起删除
* 改：real改动文件/目录名,shadow按删除后再添加处理 ，shadow被删除的metadata需要重新刮削

"""

import os
import log
import stat
import time
import shutil
import re
import filecmp
import tempfile

from config import Config
from config import SYMLINKMAXFILESIZE, ZEROBYTETHRESHOLD,SYNCWARNINGTHRESHOLD
from utils.sqls import delete_symlink_info, get_symlink_info_formatted


default_options = {
    'verbose': False,
    'diff': False,
    'sync': False,
    'update': False,
    'single': False,
    'purge': False,
    'force': False,
    'twoway': False,
    'create': False,
    'ctime': False,
    'content': False,
    'only': [],
    'exclude': [],
    'include': [],
    'ignore': [],
}

class DCMP(object):
    """用来存储目录对比结果的object"""

    def __init__(self, l, r, c):
        self.left_only = l
        self.right_only = r
        self.common = c


class Syncer(object):
    """
    包含各种主要同步功能的类
    """

    def __init__(self, drive_type,category, rel_folder, action, **options):


        # 初始化变量

        self._drive_type = drive_type
        self._category = category
        if rel_folder == '/':
            self._rel_folder = ''
        else:
            self._rel_folder = rel_folder
        
        self.init_config(options)

        # 获取action字段的必须内容，用来确认运行模式
        # 包括：diff(只报告不同处),sync(同步俩文件夹),update(更新已存在的文件)
        self._mainfunc = getattr(self, action)

        # excludes .dirsync file by default, must explicitly be in include
        # not to be excluded
        self._exclude.append('^\.dirsync$')
        self._exclude.append('.+\.nfo$')
        if not self._single_mode:
            self._exclude.append('clfs.+')
            self._include.append('tvshow.nfo')
            self._include.append('movie.nfo')

        if not os.path.isdir(self._dir1):
            raise ValueError("[x] 源目录不存在！")

        if not self._maketarget and not os.path.isdir(self._dir2):
            raise ValueError(
                "[x] 目标目录 %s 不存在！ "
                "(尝试用 -c 或 --create 选项忽略不存在错误直接创建目录)." % self._dir2)

    def init_config(self,options):
        """
        初始化配置和变量
        """
        config = Config()
        cloud = config.get_config('cloud')
        if cloud:
            self._cloud_root_path = cloud.get('cloud_root_path')
            self._native_root_path = cloud.get('native_root_path')

        # 初始化各项内部变量
        self._dir1 = os.path.join(self._cloud_root_path,self._drive_type,self._category,self._rel_folder)
        self._dir2 =  os.path.join(self._native_root_path,self._drive_type,self._category,self._rel_folder)

        self._copyfiles = True
        self._updatefiles = True
        self._creatdirs = True

        self._changed = []
        self._added = []
        self._deleted = []

        # 初始化状态变量
        self._numdirs = 0
        self._numfiles = 0
        self._numdelfiles = 0
        self._numdeldirs = 0
        self._numnewdirs = 0
        self._numcontupdates = 0
        self._numtimeupdates = 0
        self._starttime = 0.0
        self._endtime = 0.0

        # 初始化失败状态变量
        self._numcopyfld = 0
        self._numupdsfld = 0
        self._numdirsfld = 0
        self._numdelffld = 0
        self._numdeldfld = 0



        #获取option字段的的内容，都是附加信息
        def get_option(name):
            return options.get(name, default_options[name])

        self._verbose = get_option('verbose') # 提供详细的输出
        self._purge = get_option('purge') # 同步时清除文件（默认不清除）
        self._copydirection = 2 if get_option('twoway') else 0  #twoway就双向同步 
        self._forcecopy = get_option('force')  # 通过尝试更改文件权限来强制复制文件
        self._maketarget = get_option('create')  # 如果目标目录不存在，则创建目标目录（默认情况下，目标目录应该存在。）
        self._use_ctime = get_option('ctime') # 考虑创建时间 (Windows) 或最后一次元数据更改 (Unix)
        self._use_content = get_option('content') #只考虑文件的内容。仅同步不同的文件。双向同步时，如果dst和src同时存在，则src内容优先
        self._single_mode = get_option('single') # single模式

        self._ignore = get_option('ignore') # 忽略项
        self._only = get_option('only')  # 只包含项(排除所有其他的)
        self._exclude = list(get_option('exclude')) # 排除项
        self._include = get_option('include') # 包含项 (优先级高于排除项)

    def validate_path(self,path):
        path = path.replace('\xa0', ' ')
        
        return(path)

    def _compare(self, dir1, dir2):
        """ 比较两个目录的内容 """
        #检查与shadow列表不一致处，只软链接媒体文件，只同步简单nfo

        left = set()
        right = set()

        # 目录计数器
        self._numdirs += 1
        # 组合忽略和排除项的正则表达式
        excl_patterns = set(self._exclude).union(self._ignore)


        # 遍历源目录的所有文件/文件夹
        for cwd, dirs, files in os.walk(dir1):
            self._numdirs += len(dirs)
            for f in dirs + files:
                # 转换为相对路径，以便后续与目标目录的比对
                path = os.path.relpath(os.path.join(cwd, f), dir1) 
                re_path = path.replace('\\', '/') 

                # 筛选 only 项
                if self._only:
                    for pattern in self._only:
                        if re.match(pattern, re_path):
                            # go to exclude and ignore filtering
                            break
                    else:
                        # next item, this one does not match any pattern
                        # in the _only list
                        continue

                # 筛选 include 项
                add_path = False
                for pattern in self._include:   # for ... else ... for完全执行结束后运行else语句，如果中途break则不执行else语句
                    if re.match(pattern, re_path):
                        add_path = True
                        break
                else:
                    # include 优先级高于 exclude 如果没有 include 才来筛选 exclude
                    # path was not in includes
                    # test if it is in excludes
                    for pattern in excl_patterns:
                        if re.match(pattern, re_path):
                            # path is in excludes, do not add it
                            break
                    else:
                        # path was not in excludes
                        # it should be added
                        add_path = True

                # 如果是简单nfo 加进去    
                if (f == 'movie.nfo') or (f == 'tvshow.nfo'):
                    add_path = True
                
                if ('clfs.' in f):
                    add_path = False

                # 如果 add_path 为 True 就加进去
                if add_path:
                    left.add(path)
                    anc_dirs = re_path.split('/')[:-1]
                    anc_dirs_path = '/'
                    for ad in anc_dirs[1:]:
                        anc_dirs_path = os.path.join(anc_dirs_path, ad)
                        left.add(anc_dirs_path)

        # 遍历目标目录的所有文件/文件夹
        symlink_info_list = get_symlink_info_formatted(driveType=self._drive_type,category=self._category,symlinkPath=self._rel_folder,state='Y',like=True)
        for symlink_info in symlink_info_list:
            rel_path = symlink_info['symlinkPath']
            # 如果根目录不是 / 就求一下rel_folder
            if self._rel_folder != '/':
                rel_path = os.path.relpath(rel_path,self._rel_folder)
            
            re_path = rel_path.replace('\\', '/')
            for pattern in self._ignore:
                if re.match(pattern, re_path):
                    break
            else:
                # 文件本身
                right.add(path)

                # 文件自带的nfo
                fullpath = os.path.join(self._dir2,rel_path)
                anc_dir_nfo = os.path.dirname(fullpath)
                nfo_path = os.path.join(anc_dir_nfo,'tvshow.nfo')
                rel_nfo_path = os.path.relpath(nfo_path,self._dir2)
                if os.path.exists(nfo_path):
                    right.add(rel_nfo_path)
                else:
                    anc_dir_nfo = os.path.dirname(anc_dir_nfo)
                    nfo_path = os.path.join(anc_dir_nfo,'tvshow.nfo')
                    rel_nfo_path = os.path.relpath(nfo_path,self._dir2)
                    if os.path.exists(nfo_path):
                        right.add(rel_nfo_path)
                
                # 文件所在的文件夹
                anc_dir = os.path.dirname(rel_path)
                if anc_dir:
                    right.add(anc_dir)
                    if anc_dir not in left:
                        self._numdirs += 1

        
        common = left.intersection(right)
        # 移除相同部分
        left.difference_update(common)
        right.difference_update(common)
        # 返回一个容器
        return DCMP(left, right, common)


    def _compare_single(self, dir1, dir2):
        """ 比较两个目录的内容 """
        #检查与shadow列表不一致处，只软链接媒体文件，只同步简单nfo

        left = set()
        right = set()

        # 目录计数器
        self._numdirs += 1
        # 组合忽略和排除项的正则表达式
        excl_patterns = set(self._exclude).union(self._ignore)


        # 遍历源目录的所有文件/文件夹
        for cwd, dirs, files in os.walk(dir1):
            self._numdirs += len(dirs)
            for f in files:
                path = os.path.join(cwd, f)
                re_path = path.replace('\\', '/') 
                zeroByteFile = os.path.getsize(re_path) < ZEROBYTETHRESHOLD
                # 筛选 only 项
                if self._only:
                    for pattern in self._only:
                        if re.match(pattern, re_path):
                            # go to exclude and ignore filtering
                            break
                    else:
                        # next item, this one does not match any pattern
                        # in the _only list
                        continue

                # 筛选 include 项
                add_path = False
                for pattern in self._include:   # for ... else ... for完全执行结束后运行else语句，如果中途break则不执行else语句
                    if re.match(pattern, re_path):
                        add_path = True
                        break
                else:
                    # include 优先级高于 exclude 如果没有 include 才来筛选 exclude
                    # path was not in includes
                    # test if it is in excludes
                    for pattern in excl_patterns:
                        if re.match(pattern, re_path):
                            # path is in excludes, do not add it
                            break
                    else:
                        # path was not in excludes
                        # it should be added
                        add_path = True

                # 如果 add_path 为 True 就加进去
                if add_path:
                    if not zeroByteFile: # 筛掉0B文件
                        left.add(path)
                    anc_dirs = re_path.split('/')[:-1]
                    anc_dirs_path = '/'
                    for ad in anc_dirs[1:]:
                        anc_dirs_path = os.path.join(anc_dirs_path, ad)
                        left.add(anc_dirs_path)

        # 遍历目标目录的所有文件
        symlink_info_list = get_symlink_info_formatted(driveType=self._drive_type,category=self._category,symlinkPath=self._rel_folder,state='Y',like=True)
        for symlinkPath,symlink_info in symlink_info_list.items():
            right.add(os.path.join(self._dir1,symlink_info['realPath']))

        common = left.intersection(right)
        # 移除相同部分
        left.difference_update(common)
        right.difference_update(common)

        # 返回一个容器
        return DCMP(left, right, common)



    def do_work(self):
        """ 干活 """
        # 开始计时
        self._starttime = time.time()
        # 如果目标目录不存在
        if not os.path.isdir(self._dir2):
            # 如果有maketarget选项，就新建一个目录
            if self._maketarget:
                if self._verbose:
                    log.info('【ShadowSync】目标目录： %s 不存在，新建中' % self._dir2)
                try:
                    os.makedirs(self._dir2)
                    self._numnewdirs += 1
                except Exception as e:
                    log.error('【ShadowSync】创建目标目录时发生错误： %s' % str(e))
                    return None

        # 完事！
        self._mainfunc()
        self._endtime = time.time()

    def _dowork(self, dir1, dir2, copyfunc=None, updatefunc=None):
        """ 内部干活 """

        if self._verbose:
            log.info('【ShadowSync】源目录为: %s:' % dir1)

        if self._single_mode:
            self._dcmp = self._compare_single(dir1,dir2)
        else:
            self._dcmp = self._compare(dir1, dir2)
        

        #保险步骤，防止CloudDrive掉盘误删shadow
        if len(self._dcmp.right_only) > SYNCWARNINGTHRESHOLD:
            print('[?] 检测到大于 %s 项的本地删除操作，请确认CloudDrive服务良好，继续同步y/放弃同步n'%SYNCWARNINGTHRESHOLD)
            while True:
                warningConfirmed = input()
                if warningConfirmed == 'y':
                    print('[!] 确认继续同步')
                    break
                if warningConfirmed == 'n':
                    print('[x] 用户取消，已结束同步')
                    return
                else:
                    print('[x] 请输入正确的选项，注意小写！')
            
        # 只在目标目录存在的文件/文件夹
        if self._purge:
            for f2 in self._dcmp.right_only:
                symlink_infos = get_symlink_info_formatted(driveType=self._drive_type,category=self._category,realPath=f2,state='Y',like=False)
                if len(symlink_infos) == 1:
                    # 如果找到了记录了，说明是个链接
                    for symlinkPath,symlink_info in symlink_infos.items():
                        rel_symlink_path = symlinkPath
                        f2id = symlink_info['id']
                    fullf2 = os.path.join(self._native_root_path,self._drive_type,self._category,rel_symlink_path)
                elif len(symlink_infos) == 0:
                    # 如果没找到记录，说明是个nfo文件
                    fullf2 = os.path.join(self._dir2, f2)
                else:
                    log.error('【ShadowSync】找到了多个记录，请检查！')
                
                if self._verbose:
                    log.info('【ShadowSync】正在删除 %s' % fullf2)
                try:
                    # 如果是文件
                    if os.path.isfile(fullf2):
                        try:
                            try:
                                os.remove(fullf2)
                            except PermissionError as e:
                                os.chmod(fullf2, stat.S_IWRITE)
                                os.remove(fullf2)
                            self._deleted.append(fullf2)
                            self._numdelfiles += 1
                        except OSError as e:
                            self.log( '[x]删除目标目录 文件 时发生错误： %s'% str(e))
                            self._numdelffld += 1
                    # 如果是文件夹
                    elif os.path.isdir(fullf2):
                        try:
                            shutil.rmtree(fullf2, True)
                            self._deleted.append(fullf2)
                            self._numdeldirs += 1
                        except shutil.Error as e:
                            log.error('【ShadowSync】删除目标目录 文件夹 时发生错误： %s'%str(e))
                            self._numdeldfld += 1
                    # 如果是软链接
                    elif os.path.islink(fullf2):
                        try:
                            # 删除软链接，同时observer会把它tag为N
                            os.unlink(fullf2)
                            # 因为是自动删除的，不用经过确认直接删除软链接数据库记录
                            delete_symlink_info(f2id)
                            if self._single_mode:
                                # 删除软链接相关的metadata
                                pathf2,filef2 = os.path.split(fullf2)
                                namef2 = os.path.splitext(filef2)[0]
                                for cwd, dirs, files in os.walk(pathf2):
                                    for f in files:
                                        ipath = os.path.join(cwd, f)
                                        # 所有的link都是电影文件
                                        if ipath.find(namef2) != -1:
                                            try:
                                                log.info('【ShadowSync】正在删除软链接关联元数据 %s' % ipath)
                                                os.remove(ipath)
                                                self._deleted.append(ipath)
                                                self._numdelfiles += 1
                                            except OSError as e:
                                                log.error('【ShadowSync】删除目标目录 元数据 时发生错误： %s'%str(e))
                                                self._numdelffld += 1

                                # 如果目录中没有其他软链接，则删除目录内容和目录
                                dirp,fname = os.path.split(fullf2)
                                for cwd, dirs, files in os.walk(dirp):
                                    for f in files:
                                        subfpath = os.path.join(cwd, f)
                                        if os.path.islink(subfpath):
                                            break
                                    else:
                                        if self._verbose:
                                            log.info('【ShadowSync】正在删除软链接关联文件夹 %s' % dirp)
                                        try:
                                            shutil.rmtree(dirp, True)
                                            self._deleted.append(dirp)
                                            self._numdeldirs += 1
                                        except shutil.Error as e:
                                            log.error('【ShadowSync】删除 软链接关联文件夹 时发生错误： %s'%str(e))
                                            self._numdeldfld += 1
                                

                        except OSError as e:
                            log.error('【ShadowSync】删除目标目录 文件软链接 时发生错误： %s'% str(e))
                            self._numdelffld += 1
                except Exception as e:  # of any use ?
                    log.error('【ShadowSync】清理目标目录 时发生错误： %s' % str(e))
                    continue

        # 只在源目录存在的文件/文件夹
        for f1 in self._dcmp.left_only:
            try:
                st = os.stat(os.path.join(self._dir1, f1))
            except os.error:
                continue
            # 判断是否是文件，是就复制文件
            if stat.S_ISREG(st.st_mode):
                if copyfunc:
                        copyfunc(f1, self._dir1, self._dir2,islink=(st.st_size > SYMLINKMAXFILESIZE))
                        self._added.append(os.path.join(self._dir2, f1))
            #判断是不是文件夹，不存在就创建
            elif stat.S_ISDIR(st.st_mode):
                to_make = os.path.join(self._dir2, f1)
                if not os.path.exists(to_make):
                    os.makedirs(to_make)
                    self._numnewdirs += 1
                    self._added.append(to_make)
        
        
        if not self._single_mode:
            # 共有的文件/文件夹
            for f1 in self._dcmp.common:
                try:
                    st = os.stat(os.path.join(self._dir1, f1))
                except os.error:
                    continue
                
                # 判断是否是文件，是就更新文件
                if stat.S_ISREG(st.st_mode):
                    if updatefunc:
                        updatefunc(f1, self._dir1, self._dir2)
                # 文件夹的话就没有事情做

    def _symlink(self, target, link_name, overwrite=False):
        '''
        Create a symbolic link named link_name pointing to target.
        If link_name exists then FileExistsError is raised, unless overwrite=True.
        When trying to overwrite a directory, IsADirectoryError is raised.
        '''

        if not overwrite:
            os.symlink(target, link_name)
            return

        link_dir = os.path.dirname(link_name)
        # Create link to target with temporary filename
        while True:
            temp_link_name = tempfile.mktemp(dir=link_dir)
            try:
                os.symlink(target, temp_link_name)
                break
            except FileExistsError:
                pass

        try:
            # Pre-empt os.replace on a directory with a nicer message
            if not os.path.islink(link_name) and os.path.isdir(link_name):
                raise IsADirectoryError(f"[!] 无法在已存在的目录上建立软链接: '{link_name}'")
            os.replace(temp_link_name, link_name)
        except:
            if os.path.islink(temp_link_name):
                os.remove(temp_link_name)
            raise



    def _copy(self, filename, dir1, dir2,islink):
        """ 内部函数：复制文件 """

        # NOTE: dir1 is source & dir2 is target
        if self._copyfiles:
            dir1 = os.path.normpath(dir1)
            dir2 = os.path.normpath(dir2)

            rel_path = filename.replace('\\', '/').split('/')
            rel_dir = os.path.normpath('/'.join(rel_path[:-1]))
            filename = rel_path[-1]
            dir2_root = dir2

            if self._single_mode:
                if dir2_root.find('电影') != -1:
                    dir2 = rel_dir.replace(dir1,dir2 +'/' +filename.split(' - ')[0])
                else:
                    dir2 = rel_dir.replace(dir1,dir2 + '/temp')
                
                dir1 = rel_dir
            else:
                dir1 = os.path.join(dir1, rel_dir)
                dir2 = os.path.join(dir2, rel_dir)

            if self._verbose:
                if islink:
                    log.info('【ShadowSync】正在软链接 %s 从 %s 到 %s' %
                            (filename, dir1, dir2))
                else:
                    log.info('【ShadowSync】正在复制 %s 从 %s 到 %s' %
                            (filename, dir1, dir2))
            try:
                # source to target
                if self._copydirection == 0 or self._copydirection == 2:

                    if not os.path.exists(dir2):
                        if self._forcecopy:
                            # 1911 = 0o777
                            os.chmod(os.path.dirname(dir2_root), 1911)
                        try:
                            os.makedirs(dir2)
                            self._numnewdirs += 1
                        except OSError as e:
                            log.error(str(e))
                            self._numdirsfld += 1

                    if self._forcecopy:
                        os.chmod(dir2, 1911)  # 1911 = 0o777

                    sourcefile = os.path.join(dir1, filename)
                    try:
                        if os.path.islink(sourcefile):
                            os.symlink(os.readlink(sourcefile),
                                       os.path.join(dir2, filename))
                        else:
                            #复制还是软链接
                            if islink:
                                self._symlink(sourcefile,os.path.join(dir2, filename))
                            else:
                                shutil.copy2(sourcefile, dir2)
                        self._numfiles += 1
                    except (IOError, OSError) as e:
                        log.error(str(e))
                        self._numcopyfld += 1

                if self._copydirection == 1 or self._copydirection == 2:
                    # target to source

                    if not os.path.exists(dir1):
                        if self._forcecopy:
                            # 1911 = 0o777
                            os.chmod(os.path.dirname(self.dir1_root), 1911)

                        try:
                            os.makedirs(dir1)
                            self._numnewdirs += 1
                        except OSError as e:
                            log.error(str(e))
                            self._numdirsfld += 1

                    targetfile = os.path.abspath(os.path.join(dir1, filename))
                    if self._forcecopy:
                        os.chmod(dir1, 1911)  # 1911 = 0o777

                    sourcefile = os.path.join(dir2, filename)

                    try:
                        if os.path.islink(sourcefile):
                            os.symlink(os.readlink(sourcefile),
                                       os.path.join(dir1, filename))
                        else:
                            shutil.copy2(sourcefile, targetfile)
                        self._numfiles += 1
                    except (IOError, OSError) as e:
                        log.error(str(e))
                        self._numcopyfld += 1

            except Exception as e:
                log.error('【ShadowSync】复制/软链接 %s 文件过程中发生错误' % filename)
                log.error(str(e))

    def _cmptimestamps(self, filest1, filest2):
        """ 比对两文件修改时间，如果源比目标更新则返回 True """

        mtime_cmp = int((filest1.st_mtime - filest2.st_mtime) * 1000) > 0
        if self._use_ctime:
            return mtime_cmp or \
                   int((filest1.st_ctime - filest2.st_mtime) * 1000) > 0
        else:
            return mtime_cmp

    def _update(self, filename, dir1, dir2):
        """ Private function for updating a file based on
        last time stamp of modification or difference of content"""

        # NOTE: dir1 is source & dir2 is target
        if self._updatefiles:

            file1 = os.path.join(dir1, filename)
            file2 = os.path.join(dir2, filename)

            try:
                st1 = os.stat(file1)
                st2 = os.stat(file2)
            except os.error:
                return -1

            # Update will update in both directions depending
            # on ( the timestamp of the file or its content ) & copy-direction.

            if self._copydirection == 0 or self._copydirection == 2:

                # If flag 'content' is used then look only at difference of file
                # contents instead of time stamps.
                # Update file if file's modification time is older than
                # source file's modification time, or creation time. Sometimes
                # it so happens that a file's creation time is newer than it's
                # modification time! (Seen this on windows)
                need_upd = (not filecmp.cmp(file1, file2, False)) if self._use_content else self._cmptimestamps(st1, st2)
                if need_upd:
                    if self._verbose:
                        # source to target
                        log.info('【ShadowSync】更新文件 %s 中' % file2)
                    try:
                        if self._forcecopy:
                            os.chmod(file2, 1638)  # 1638 = 0o666

                        try:
                            if os.path.islink(file1):
                                os.symlink(os.readlink(file1), file2)
                            else:
                                try:
                                    shutil.copy2(file1, file2)
                                except PermissionError as e:
                                    os.chmod(file2, stat.S_IWRITE)
                                    shutil.copy2(file1, file2)
                            self._changed.append(file2)
                            if self._use_content:
                               self._numcontupdates += 1
                            else:
                               self._numtimeupdates += 1
                            return 0
                        except (IOError, OSError) as e:
                            log.error(str(e))
                            self._numupdsfld += 1
                            return -1

                    except Exception as e:
                        log.error(str(e))
                        return -1

            if self._copydirection == 1 or self._copydirection == 2:

                # No need to do reverse synchronization in case of content comparing.
                # Update file if file's modification time is older than
                # source file's modification time, or creation time. Sometimes
                # it so happens that a file's creation time is newer than it's
                # modification time! (Seen this on windows)
                need_upd = False if self._use_content else self._cmptimestamps(st2, st1)
                if need_upd:
                    if self._verbose:
                        # target to source
                        log.info('【ShadowSync】更新文件 %s 中' % file1)
                    try:
                        if self._forcecopy:
                            os.chmod(file1, 1638)  # 1638 = 0o666

                        try:
                            if os.path.islink(file2):
                                os.symlink(os.readlink(file2), file1)
                            else:
                                shutil.copy2(file2, file1)
                            self._changed.append(file1)
                            self._numtimeupdates += 1
                            return 0
                        except (IOError, OSError) as e:
                            log.error(str(e))
                            self._numupdsfld += 1
                            return -1

                    except Exception as e:
                        log.error(str(e))
                        return -1

        return -1

    def _dirdiffandcopy(self, dir1, dir2):
        """
        Private function which does directory diff & copy
        """
        self._dowork(dir1, dir2, self._copy)

    def _dirdiffandupdate(self, dir1, dir2):
        """
        Private function which does directory diff & update
        """
        self._dowork(dir1, dir2, None, self._update)

    def _dirdiffcopyandupdate(self, dir1, dir2):
        """
        Private function which does directory diff, copy and update (synchro)
        """
        self._dowork(dir1, dir2, self._copy, self._update)

    def _diff(self, dir1, dir2):
        """
        Private function which only does directory diff
        """

        self._dcmp = self._compare(dir1, dir2)

        if self._dcmp.left_only:
            log.info('【ShadowSync】只在源目录 %s 的' % dir1)
            for x in sorted(self._dcmp.left_only):
                log.info('【ShadowSync】>> %s' % x)
            self.log('')

        if self._dcmp.right_only:
            log.info('【ShadowSync】只在目标目录 %s 的' % dir2)
            for x in sorted(self._dcmp.right_only):
                log.info('【ShadowSync】<< %s' % x)
            self.log('')

        if self._dcmp.common:
            log.info('【ShadowSync】%s 和 %s 共有的2' % (self._dir1, self._dir2))
            for x in sorted(self._dcmp.common):
                log.info('【ShadowSync】-- %s' % x)
        else:
            log.error('【ShadowSync】没有共有的文件或子目录')

    def sync(self):
        """ Sync 将会尝试同步两个目录的内容，如果有不同，将会复制源目录文件到新目录，并建立对应文件夹，
        如果 Purge 选项激活，目标目录中的不同部分将会被删除， Sync 是在源目录到目标目录方向上完成的
        """

        self._copyfiles = True
        self._updatefiles = True
        self._creatdirs = True
        self._copydirection = 0

        if self._verbose:
            log.info('【ShadowSync】正在同步目录： %s 到 %s' %
                     (self._dir1, self._dir2))
        if self._single_mode:
            self._dowork(self._dir1, self._dir2, self._copy)
        else:
            self._dirdiffcopyandupdate(self._dir1, self._dir2)

    def update(self):
        """ Update 将尝试更新目标目录和源目录。 只会更新两个目录共有的文件，不会创建新的文件或目录 """

        self._copyfiles = False
        self._updatefiles = True
        self._purge = False
        self._creatdirs = False

        if self._verbose:
            log.info('【ShadowSync】正在更新目录： %s 与 %s' %
                     (self._dir2, self._dir1))
        self._dirdiffandupdate(self._dir1, self._dir2)

    def diff(self):
        """
        只报告两个目录之间的内容差异
        """

        self._copyfiles = False
        self._updatefiles = False
        self._purge = False
        self._creatdirs = False

        log.info('【ShadowSync】正在比较目录差异： %s 与 %s' %
                 (self._dir2, self._dir1))
        self._diff(self._dir1, self._dir2)

    def report(self):
        """ 最后打印工作报告 """

        # We need only the first 4 significant digits
        tt = (str(self._endtime - self._starttime))[:4]

        log.info('【ShadowSync】完成同步任务总用时 %s 秒' % (tt))
        log.info('【ShadowSync】共解析 %d 个文件夹,复制了 %d 个文件' %
                 (self._numdirs, self._numfiles))
        if self._numdelfiles:
            log.info('【ShadowSync】清理了 %d 个文件' % self._numdelfiles)
        if self._numdeldirs:
            log.info('【ShadowSync】清理了 %d 个文件夹' % self._numdeldirs)
        if self._numnewdirs:
            log.info('【ShadowSync】创建了 %d 个文件夹' % self._numnewdirs)
        if self._numcontupdates:
            log.info('【ShadowSync】依据文件内容更新了 %d 个文件' % self._numcontupdates)
        if self._numtimeupdates:
            log.info('【ShadowSync】依据时间戳更新了 %d 个文件' % self._numtimeupdates)

        # Failure stats
        self.log('')
        if self._numcopyfld:
            log.error('【ShadowSync】复制文件过程出现 %d 个错误'
                     % self._numcopyfld)
        if self._numdirsfld:
            log.error('【ShadowSync】复制文件夹过程出现 %d 个错误'
                     % self._numdirsfld)
        if self._numupdsfld:
            log.error('【ShadowSync】更新文件过程出现 %d 个错误'
                     % self._numupdsfld)
        if self._numdeldfld:
            log.error('【ShadowSync】清理文件夹过程出现 %d 个错误'
                     % self._numdeldfld)
        if self._numdelffld:
            log.error('【ShadowSync】清理文件过程出现 %d 个错误'
                     % self._numdelffld)
