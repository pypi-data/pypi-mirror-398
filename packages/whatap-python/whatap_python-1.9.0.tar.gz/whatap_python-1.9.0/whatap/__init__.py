import logging as logging_module
import os
import platform
import sys
import subprocess, signal
import time
from whatap import build
from whatap.util.date_util import DateUtil
import threading
import builtins

__version__ = build.version

LOGGING_MSG_FORMAT = '[%(asctime)s] : - %(message)s'
LOGGING_DATE_FORMAT = '%Y-%m-%d  %H:%M:%S'

logging = logging_module.getLogger(__name__)

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

ROOT_DIR = __file__


class ContextFilter(logging_module.Filter):
    def __init__(self):
        super(ContextFilter, self).__init__()
        self.last_id = None
    
    def filter(self, record):
        try:
            if record.id:
                if self.last_id == record.id:
                    return False
                
                self.last_id = record.id
                return True
        
        except Exception as e:
            record.id = ''
            return True

    

from whatap.conf.configure import Configure as conf
CONFIG_FILE_NAME = 'whatap.conf'
LOG_FILE_NAME = 'whatap-hook.log'

isFrappeCommands = "get-frappe-commands" in sys.argv if hasattr(sys, "argv") else False

def preview_whatap_conf(option_name:str):
    home = os.environ.get('WHATAP_HOME', '.')
    whatap_config = os.path.join(home, 'whatap.conf')


    """
    현재 preview_whatap_conf 를 사용중인 옵션
    - ignore_whatap_stdout (False)
    - standalone_enabled (False)
    - counter_thread_enabled (False)
    """
    value = 'false'
    try:
        with open(whatap_config) as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith(option_name):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        value = parts[1].strip()
                    break
        return value

    except FileNotFoundError:
        return value

    except Exception as e:
        print(f'WHATAP: config parse error ({e!r})')
        return value



ignore_whatap_stdout = preview_whatap_conf("ignore_whatap_stdout")



original_print = builtins.print

def print_option(func):
    def wrapper(*args, **kwargs):

        if(ignore_whatap_stdout == 'false'):
            result = func(*args, **kwargs)
        else:
            result = None
        return result
    return wrapper

__builtins__ = dict(__builtins__)
__builtins__['print'] = print_option(original_print)


def whatap_print(*args):
    if isFrappeCommands:
        logging.info(*args)
    else:
        if len(args) > 0:
            message = " ".join(args)
            print(message)

class Logger(object):
    def __init__(self):
        self.logger = logging
        self.logger.addFilter(ContextFilter())
        self.handler = None
        
        self.create_log()
    
    def create_log(self):
        os.environ['WHATAP_LOGS'] = os.path.join(os.environ['WHATAP_HOME'],
                                                 'logs')
        if not os.path.exists(os.environ['WHATAP_LOGS']):
            try:
                os.mkdir(os.environ['WHATAP_LOGS'])
            
            except Exception as e:
                whatap_print('WHATAP: LOG FILE WRITE ERROR.')
                whatap_print(
                    'WHATAP: Try to execute command. \n  {}'.format(
                        'sudo mkdir -m 777 -p $WHATAP_HOME/logs`'))
        
        self.print_log()
    
    def print_log(self):
        try:
            if self.handler:
                self.logger.removeHandler(self.handler)
            
            temp_logging_msg_format = '[%(asctime)s] : %(id)s - %(message)s'
            logging_format = logging_module.Formatter(
                fmt=temp_logging_msg_format, datefmt=LOGGING_DATE_FORMAT)
            
            fh = logging_module.FileHandler(
                os.path.join(os.environ['WHATAP_LOGS'], LOG_FILE_NAME))
            fh.setFormatter(logging_format)
            self.logger.addHandler(fh)
            self.handler = fh
            
            self.logger.setLevel(logging_module.DEBUG)
        except Exception as e:
            whatap_print('WHATAP: LOGGING ERROR: {}'.format(e))
        else:
            self.print_whatap()
    
    def print_whatap(self):
        str = '\n' + \
              ' _      ____       ______' + build.app + '-AGENT  \n' + \
              '| | /| / / /  ___ /_  __/__ ____' + '\n' + \
              '| |/ |/ / _ \\/ _ `// / / _ `/ _ \\' + '\n' + \
              '|__/|__/_//_/\\_,_//_/  \\_,_/ .__/' + '\n' + \
              '                          /_/' + '\n' + \
              'Just Tap, Always Monitoring' + '\n' + \
              'WhaTap ' + build.app + ' Agent version ' + build.version + ', ' + build.release_date + '\n\n'
        
        str += '{0}: {1}\n'.format('WHATAP_HOME', os.environ['WHATAP_HOME'])
        str += '{0}: {1}\n'.format('Config', os.path.join(os.environ['WHATAP_HOME'],
                                                os.environ['WHATAP_CONFIG']))
        str += '{0}: {1}\n\n'.format('Logs', os.environ['WHATAP_LOGS'])
        
        whatap_print(str)
        logging.debug(str)


