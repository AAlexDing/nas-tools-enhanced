import log
from service.scheduler import Scheduler
from service.sync import Sync
from cloud.monitor import CloudLocalMonitor

def run_scheduler():
    """
    启动定时服务
    """
    try:
        Scheduler().run_service()
    except Exception as err:
        log.error("【RUN】启动定时服务失败：%s" % str(err))


def stop_scheduler():
    """
    停止定时服务
    """
    try:
        Scheduler().stop_service()
    except Exception as err:
        log.debug("【RUN】停止定时服务失败：%s" % str(err))


def restart_scheduler():
    """
    重启定时服务
    """
    stop_scheduler()
    run_scheduler()


def run_monitor():
    """
    启动监控
    """
    try:
        Sync().run_service()
    except Exception as err:
        log.error("【RUN】启动目录同步服务失败：%s" % str(err))


def stop_monitor():
    """
    停止监控
    """
    try:
        Sync().stop_service()
    except Exception as err:
        log.error("【RUN】停止目录同步服务失败：%s" % str(err))


def restart_monitor():
    """
    重启监控
    """
    stop_monitor()
    run_monitor()

###############################

def run_cloud_local_monitor():
    """
    启动本地监控
    """
    try:
        CloudLocalMonitor().run_service()
    except Exception as err:
        log.error("【RUN】启动本地软链接监控服务失败：%s" % str(err))


def stop_cloud_local_monitor():
    """
    停止本地监控
    """
    try:
        CloudLocalMonitor().stop_service()
    except Exception as err:
        log.error("【RUN】停止本地软链接监控服务失败：%s" % str(err))


def restart_cloud_local_monitor():
    """
    重启本地监控
    """
    stop_cloud_local_monitor()
    run_cloud_local_monitor()

###############################################