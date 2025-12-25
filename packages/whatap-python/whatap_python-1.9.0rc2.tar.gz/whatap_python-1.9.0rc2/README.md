# Whatap Python Agent
    


## 에이전트 구조


- [디렉토리 구조 및 개발환경](./docs/development-environment)
- [Python 에이전트의 실행 구조 및 통신 흐름 이해](./docs/agent-architecture)
- [Python 에이전트의 배포](./docs/how-to-release)



## 에이전트 프로세스


- [Python 에이전트의 초기화 작업](./docs/agent-process/0.%20Initialize)
- [Python 에이전트의 모듈 후킹](./docs/agent-process/1.%20hooking)
- [Python 에이전트의 카운터 스레드 작동 과정](./docs/agent-process/2.%20counter-thread)
- [Python 에이전트의 데이터 전송 과정](./docs/agent-process/3.%20udp-communication)



## 확인 및 검증이 필요한 부분

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unsupported web frameworks WSGI

If you want WSGI Application monitoring, include the @register_app decorator.

  .. code:: python

    import whatap

    @whatap.register_app
    def simple_app(environ, start_response):
    """Simplest possible application object"""
        status = '200 OK'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return ['Hello world!\n']



~~~~~~~~~~~~~~~~
Method Profiling

If you want method profiling, include the @method_profiling decorator.

  .. code:: python

    from whatap import method_profiling

    @method_profiling
    def db_connection():
        db.connect('mysql:// ..')

    @method_profiling
    def query():
        db.select('select * from ..')

      ....

Batch Monitoring
----------------

for Batch job.

Configuration
~~~~~~~~~~~~~

Set Environment valiable configuration.

  .. code:: bash

    $ export WHATAP_BATCH_HOME=[PATH]
    $ cat >> $WHATAP_BATCH_HOME/whatap.conf << EOF
    license=[LICENSE_KEY]
    whatap.server.host=[HOST_ADDR]

    app_name=batch
    app_process_name=batch
    EOF


Usage
~~~~~

Start bach agent.

  .. code:: bash

    $ whatap-start-batch

Example code
~~~~~~~~~~~~

  .. code:: python

    from whatap import method_profiling

    class Command(BaseCommand):

        @batch_profiling
        def handle(self, *args, **options):
            // batch code..
            ....

Restart
-------

Your Application restart.