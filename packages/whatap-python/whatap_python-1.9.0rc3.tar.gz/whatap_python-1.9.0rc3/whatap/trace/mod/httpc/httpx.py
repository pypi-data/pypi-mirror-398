from whatap.trace.mod.application.wsgi import transfer, trace_handler, \
    interceptor_httpc_request


def instrument_httpx(module):
    def wrapper(fn):
        @trace_handler(fn)
        def trace(*args, **kwargs):
            if len(args) >= 2 and hasattr(args[1], 'headers') and hasattr(args[1], 'url'):
                request = args[1]
                request.headers = transfer(request.headers)
                httpc_url = str(request.url)

            # 2. stream call: send(request=request, ...)
            elif len(args) == 1 and 'request' in kwargs:
                request = kwargs['request']
                if hasattr(request, 'headers') and hasattr(request, 'url'):
                    request.headers = transfer(request.headers)
                    httpc_url = str(request.url)
                else:
                    httpc_url = "invalid_request_object"

            # 3. 예상치 못한 패턴
            else:
                httpc_url = "httpx_unknown_pattern"

            return interceptor_httpc_request(fn, httpc_url, *args, **kwargs)

        return trace

    if hasattr(module, 'Client') and hasattr(module.Client, 'send'):
        module.Client.send = wrapper(module.Client.send)


    if hasattr(module, 'AsyncClient') and hasattr(module.AsyncClient, 'send'):
        module.AsyncClient.send = wrapper(module.AsyncClient.send)