def read_file(home, file_name):
    data = ''
    try:
        f = open(os.path.join(os.environ.get(home), file_name), 'r+')
        data = str(f.readline()).strip()
        f.close()
    finally:
        return data


def write_file(home, file_name, value):
    try:
        f = open(os.path.join(os.environ.get(home), file_name), 'w+')
        f.write(value)
        f.close()
    except Exception as e:
        whatap_print('WHATAP: WHATAP HOME ERROR. (path: {})'.format(os.path.join(os.environ.get(home))))
        whatap_print(
            'WHATAP: Try to execute command. \n  {}'.format(
                '`sudo chmod -R 777 $WHATAP_HOME`'))
        return False
    else:
        return True


def check_whatap_home(target='WHATAP_HOME'):
    whatap_home = os.environ.get(target)
    if not whatap_home:
        whatap_home = find_whatap_conf()
    if not whatap_home:
        whatap_print('WHATAP: ${} is empty'.format(target))
    
    return whatap_home


def init_config(home):
    whatap_home = os.environ.get(home)
    if not whatap_home:
        whatap_home = find_whatap_conf()
    if not whatap_home:
        whatap_home = read_file(home, home.lower())
        if not whatap_home:
            whatap_home = os.getcwd()
            os.environ[home] = whatap_home
            
            whatap_print('WHATAP: WHATAP_HOME is empty')
            whatap_print(
                'WHATAP: WHATAP_HOME set default CURRENT_WORKING_DIRECTORY value')
            whatap_print('CURRENT_WORKING_DIRECTORY is {}\n'.format(whatap_home))
    
    if not write_file(home, home.lower(), whatap_home):
        return False
    
    os.environ[home] = whatap_home
    config_file = os.path.join(os.environ[home],
                               CONFIG_FILE_NAME)
    
    if not os.path.exists(config_file):
        with open(
                os.path.join(os.path.dirname(__file__),
                             CONFIG_FILE_NAME),
                'r') as f:
            content = f.read()
            try:
                with open(config_file, 'w+') as new_f:
                    new_f.write(content)
            except Exception as e:
                whatap_print('WHATAP: PERMISSION ERROR: {}'.format(e))
                whatap_print(
                    'WHATAP: Try to execute command. \n  {}'.format(
                        '`sudo chmod -R 777 $WHATAP_HOME`'))
                return False
    
    return True


def update_config(home, opt_key, opt_value):
    config_file = os.path.join(os.environ[home],
                               CONFIG_FILE_NAME)
    try:
        with open(config_file, 'r+') as f:
            is_update = False
            content = ''
            for line in f:
                if line:
                    key = line.split('=')[0].strip()
                    if key == opt_key:
                        is_update = True
                        line = '{0}={1}\n'.format(key, opt_value)
                    
                    content += line
            if not is_update:
                content += '\n{0}={1}\n'.format(opt_key, opt_value)
            open(config_file, 'w+').write(content)
    
    except Exception as e:
        whatap_print('WHATAP: OPTION ERROR: {}'.format(e))


