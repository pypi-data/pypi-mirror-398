from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

import matlab.engine
from tqdm import tqdm

_DEFAULT_DCT_ANCHORS: tuple[str, ...] = ("initialise_gt",)


class MatlabConnector:
    def __init__(self, sessionId=None, load_dct=True):
        self.eng: matlab.engine.MatlabEngine | None = None
        self.session_id: str | None = None
        self._owns_engine = False
        self.functions: dict[str, str] = {}

        # Start MATLAB engine
        # Function to extract datetime from string
        def extract_datetime(s):
            date_time_str = "_".join(
                s.split("_")[1:]
            )  # Join all parts except the first one
            return datetime.strptime(date_time_str, "%Y_%m_%d_%H_%M_%S")

        session_name = sessionId
        if isinstance(session_name, (list, tuple)):
            session_name = session_name[0] if session_name else None
        if session_name is None:
            sessions = matlab.engine.find_matlab()
            if not sessions:
                print("No MATLAB session found")
                return
            if len(sessions) == 1:
                session_name = sessions[0]
            else:
                filtered = [i for i in sessions if Path.home().parts[-1] in i]
                candidates = filtered or sessions
                if len(candidates) == 1:
                    session_name = candidates[0]
                else:
                    datetimes = [extract_datetime(s) for s in candidates]
                    most_recent = max(datetimes)
                    session_name = candidates[datetimes.index(most_recent)]
                    print(
                        "Multiple MATLAB sessions found, the last launched is "
                        f"chosen by default: {session_name}"
                    )

        if session_name is None:
            print("No MATLAB session available")
            return

        try:
            self.eng = matlab.engine.connect_matlab(session_name)
            self.session_id = session_name
            print(f"Connected to existing MATLAB session: {session_name}.")
            self.setworkspace()
        except matlab.engine.EngineError:
            print("Connection not established, check the input name")
            return

        if load_dct and self.eng is not None:
            self.parse_matlab_functions()

    def __del__(self):
        # Stop MATLAB engine
        if self._owns_engine and getattr(self, "eng", None) is not None:
            try:
                self.eng.quit()
            except Exception as e:
                print(f"Error quitting MATLAB engine: {e}")

    def resolve_dct_root(self, *, anchors: Iterable[str] | None = None) -> Path:
        if self.eng is None:
            raise RuntimeError(
                "MATLAB engine is not connected; cannot resolve DCT root."
            )

        candidates = tuple(anchors) if anchors is not None else _DEFAULT_DCT_ANCHORS
        last_exc: matlab.engine.MatlabExecutionError | None = None

        for candidate in candidates:
            try:
                result = self.eng.eval(f"fileparts(which('{candidate}'))", nargout=1)
            except matlab.engine.MatlabExecutionError as exc:
                last_exc = exc
                continue
            if result:
                return Path(result)

        raise RuntimeError(
            f"Unable to determine DCT root from anchors {candidates}; "
            "ensure `module load dct` ran before starting MATLAB."
        ) from last_exc

    def parse_matlab_functions(self, path=None):
        if self.eng is None:
            raise RuntimeError(
                "MATLAB engine is not connected; cannot parse functions."
            )

        if path is None:
            path = self.resolve_dct_root()

        root = Path(path)
        for filepath in tqdm(root.glob("**/*.m")):
            self.add_function(filepath.stem, filepath.stem)

    def add_function(self, name, function):
        # Add MATLAB function to dictionary
        if name not in self.functions:
            self.functions[name] = function

    def __getattr__(self, name):
        if self.eng is None:
            raise AttributeError(
                "'MatlabConnector' is not connected to a MATLAB session."
            )

        try:
            matlab_attr = getattr(self.eng, name)
        except AttributeError as error:
            raise AttributeError(
                f"'MatlabConnector' object has no attribute '{name}'"
            ) from error

        def matlab_function(*args, **kwargs):
            if "nargout" not in kwargs:
                kwargs["nargout"] = 0
            return matlab_attr(*args, **kwargs)

        return matlab_function

    def __dir__(self):
        # Include dynamically added methods in the list of attributes
        return super().__dir__() + list(self.functions.keys())

    def setworkspace(self):
        self.eng.workspace["isEngine"] = True

    def unsetworkspace(self):
        self.eng.workspace["isEngine"] = False


# Example usage:
if __name__ == "__main__":
    ml = MatlabConnector()
