from __future__ import annotations

import configparser
import contextlib
import glob
import importlib
import logging
import os
from datetime import datetime
from numbers import Number
from typing import Any

# import dct.dct_launch as dct_launch
import numpy as np

try:
    from esrf_pathlib import ESRFPath as Path
except ImportError:
    from pathlib import Path
try:
    from esrf_loadFile import loadFile
except ImportError:
    from esrf_statusgui.data_managment.loadFile import loadFile
from tqdm import tqdm

from esrf_statusgui.data_managment.dct_parameter import dct_parameter
from esrf_statusgui.exp_methods.dct.gtFsimCheckMissingGrains import (
    gtFsimCheckMissingGrains,
)
from esrf_statusgui.exp_methods.MasterClass_Status import Experiment, Status

logger = logging.getLogger(__name__)
# dev:
# logging.basicConfig(level=logging.DEBUG)
# prod:
logging.basicConfig(level=logging.INFO)


class dct_status(Experiment):
    def __init__(self, dpath: Path):
        super().__init__()
        self.main_path = Path(dpath)
        if not self.main_path.exists():
            self.components = []
            return
        if not (self.main_path / "parameters.h5").exists():
            if (self.main_path / "parameters.mat").exists():
                logging.warning("No parameters.h5 file found")
                # [
                #     os.path.abspath(dct_launch.__file__),
                #     "matlab_script",
                #     "skip_functions_check",
                #     "--script",
                #     f"cd('{self.main_path}');p=gtLoadParameters;gtSaveParameters(p);exit",
                # ]
                # try:
                #     launcher = dct_launch.DCTLauncher(command)
                #     launcher.run()
                # except:
                #     logging.error("Parameters and DB convertion to h5 did not work")
        else:
            if not (self.main_path / "DB.h5").exists():
                logging.warning("No DB.h5 file found")
                # [
                #     os.path.abspath(dct_launch.__file__),
                #     "matlab_script",
                #     "-v",
                #     "13",
                #     "skip_functions_check",
                #     "--script",
                #     f"convertDB('{self.main_path}');exit",
                # ]
                # try:
                #     launcher = dct_launch.Launcher(command)
                #     launcher.run()
                # except:
                #     logging.error("DB convertion to h5 did not work")

        self.name = self.main_path.parts[-1]
        self.parameters = Parameters(self.main_path / "parameters.h5")
        self.db = DataBase(self.main_path / "DB.h5", self.parameters)
        self.raw = RawData(self.parameters, self.db)
        self.pp = PreProcessed(self.parameters, self.db)
        self.seg = Segmentation(self.parameters, self.db)
        self.pairMatch = PairMatch(self.parameters, self.db)
        self.indexing = Indexing(self.parameters, self.db)
        self.fwdSim = ForwardSim(self.parameters, self.db)
        self.grainsRecon = GrainsReconstruction(self.parameters, self.db)
        self.assembleVolume = AssembleVolume(self.parameters, self.db)
        self.components = [
            (self.parameters, [], "Parameters"),
            (self.db, [], "Database"),
            (self.raw, [], "Setup H5"),
            (self.pp, [self.raw], "Pre-processing"),
            (self.seg, [], "Segmentation"),
            (self.pairMatch, [], "Pair matching"),
            (self.indexing, [self.pairMatch], "Indexing"),
            (self.fwdSim, [self.indexing], "Forward simulation"),
            (self.grainsRecon, [], "Grains reconstruction"),
            (self.assembleVolume, [], "Assembled volumes"),
        ]


class Parameters(Status):
    def __init__(self, main_path: Path | None = None):
        super().__init__()
        if main_path is None:
            main_path = Path.cwd() / "parameters.h5"
        if not hasattr(self, "acq"):
            try:
                parameters_data = dct_parameter(main_path)
            except Exception:
                logger.exception(
                    "Failed to load parameters from %s, falling back to defaults",
                    main_path,
                )
                parameters_data = dct_parameter()
                self.problem_list.append("Empty parameters in parameters.h5 file")
            for key, value in vars(
                parameters_data
            ).items():  # Dynamically add all attributes
                setattr(self, key, value)

    def loadStatusFiles(self):
        super().loadStatusFiles()
        self.statusFilesLaunched = True
        self.statusDetailedLaunched = True
        if not self.acq.energy():
            self.problem_list.append("Empty parameters in parameters.h5 file")
        else:
            self.filesOk = True
            self.detailedOK = True
            self.details.append(
                f"Found a parameters file...\n  Dataset name is {self.acq.name()}"
            )


