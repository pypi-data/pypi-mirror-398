
codes = {
    200: 'success',
    201: 'Auth failed',
    202: 'Missing Manditory Params',
    203: 'Controller disabled',
    204: 'Scheduling failed',
    205: 'Password Mismatch',
    206: 'Oops Something Went Wrong. Try a new user name.',
    207: 'Username does not exist.',
    208: 'Invalid Param Type Cast',
    209: 'Values in submission must be unique',
    290: 'Api Error'

}


class Response:
    def __init__(self, res=None):
        self.res = dict({'success': True, 'data': {}, 'response_code': 200, 'msg': 'success'})

        if isinstance(res, Response):
            self.data(Response.msg['data'])
            tmp = Response
            tmp.pop('data')
        elif isinstance(res, dict):
            self.res = res

    def method(self, m=False):
        if m:
            self.res['method'] = m
        return self

    def fail(self, err_code):
        self.res['success'] = False
        self.res['response_code'] = err_code
        self.res['msg'] = codes[err_code]
        return self

    def success(self):
        return self.res['success']

    def data(self, data):
        if isinstance(data,list):
            self.res['data'] = dict(**self.res['data'], **{'records': data})
            return self

        if not isinstance(data, dict):
            raise TypeError('data object must be of type dict or list')
            return

        self.res['data'] = dict(**self.res['data'], **data)
        return self

    def msg(self):
        return self.res


class PubResponse(Response):
    def __init__(self, channel, method, res=None):
        Response.__init__(self, res)
        self._channel = channel
        self.all = all

        if isinstance(res, PubResponse):
            self.data(PubResponse.msg['data'])
            tmp = PubResponse
            tmp.pop('data')
        self.res['channel'] = channel
        self.res['method'] = method

    def channel(self):
        return self._channel

    def method(self, method=None):
        if method is None:
            return self._res['method']
        self.res['method'] = method
        return self






