__version__ = "0.74.0"

from rdworks.conf import Conf
from rdworks.mol import Mol
from rdworks.mollibr import MolLibr
from rdworks.microstate import State, StateEnsemble, StateNetwork
from rdworks.matchedseries import MatchedSeries

import rdkit
import logging

__rdkit_version__ = rdkit.rdBase.rdkitVersion
rdkit_logger = rdkit.RDLogger.logger().setLevel(rdkit.RDLogger.CRITICAL)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # level: DEBUG < INFO < WARNING < ERROR < CRITICAL

logger_stream = logging.StreamHandler()  # sys.stdout or sys.stderr
logger_format = logging.Formatter(
    fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger_stream.setFormatter(logger_format)
logger.addHandler(logger_stream)