class DataBase(Status):
    _SQL_DEFAULTS = {
        "host": "graindb.esrf.fr",
        "user": "gtadmin",
        "password": "gtadmin",
        "database": "graintracking",
        "port": 3306,
    }
    _SQL_ENV_MAP = {
        "host": ("STATUSGUI_SQL_HOST", "MYSQL_HOST", "GT_DB_HOST"),
        "port": ("STATUSGUI_SQL_PORT", "MYSQL_TCP_PORT"),
        "user": ("STATUSGUI_SQL_USER", "MYSQL_USER", "GT_DB_USER"),
        "password": (
            "STATUSGUI_SQL_PASSWORD",
            "MYSQL_PWD",
            "MYSQL_PASSWORD",
            "GT_DB_PASSWORD",
        ),
        "database": (
            "STATUSGUI_SQL_DATABASE",
            "MYSQL_DATABASE",
            "MYSQL_DB",
            "GT_DB_NAME",
        ),
        "unix_socket": ("STATUSGUI_SQL_SOCKET", "MYSQL_UNIX_PORT"),
    }
    _SQL_CNF_ENV = "STATUSGUI_SQL_CNF"
    _SQL_CNF_SECTION_ENV = "STATUSGUI_SQL_CNF_SECTION"
    _SQL_CNF_DEFAULT_SECTION = "client"
    _SQL_DEFAULT_CNF_LOCATIONS = (
        Path.home() / ".my.cnf",
        Path.home() / ".mysql.cnf",
    )
    _SQL_CONNECTOR_ORDER = (
        "mysql.connector",
        "pymysql",
        "MySQLdb",
    )
    _SQL_ALCHEMY_DIALECTS = (
        ("mysql+mysqlconnector", "mysql.connector"),
        ("mysql+pymysql", "pymysql"),
        ("mysql+mysqldb", "MySQLdb"),
    )

    def __init__(
        self, main_path: Path | None = None, parameters: Parameters | None = None
    ):
        super().__init__()
        self.parameters = parameters
        self.sql_table_name: str | None = self._resolve_pair_table_name(parameters)
        self.sql_table_exists = False
        self.sql_table_rows: int | None = None
        self.sql_check_error: str | None = None
        if main_path is None:
            main_path = Path.cwd() / "DB.h5"
        self.main_path = main_path

        if not hasattr(self, "spotpairs"):
            if main_path.exists():
                db_data = loadFile(main_path)
                for key in db_data.get_keys():  # Unpack all attributes from db_data
                    setattr(self, key, db_data.get_value(key))
            else:
                self._probe_sql_table()
                if self.sql_table_exists:
                    self.problem_list.append(
                        "The database exists on the SQL server only. Reading the SQL database is not implemented yet."
                    )

    def loadStatusFiles(self):
        super().loadStatusFiles()
        self.statusFilesLaunched = True
        self.statusDetailedLaunched = True
        h5_has_spotpairs = hasattr(self, "spotpairs")
        sql_available = self.sql_table_exists

        if h5_has_spotpairs or sql_available:
            self.filesOk = True
            self.detailedOK = True
            if h5_has_spotpairs:
                self.details.append("Database file loaded successfully and not empty")
            if sql_available and self.sql_table_name:
                msg = f"SQL table '{self.sql_table_name}' detected"
                if self.sql_table_rows is not None:
                    msg += f" (~{self.sql_table_rows} rows reported)"
                self.details.append(msg)
            elif self.sql_check_error:
                self.details.append(f"SQL lookup failed: {self.sql_check_error}")
        else:
            issue = "Empty database in DB.h5 file"
            if self.sql_table_name:
                issue += f" and SQL table '{self.sql_table_name}' not found"
            self.problem_list.append(issue)
            if self.sql_check_error:
                self.problem_list.append(
                    f"SQL table check failed: {self.sql_check_error}"
                )

    def _resolve_pair_table_name(self, parameters: Parameters | None) -> str | None:
        if (
            not parameters
            or not hasattr(parameters, "acq")
            or not hasattr(parameters.acq, "pair_tablename")
        ):
            return None
        try:
            value = parameters.acq.pair_tablename()
        except Exception:
            logger.debug(
                "Unable to resolve pair_tablename from parameters", exc_info=True
            )
            return None
        return str(value) if value else None

    def _probe_sql_table(self):
        if not self.sql_table_name:
            return
        credentials = self._build_sql_credentials()
        if not credentials:
            self.sql_check_error = (
                "SQL credentials not configured "
                "(set STATUSGUI_SQL_* env vars or ~/.my.cnf)"
            )
            return
        try:
            exists, approx_rows = self._query_sql_table(
                credentials, self.sql_table_name
            )
        except Exception as exc:
            self.sql_check_error = str(exc)
            logger.debug("SQL spotpairs lookup failed", exc_info=True)
            return
        self.sql_table_exists = exists
        self.sql_table_rows = approx_rows

    def _build_sql_credentials(self) -> dict[str, Any] | None:
        # Start with hardcoded defaults used by the MATLAB tools (mym)
        credentials: dict[str, Any] = dict(self._SQL_DEFAULTS)

        cnf_path = os.environ.get(self._SQL_CNF_ENV)
        candidate_paths: list[Path] = []
        if cnf_path:
            candidate_paths.append(Path(cnf_path))
        candidate_paths.extend(self._SQL_DEFAULT_CNF_LOCATIONS)

        for path in candidate_paths:
            try:
                if path and path.exists():
                    cnf_credentials = self._read_mysql_cnf(path)
                    if cnf_credentials:
                        credentials.update(cnf_credentials)
                        break
            except Exception:
                logger.debug(
                    "Failed to read SQL credentials from %s", path, exc_info=True
                )

        credentials.update(self._read_env_credentials())

        host, embedded_port = self._split_host_port(credentials.get("host"))
        if host:
            credentials["host"] = host
        if embedded_port and not credentials.get("port"):
            credentials["port"] = embedded_port

        if not credentials.get("database"):
            inferred_schema, _ = self._split_table_identifier(self.sql_table_name)
            if inferred_schema:
                credentials["database"] = inferred_schema
        port = credentials.get("port")
        if port:
            try:
                credentials["port"] = int(str(port))
            except (TypeError, ValueError):
                logger.debug("Ignoring invalid SQL port value: %s", port)
                credentials.pop("port", None)

        credentials = {k: v for k, v in credentials.items() if v not in (None, "")}

        if not all(credentials.get(item) for item in ("host", "user", "database")):
            return None

        return credentials

    def _read_env_credentials(self) -> dict[str, Any]:
        env_credentials: dict[str, Any] = {}
        for key, env_names in self._SQL_ENV_MAP.items():
            for env_name in env_names:
                value = os.environ.get(env_name)
                if value:
                    env_credentials[key] = value
                    break
        return env_credentials

    def _read_mysql_cnf(self, path: Path) -> dict[str, Any]:
        parser = configparser.ConfigParser()
        parser.read(path)
        section = os.environ.get(
            self._SQL_CNF_SECTION_ENV, self._SQL_CNF_DEFAULT_SECTION
        )
        if not parser.has_section(section):
            return {}
        cnf_map = {}
        for key in ("host", "user", "password", "port", "database", "db", "socket"):
            if parser.has_option(section, key):
                value: str = parser.get(section, key)
                if key == "socket":
                    cnf_map["unix_socket"] = value
                elif key == "db":
                    cnf_map["database"] = value
                else:
                    cnf_map[key] = value
        return cnf_map

    def _split_host_port(self, host: str | None) -> tuple[str | None, int | None]:
        if not host:
            return None, None
        if ":" not in host:
            return host, None
        name, _, port_str = host.partition(":")
        try:
            port_val = int(port_str)
        except (TypeError, ValueError):
            port_val = None
        return name or None, port_val

    def _split_table_identifier(self, table_name: str | None) -> tuple[str | None, str]:
        if not table_name:
            return None, ""
        if "." in table_name:
            schema, table = table_name.split(".", 1)
            return schema or None, table
        return None, table_name

    def _build_connection_kwargs(
        self, credentials: dict[str, Any], schema: str
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "host": credentials.get("host"),
            "user": credentials.get("user"),
            "database": schema,
            "password": credentials.get("password"),
        }
        if credentials.get("port"):
            kwargs["port"] = credentials["port"]
        if credentials.get("unix_socket"):
            kwargs["unix_socket"] = credentials["unix_socket"]
        return {key: value for key, value in kwargs.items() if value not in (None, "")}

    def _query_sql_table(
        self, credentials: dict[str, Any], table_name: str
    ) -> tuple[bool, int | None]:
        schema_override, bare_table = self._split_table_identifier(table_name)
        schema = schema_override or credentials.get("database")
        if not schema:
            raise ValueError(
                "Missing database/schema name for SQL lookup; set STATUSGUI_SQL_DATABASE"
            )

        last_error: Exception | None = None
        if self._module_available("sqlalchemy"):
            try:
                return self._query_sql_table_sqlalchemy(credentials, schema, bare_table)
            except Exception as exc:  # noqa: BLE001
                last_error = exc

        for module_name in self._SQL_CONNECTOR_ORDER:
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                continue
            try:
                connection = self._connect_with_module(
                    module, module_name, credentials, schema
                )
            except Exception as exc:
                last_error = exc
                continue
            try:
                with contextlib.closing(connection.cursor()) as cursor:
                    cursor.execute(
                        (
                            "SELECT TABLE_ROWS FROM information_schema.tables "
                            "WHERE table_schema = %s AND table_name = %s"
                        ),
                        (schema, bare_table),
                    )
                    row = cursor.fetchone()
                    if not row:
                        return False, None
                    approx_rows = row[0]
                    if isinstance(approx_rows, Number):
                        approx_rows = int(approx_rows)
                    return True, approx_rows
            finally:
                with contextlib.suppress(Exception):
                    connection.close()
        if last_error:
            raise last_error
        raise ImportError(
            "No supported MySQL connector is installed "
            "(tried mysql.connector, PyMySQL, and MySQLdb)"
        )

    def _query_sql_table_sqlalchemy(
        self, credentials: dict[str, Any], schema: str, bare_table: str
    ) -> tuple[bool, int | None]:
        sqlalchemy = importlib.import_module("sqlalchemy")
        text = sqlalchemy.text
        errors: list[Exception] = []
        for drivername, module_name in self._SQL_ALCHEMY_DIALECTS:
            if module_name and not self._module_available(module_name):
                continue
            query_params = {}
            if credentials.get("unix_socket"):
                query_params["unix_socket"] = credentials["unix_socket"]
            url = sqlalchemy.engine.URL.create(
                drivername=drivername,
                username=credentials.get("user"),
                password=credentials.get("password"),
                host=credentials.get("host"),
                port=credentials.get("port"),
                database=schema,
                query=query_params or None,
            )
            engine = sqlalchemy.create_engine(url, pool_pre_ping=True)
            try:
                with engine.connect() as conn:
                    approx_rows = conn.execute(
                        text(
                            "SELECT TABLE_ROWS FROM information_schema.tables "
                            "WHERE table_schema = :schema AND table_name = :table"
                        ),
                        {"schema": schema, "table": bare_table},
                    ).scalar()
                    if isinstance(approx_rows, Number):
                        approx_rows = int(approx_rows)
                    return True, approx_rows
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)
                continue
            finally:
                with contextlib.suppress(Exception):
                    engine.dispose()
        if errors:
            raise errors[-1]
        raise ImportError(
            "SQLAlchemy is installed but no compatible MySQL driver module was found"
        )

    def _module_available(self, module_name: str) -> bool:
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    def _connect_with_module(
        self,
        module: Any,
        module_name: str,
        credentials: dict[str, Any],
        schema: str,
    ):
        kwargs = self._build_connection_kwargs(credentials, schema)
        if module_name in ("MySQLdb", "pymysql"):
            if "database" in kwargs:
                kwargs["db"] = kwargs.pop("database")
        if module_name == "MySQLdb" and "password" in kwargs:
            kwargs["passwd"] = kwargs.pop("password")
        return module.connect(**kwargs)


