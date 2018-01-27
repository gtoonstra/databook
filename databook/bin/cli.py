#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import logging
import argparse
import os
import subprocess
import textwrap
import signal
import psutil
import time
import sys

from collections import namedtuple
from dateutil.parser import parse as parsedate
from databook import configuration as conf
from databook import settings
from databook.www.app import cached_app
from databook.utils.logging_mixin import LoggingMixin


log = LoggingMixin().log


Arg = namedtuple(
    'Arg', ['flags', 'help', 'action', 'default', 'nargs', 'type', 'choices', 'metavar'])
Arg.__new__.__defaults__ = (None, None, None, None, None, None, None)


def setup_locations(process, pid=None, stdout=None, stderr=None, log=None):
    if not stderr:
        stderr = os.path.join(os.path.expanduser(settings.DATABOOK_HOME), "databook-{}.err".format(process))
    if not stdout:
        stdout = os.path.join(os.path.expanduser(settings.DATABOOK_HOME), "databook-{}.out".format(process))
    if not log:
        log = os.path.join(os.path.expanduser(settings.DATABOOK_HOME), "databook-{}.log".format(process))
    if not pid:
        pid = os.path.join(os.path.expanduser(settings.DATABOOK_HOME), "databook-{}.pid".format(process))

    return pid, stdout, stderr, log


def restart_workers(gunicorn_master_proc, num_workers_expected):
    """
    Runs forever, monitoring the child processes of @gunicorn_master_proc and
    restarting workers occasionally.

    Each iteration of the loop traverses one edge of this state transition
    diagram, where each state (node) represents
    [ num_ready_workers_running / num_workers_running ]. We expect most time to
    be spent in [n / n]. `bs` is the setting webserver.worker_refresh_batch_size.

    The horizontal transition at ? happens after the new worker parses all the
    dags (so it could take a while!)

       V ────────────────────────────────────────────────────────────────────────┐
    [n / n] ──TTIN──> [ [n, n+bs) / n + bs ]  ────?───> [n + bs / n + bs] ──TTOU─┘
       ^                          ^───────────────┘
       │
       │      ┌────────────────v
       └──────┴────── [ [0, n) / n ] <─── start

    We change the number of workers by sending TTIN and TTOU to the gunicorn
    master process, which increases and decreases the number of child workers
    respectively. Gunicorn guarantees that on TTOU workers are terminated
    gracefully and that the oldest worker is terminated.
    """

    def wait_until_true(fn):
        """
        Sleeps until fn is true
        """
        while not fn():
            time.sleep(0.1)

    def get_num_workers_running(gunicorn_master_proc):
        workers = psutil.Process(gunicorn_master_proc.pid).children()
        return len(workers)

    def start_refresh(gunicorn_master_proc):
        batch_size = conf.getint('webserver', 'worker_refresh_batch_size')
        log.debug('%s doing a refresh of %s workers', state, batch_size)
        sys.stdout.flush()
        sys.stderr.flush()

        excess = 0
        for _ in range(batch_size):
            gunicorn_master_proc.send_signal(signal.SIGTTIN)
            excess += 1
            wait_until_true(lambda: num_workers_expected + excess ==
                                    get_num_workers_running(gunicorn_master_proc))

    wait_until_true(lambda: num_workers_expected ==
                            get_num_workers_running(gunicorn_master_proc))

    while True:
        num_workers_running = get_num_workers_running(gunicorn_master_proc)
        num_ready_workers_running = get_num_ready_workers_running(gunicorn_master_proc)

        state = '[{0} / {1}]'.format(num_ready_workers_running, num_workers_running)

        # Whenever some workers are not ready, wait until all workers are ready
        if num_ready_workers_running < num_workers_running:
            log.debug('%s some workers are starting up, waiting...', state)
            sys.stdout.flush()
            time.sleep(1)

        # Kill a worker gracefully by asking gunicorn to reduce number of workers
        elif num_workers_running > num_workers_expected:
            excess = num_workers_running - num_workers_expected
            log.debug('%s killing %s workers', state, excess)

            for _ in range(excess):
                gunicorn_master_proc.send_signal(signal.SIGTTOU)
                excess -= 1
                wait_until_true(lambda: num_workers_expected + excess ==
                                        get_num_workers_running(gunicorn_master_proc))

        # Start a new worker by asking gunicorn to increase number of workers
        elif num_workers_running == num_workers_expected:
            refresh_interval = conf.getint('webserver', 'worker_refresh_interval')
            log.debug(
                '%s sleeping for %ss starting doing a refresh...',
                state, refresh_interval
            )
            time.sleep(refresh_interval)
            start_refresh(gunicorn_master_proc)

        else:
            # num_ready_workers_running == num_workers_running < num_workers_expected
            log.error((
                "%s some workers seem to have died and gunicorn"
                "did not restart them as expected"
            ), state)
            time.sleep(10)
            if len(
                psutil.Process(gunicorn_master_proc.pid).children()
            ) < num_workers_expected:
                start_refresh(gunicorn_master_proc)