def config(home):
    os.environ['WHATAP_CONFIG'] = CONFIG_FILE_NAME
    
    from whatap.conf.configure import Configure as conf
    if conf.init():
        from whatap.net.packet_enum import PacketEnum
        PacketEnum.PORT = int(conf.net_udp_port)

        from whatap.conf.license import License
        conf.PCODE = License.getProjectCode(conf.license)

        import whatap.counter

        hooks(home)


from whatap.trace.trace_import import ImportFinder
from whatap.trace.trace_module_definition import DEFINITION, IMPORT_HOOKS, \
    PLUGIN


def hooks(home):
    try:
        for key, value_list in DEFINITION.items():
            for value in value_list:
                if len(value) == 3 and not value[2]:
                    continue
                
                IMPORT_HOOKS[value[0]] = {'def': value[1],
                                          'module': '{0}.{1}.{2}.{3}'.format(
                                              'whatap',
                                              'trace',
                                              'mod',
                                              key)}
    except Exception as e:
        logging.debug(e, extra={'id': 'MODULE ERROR'})
    finally:
        try:
            if conf.trace_logging_enabled:
                logging_module = sys.modules.get("logging")
                from whatap.trace.mod.logging import instrument_logging
                instrument_logging(logging_module)

            if conf.hook_method_patterns:
                from whatap.trace.mod.plugin import instrument_plugin
                patterns = conf.hook_method_patterns.split(',')
                for pattern in patterns:
                    pattern=pattern.strip()
                
                    module_name, class_def = pattern.split(':')
                    if not PLUGIN.get(module_name):
                        PLUGIN[module_name] = []
                    PLUGIN[module_name].append(class_def)
                    
                    DEFINITION["plugin"].append(
                        (module_name, 'instrument_plugin'))
                    
                    key = 'plugin'
                    for value in DEFINITION[key]:
                        IMPORT_HOOKS[value[0]] = {'def': value[1],
                                                  'module': '{0}.{1}.{2}.{3}'.format(
                                                      'whatap',
                                                      'trace',
                                                      'mod',
                                                      key)}

            if conf.standalone_enabled:
                if conf.standalone_type == 'multiple-transaction':
                    from whatap.trace.mod.standalone.multiple import instrument_standalone_multiple
                    instrument_standalone_multiple()
                else:
                    from whatap.trace.mod.standalone.single import instrument_standalone_single
                    instrument_standalone_single()
        
        except Exception as e:
            logging.debug(e, extra={'id': 'PLUGIN ERROR'})
        finally:
            sys.meta_path.insert(0, ImportFinder())
            logging.debug('WHATAP AGENT START!', extra={'id': 'WA000'})


def agent():
    home = 'WHATAP_HOME'
    whatap_home = os.environ.get(home)
    if not whatap_home:
        whatap_home = read_file(home, home.lower())
        if not whatap_home:
            whatap_home = os.getcwd()
            os.environ[home] = whatap_home
            
            whatap_print('WHATAP: WHATAP_HOME is empty')
            whatap_print(
                'WHATAP: WHATAP_HOME set default CURRENT_WORKING_DIRECTORY value')
            whatap_print('CURRENT_WORKING_DIRECTORY is {}\n'.format(whatap_home))
    
    if write_file(home, home.lower(), whatap_home):
        os.environ['WHATAP_HOME'] = whatap_home
        
        whatap_code_start = preview_whatap_conf("whatap_code_start")
        if whatap_code_start == 'true':
            t = threading.Thread(target=go)
            t.setDaemon(True)
            t.start()
        config(home)

ARCH = {
    'x86_64': 'amd64',
    'x86': '386',
    'x86_32': '386',
    'ARM': 'arm',
    'AArch64': 'arm64',
    'arm64': 'arm64',
    'aarch64': 'arm64'
}

AGENT_NAME = 'whatap_python'