class RawData(Status):
    def __init__(self, parameters, db):
        super().__init__()
        self.parameters = parameters
        self.db = db
        self.totproj = None
        self.extra_proj = None
        self.nrefgroups = None
        self.totref = None
        self.totrefHST = None
        self.im = None
        self.ref = None
        self.dark = None
        self.cp_im = None
        self.cp_ref = None
        self.cp_dark = None
        self.pp_im = None

    def load_images(self):
        # Images
        if self.parameters.acq.dir() is None:
            self.problem_list.append(
                "load_images skipped: nof_phases() is None"
            )  # Optional logging
            return
        if self.parameters.acq.type().lower() == "360degree":
            self.totproj = 2 * self.parameters.acq.nproj()
        elif self.parameters.acq.type.lower() == "180degree":
            self.totproj = self.parameters.acq.proj()
        else:
            self.problem_list.append("Unknown type of scan. Check parameters.acq.type!")

        if self.parameters.acq.mono_tune() != 0:
            self.extra_refs = (
                self.totproj
                // (self.parameters.acq.refon() * self.parameters.acq.mono_tune())
            ) * self.parameters.acq.nref()
        else:
            self.extra_refs = 0

        if int(self.parameters.acq.interlaced_turns()) == 0:
            filename = f"{self.parameters.acq.name()}{int(self.totproj // 100)}0*.edf"
        elif self.parameters.acq.interlaced_turns() > 0:
            filename = f"{self.parameters.acq.name()}*_{int(self.totproj // 100)}0*.edf"

        if (self.parameters.acq.dir() / "0_rawdata" / "Orig" / filename).exists():
            self.extra_proj = sum(
                1
                for item in (
                    self.parameters.acq.dir() / "0_rawdata" / "Orig" / filename
                ).iterdir()
                if item.is_dir()
            )
        else:
            self.extra_proj = 0

        self.nrefgroups = (self.totproj // self.parameters.acq.refon()) + 1
        self.totref = self.nrefgroups * self.parameters.acq.nref() + self.extra_refs

        if self.parameters.acq.mono_tune() == 0:
            self.totrefHST = (self.totproj // self.parameters.acq.refon()) + 1
        else:
            self.totrefHST = (
                (self.totproj // self.parameters.acq.refon())
                + 1
                + (
                    self.totproj
                    // (self.parameters.acq.refon() * self.parameters.acq.mono_tune())
                )
            )
        if self.parameters.prep.absint():
            self.totabsmed = self.totproj // self.parameters.prep.absint()
        else:
            self.totabsmed = 0
        if self.parameters.prep.fullint():
            self.totfullmed = self.totproj // self.parameters.prep.fullint()
        else:
            self.totfullmed = 0
        return True

    @staticmethod
    def _count_recursive(root: Path, pattern: str) -> int:
        # Stream matches; no lists in memory
        return sum(1 for _ in glob.iglob(str(root / "**" / pattern), recursive=True))

    def loadStatusFiles(self):
        super().loadStatusFiles()

        # Cache repeated lookups
        acq = self.parameters.acq
        acq_dir: Path = acq.dir()
        acq_name: str = acq.name() or ""
        sensor: str = acq.sensortype()

        im_loaded = False
        if not self.totproj:
            im_loaded = self.load_images()
        if not im_loaded:
            self.problem_list.append("loadStatusDetailed skipped: nof_phases() is None")
            return

        self.details.append("Checking what images are present")

        # ---- FULL (preprocessing) images ----
        pp_root = acq_dir / "1_preprocessing" / "full"
        pp_full_count = self._count_recursive(pp_root, "full*.edf")
        # Only keep the count; avoid storing all paths unless you really need them later
        self.pp_im = None  # or [] if other code expects a list
        self.details.append(
            f"  Found {pp_full_count} full images out of {self.totproj} expected"
        )
        if pp_full_count != self.totproj:
            self.problem_list.append(
                "missing full images : possible gtCreateFullLive problem"
            )

        # ---- RAW / ORIG H5 ----
        self.details.append("  Checking raw and copied corrected images:")
        orig_root = acq_dir / "0_rawdata" / "Orig"
        first_h5 = next(orig_root.glob("*.h5"), None)

        self.im = 0
        self.ref = 0
        self.dark = 0

        if first_h5:
            try:
                h5_orig = loadFile(
                    first_h5
                )  # Assuming this returns an object (not a context manager)

                # Images (_2_1)
                m21 = getattr(getattr(h5_orig, "_2_1", None), "measurement", None)
                arr = getattr(m21, sensor, None)
                self.im = arr.shape[0] if arr is not None else 0
                self.details.append(
                    f"    Found {self.im} raw images out of {self.totproj + self.extra_proj} expected"
                )
                if self.im < self.totproj:
                    self.problem_list.append(
                        "missing raw images: possible gtCopyCorrectUndistortCondor problem"
                    )

                # References (_1_1 + _3_1)
                m11 = getattr(getattr(h5_orig, "_1_1", None), "measurement", None)
                m31 = getattr(getattr(h5_orig, "_3_1", None), "measurement", None)
                ref1 = getattr(m11, sensor, None)
                ref3 = getattr(m31, sensor, None)
                self.ref = (ref1.shape[0] if ref1 is not None else 0) + (
                    ref3.shape[0] if ref3 is not None else 0
                )
                self.details.append(
                    f"    Found {self.ref} raw references out of {self.totref} expected"
                )
                if self.ref != self.totref:
                    self.problem_list.append(
                        "missing raw reference images: possible gtCopyCorrectUndistortCondor problem"
                    )

                # Dark (_4_1)
                m41 = getattr(getattr(h5_orig, "_4_1", None), "measurement", None)
                dark = getattr(m41, sensor, None)
                self.dark = dark.shape[0] if dark is not None else 0
                if self.dark == 0:
                    self.problem_list.append(
                        "missing raw dark image: possible gtCopyCorrectUndistortCondor problem"
                    )

            except Exception:
                self.problem_list.append(
                    "Impossible to read Orig images in 0_rawdata folder"
                )
                self.im = self.ref = self.dark = 0
        else:
            self.problem_list.append("No Orig folder in 0_rawdata")

        # ---- COPIED / TREATED images (counts only) ----
        if acq_name:
            raw_named_root = acq_dir / "0_rawdata" / acq_name

            cp_im_count = self._count_recursive(raw_named_root, f"{acq_name}*.edf")
            self.details.append(
                f"    Found {cp_im_count} copied images out of {self.totproj + self.extra_proj} expected"
            )
            if cp_im_count < self.totproj + self.extra_proj:
                self.problem_list.append(
                    "missing copied images: possible gtCopyCorrectUndistortCondor problem"
                )

            cp_ref_count = self._count_recursive(raw_named_root, "ref*_*.edf")
            self.details.append(
                f"    Found {cp_ref_count} copied references out of {self.totref} expected"
            )
            if cp_ref_count != self.totref:
                self.problem_list.append(
                    "missing copied reference images: possible gtCopyCorrectUndistortCondor problem"
                )

            cp_dark_count = self._count_recursive(raw_named_root, "dark*.edf")
            if cp_dark_count > 0:
                self.details.append("    Found at least one copied dark images")
        else:
            # Keep behavior but avoid scanning needlessly
            cp_im_count = 0
            cp_ref_count = 0
            cp_dark_count = 0
            self.details.append(
                f"    Found {0} copied images out of {self.totproj + self.extra_proj} expected"
            )
            self.details.append(
                f"    Found {0} copied references out of {self.totref} expected"
            )

        # ---- Final status ----
        self.filesOk = (
            (acq_name != "")
            and (cp_im_count == self.totproj + self.extra_proj)
            and (cp_ref_count == self.totref)
            and (cp_dark_count > 0)
        )
        if not self.filesOk:
            self.problem_list.append("possible problem during image copying")


class PreProcessed(Status):
    def __init__(self, parameters, db):
        super().__init__()
        self.parameters = parameters
        self.db = db
        self.nrefHST = None
        self.nabs = None
        self.nabsmed = None
        self.nfullmed = None

    def loadStatusFiles(self, rawData=None):
        super().loadStatusFiles()
        if self.parameters.acq.dir() is None:
            self.problem_list.append(
                "loadStatusFiles skipped: dir() is None"
            )  # Optional logging
            return
        if rawData is not None:
            self.rawData = rawData
        else:
            self.rawData = RawData(self.parameters, self.db)
        if not self.rawData.detailedOK:
            self.rawData.loadStatusDetailed()
        self.details.append("  Checking for preprocessed images...")
        if (
            self.rawData.totrefHST
            and self.rawData.totproj
            and self.rawData.totabsmed
            and self.rawData.totfullmed
        ):
            if self.parameters.acq.name():
                self.nrefHST = [
                    folder
                    for folder in (
                        self.parameters.acq.dir()
                        / "0_rawdata"
                        / self.parameters.acq.name()
                    ).glob("**/refHST*.edf")
                ]
            else:
                self.nrefHST = []
            self.details.append(
                f"    Found {len(self.nrefHST)} refHST images out of {self.rawData.totrefHST} expected"
            )
            if len(self.nrefHST) != self.rawData.totrefHST:
                self.problem_list.append(
                    "missing refHST images : possible gtSequenceMedianRefs problem"
                )

            self.nabs = [
                folder
                for folder in (
                    self.parameters.acq.dir() / "1_preprocessing" / "abs"
                ).glob("**/abs*.edf")
            ]
            if self.parameters.acq.interlaced_turns() > 0:
                self.nabs_renum = [
                    folder
                    for folder in (
                        self.parameters.acq.dir() / "1_preprocessing" / "abs"
                    ).glob("**/abs_renumbered*.edf")
                ]
                self.details.append(
                    "    abs_renumbered images have already been created"
                )
            else:
                self.nabs_renum = []
            self.details.append(
                f"    Found {len(self.nabs)} abs images out of {self.rawData.totproj + len(self.nabs_renum)} expected"
            )
            if len(self.nabs) != self.rawData.totproj + len(self.nabs_renum):
                self.problem_list.append(
                    "missing abs images : possible gtCreateAbsLive problem"
                )

            self.nabsmed = [
                folder
                for folder in (
                    self.parameters.acq.dir() / "1_preprocessing" / "abs"
                ).glob("**/med*.edf")
            ]
            self.details.append(
                f"    Found {len(self.nabsmed)} abs median images out of {self.rawData.totabsmed} expected"
            )
            if len(self.nabsmed) != self.rawData.totabsmed:
                self.problem_list.append(
                    "missing abs median images : possible gtAbsMedianLive problem"
                )

            self.nfullmed = [
                folder
                for folder in (
                    self.parameters.acq.dir() / "1_preprocessing" / "full"
                ).glob("**/med*.edf")
            ]
            self.details.append(
                f"    Found {len(self.nfullmed)} full median images out of {self.rawData.totfullmed} expected"
            )
            if len(self.nfullmed) != self.rawData.totfullmed:
                self.problem_list.append(
                    "missing full median images : possible gtMovingMedianLive problem"
                )

            # was preprocessing successful?
            if (
                len(self.nrefHST) == self.rawData.totrefHST
                and len(self.nabs) == self.rawData.totproj + len(self.nabs_renum)
                and len(self.nabsmed) == self.rawData.totabsmed
                and len(self.nfullmed) == self.rawData.totfullmed
            ):
                self.filesOk = True
            if not self.filesOk:
                self.problem_list.append("possible problem during image preprocessing")
        else:
            self.problem_list.append(
                "possible problem during gtSetupH5. Run the RawData check for more details"
            )


class Segmentation(Status):
    def __init__(self, parameters, db):
        super().__init__()
        self.parameters = parameters
        self.db = db
        self.method = None
        self.fullmedianvals = None
        self.fullmedianvals_fin = None
        self.tot_seeds = None
        self.done_seeds = None
        self.difblobs = None
        self.difspots = None

    def loadStatusFiles(self):
        super().loadStatusFiles()
        if self.parameters.acq.dir() is None:
            self.problem_list.append(
                "loadStatusFiles skipped: dir() is None"
            )  # Optional logging
            return
        self.filesOk = (
            (self.parameters.acq.dir() / "2_difblob/difblob.h5").exists()
            & (self.parameters.acq.dir() / "2_difspot/difspot.h5").exists()
        ) | (
            (self.parameters.acq.dir() / "2_difblob/difblob.mat").exists()
            & (self.parameters.acq.dir() / "2_difspot/difspot.mat").exists()
        )

    def loadStatusDetailed(self):
        super().loadStatusDetailed()
        self.problem_list = []
        self.details = []
        try:
            if hasattr(self.db, "difspot") and hasattr(self.db, "difblob"):
                difspot = self.db.difspot.get_value("count")
                difblob = self.db.difblob.get_value("count")
                self.details.append(f"Found {difspot} dispots for {difblob} difblobs")
            if self.parameters.acq.dir() is None:
                self.problem_list.append(
                    "loadStatusDetailed skipped: dir() is None"
                )  # Optional logging
                return
            if self.parameters.seg.method().lower() == "doublethr":
                self.details.append("Segmentation method: Double threshold")
                if hasattr(self.db, "fullmedianvals"):
                    self.fullmedianvals = self.db.fullmedianvals.get_value("count")
                    self.fullmedianvals_fin = (
                        sum(
                            1
                            for val in self.db.fullmedianvals.get_value("ndx")
                            if val != 0
                        )
                        + 1
                    )
                self.details.append(
                    f"  Segmentation completed {self.fullmedianvals_fin} images out of {self.fullmedianvals}"
                )
                if self.fullmedianvals != self.fullmedianvals_fin:
                    self.problem_list.append(
                        "gtSeedSegmentation_doublethr has not finished"
                    )

                # seed segmentation progress
                if hasattr(self.db, "seeds"):
                    self.tot_seeds = self.db.seeds.get_value("count")
                else:
                    self.tot_seeds = 0
                if hasattr(self.db, "seeds_tmp"):
                    self.done_seeds = self.db.seeds_tmp.get_value("count")
                else:
                    self.done_seeds = 0
                if self.done_seeds != self.tot_seeds:
                    self.problem_list.append(
                        "gtSegmentDiffractionBlobs_doublethr has not finished"
                    )
                self.details.append(
                    f"  Segmentation has treated {self.done_seeds} out of {self.tot_seeds} seeds"
                )

                # was segmentation successful?
                if (
                    self.fullmedianvals == self.fullmedianvals_fin
                    and self.done_seeds == self.tot_seeds
                ):
                    self.detailedOK = True
                if not self.detailedOK:
                    self.problem_list.append(
                        "possible problem during image segmentation"
                    )

            elif self.parameters.seg.method().lower() == "doublethr_new":
                self.details.append("Segmentation method: Double threshold NEW GUI")
                if hasattr(self.db, "fullmedianvals"):
                    self.fullmedianvals = self.db.fullmedianvals.get_value("count")
                    if "ndx" in self.db.fullmedianvals.get_keys():
                        self.fullmedianvals_fin = (
                            sum(
                                1
                                for val in self.db.fullmedianvals.get_value("ndx")
                                if val != 0
                            )
                            + 1
                        )
                    else:
                        self.fullmedianvals_fin = 0
                    if (
                        self.parameters.seg.writeblobs()
                        or self.parameters.seg.writehdf5()
                    ):
                        self.details.append(
                            f"  Segmentation completed {self.fullmedianvals_fin} images out of {self.fullmedianvals}"
                        )
                        if self.fullmedianvals != self.fullmedianvals_fin:
                            self.problem_list.append(
                                "gtSegmentationDoubleThreshold has not finished"
                            )

                        # was segmentation successful?
                        if self.fullmedianvals == self.fullmedianvals_fin:
                            self.detailedOK = True
                        if not self.detailedOK:
                            self.problem_list.append(
                                "possible problem during image segmentation"
                            )
                    else:
                        self.detailedOK = True

            elif self.parameters.seg.method().lower() == "singlethr":
                self.details.append("Segmentation method: Single threshold")
                self.detailedOK = True
            else:
                self.problem_list.append("Segmentation method not recognised!")

            # blob segmentation progress
            if hasattr(self.db, "difblob"):
                self.difblobs = self.db.difblob.get_value("count")
                self.details.append(f"  Segmentation has found {self.difblobs} blobs")
                if self.difblobs <= 1:
                    self.problem_list.append(
                        "possible problem during segmentation of blobs"
                    )
                    self.detailedOK = False
            else:
                self.problem_list.append("Difblobs not found into the database")
                self.detailedOK = False

            # spot segmentation progress
            if hasattr(self.db, "difspot"):
                self.difspots = self.db.difspot.get_value("count")
                self.details.append(
                    f"  Database has stored {self.difspots} difspots from {self.difblobs} blobs"
                )
                if self.difspots <= 1:
                    self.problem_list.append(
                        "possible problem during segmentation of spots"
                    )
                    self.detailedOK = False
            else:
                self.problem_list.append("Difspots not found into the database")
                self.detailedOK = False
        except Exception:
            logger.exception("Failed to determine segmentation status")
            self.problem_list.append("Impossible to determine the status.")
            self.detailedOK = False


class PairMatch(Status):
    def __init__(self, parameters, db):
        super().__init__()
        self.parameters = parameters
        self.db = db
        if hasattr(self.parameters, "acq"):
            if self.parameters.acq.nof_phases():
                self.n_pairs = [0] * int(self.parameters.acq.nof_phases())
                self.match_ok = [False] * int(self.parameters.acq.nof_phases())
        else:
            self.n_pairs = []
            self.match_ok = []

    def loadStatusFiles(self):
        super().loadStatusFiles()
        if self.parameters.acq.dir() is None:
            self.problem_list.append(
                "loadStatusFiles skipped: dir() is None"
            )  # Optional logging
            return
        self.filesOk = (
            self.parameters.acq.dir() / "3_pairmatching/pairmatch.mat"
        ).exists()

    def loadStatusDetailed(self):
        # TODO: Add reading of pairmatch.mat and DifspotTable.mat if available (Wolfgang's way of writing spots and pairs)
        super().loadStatusDetailed()
        self.problem_list = []
        self.details = []
        if self.parameters.acq.nof_phases() is None:
            self.problem_list.append(
                "loadStatusDetailed skipped: nof_phases() is None"
            )  # Optional logging
            return
        for ii in range(int(self.parameters.acq.nof_phases())):
            self.details.append(f"Checking pair matching for phase {ii + 1}:\n")
            if hasattr(self.db, "spotpairs"):
                if self.db.spotpairs.get_value("phasetype"):
                    self.n_pairs[ii] = sum(
                        1
                        for i in self.db.spotpairs.get_value("phasetype")
                        if i == ii + 1
                    )
                else:
                    self.n_pairs[ii] = 0
                if self.n_pairs[ii] == 0:
                    pair_percentage = 0
                    self.problem_list.append(
                        f"possible problem during pair matching for phase {ii + 1}"
                    )
                    self.match_ok[ii] = False
                else:
                    pair_percentage = (
                        100
                        * (2 * self.n_pairs[ii])
                        / self.db.difspot.get_value("count")
                    )
                    self.match_ok[ii] = True
                self.details.append(
                    "  Database has {} spot pairs for phase {} from {} difspots ({:.1f}% matching)\n".format(
                        self.n_pairs[ii],
                        ii + 1,
                        self.db.difspot.get_value("count"),
                        pair_percentage,
                    )
                )
                self.details.append(" ")
            else:
                self.match_ok[ii] = False
        self.detailedOK = all(self.match_ok)


class Indexing(Status):
    def __init__(self, parameters, db):
        super().__init__()
        self.parameters = parameters
        self.db = db
        if self.parameters.acq.nof_phases():
            self.n_grains = [0] * int(self.parameters.acq.nof_phases())
            self.n_pairs_inp = [0] * int(self.parameters.acq.nof_phases())
            self.n_pairs_index = [0] * int(self.parameters.acq.nof_phases())
            self.index_ok = [False] * int(self.parameters.acq.nof_phases())
        else:
            self.n_grains = []
            self.n_pairs_inp = []
            self.n_pairs_index = []
            self.index_ok = []

    def loadStatusFiles(self, _=None):
        super().loadStatusFiles()
        if self.parameters.acq.dir() is None:
            self.problem_list.append(
                "loadStatusFiles skipped: dir() is None"
            )  # Optional logging
            return
        self.filesOk = (
            (self.parameters.acq.dir() / "4_grains/sample.mat").exists()
            & (self.parameters.acq.dir() / "4_grains/spot2grain.mat").exists()
            & (self.parameters.acq.dir() / "4_grains/phase_01/index.mat").exists()
        )

    def loadStatusDetailed(self, pairMatch=None):
        super().loadStatusDetailed()
        self.problem_list = []
        self.details = []
        if self.parameters.acq.nof_phases() is None:
            self.problem_list.append(
                "loadStatusDetailed skipped: nof_phases() is None"
            )  # Optional logging
            return
        if pairMatch is not None:
            self.pairMatch = pairMatch
        else:
            self.pairMatch = PairMatch(self.parameters, self.db)
        if not self.pairMatch.detailedOK:
            self.pairMatch.loadStatusDetailed()
        self.details.append("% is there an input file?")
        for ii in range(int(self.parameters.acq.nof_phases())):
            self.details.append(f"Checking indexing for phase {ii + 1}:\n")
            d = os.listdir(f"{self.parameters.acq.dir()}/4_grains/phase_{ii + 1:02d}")
            if "index_input.mat" in d:
                self.details.append(
                    f"  Indexing input file found for phase {ii + 1:02d}:\n"
                )
                index_input_path = f"{self.parameters.acq.dir()}/4_grains/phase_{ii + 1:02d}/index_input.mat"
                try:
                    inp = loadFile(index_input_path)
                except Exception:
                    logger.exception(
                        "Failed to load indexing input file %s", index_input_path
                    )
                    inp = None
                if inp is None:
                    self.problem_list.append(
                        "  Indexing input file found but not readable"
                    )
                    self.index_ok[ii] = False
                    continue
                self.details.append(
                    "    This file was created {}\n".format(
                        datetime.fromtimestamp(
                            os.path.getmtime(index_input_path)
                        ).isoformat()
                    )
                )
                self.n_pairs_inp[ii] = inp.get_size("tot/pairid")
                if self.n_pairs_inp[ii] != self.pairMatch.n_pairs[ii]:
                    self.details.append("    !!! Strong warning !!!")
                    self.details.append(
                        "    Number of pairs in the indexing input file does not match the spotpair table"
                    )
                    self.problem_list.append(
                        'If you have update the pair matching, un-check "use input file" in gtSetupIndexing'
                    )
                    self.problem_list.append(
                        f"possible problem during indexing for phase {ii + 1}"
                    )
                    self.index_ok[ii] = False
                else:
                    self.details.append(
                        "    Indexing input looks consistant with the spot pairs table"
                    )
                    self.index_ok[ii] = True

                # is there an output file?
                if "index.mat" in d:
                    self.details.append(
                        f"  Indexing results found for phase {ii + 1:02d}:"
                    )
                    index_path = f"{self.parameters.acq.dir()}/4_grains/phase_{ii + 1:02d}/index.mat"
                    self.details.append(
                        "    Latest output file date: {}".format(
                            datetime.fromtimestamp(
                                os.path.getmtime(index_path)
                            ).isoformat()
                        )
                    )
                    try:
                        a = loadFile(index_path)
                    except Exception:
                        logger.exception(
                            "Failed to load indexing output file %s", index_path
                        )
                        a = None
                    if a is None:
                        self.problem_list.append(
                            "  Indexing output file found but not readable"
                        )
                        self.index_ok[ii] = False
                        continue
                    self.n_grains[ii] = len(a.get_value("grain"))
                    self.details.append(
                        f"    Latest output contains {self.n_grains[ii]} indexed grains"
                    )
                    self.n_pairs_index[ii] = sum(
                        i for i in a.get_value("allgrainstat/nof_pairs")
                    )
                    self.details.append(
                        f"    Latest output contains {self.n_pairs_index[ii]} indexed pairs in total"
                    )
                    if datetime.fromtimestamp(
                        os.path.getmtime(index_input_path)
                    ) > datetime.fromtimestamp(os.path.getmtime(index_path)):
                        self.problem_list.append("    !!! Strong warning !!!")
                        self.problem_list.append(
                            "    Input file is newer than the output file! Indexing has started but not finished"
                        )
                        self.index_ok[ii] = False
                    else:
                        self.details.append(
                            "    Indexing input looks consistant with the spot pairs table"
                        )
                        self.index_ok[ii] = True
                else:
                    self.problem_list.append(
                        f"  No indexing output found for phase {ii + 1:02d}"
                    )
                    self.index_ok[ii] = False
            else:
                self.problem_list.append(f"  No indexing input file for phase {ii + 1}")
                self.index_ok[ii] = False
        self.detailedOK = all(self.index_ok)


class ForwardSim(Status):
    def __init__(self, parameters, db):
        super().__init__()
        self.parameters = parameters
        self.db = db
        if self.parameters.acq.nof_phases():
            self.n_grains_mat = [0] * int(self.parameters.acq.nof_phases())
            self.fsim_ok = [True] * int(self.parameters.acq.nof_phases())
            self.conflicts_ok = [False] * int(self.parameters.acq.nof_phases())
        else:
            self.n_grains_mat = []
            self.fsim_ok = []
            self.conflicts_ok = []
        self.sample = []

    def loadStatusFiles(self, _=None):
        super().loadStatusFiles()
        if self.parameters.acq.dir() is None:
            self.problem_list.append(
                "loadStatusFiles skipped: dir() is None"
            )  # Optional logging
            return
        grains = sum(
            1
            for root, _, files in os.walk(
                self.parameters.acq.dir() / "4_grains/phase_01"
            )
            for file in files
            if (file.endswith(".mat") and "grain_" in file and "details" not in file)
        )
        self.filesOk = grains > 1
        self.details.append(f"Found {grains} grains in for phase 01")

    def loadStatusDetailed(self, indexing=None):
        super().loadStatusDetailed()
        self.problem_list = []
        self.details = []
        if self.parameters.acq.nof_phases() is None:
            self.problem_list.append(
                "loadStatusDetailed skipped: nof_phases() is None"
            )  # Optional logging
            return
        if indexing is not None:
            self.indexing = indexing
        else:
            self.indexing = Indexing(self.parameters, self.db)
        if not self.indexing.detailedOK:
            self.indexing.loadStatusDetailed()

        sample_path = f"{self.parameters.acq.dir()}/4_grains/sample.h5"
        if os.path.isfile(sample_path):
            try:
                sample = loadFile(sample_path, from_mat=True)
            except Exception:
                logger.exception("Failed to load sample data from %s", sample_path)
                sample = None
        else:
            sample_path = f"{self.parameters.acq.dir()}/4_grains/sample.mat"
            if os.path.isfile(sample_path):
                try:
                    sample = loadFile(sample_path, from_mat=True)
                except Exception:
                    logger.exception("Failed to load sample data from %s", sample_path)
                    sample = None
            else:
                self.problem_list.append("No 4_grains/sample./{h5, mat/} file found")
                return

        if sample is None:
            self.problem_list.append("No sample.mat or sample.h5 file found")
            return
        if "sample" in sample.get_keys():
            sample = sample.get_value("sample")
        if "phases" not in sample.get_keys():
            self.problem_list.append("No phases found in sample.mat")
            return

        grains_conflicts = None
        grains_conflict_path = (
            f"{self.parameters.acq.dir()}/4_grains/grains_conflicts.mat"
        )
        if os.path.isfile(grains_conflict_path):
            grains_conflicts = loadFile(grains_conflict_path)
            self.conflicts_ok = [True] * int(self.parameters.acq.nof_phases())

        for ii in range(int(self.parameters.acq.nof_phases())):
            dd = os.listdir(f"{self.parameters.acq.dir()}/4_grains/phase_{ii + 1:02d}")
            d = [x for x in dd if "grain_" in x and "details" not in x]
            self.n_grains_mat[ii] = len(d)
            if self.indexing.n_grains[ii] == self.n_grains_mat[ii]:
                self.details.append(
                    f"Correct number ({self.n_grains_mat[ii]}) of grain_####.mat files found\n"
                )
            elif self.n_grains_mat[ii] == 0:
                self.problem_list.append("No grain_####.mat file found\n")
            else:
                self.problem_list.append("Some grain_####.mat files missing!\n")
            if grains_conflicts:
                if self.conflicts_ok[ii] and self.n_grains_mat[ii] != len(
                    getattr(grains_conflicts.grains, f"_{ii + 1:02d}")
                ):
                    self.details.append("Grains_conflicts.mat exists!\n")
                    self.details.append(
                        f"  Wrong size for grains_conflicts for phase {ii + 1}\n"
                    )
                    self.conflicts_ok[ii] = False

            check = np.zeros((3, len(d)), dtype=bool)
            self.details.append(
                f"Checking grain_####.mat files for phase {ii + 1:02d}: "
            )
            n_spots_fsim = np.zeros(len(d))
            for jj, filename in enumerate(tqdm(sorted(d))):
                try:
                    b = loadFile(
                        f"{self.parameters.acq.dir()}/4_grains/phase_{ii + 1:02d}/{filename}"
                    )
                    format_phase = len(sample.get_keys("phases")[0])
                    sample_centers_shape = sample.get_size(
                        f"phases/{ii + 1:0{format_phase}d}/center"
                    )
                    sample_flip = sample_centers_shape[0] == 3
                    if sample_flip:
                        sample_center = (
                            sample.get_value(f"phases/{ii + 1:0{format_phase}d}/center")
                        )[:, jj]
                    else:
                        sample_center = (
                            sample.get_value(f"phases/{ii + 1:0{format_phase}d}/center")
                        )[jj, :]
                    if np.allclose(b.get_value("center"), sample_center):
                        check[0, jj] = True
                    if (
                        b.get_value("completeness")
                        == sample.get_value(
                            f"phases/{ii + 1:0{format_phase}d}/completeness"
                        )[jj]
                    ):
                        check[1, jj] = True
                    if (
                        self.conflicts_ok[ii]
                        and np.all(
                            np.isin(
                                b.get_value("difspotID"),
                                grains_conflicts.get_value(
                                    f"analyser_{ii + 1:02d}/difspotID"
                                ),
                            )
                        )
                    ) or not grains_conflicts:
                        check[2, jj] = True
                    n_spots_fsim[jj] = 0
                    if "difspotID" in b.get_keys():
                        difspot_size = b.get_size("difspotID")
                        if isinstance(difspot_size, tuple):
                            # difspot arrays can come back as 2D; mirror MATLAB's length() by
                            # taking the largest dimension so row/column vectors behave the same
                            n_spots_fsim[jj] = max(difspot_size) if difspot_size else 0
                        elif isinstance(difspot_size, Number):
                            n_spots_fsim[jj] = difspot_size
                except Exception:
                    logger.exception(
                        "Error reading grain_####.mat file: %s",
                        f"{self.parameters.acq.dir()}/4_grains/phase_{ii + 1:02d}/{filename}",
                    )
                    self.problem_list.append(
                        f"  Error reading grain_####.mat file: {filename}"
                    )
                    check[:, jj] = False
                    n_spots_fsim[jj] = 0

            if not np.all(check[0, :]):
                self.problem_list.append(
                    "Sample.mat and grain_####.mat have different center values for grains: "
                )
                self.problem_list.append(
                    ", ".join([str(i + 1) for i, x in enumerate(check[0, :]) if not x])
                )
            if not np.all(check[1, :]):
                self.problem_list.append(
                    "Sample.mat and grain_####.mat have different completeness values for grains: "
                )
                self.problem_list.append(
                    ", ".join([str(i + 1) for i, x in enumerate(check[1, :]) if not x])
                )
            if not np.all(check[2, :]):
                self.problem_list.append(
                    "grains_conflicts.mat and grain_####.mat have different difspotID values for grains: "
                )
                self.problem_list.append(
                    ", ".join([str(i + 1) for i, x in enumerate(check[2, :]) if not x])
                )

            self.fsim_ok[ii] = np.any(check)

            if not self.conflicts_ok[ii] and os.path.isfile(
                f"{self.parameters.acq.dir()}/4_grains/grains_conflicts.mat"
            ):
                self.problem_list.append(
                    f"grains_conflicts.mat has different length wrt the number of indexed grains: {len(grains_conflicts.grain[ii])} vs {self.n_grains_mat[ii]}"
                )
                self.problem_list.append(
                    "  Suggestion: run again gtAnalyseGrainsConflicts(true,true)"
                )
                self.fsim_ok[ii] = False

            self.details.append(
                f"  Total number of fsim spots is {np.sum(n_spots_fsim)}\n"
            )
            self.details.append(
                f"  Average number of fsim spots per grain is {np.mean(n_spots_fsim):.1f}\n"
            )
            self.details.append(
                f"  Min (max) number of fsim spots per grain is {np.min(n_spots_fsim)} ({np.max(n_spots_fsim)})\n"
            )

        for ii in range(int(self.parameters.acq.nof_phases())):
            self.details.append(
                f"Check forward simulation using gtFsimCheckMissingGrains for phase {ii + 1:02d}:\n"
            )
            list_g = gtFsimCheckMissingGrains(ii + 1, self.parameters.acq.dir())
            if not list_g["ind"] and not list_g["old"]:
                self.details.append("  Forward simulation seems ok\n")
                self.fsim_ok[ii] = self.fsim_ok[ii] * True
            elif list_g["ind"]:
                self.details.append(
                    "  Forward simulation failed for {} grains:\n".format(
                        len(list_g["ind"])
                    )
                )
                self.details.append("  grain_####.mat does not exist for grains:\n")
                self.details.append(list_g["ind"])
                self.fsim_ok[ii] = False
            elif list_g["old"]:
                self.details.append(
                    "  Forward simulation has to be checked for {} grains:\n".format(
                        len(list_g["old"])
                    )
                )
                self.details.append("  grain_####.mat is old for grains:\n")
                self.details.append(list_g["old"])
                self.fsim_ok[ii] = False
            if list_g["checkFsim"]:
                self.details.append(
                    "  Wrong grainid for {} grains from Forward Simulation:\n".format(
                        len(list_g["checkFsim"])
                    )
                )
                self.details.append("  grain_####.mat has wrong grainid for grains:\n")
                self.details.append(list_g["checkFsim"])
                self.fsim_ok[ii] = False
            if list_g["checkIndexter"]:
                self.details.append(
                    "  Wrong grainid for {} grains from Indexter:\n".format(
                        len(list_g["checkIndexter"])
                    )
                )
                self.details.append("  index.mat:grain has wrong grainid for grains:\n")
                self.details.append(list_g["checkIndexter"])
                self.fsim_ok[ii] = False
            self.details.append(" ")
        self.detailedOK = all(self.fsim_ok)


class GrainsReconstruction(Status):
    def __init__(self, parameters, db):
        super().__init__()
        self.parameters = parameters
        self.db = db
        self.status = None

    def gtReconstructedGrains(self, phase=0, num_grains=0):
        algo_keys = ["ODF6D", "VOL3D", "SEG"]
        out = {
            "ODF6D": [False] * num_grains,
            "VOL3D": [False] * num_grains,
            "SEG": [False] * num_grains,
        }

        for ii in tqdm(range(num_grains)):
            file_path = Path(
                f"{str(self.parameters.acq.dir())}/4_grains/phase_{phase + 1:02d}/grain_details_{ii + 1:04d}.mat"
            )
            if file_path.exists():
                fid = loadFile(file_path)
                for algo in algo_keys:
                    if algo in fid.get_keys():
                        out[algo][ii] = True
        return out

    def loadStatusFiles(self):
        super().loadStatusFiles()
        if self.parameters.acq.dir() is None:
            self.problem_list.append(
                "loadStatusFiles skipped: dir() is None"
            )  # Optional logging
            return
        self.filesOk = (
            sum(
                1
                for root, _, files in os.walk(
                    self.parameters.acq.dir() / "4_grains/phase_01"
                )
                for file in files
                if file.endswith(".mat") and "grain_details" in file
            )
            > 1
        )

    def loadStatusDetailed(self):
        super().loadStatusDetailed()
        self.problem_list = []
        self.details = []
        pluriel = ["s", ""]

        sample_path = f"{self.parameters.acq.dir()}/4_grains/sample.h5"
        if os.path.isfile(sample_path):
            try:
                sample = loadFile(sample_path, from_mat=True)
            except Exception:
                logger.exception("Failed to load sample data from %s", sample_path)
                sample = None
        else:
            sample_path = f"{self.parameters.acq.dir()}/4_grains/sample.mat"
            if os.path.isfile(sample_path):
                try:
                    sample = loadFile(sample_path, from_mat=True)
                except Exception:
                    logger.exception("Failed to load sample data from %s", sample_path)
                    sample = None
            else:
                self.problem_list.append("No 4_grains/sample./{h5, mat/} file found")
                return

        if sample is None:
            self.problem_list.append("No sample.mat or sample.h5 file found")
            return
        if "sample" in sample.get_keys():
            sample = sample.get_value("sample")
        if "phases" not in sample.get_keys():
            self.problem_list.append("No phases found in sample.mat")
            return

        format_phase = len(sample.get_keys("phases")[0])
        ech_name = self.parameters.acq.name()
        num_phases = sample.get_size("phases")
        phases_names = []
        phases_nbgrains = []
        phases_reconstructed_VOL3D = []
        phases_reconstructed_ODF6D = []
        phases_reconstructed_SEG = []

        for i in range(num_phases):
            phases_names.append(
                sample.get_value(f"phases/{i + 1:0{format_phase}d}/phaseName")
            )
            nb_grains = sample.get_size(
                f"phases/{i + 1:0{format_phase}d}/selectedGrains"
            )
            if isinstance(nb_grains, tuple):
                # Mirror MATLAB length: use the largest dimension for row/column vectors
                nb_grains = max(nb_grains) if nb_grains else 0
            elif isinstance(nb_grains, Number):
                nb_grains = int(nb_grains)
            else:
                nb_grains = 0
            phases_nbgrains.append(nb_grains)

        self.details.append(f"DCT sample {ech_name}")
        self.details.append(
            f"({num_phases} phase{pluriel[1 if num_phases > 1 else 0]})"
        )

        for i in range(num_phases):
            grains_check = self.gtReconstructedGrains(i, phases_nbgrains[i])
            phases_reconstructed_VOL3D.append(grains_check["VOL3D"])
            phases_reconstructed_ODF6D.append(grains_check["ODF6D"])
            phases_reconstructed_SEG.append(grains_check["SEG"])

            self.details.append(
                f"    * {phases_names[i]} : {phases_nbgrains[i]} grains \n"
            )
            self.details.append("        reconstruction")
            self.details.append(
                f"           3D  {sum(phases_reconstructed_VOL3D[i]):04d}/{phases_nbgrains[i]:04d} grains \n"
            )
            self.details.append(
                f"           6D  {sum(phases_reconstructed_ODF6D[i]):04d}/{phases_nbgrains[i]:04d} grains \n"
            )
            self.details.append(
                f"           SEG {sum(phases_reconstructed_SEG[i]):04d}/{phases_nbgrains[i]:04d} grains \n"
            )

            if not all(phases_reconstructed_VOL3D[i]):
                if (
                    sum(1 for val in phases_reconstructed_VOL3D[i] if not val)
                    == phases_nbgrains[i]
                ):
                    self.details.append(
                        "Maybe 3D SIRT reconstruction was not run yet..."
                    )
                else:
                    self.details.append("  Missing grain_####.mat:VOL3D for ID(s):")
                    self.details.append(
                        " | ".join(
                            [
                                str(index + 1)
                                for index, value in enumerate(
                                    phases_reconstructed_VOL3D[i]
                                )
                                if not value
                            ]
                        )
                    )

            else:
                self.detailedOK = True
            if not all(phases_reconstructed_ODF6D[i]):
                if (
                    sum(1 for val in phases_reconstructed_ODF6D[i] if not val)
                    == phases_nbgrains[i]
                ):
                    self.details.append("Maybe 6D reconstruction was not run yet...")
                else:
                    self.details.append("  Missing grain_####.mat:ODF6D for ID(s):")
                    self.details.append(
                        " | ".join(
                            [
                                str(index + 1)
                                for index, value in enumerate(
                                    phases_reconstructed_ODF6D[i]
                                )
                                if not value
                            ]
                        )
                    )
            else:
                self.detailedOK = True
            if not all(phases_reconstructed_SEG[i]):
                if (
                    sum(1 for val in phases_reconstructed_SEG[i] if not val)
                    == phases_nbgrains[i]
                ):
                    self.details.append("Maybe reconstruction was not run yet...")
                else:
                    self.details.append("  Missing grain_####.mat:SEG for ID(s):")
                    self.details.append(
                        " | ".join(
                            [
                                str(index + 1)
                                for index, value in enumerate(
                                    phases_reconstructed_SEG[i]
                                )
                                if not value
                            ]
                        )
                    )

            else:
                self.detailedOK = self.detailedOK * True


class AssembleVolume(Status):
    def __init__(self, parameters, db):
        super().__init__()
        self.parameters = parameters
        self.db = db
        self.status = None

    def loadStatusFiles(self):
        super().loadStatusFiles()
        if self.parameters.acq.dir() is None:
            self.problem_list.append(
                "loadStatusFiles skipped: dir() is None"
            )  # Optional logging
            return
        self.details.append("Check reconstructed/assembled volumes:\n")
        if Path(f"{self.parameters.acq.dir()}/5_reconstruction").exists():
            d = os.listdir(f"{self.parameters.acq.dir()}/5_reconstruction")
        else:
            d = {}
        if "volume_absorption.mat" in d:
            self.details.append(
                "  Found absorption reconstruction: volume_absorption.mat"
            )
            self.details.append(
                f"    File date is {datetime.fromtimestamp(os.path.getmtime(os.path.join(self.parameters.acq.dir(), '5_reconstruction', 'volume_absorption.mat'))).isoformat()}"
            )

        else:
            self.details.append("  No absorption reconstruction found")

        if "volume_mask.mat" in d:
            self.details.append("  Found absorption mask: volume_mask.mat")
            self.details.append(
                f"    File date is {datetime.fromtimestamp(os.path.getmtime(os.path.join(self.parameters.acq.dir(), '5_reconstruction', 'volume_mask.mat'))).isoformat()}"
            )
        else:
            self.details.append("  No absorption mask found")

        for ii in range(int(self.parameters.acq.nof_phases())):
            if f"phase_{ii + 1:02d}_vol.mat" in d:
                self.details.append(
                    f"  Found DCT reconstruction for phase {ii + 1}: phase_{ii + 1:02d}_vol.mat"
                )
                self.details.append(
                    f"    File date is {datetime.fromtimestamp(os.path.getmtime(f'{self.parameters.acq.dir()}/5_reconstruction/phase_{ii + 1:02d}_vol.mat')).isoformat()}"
                )

            else:
                self.problem_list.append(
                    f"  No DCT reconstruction found for phase {ii + 1}"
                )

        if "volume.mat" in d:
            self.details.append("  Found DCT reconstruction: volume.mat")
            self.details.append(
                f"    File date is {datetime.fromtimestamp(os.path.getmtime(os.path.join(self.parameters.acq.dir(), '5_reconstruction', 'volume.mat'))).isoformat()}"
            )
        else:
            self.problem_list.append("  No DCT reconstruction found")

        if "volume_dilated.mat" in d:
            self.details.append(
                "  Found postprocessed DCT reconstruction: volume_dilated.mat"
            )
            self.details.append(
                f"    File date is {datetime.fromtimestamp(os.path.getmtime(os.path.join(self.parameters.acq.dir(), '5_reconstruction', 'volume_dilated.mat'))).isoformat()}"
            )
        else:
            self.details.append("  No postprocessed DCT reconstruction found")

        self.filesOk = not self.problem_list


if __name__ == "__main__":
    path = "/data/id11/inhouse2/test_data_DCT/Ti7Al_Round_robin/PROCESSED_DATA/sam_19/2024_10_18_sam_19_redo_dct1_REF"
    dct_para = dct_status(path)
    dct_para.loadStatusFiles()
    dct_para.loadStatusDetailed()
    # dct_para.print_status()
    print(
        "==========================================================================================="
    )
    print(dct_para.print_status())
