# Vacation work just-do-it
# Creating something for fun just to ease stress.
# What can I draw?

import turtle
from PyQt5.QtWidgets import*
import sys
from PyQt5.QtGui import*

class ForFun(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle("Luvolwethu's Vision Board")
        self.setGeometry(50, 100, 1000, 1000)
        self.setStyleSheet(f"background-color: lightblue;")
        
        # Creating the picture...
        check = QCheckBox()
        self.pic_label = QLabel()
        self.pic_label.setPixmap(QPixmap("upper.png"))
        self.pic_label.setMaximumSize(300,300)
        
        # Creating buttons
        self.button1 = QPushButton("Yes Please")
        
        # Creating the layout
        self.grid = QGridLayout()
        self.grid.addWidget(self.pic_label, 2, 2, 2, 10)
        self.grid.addWidget(self.button1, 0, 0)
        self.setLayout(self.grid)
        
def main():
    app = QApplication(sys.argv)
    widget = ForFun()
    widget.show()
    sys.exit(app.exec_())
if __name__ == "__main__":
    main()