def go(batch=False, opts={}):
    newenv=os.environ.copy()
    newenv['WHATAP_VERSION'] = build.version
    newenv['whatap.start'] = str(DateUtil.now())
    newenv['python.uptime'] = str(DateUtil.datetime())
    newenv['python.version'] = sys.version
    newenv['python.tzname'] = time.tzname[0]
    newenv['os.release'] = platform.release()
    newenv['sys.version_info'] = str(sys.version_info)
    newenv['sys.executable'] = sys.executable
    newenv['sys.path'] = str(sys.path)
    newenv.update(opts)

    if not batch:
        home = 'WHATAP_HOME'
        file_name = AGENT_NAME + '.pid'
    else:
        home = 'WHATAP_HOME_BATCH'
        file_name = AGENT_NAME + '.pid.batch'

    def get_pname(pid):
        # Linux/Unix: use /proc filesystem
        if sys.platform != 'win32':
            cmdlinepath = os.path.join('/proc', str(pid), 'cmdline')
            if os.path.exists(cmdlinepath):
                with open(cmdlinepath) as f:
                    content = f.read()
                    if content:
                        return content.strip()
        else:
            # Windows: use psutil to get process name
            try:
                import psutil
                process = psutil.Process(int(pid))
                return ' '.join(process.cmdline())
            except:
                pass
        return ''

    pid = read_file(home, file_name)
    if pid and get_pname(pid).find('whatap_python') >= 0:
        if sys.platform == 'win32':
            # Windows: Don't kill, just skip
            whatap_print('WHATAP: Agent already running (PID: {}). Skipping duplicate execution.'.format(pid))
            return
        else:
            # Unix/Linux: kill and replace existing process
            try:
                import signal
                os.kill(int(pid), signal.SIGKILL)
            except Exception:
                pass

    try:
        home_path= os.environ.get(home)

        # Windows uses .exe extension
        agent_binary_name = AGENT_NAME + '.exe' if sys.platform == 'win32' else AGENT_NAME
        dest_agent = os.path.join(home_path, agent_binary_name)

        # Try to remove existing binary
        # Windows: File may still be locked even after waiting, ignore error and use existing binary
        # Unix/Linux: Removal should always succeed
        needs_deployment = False
        if os.path.exists(dest_agent):
            try:
                os.remove(dest_agent)
                needs_deployment = True
            except (OSError, PermissionError) as e:
                if sys.platform == 'win32':
                    # Windows: File is still locked, use existing binary
                    pass
                else:
                    # Unix/Linux: This should not happen
                    raise
        else:
            needs_deployment = True

        # Windows doesn't use architecture subdirectories (only single x64 binary for now)
        if sys.platform == 'win32':
            source_cwd = os.path.join(os.path.dirname(__file__), 'agent', 'windows')
        else:
            source_cwd = os.path.join(os.path.join(os.path.dirname(__file__), 'agent'), platform.system().lower(),
                                      ARCH[platform.machine()])

        source_agent = os.path.join(source_cwd, agent_binary_name)

        # Deploy agent binary only if needed
        if needs_deployment:
            # Try symlink first (Unix/Linux or Windows with proper permissions)
            try:
                os.symlink(source_agent, dest_agent)
            except (OSError, NotImplementedError):
                # Fallback to copy on Windows or when symlink fails
                import shutil
                shutil.copy2(source_agent, dest_agent)
                # Make executable on Unix-like systems
                if sys.platform != 'win32':
                    os.chmod(dest_agent, 0o755)

        sockfile_path = os.path.join(home_path, 'run')
        if not os.path.exists(sockfile_path):
            os.mkdir(sockfile_path)
        newenv['whatap.enabled'] = 'True'
        newenv['WHATAP_PID_FILE'] = file_name
        newenv['PYTHON_PARENT_APP_PID'] = str(os.getpid())

        # Windows uses absolute path, Unix/Linux uses relative path
        if sys.platform == 'win32':
            agent_cmd = os.path.join(home_path, agent_binary_name)
        else:
            agent_cmd = './{0}'.format(agent_binary_name)

        # Windows: Use -t flag only (no -d flag support) and run in background with DETACHED_PROCESS
        # Unix/Linux: Use -t and -d flags, daemon mode handles background execution
        if sys.platform == 'win32':
            # Windows: Run in detached background process
            DETACHED_PROCESS = 0x00000008
            process = subprocess.Popen([agent_cmd, '-t', '3','foreground'],
                                       cwd=home_path, env=newenv,
                                       creationflags=DETACHED_PROCESS,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Give it a moment to start
            time.sleep(0.5)
            if process.poll() is not None:
                # Process ended unexpectedly, read output
                stdouts, errs = process.communicate()
                whatap_print("executed golang module ", str(stdouts,"utf8"), str(errs, "utf8"))
            else:
                # Write PID to file for process tracking
                write_file(home, file_name, str(process.pid))
                whatap_print("executed golang module in background (PID: {})".format(process.pid))
        else:
            # Unix/Linux: Run with daemon flag
            process = subprocess.Popen([agent_cmd, '-t', '3', '-d', '1'],
                                       cwd=home_path, env=newenv,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdouts, errs = process.communicate()
            whatap_print("executed golang module ", str(stdouts,"utf8"), str(errs, "utf8"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        whatap_print('WHATAP: AGENT ERROR: {}'.format(e))
    else:
        whatap_print('WHATAP: AGENT UP! (process name: {})\n'.format(AGENT_NAME))

import signal

from whatap.trace.mod.application.wsgi import interceptor, start_interceptor, \
    end_interceptor, trace_handler, interceptor_step_error
from whatap.trace.mod.application.fastapi import interceptor_error_log
from whatap.trace.trace_context import TraceContext, TraceContextManager

def register_app(fn):
    @trace_handler(fn, True)
    def trace(*args, **kwargs):
        callback = None
        try:
            environ = args[0]
            callback = interceptor((fn, environ), *args, **kwargs)
        except Exception as e:
            logging.debug('WHATAP(@register_app): ' + str(e),
                          extra={'id': 'WA777'}, exc_info=True)
        finally:
            return callback if callback else fn(*args, **kwargs)
    
    if not os.environ.get('whatap.enabled'):
        agent()
    
    return trace


def method_profiling(fn):
    def trace(*args, **kwargs):
        callback = None
        try:
            ctx = TraceContext()
            ctx.service_name=fn.__name__
            start_interceptor(ctx)
            callback = fn(*args, **kwargs)
        except Exception as e:
            ctx = TraceContextManager.getLocalContext()
            interceptor_step_error(e, ctx=ctx)
            interceptor_error_log(ctx.id, e, fn, args, kwargs)
            logging.debug('WHATAP(@method_profiling): ' + str(e),
                          extra={'id': 'WA776'}, exc_info=True)
        finally:
            ctx = TraceContextManager.getLocalContext()
            end_interceptor(ctx=ctx)
            return callback
    
    if not os.environ.get('whatap.enabled'):
        agent()
    
    return trace


def batch_agent():
    home = 'WHATAP_HOME_BATCH'
    batch_home = os.environ.get(home)
    if not batch_home:
        if not read_file(home, home.lower()):
            whatap_print('WHATAP: WHATAP_HOME_BATCH is empty')
            return
    
    if write_file(home, home.lower(), batch_home):
        os.environ['WHATAP_HOME_BATCH'] = batch_home
        os.environ['WHATAP_HOME'] = batch_home
        go(batch=True)


def batch_profiling(fn):
    import inspect
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    
    def trace(*args, **kwargs):
        if not os.environ.get('whatap.batch.enabled'):
            home = 'WHATAP_HOME_BATCH'
            batch_home = read_file(home, home.lower())
            if not batch_home:
                whatap_print(
                    'WHATAP(@batch_profiling): try, whatap-start-batch')
                return fn(*args, **kwargs)
            else:
                os.environ['whatap.batch.enabled'] = 'True'
                os.environ['WHATAP_HOME_BATCH'] = batch_home
                os.environ['WHATAP_HOME'] = batch_home
                config(home)
        
        callback = None
        try:
            ctx = TraceContext()
            ctx.service_name=os.path.basename(module.__file__)
            ctx = start_interceptor(ctx)
            
            callback = fn(*args, **kwargs)
            end_interceptor(thread_id=ctx.thread_id)
        except Exception as e:
            logging.debug('WHATAP(@batch_profiling): ' + str(e),
                          extra={'id': 'WA777'}, exc_info=True)
        finally:
            return callback if callback else fn(*args, **kwargs)
    
    return trace


import os, time
import errno
import sys

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    # fcntl is not available on Windows
    HAS_FCNTL = False
    if sys.platform == 'win32':
        try:
            import msvcrt
            HAS_MSVCRT = True
        except ImportError:
            HAS_MSVCRT = False
    else:
        HAS_MSVCRT = False

# Windows uses different default temp path
if sys.platform == 'win32':
    import tempfile
    default_lock_file = os.path.join(tempfile.gettempdir(), 'whatap-python.lock')
else:
    default_lock_file = '/tmp/whatap-python.lock'

def openPortFile(filepath=os.environ.get('WHATAP_LOCK_FILE', default_lock_file)):
    f = None
    i=0
    while f == None and i < 100:
        try:
            f = open(filepath, 'r+')
        except IOError as e:
            if e.errno == 2:
                prefix = os.path.split(filepath)[0]
                try:
                    if not os.path.exists(prefix):
                        os.makedirs(prefix)
                    f = open(filepath, 'w+')
                except:
                    pass
        i += 1

    if f:
        try:
            if HAS_FCNTL:
                fcntl.lockf(f, fcntl.LOCK_EX)
            elif HAS_MSVCRT:
                # Windows file locking using msvcrt
                try:
                    # Use non-blocking lock to avoid OSError
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError:
                    # File already locked by another process, skip locking
                    pass
            # If no locking mechanism available, proceed without lock
            return f
        except Exception as e:
            whatap_print(e)
            try:
                f.close()
            except:
                pass
    return None

def get_port_number(port=6600, home=os.environ.get('WHATAP_HOME')):
    if not home:
        return None

    for i in range(100):
        f = openPortFile()
        if not f:
            if i > 50:
                time.sleep(0.1)
            continue
    if f:
        lastPortFound = None
        for l in f.readlines():
            l = l.strip()
            try:
                (portFound, portHome) = l.split()
                portFound = int(portFound)
            except:
                continue
            if home == portHome:
                return portFound
            if not lastPortFound or lastPortFound < portFound:
                lastPortFound = int(portFound)
        if not lastPortFound:
            lastPortFound = port
        else:
            lastPortFound += 1
        f.write(str(lastPortFound))
        f.write('\t')
        f.write(home)
        f.write('\n')
        try:
            if HAS_FCNTL:
                fcntl.lockf(f, fcntl.LOCK_UN)
            elif HAS_MSVCRT:
                # Windows file unlocking using msvcrt
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
        except:
            pass
        f.close()
        return lastPortFound
            
    return port


def configPort():
    port = get_port_number()
    if port:
        update_config('WHATAP_HOME', 'net_udp_port', str(port))
        return port


def find_whatap_conf():
    # 1. 현재 디렉토리 검색
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    conf_path = os.path.join(parent_dir, 'whatap.conf')
    if os.path.exists(conf_path):
        os.environ['WHATAP_HOME'] = parent_dir
        return conf_path

    # 2. 상위 디렉토리들 검색
    current = parent_dir
    # Cross-platform root detection: keep going until dirname doesn't change
    while True:
        conf_path = os.path.join(current, 'whatap.conf')
        if os.path.exists(conf_path):
            os.environ['WHATAP_HOME'] = current
            return conf_path
        parent = os.path.dirname(current)
        # Stop at root (Unix: '/', Windows: 'C:\' or similar)
        if parent == current:
            break
        current = parent

    return None