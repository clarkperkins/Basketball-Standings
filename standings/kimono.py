from urllib import urlencode

import requests
import json

KIMONO_URL = 'https://www.kimonolabs.com/api{2}/{0}?{1}'
VALID_TYPES = ('json', 'csv', 'rss')


class InvalidDataType(TypeError):
    pass


class DataError(SystemError):
    pass


class KimonoClient(object):
    """
    A generic client to use with kimonolabs APIs
    """
    def __init__(self, api_id, api_key):
        super(KimonoClient, self).__init__()
        self.api_id = api_id
        self.api_key = api_key

    def _do_get(self, params, extra=''):
        if params is None:
            params = {}

        # Add in the apikey
        params['apikey'] = self.api_key
        # params['kimmodify'] = 1

        # urlencode everything
        keys = sorted(params)
        values = list(map(params.get, keys))
        querystring = urlencode(list(zip(keys, values)))

        # Make the request
        r = requests.get(
            KIMONO_URL.format(self.api_id, querystring, extra),
            headers={'Accept': 'application/json'}
        )

        try:
            ret = r.json()

            if ret.get('status') == 'Error':
                raise DataError(ret['error'])
            return ret['results']
        except ValueError:
            raise DataError(r.text)
        except KeyError:
            print r.text
            return {}

    def get(self, params=None):
        return self._do_get(params)

    def get_fresh(self, params=None):
        return self._do_get(params, '/ondemand')