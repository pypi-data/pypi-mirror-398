import datetime
import logging
import traceback

from lesscode_utils.request import get_basic_auth, sync_common_post, sync_common_request


class AirflowUtil:
    def __init__(self, url, username, password):
        self.auth = get_basic_auth(username, password) if username and password else None
        self.url = url

    def run(self, conf):
        headers = {
            'content-type': 'application/json'
        }
        data = {
            "execution_date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f+08:00"),
            "conf": conf
        }
        res = sync_common_post(self.url, json=data, result_type="origin", headers=headers, auth=self.auth)
        return res

    def handle(self, params=None, data=None, json=None, method="post"):
        headers = {
            'content-type': 'application/json'
        }
        try:
            res = sync_common_request(method=method, url=self.url, json=json, data=data, params=params,
                                      result_type="origin", headers=headers, auth=self.auth)
            if res.status_code != 200:
                logging.error(f"Airflow status_code={res.status_code}")
                logging.error(f"Airflow res={res.json()}")
            else:
                return res
        except Exception as e:
            logging.error(traceback.print_stack())


class AirflowUtilV2:
    def __init__(self, base_url, username, password):
        self.auth = get_basic_auth(username, password) if username and password else None
        self.base_url = base_url

    def run(self, path, conf):
        url = self.base_url + path
        headers = {
            'content-type': 'application/json'
        }
        data = {
            "execution_date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f+08:00"),
            "conf": conf
        }
        res = sync_common_post(url, json=data, result_type="origin", headers=headers, auth=self.auth)
        return res

    def handle(self, path, params=None, data=None, json=None, method="post"):
        url = self.base_url + path
        headers = {
            'content-type': 'application/json'
        }
        try:
            res = sync_common_request(method=method, url=url, json=json, data=data, params=params,
                                      result_type="origin", headers=headers, auth=self.auth)
            if res.status_code != 200:
                logging.error(f"Airflow status_code={res.status_code}")
                logging.error(f"Airflow res={res.json()}")
            else:
                return res
        except Exception as e:
            logging.error(traceback.print_stack())
