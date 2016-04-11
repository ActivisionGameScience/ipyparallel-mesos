import time
import os
import json

from traitlets import (
    Any, Integer, CFloat, List, Unicode, Dict, Instance, HasTraits, CRegExp
)
import requests

from ipyparallel.apps.launcher import BaseLauncher, ControllerMixin, EngineMixin 


class MarathonLauncher(BaseLauncher):
    raw_marathon_api_url = '{}/v2/apps/{}' 
    base_marathon_config = {
        'mem': 1024,
        'env': {},
        'instances': 1,
        'container': {
            'docker': {
                'image': '',
                'forcePullImage': True
            },
            'type': 'DOCKER'},
        'cpus': 0.9,
        'id': ''
    }

    marathon_api = Unicode('', config=True,
        help="host and port for marathon api")
        
    controller_marathon_app_group = Unicode('', config=True,
        help="Marathon application id path")

    controller_app_name = 'controller'

    controller_config_port = Unicode('1235', config=True,
        help="Port controller exposes to share client/engine configs")

    controller_docker_image = Unicode('', config=True,
        help="Docker image of controller to launch")

    engine_docker_image = Unicode('', config=True,
        help="Docker image of engine to launch")


    @property
    def controller_marathon_id(self):
        return '{}{}'.format(self.controller_marathon_app_group, self.controller_app_name)

    @property
    def controller_marathon_url(self):
        return '{}/v2/apps/{}'.format(self.marathon_api, self.controller_marathon_id)

    def __init__(self, work_dir=u'.', config=None, **kwargs):
        super(MarathonLauncher, self).__init__(
            work_dir=work_dir, config=config, **kwargs
        )
        assert self.marathon_api, "marathon_api is required"
        assert self.controller_marathon_app_group, "controller_marathon_id is required"
        
    def _wait_for_marathon_app_to_start(self, app_url, tries=20, sleep=0.5):
        for i in range(tries):
            app_resp = requests.get(app_url)
            if app_resp.ok:
                app_info = app_resp.json()
                if app_info['app']['instances'] == app_info['app']['tasksRunning']:
                    return app_info 
            time.sleep(sleep)
        raise RuntimeError("Marathon App did not start correctly")


class MarathonControllerLauncher(MarathonLauncher):
    """Docstring for M. """

    def find_args(self):
        return self.marathon_api + self.controller_marathon_id

    def start(self):
        marathon_config = self._build_marathon_config()
        controller = self._start_marathon_app(marathon_config)
        self.notify_start(controller['app']['tasks'][0]['id'])
        self._write_client_connection_dict(controller)

    def _write_client_connection_dict(self, controller):
        controller_config_url = 'http://{}:{}/ipcontroller-client.json'.format(controller['app']['tasks'][0]['host'], self.controller_config_port)
        # HACKY RETRY FIX
        for i in range(10):
            try:
                resp = requests.get(controller_config_url)
                if resp.ok:
                    return self._save_connection_dict(resp.json())
                time.sleep(0.2)
            except requests.exceptions.ConnectionError:
                time.sleep(0.2)
        raise RuntimeError("Failed to write client connection dict")


    def _save_connection_dict(self, connection_dict):
        fname = 'ipcontroller-client.json'
        fname = os.path.join(self.profile_dir, 'security', fname)
        self.log.info("writing connection info to %s", fname)
        with open(fname, 'w') as f:
            f.write(json.dumps(connection_dict, indent=2))

    def stop(self):
        self._stop_marathon_app(self.controller_marathon_id)
        self.notify_stop(self)

    def _start_marathon_app(self, marathon_config):
        full_marathon_api = self.raw_marathon_api_url.format(self.marathon_api, '')
        res = requests.post(full_marathon_api, json=marathon_config)
        assert res.ok, res.json()
        return self._wait_for_controller_to_start()

    def _wait_for_controller_to_start(self):
        return self._wait_for_marathon_app_to_start(self.controller_marathon_url)

    def _stop_marathon_app(self, application_id):
        full_marathon_api = self.raw_marathon_api_url.format(self.marathon_api, application_id)
        res = requests.delete(full_marathon_api)
        assert res.ok, res.json()

    def _build_marathon_config(self):
        marathon_config = self.base_marathon_config.copy()
        marathon_config['id'] = self.controller_marathon_id
        marathon_config['container']['docker']['network'] = 'HOST'
        marathon_config['container']['docker']['image'] = self.controller_docker_image
        marathon_config['env'] = {
            'CONTROLLER_CONFIG_PORT': self.controller_config_port
        }
        return marathon_config


class MarathonEngineLauncher(MarathonLauncher):
    """Docstring for M. """
    engine_app_name = 'engine'

    @property
    def engine_marathon_id(self):
        return '{}{}'.format(self.controller_marathon_app_group, self.engine_app_name)

    @property
    def engine_marathon_url(self):
        return '{}/v2/apps/{}'.format(self.marathon_api, self.engine_marathon_id)

    def find_args(self):
        return self.marathon_api + self.engine_marathon_id

    def start(self, n):
        marathon_config = self._build_marathon_config(n)
        self._start_marathon_app(marathon_config)
        engines = self._wait_for_engines_to_start()
        for task in engines['app']['tasks']:
            self.notify_start(task['id'])

    def stop(self):
        self._stop_marathon_app(self.engine_marathon_id)
        self.notify_stop(self)

    def _wait_for_engines_to_start(self):
        return self._wait_for_marathon_app_to_start(self.engine_marathon_url)

    def _start_marathon_app(self, marathon_config):
        full_marathon_api = self.raw_marathon_api_url.format(self.marathon_api, '')
        res = requests.post(full_marathon_api, json=marathon_config)
        assert res.ok, res.json()
        return res.json()

    def _stop_marathon_app(self, application_id):
        full_marathon_api = self.raw_marathon_api_url.format(self.marathon_api, application_id)
        res = requests.delete(full_marathon_api)
        assert res.ok, res.json()

    def _build_marathon_config(self, n=1):
        assert self.engine_docker_image, "engine_docker_image is required"

        marathon_config = self.base_marathon_config.copy()
        marathon_config['id'] = self.engine_marathon_id
        marathon_config['instances'] = n
        marathon_config['container']['docker']['image'] = self.engine_docker_image
        marathon_config['env'] = {
            'MARATHON_MASTER': self.marathon_api,
            'CONTROLLER_MARATHON_ID': self.controller_marathon_id,
            
        }
        return marathon_config