def get_num_ready_workers_running(gunicorn_master_proc):
    workers = psutil.Process(gunicorn_master_proc.pid).children()

    def ready_prefix_on_cmdline(proc):
        try:
            cmdline = proc.cmdline()
            if len(cmdline) > 0:
                return settings.GUNICORN_WORKER_READY_PREFIX in cmdline[0]
        except psutil.NoSuchProcess:
            pass
        return False

    ready_workers = [proc for proc in workers if ready_prefix_on_cmdline(proc)]
    return len(ready_workers)


def webserver(args):
    print(settings.HEADER)

    app = cached_app(conf)
    access_logfile = args.access_logfile or conf.get('webserver', 'access_logfile')
    error_logfile = args.error_logfile or conf.get('webserver', 'error_logfile')
    num_workers = args.workers or conf.get('webserver', 'workers')
    worker_timeout = (args.worker_timeout or
                      conf.get('webserver', 'web_server_worker_timeout'))
    ssl_cert = args.ssl_cert or conf.get('webserver', 'web_server_ssl_cert')
    ssl_key = args.ssl_key or conf.get('webserver', 'web_server_ssl_key')
    if not ssl_cert and ssl_key:
        raise DatabookException(
            'An SSL certificate must also be provided for use with ' + ssl_key)
    if ssl_cert and not ssl_key:
        raise DatabookException(
            'An SSL key must also be provided for use with ' + ssl_cert)

    if args.debug:
        print(
            "Starting the web server on port {0} and host {1}.".format(
                args.port, args.hostname))
        app.run(debug=True, port=args.port, host=args.hostname,
                ssl_context=(ssl_cert, ssl_key) if ssl_cert and ssl_key else None)
    else:
        pid, stdout, stderr, log_file = setup_locations("webserver", args.pid, args.stdout, args.stderr, args.log_file)
        if args.daemon:
            handle = setup_logging(log_file)
            stdout = open(stdout, 'w+')
            stderr = open(stderr, 'w+')

        print(
            textwrap.dedent('''\
                Running the Gunicorn Server with:
                Workers: {num_workers} {args.workerclass}
                Host: {args.hostname}:{args.port}
                Timeout: {worker_timeout}
                Logfiles: {access_logfile} {error_logfile}
                =================================================================\
            '''.format(**locals())))

        run_args = [
            'gunicorn',
            '-w', str(num_workers),
            '-k', str(args.workerclass),
            '-t', str(worker_timeout),
            '-b', args.hostname + ':' + str(args.port),
            '-n', 'databook-webserver',
            '-p', str(pid),
            '-c', 'python:databook.www.gunicorn_config'
        ]

        if args.access_logfile:
            run_args += ['--access-logfile', str(args.access_logfile)]

        if args.error_logfile:
            run_args += ['--error-logfile', str(args.error_logfile)]

        if args.daemon:
            run_args += ['-D']

        if ssl_cert:
            run_args += ['--certfile', ssl_cert, '--keyfile', ssl_key]

        run_args += ["databook.www.app:cached_app()"]

        gunicorn_master_proc = None

        def kill_proc(dummy_signum, dummy_frame):
            gunicorn_master_proc.terminate()
            gunicorn_master_proc.wait()
            sys.exit(0)

        def monitor_gunicorn(gunicorn_master_proc):
            # These run forever until SIG{INT, TERM, KILL, ...} signal is sent
            if conf.getint('webserver', 'worker_refresh_interval') > 0:
                restart_workers(gunicorn_master_proc, num_workers)
            else:
                while True:
                    time.sleep(1)

        if args.daemon:
            base, ext = os.path.splitext(pid)
            ctx = daemon.DaemonContext(
                pidfile=TimeoutPIDLockFile(base + "-monitor" + ext, -1),
                files_preserve=[handle],
                stdout=stdout,
                stderr=stderr,
                signal_map={
                    signal.SIGINT: kill_proc,
                    signal.SIGTERM: kill_proc
                },
            )
            with ctx:
                subprocess.Popen(run_args, close_fds=True)

                # Reading pid file directly, since Popen#pid doesn't
                # seem to return the right value with DaemonContext.
                while True:
                    try:
                        with open(pid) as f:
                            gunicorn_master_proc_pid = int(f.read())
                            break
                    except IOError:
                        log.debug("Waiting for gunicorn's pid file to be created.")
                        time.sleep(0.1)

                gunicorn_master_proc = psutil.Process(gunicorn_master_proc_pid)
                monitor_gunicorn(gunicorn_master_proc)

            stdout.close()
            stderr.close()
        else:
            gunicorn_master_proc = subprocess.Popen(run_args, close_fds=True)

            signal.signal(signal.SIGINT, kill_proc)
            signal.signal(signal.SIGTERM, kill_proc)

            monitor_gunicorn(gunicorn_master_proc)


