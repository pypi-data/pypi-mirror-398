import os
from pathlib import Path
import sys

import Orange.data
from Orange.data import Table, Domain, StringVariable, ContinuousVariable
from AnyQt.QtWidgets import QApplication
from Orange.widgets import widget
from Orange.widgets.utils.signals import Input, Output

if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.AAIT.utils.import_uic import uic
    from Orange.widgets.orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file
    from Orange.widgets.orangecontrib.AAIT.utils import thread_management
else:
    from orangecontrib.AAIT.utils.import_uic import uic
    from orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file
    from orangecontrib.AAIT.utils import thread_management


@apply_modification_from_python_file(filepath_original_widget=__file__)
class OWFileSyncChecker(widget.OWWidget):
    name = "File Sync Checker"
    description = 'Verify if the files contained in Data are the same as the files contained in Reference. The verification is done thanks to both the "path" and "file size" columns.'
    category = "AAIT - TOOLBOX"
    icon = "icons/owfilesyncchecker.svg"
    if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
        icon = "icons_dev/owfilesyncchecker.svg"
    gui = os.path.join(os.path.dirname(os.path.abspath(__file__)), "designer/owfilesyncchecker.ui")
    want_control_area = False
    priority = 1060

    class Inputs:
        data = Input("Data", Orange.data.Table)
        reference = Input("Reference", Orange.data.Table)

    class Outputs:
        data = Output("Files only in Data", Orange.data.Table)
        processed = Output("Files in Data & Reference", Orange.data.Table)

    @Inputs.data
    def set_data(self, in_data):
        self.data = in_data
        if self.autorun:
            self.run()

    @Inputs.reference
    def set_reference(self, in_reference):
        self.reference = in_reference
        if self.autorun:
            self.run()


    def __init__(self):
        super().__init__()
        # Qt Management
        self.setFixedWidth(470)
        self.setFixedHeight(300)
        uic.loadUi(self.gui, self)

        # Data Management
        self.data = None
        self.reference = "default"
        self.autorun = True
        self.thread = None
        self.result = None
        self.post_initialized()

    def run(self):
        self.warning("")
        self.error("")

        # If Thread is already running, interrupt it
        if self.thread is not None:
            if self.thread.isRunning():
                self.thread.safe_quit()

        if self.data is None:
            self.Outputs.data.send(None)
            self.Outputs.processed.send(None)
            return

        if self.reference == "default":
            self.Outputs.data.send(None)
            self.Outputs.processed.send(None)
            return

        if self.reference is None:
            self.warning('There is no Reference table. All the files in Data will be considered as new files.')
            self.Outputs.data.send(self.data)
            self.Outputs.processed.send(None)
            return

        if "path" not in self.data.domain or "path" not in self.reference.domain:
            self.error('You need a "path" column in both Data and Reference tables.')
            return

        if "file size" not in self.data.domain:
            self.warning('There is no "file size" column in your Data table. All the files in Data will be considered as new files.')
            self.Outputs.data.send(self.data)
            self.Outputs.processed.send(None)
            return

        if "file size" not in self.reference.domain:
            self.warning('There is no "file size" column in your Reference table. All the files in Data will be considered as new files.')
            self.Outputs.data.send(self.data)
            self.Outputs.processed.send(None)
            return

        # Start progress bar
        self.progressBarInit()

        # Start threading
        self.thread = thread_management.Thread(self.check_for_sync, self.data, self.reference)
        self.thread.progress.connect(self.handle_progress)
        self.thread.result.connect(self.handle_result)
        self.thread.finish.connect(self.handle_finish)
        self.thread.start()

    def check_for_sync(self, table_data, table_reference, progress_callback=None, argself=None):

        def fast_norm(path_str):
            p = Path(path_str).expanduser()
            try:
                p = p.absolute()  # no disk access
            except OSError:
                pass

            s = str(p)
            if os.name == "nt":
                return s.replace("/", "\\").lower()
            return s

        reference = table_reference.copy()

        # ---- Extract & normalize paths ----
        paths_data = {
            fast_norm(row["path"].value): int(row["file size"].value)
            for row in table_data
        }

        paths_ref = {}
        ref_row_for_path = {}
        for i, row in enumerate(reference):
            p = fast_norm(row["path"].value)
            paths_ref[p] = int(row["file size"].value)
            ref_row_for_path[p] = i

        progress_update(20, progress_callback)

        # ---- Compute aligned roots once ----
        def common_root(keys):
            if not keys:
                return Path(".")
            return get_common_path([Path(k) for k in keys])

        common_data = common_root(paths_data.keys())
        common_ref = common_root(paths_ref.keys())

        # ---- Align reference paths quickly ----
        aligned_ref = {}
        for p, size in paths_ref.items():
            try:
                rel = Path(p).relative_to(common_ref)
                new = str((common_data / rel).absolute())
            except Exception:
                new = p
            aligned_ref[new] = size


        progress_update(50, progress_callback)

        set_data = set(paths_data.keys())
        set_ref = set(aligned_ref.keys())

        common = set_data & set_ref
        only_data = set_data - set_ref
        only_ref = set_ref - set_data

        print(f"Files in common: {len(common)}")
        print(f"Only in data: {len(only_data)}")
        print(f"Only in ref: {len(only_ref)}")

        # ---- Collect process list + rows to remove ----
        files_to_process = []
        remove_indices = set()

        for p in common:
            if paths_data[p] != aligned_ref[p]:
                files_to_process.append([Path(p), paths_data[p]])
                if p in ref_row_for_path:
                    remove_indices.add(ref_row_for_path[p])

        progress_update(60, progress_callback)

        for p in only_data:
            files_to_process.append([Path(p), paths_data[p]])


        progress_update(70, progress_callback)

        for p in only_ref:
            if p in ref_row_for_path:
                remove_indices.add(ref_row_for_path[p])


        progress_update(80, progress_callback)

        # ---- Build new reference table once ----
        if remove_indices:
            keep_rows = [i for i in range(len(reference)) if i not in remove_indices]
            reference = reference[keep_rows]

        # ---- Re-align paths in reference ----
        for row in reference:
            p = fast_norm(row["path"].value)
            try:
                rel = Path(p).relative_to(common_ref)
                row["path"] = str((common_data / rel).absolute())
            except Exception:
                pass

        progress_update(100, progress_callback)

        # ---- Build output table ----
        path_var = StringVariable("path")
        size_var = ContinuousVariable("file size")
        dom = Domain([], metas=[path_var, size_var])
        out_data = Table.from_list(dom, files_to_process)

        return out_data, reference



    def handle_progress(self, value: float) -> None:
        self.progressBarSet(value)

    def handle_result(self, result):
        data = result[0]
        processed_data = result[1]
        try:
            self.Outputs.data.send(data)
            self.Outputs.processed.send(processed_data)
            self.data = None
            self.reference = "default"
        except Exception as e:
            print("An error occurred when sending out_data:", e)
            self.Outputs.data.send(None)
            return

    def handle_finish(self):
        self.progressBarFinished()


    def post_initialized(self):
        pass


def progress_update(value, progress_callback):
    if progress_callback is not None:
        progress_value = float(value)
        progress_callback(progress_value)


def remove_from_table(filepath, table):
    """
    Remove rows from the Orange table where 'path' matches the given filepath.
    """
    filepath = Path(filepath).resolve()

    filtered_table = Table.from_list(
        domain=table.domain,
        rows=[row for row in table
              if Path(str(row["path"].value)).resolve() != filepath]
    )
    return filtered_table


def get_common_path(paths):
    """
    Find the common root directory among a list of file paths.

    - If the list contains only one path, the parent directory of that path
      is returned (to ensure the result is always a directory).
    - If the list contains multiple paths, their deepest shared parent
      directory is returned using os.path.commonpath.

    Parameters
    ----------
    paths : list[pathlib.Path] or list[str]
        A list of file or directory paths.

    Returns
    -------
    pathlib.Path
        The common root directory as a Path object.
    """
    paths = [str(p) for p in paths]

    if len(paths) == 1:
        return Path(paths[0]).parent
    else:
        return Path(os.path.commonpath(paths))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = OWFileSyncChecker()
    my_widget.show()
    if hasattr(app, "exec"):
        app.exec()
    else:
        app.exec_()
