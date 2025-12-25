from AnyQt.QtWidgets import QApplication
from AnyQt.QtCore import QTimer
#allows displaying a widget on opening
# add (not sure!)
# save_position = False
# after class declaration
# call show_and_adjust_at_opening at the end of init
def show_and_adjust_at_opening(argself,str_position):
    # "left", "top-left", "bottom-left","bottom", "bottom-left", "bottom-right"
    str_position=str(str_position)
    if str_position=="None" or str_position=="none":
        return
    argself.show()
    QTimer.singleShot(1000, lambda: adjust_to_quarter(argself,str_position))


def adjust_to_quarter(argself, position: str):
    """
    Resize and position the widget depending on a screen region:
    - left / right  → full height, half width
    - top / bottom  → full width, half height
    - corners       → quarter (half width × half height)
    """
    app = QApplication.instance()
    screen = app.primaryScreen().availableGeometry()

    sw, sh = screen.width(), screen.height()

    if position == "fullscreen":
        # full screen
        w, h = sw, sh
    # ---- CALCUL TAILLE ----
    elif position in ("left", "right"):
        # full height, half width
        w, h = sw // 2, sh

    elif position in ("top", "bottom"):
        # full width, half height
        w, h = sw, sh // 2

    elif position in ("top-left", "top-right", "bottom-left", "bottom-right"):
        # quarter (default case)
        w, h = sw // 2, sh // 2
    elif position == "none" or position == "None":
        return  # ou ne rien faire
    else:
        # fallback: centered
        w, h = sw // 2, sh // 2

    # ---- CALCUL POSITION ----
    if position in ("left", "top-left", "bottom-left"):
        x = screen.x()
    elif position in ("right", "top-right", "bottom-right"):
        x = screen.x() + sw - w
    else:
        x = screen.x() + (sw - w) // 2

    if position in ("top", "top-left", "top-right"):
        y = screen.y()
    elif position in ("bottom", "bottom-left", "bottom-right"):
        y = screen.y() + sh - h
    else:
        y = screen.y() + (sh - h) // 2

    # ---- APPLIQUER ----
    argself.resize(w, h)
    argself.move(x, y)