class CLIFactory(object):
    args = {
        # Shared
        'pid': Arg(
            ("--pid",), "PID file location",
            nargs='?'),
        'daemon': Arg(
            ("-D", "--daemon"), "Daemonize instead of running "
                                "in the foreground",
            "store_true"),
        'stderr': Arg(
            ("--stderr",), "Redirect stderr to this file"),
        'stdout': Arg(
            ("--stdout",), "Redirect stdout to this file"),
        'log_file': Arg(
            ("-l", "--log-file"), "Location of the log file"),
        # webserver
        'port': Arg(
            ("-p", "--port"),
            default=conf.get('webserver', 'WEB_SERVER_PORT'),
            type=int,
            help="The port on which to run the server"),
        'ssl_cert': Arg(
            ("--ssl_cert",),
            default=conf.get('webserver', 'WEB_SERVER_SSL_CERT'),
            help="Path to the SSL certificate for the webserver"),
        'ssl_key': Arg(
            ("--ssl_key",),
            default=conf.get('webserver', 'WEB_SERVER_SSL_KEY'),
            help="Path to the key to use with the SSL certificate"),
        'workers': Arg(
            ("-w", "--workers"),
            default=conf.get('webserver', 'WORKERS'),
            type=int,
            help="Number of workers to run the webserver on"),
        'workerclass': Arg(
            ("-k", "--workerclass"),
            default=conf.get('webserver', 'WORKER_CLASS'),
            choices=['sync', 'eventlet', 'gevent', 'tornado'],
            help="The worker class to use for Gunicorn"),
        'worker_timeout': Arg(
            ("-t", "--worker_timeout"),
            default=conf.get('webserver', 'WEB_SERVER_WORKER_TIMEOUT'),
            type=int,
            help="The timeout for waiting on webserver workers"),
        'hostname': Arg(
            ("-hn", "--hostname"),
            default=conf.get('webserver', 'WEB_SERVER_HOST'),
            help="Set the hostname on which to run the web server"),
        'debug': Arg(
            ("-d", "--debug"),
            "Use the server that ships with Flask in debug mode",
            "store_true"),
        'access_logfile': Arg(
            ("-A", "--access_logfile"),
            default=conf.get('webserver', 'ACCESS_LOGFILE'),
            help="The logfile to store the webserver access log. Use '-' to print to "
                 "stderr."),
        'error_logfile': Arg(
            ("-E", "--error_logfile"),
            default=conf.get('webserver', 'ERROR_LOGFILE'),
            help="The logfile to store the webserver error log. Use '-' to print to "
                 "stderr."),
    }
    subparsers = (
        {
            'func': webserver,
            'help': "Start the databook webserver instance",
            'args': ('port', 'workers', 'workerclass', 'worker_timeout', 'hostname',
                     'pid', 'daemon', 'stdout', 'stderr', 'access_logfile',
                     'error_logfile', 'log_file', 'ssl_cert', 'ssl_key', 'debug'),
        },
    )
    subparsers_dict = {sp['func'].__name__: sp for sp in subparsers}

    @classmethod
    def get_parser(cls, dag_parser=False):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(
            help='sub-command help', dest='subcommand')
        subparsers.required = True

        subparser_list = cls.dag_subparsers if dag_parser else cls.subparsers_dict.keys()
        for sub in subparser_list:
            sub = cls.subparsers_dict[sub]
            sp = subparsers.add_parser(sub['func'].__name__, help=sub['help'])
            for arg in sub['args']:
                if 'dag_id' in arg and dag_parser:
                    continue
                arg = cls.args[arg]
                kwargs = {
                    f: getattr(arg, f)
                    for f in arg._fields if f != 'flags' and getattr(arg, f)}
                sp.add_argument(*arg.flags, **kwargs)
            sp.set_defaults(func=sub['func'])
        return parser


def get_parser():
    return CLIFactory.get_parser()
