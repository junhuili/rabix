import docopt
import logging
import sys
import yaml
import six

from os.path import isfile

from rabix import __version__ as version
from rabix.common.errors import RabixError
from rabix.common.loadsave import JsonLoader, from_url
from rabix.common.util import rnd_name, update_config
from rabix.models import Pipeline
from rabix.runtime.engine import get_engine
from rabix.runtime.jobs import RunJob, InstallJob
from rabix.sdktools.steps import run_steps


log = logging.getLogger(__name__)


USAGE = """
Usage:
  rabix build [--config=<cfg_path>]
  rabix checksum [--method=(md5|sha1)] <jsonptr>
  rabix install [-v...] <file>
  rabix run [-v...] <file>
  rabix -h | --help
  rabix --version

Commands:
  build                     Execute steps for app building, wrapping and
                            deployment.
  checksum                  Calculate and print the checksum of json document
                            (or fragment) pointed by <jsonptr>
  install                   Install all the apps needed for running pipeline
                            described in <file>.
  run                       Run pipeline described in <file>. Depending on the
                            pipeline, additional parameters must be provided.

Options:
  -c --config=<cfg_path>    Specify path to config file [default: .rabix.yml]
  -h --help                 Display this message.
  -m --method (md5|sha1)    Checksum type [default: sha1]
  --version                 Print version to standard output and quit.
  -v --verbose              Verbosity. More Vs more output.
"""

RUN_TPL = """
Usage: rabix run [-v...] {pipeline} {arguments}

Options:
  -v --verbose                            Verbosity. More Vs more output.
  {options}
"""


def make_pipeline_usage_string(pipeline, path):
    usage_str, options = [], []
    for inp_id, inp_details in six.iteritems(pipeline.get_inputs()):
        arg = '--%s=<%s_file>%s' % (
            inp_id, inp_id, '...' if inp_details['list'] else ''
        )
        usage_str.append(
            arg if inp_details.get('required', False) else '[%s]' % arg
        )
        options.append('{0: <40}{1}'.format(
            arg, inp_details.get('description', ''))
        )
    return RUN_TPL.format(pipeline=path, arguments=' '.join(usage_str),
                          options='\n  '.join(options))


def before_task(task):
    print('Running %s' % task.task_id)
    sys.stdout.flush()


def present_outputs(outputs):
    header = False
    row_fmt = '{:<20}{:<80}'
    for out_id, file_list in six.iteritems(outputs):
        for path in file_list:
            if not header:
                print(row_fmt.format('Output ID', 'File path'))
                header = True
            print(row_fmt.format(out_id, path))


def set_log_level(v_count):
    if v_count == 0:
        level = logging.WARN
    elif v_count == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG
    logging.root.setLevel(level)


def run(path):
    pipeline = Pipeline.from_app(from_url(path))
    pipeline.validate()
    usage_str = make_pipeline_usage_string(pipeline, path)
    args = docopt.docopt(usage_str, version=version)
    set_log_level(args['--verbose'])
    inputs = {
        i[len('--'):]: args[i]
        for i in args if i.startswith('--') and i != '--verbose'
    }
    job_id = rnd_name()
    job = RunJob(job_id, pipeline, inputs=inputs)
    get_engine(before_task=before_task).run(job)
    present_outputs(job.get_outputs())
    if job.status == RunJob.FAILED:
        print(job.error_message or 'Job failed')
        sys.exit(1)


def install(pipeline):
    pipeline = Pipeline.from_app(pipeline)
    job = InstallJob(rnd_name(), pipeline)
    get_engine(before_task=before_task).run(job)
    if job.status == InstallJob.FAILED:
        print(job.error_message)
        sys.exit(1)


def checksum(jsonptr, method='sha1'):
    loader = JsonLoader()
    obj = loader.load(jsonptr)
    print(method + '$' + loader.checksum(obj, method))


def build(path='.rabix.yml'):
    if not isfile(path):
        raise RabixError('Config file %s not found!' % path)
    with open(path) as cfg:
        config = yaml.load(cfg)
        run_steps(config)


def main():
    logging.basicConfig(level=logging.WARN)
    if isfile('rabix.conf'):
        update_config()

    try:
        args = docopt.docopt(USAGE, version=version)
    except docopt.DocoptExit:
        if len(sys.argv) > 3:
            for a in sys.argv[2:]:
                if not a.startswith('-'):
                    return run(a)
        print(USAGE)
        return
    set_log_level(args['--verbose'])
    if args["run"]:
        pipeline_path = args['<file>']
        pipeline = Pipeline.from_app(from_url(pipeline_path))
        pipeline.validate()
        print(make_pipeline_usage_string(pipeline, pipeline_path))
    elif args["install"]:
        install(from_url(args['<file>']))
    elif args["checksum"]:
        checksum(args['<jsonptr>'], args['--method'])
    elif args["build"]:
        build(args.get("--config"))


if __name__ == '__main__':
    main()
