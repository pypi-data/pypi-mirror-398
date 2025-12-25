import os
import sys

from AnyQt.QtWidgets import QApplication
from Orange.widgets import widget
from Orange.widgets.utils.signals import Output
from AnyQt.QtWidgets import QLineEdit
from sentence_transformers import SentenceTransformer
from Orange.widgets.settings import Setting


if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.AAIT.utils.import_uic import uic
    from Orange.widgets.orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file
else:
    from orangecontrib.AAIT.utils.import_uic import uic
    from orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file


@apply_modification_from_python_file(filepath_original_widget=__file__)
class OWModelEmbeddings(widget.OWWidget):
    name = "Model - Embeddings"
    description = "Load the embeddings model from the user's input path."
    category = "AAIT - MODELS"
    icon = "icons/owmodel_embeddings.svg"
    if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
        icon = "icons_dev/owmodel_embeddings.svg"
    gui = os.path.join(os.path.dirname(os.path.abspath(__file__)), "designer/owmodel_embeddings.ui")
    priority = 1061
    want_control_area = False

    model_path = Setting("")

    class Outputs:
        out_model = Output("Model", SentenceTransformer, auto_summary=False)

    def __init__(self):
        super().__init__()
        # Qt Management
        self.setFixedWidth(470)
        self.setFixedHeight(300)
        uic.loadUi(self.gui, self)
        # TextEdit
        self.lineedit_path = self.findChild(QLineEdit, 'lineEdit')
        self.lineedit_path.setText(self.model_path)
        self.lineedit_path.editingFinished.connect(self.edit_model_path)

        # Load model
        self.run()


    def edit_model_path(self):
        path = self.lineedit_path.text().strip('"').strip("'")
        self.model_path = path
        self.run()


    def run(self):
        # Reset indications on widget
        self.error("")
        self.warning("")

        # Load the model and send it
        model = self.load_model()
        self.Outputs.out_model.send(model)


    def load_model(self):
        if not os.path.exists(self.model_path):
            self.error(f"Path {self.model_path} does not exist")
            return

        try:
            model = SentenceTransformer(self.model_path, device="cpu")
            return model
        except Exception as e:
            self.error(f"The model could not be loaded: {e}")
            return


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = OWModelEmbeddings()
    my_widget.show()
    if hasattr(app, "exec"):
        app.exec()
    else:
        app.exec_()
