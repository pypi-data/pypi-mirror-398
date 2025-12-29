import logging
import warnings
import os
from multiprocessing import cpu_count
import numba
from numba.core.errors import NumbaPerformanceWarning

logger = logging.getLogger(__name__)


def numba_setup() -> None:
    """This function sets defaults for environmental variables and numba
    parameters to achieve a balanced performance for most situations.
    Advanced users may want to customize these parameters.
    """

    # This is a relatively useless and very verbose and frequent warning.
    warnings.filterwarnings('ignore', category=NumbaPerformanceWarning)

    try:
        number_of_cpus = len(os.sched_getaffinity(os.getpid()))
    except AttributeError:
        logger.info('Using multiprocessing.cpu_count() to determine the number of availible CPUs.')
        number_of_cpus = cpu_count()
    if number_of_cpus >= 8:
        number_of_threads = 8
    else:
        number_of_threads = number_of_cpus
    logger.info(f'Setting the number of threads to {number_of_threads}. '
                'If your physical cores are fewer than this number, '
                'you may want to use numba.set_num_threads(n), '
                'and os.environ["OPENBLAS_NUM_THREADS"] = f"{n}" '
                'to set the number of threads to the number of '
                'physical cores n.')
    numba.set_num_threads(number_of_threads)
    os.environ['OPENBLAS_NUM_THREADS'] = f'{number_of_threads}'

    # numba.cuda has a very high output of `INFO`-level messages.
    numba_logger = logging.getLogger('numba')
    numba_logger.setLevel(logging.WARNING)
    logger.info('Setting numba log level to WARNING.')
