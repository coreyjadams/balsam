import os
import sys
import time
import subprocess
from importlib.util import find_spec

from balsam.service.models import BalsamJob
from tests.BalsamTestCase import BalsamTestCase
from tests.BalsamTestCase import create_job, create_app

from tests import util
    
class TestInsertion(BalsamTestCase):
    def setUp(self):
        from itertools import takewhile, product

        hello = find_spec("tests.benchmarks.concurrent_insert.hello").origin
        create_app(name="hello", executable=hello)
        self.launcherInfo = util.launcher_info()
        
        max_workers = self.launcherInfo.num_workers
        worker_counts = takewhile(lambda x: x<=max_workers, (2**i for i in range(20)))
        ranks_per_node = [4, 8, 16, 32]
        self.experiments = list(product(worker_counts, ranks_per_node))

    def test_concurrent_mpi_insert(self):
        '''Timing: many MPI ranks simultaneously call dag.add_job'''
        resultpath = os.path.join(util.DATA_DIR, 'concurrent_insert.dat')

        title = 'test_concurrent_mpi_insert'
        comment = 'Each rank simultaneously calls dag.add_job (num_ranks simultaneous insertions)'
        resultTable = util.FormatTable(
            'num_nodes ranks_per_node num_ranks total_time_sec'.split()
        )

        python = sys.executable
        insert_app = find_spec("tests.benchmarks.concurrent_insert.mpi_insert").origin

        for (num_nodes, rpn) in self.experiments:
            BalsamJob.objects.all().delete()

            total_ranks = num_nodes * rpn

            app_cmd = f"{python} {insert_app}"
            mpi_str = self.launcherInfo.mpi_cmd(
                self.launcherInfo.workerGroup.workers,
                app_cmd=app_cmd,
                envs={},
                num_ranks=total_ranks,
                ranks_per_node=rpn,
                threads_per_rank=1,
                threads_per_core=1
            )
            cmdline = f"time -p ( {mpi_str} )"
            stdout, elapsed_time = util.cmdline(cmdline)
            
            success = list(l for l in stdout.split('\n') if 'added job: success' in l)
            self.assertEqual(len(success), total_ranks)
            self.assertEqual(BalsamJob.objects.count(), total_ranks)

            resultTable.add_row(num_nodes=num_nodes, ranks_per_node=rpn,
                                num_ranks=total_ranks,
                                total_time_sec=elapsed_time
                                )
        
            with open(resultpath, 'w') as fp:
                fp.write(resultTable.generate(title, comment))
