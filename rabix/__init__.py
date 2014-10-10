__version__ = '0.4.0'

CONFIG = {
    'engine': {
        'class': 'rabix.runtime.engine.base.MultiprocessingEngine',
        'ram_mb': 2*1024,
    },
    'runners': {
        'InputTask': 'rabix.runtime.builtins.io.InputRunner',
        'OutputTask': 'rabix.runtime.tasks.Runner',
        'AppInstallTask': {
            'app/mock/python': 'rabix.runtime.tasks.Runner',
            'app/tool/docker': 'rabix.runtime.builtins.dockr.DockerAppInstaller',
            'app/tool/docker-wrapper': 'rabix.runtime.builtins.dockr.DockerAppInstaller',
        },
        'PipelineStepTask': {
            'app/mock/python': 'rabix.runtime.builtins.mocks.MockRunner',
            'app/tool/docker': 'rabix.runtime.builtins.dockr.DockerRunner',
            'app/tool/docker-wrapper': 'rabix.runtime.builtins.dockr.DockerWrapperRunner',
        }
    },
    'docker': {},
    'nodes': [{'node_id': 'some-id', 'ram_mb': 2*1024, 'cpu': 1}],
    'redis': {'host': 'localhost', 'port': 6379, 'password': None}
}

from rabix.common.protocol import MAPPINGS
from rabix.common.loadsave import from_url, to_json
try:
    from rabix.models import Pipeline, AppSchema, AppJsonSchema
    from rabix.runtime.builtins.dockr import DockerApp, DockerWrapperApp
    from rabix.runtime.builtins.mocks import MockApp
    MAPPINGS.update({
        'app/mock/python': MockApp,
        'app/pipeline': Pipeline,
        'app/tool/docker': DockerApp,
        'app/tool/docker-wrapper': DockerWrapperApp,
        'schema/app/sbgsdk': AppSchema,
        'schema/app': AppJsonSchema,
    })
except ImportError:
    pass
