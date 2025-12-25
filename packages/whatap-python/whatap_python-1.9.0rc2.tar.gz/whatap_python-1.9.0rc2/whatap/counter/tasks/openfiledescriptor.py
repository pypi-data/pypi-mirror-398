import whatap.net.async_sender as async_sender
from whatap.pack import tagCountPack
from whatap import DateUtil, conf
import whatap.io as whatapio
import os
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    # resource module is not available on Windows
    HAS_RESOURCE = False

currentpid = os.getpid()

if HAS_RESOURCE:
    soft_limit, _= resource.getrlimit(resource.RLIMIT_NOFILE)
else:
    soft_limit = None

class OpenFileDescriptorTask:
    def name(self):

        return "OpenFileDescriptorTask"
    
    def interval(self):
        from whatap.conf.configure import Configure as conf
        return conf.open_file_descriptor_interval
    
    def process(self):
        from whatap.conf.configure import Configure as conf
        if not conf.open_file_descriptor_enabled:
            return

        currentnofile = self.currentNofile()
        if soft_limit:
            current_nofile_pct = float(currentnofile) / float(soft_limit) * float(100)
        else:
            current_nofile_pct = "N/A"
        category = "app_filedescriptor"
        tags = dict(pid=currentpid)
        fields = dict(max_nofile = soft_limit,
                      currnet_nofile=currentnofile,
                      current_nofile_pct=current_nofile_pct )

        p = tagCountPack.getTagCountPack(
            t=DateUtil.now(),
            category=f"{category}",
            tags=tags,
            fields=fields
        )

        p.pcode = conf.PCODE
        bout = whatapio.DataOutputX()
        bout.writePack(p, None)
        packbytes = bout.toByteArray()

        async_sender.send_relaypack(packbytes)

    def currentNofile(self):
        # Windows에서는 /proc 파일시스템이 없음
        if not HAS_RESOURCE:
            # Windows: psutil을 사용하여 열린 파일 개수 확인
            try:
                import psutil
                process = psutil.Process(currentpid)
                return len(process.open_files())
            except ImportError:
                return "N/A"
            except Exception:
                return "N/A"

        # Linux/Unix: /proc 파일시스템 사용
        fd_directory = f'/proc/{currentpid}/fd'
        try:
            fd_count = len(os.listdir(fd_directory))
            return fd_count
        except FileNotFoundError:
            return "N/A"