import sys
import sqlite3
import datetime
from functools import partial

from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel,
                               QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
                               QScrollArea, QDialog, QDialogButtonBox, QLineEdit,
                               QMessageBox, QDateTimeEdit, QCalendarWidget, QTimeEdit)
from PySide6.QtCore import QSize, Qt, QTimer, QTime, QDateTime, QDate
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
class AddNewTaskDialog(QDialog):
    def __init__(self, tNow, windowTitle, defaultTitle, defaultDescription):
        super().__init__()
        self.setWindowTitle(windowTitle)

        curr_date = datetime.datetime.strptime(tNow, "%Y-%m-%d %H:%M:%S")

        buttons = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()

        titleLabel = QLabel('Title:')
        self.layout.addWidget(titleLabel)
        self.title = QLineEdit()
        self.title.setText(defaultTitle)
        self.layout.addWidget(self.title)

        descriptionLabel = QLabel("Description:")
        self.layout.addWidget(descriptionLabel)
        self.description = QLineEdit()
        self.description.setText(defaultDescription)
        self.layout.addWidget(self.description)

        endTimeLabel = QLabel('End time:')
        self.layout.addWidget(endTimeLabel)

        self.endData = QCalendarWidget()
        day = (int)(curr_date.day)
        month = (int)(curr_date.month)
        year = (int)(curr_date.year)
        date = QDate(year, month, day)
        self.endData.setSelectedDate(date)
        self.layout.addWidget(self.endData)

        self.endTime = QTimeEdit()
        hour = (int)(curr_date.hour)
        min = (int)(curr_date.minute)
        initial_time = QTime(hour, min)
        self.endTime.setTime(initial_time)

        self.layout.addWidget(self.endTime)

        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

    def getData(self):
        qdt = self.endTime.dateTime()
        qcal = self.endData.selectedDate()
        string = qcal.toString("yyyy-MM-dd") + " " + qdt.toString("HH:mm:ss")
        dt = datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
        return {"title": self.title.text(), "description": self.description.text(), "endTime": dt}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # settings
        self.setWindowTitle('To Do List')
        self.setMinimumSize(QSize(600,500))

        # mainLayout

        window = QWidget()

        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        content_layout = QHBoxLayout()
        content_layout.setAlignment(Qt.AlignCenter)
        # tasks
        tasks = QVBoxLayout()

        tasks_widget = QWidget()
        tasks_widget.setLayout(tasks)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(tasks_widget)

        # sidebar
        sidebar = QVBoxLayout()
        sidebar.setAlignment(Qt.AlignCenter)
        addTaskButton = QPushButton("Add new task")
        addTaskButton.clicked.connect(partial(self.addNewTask, tasks))
        addTaskButton.setStyleSheet("padding:  10px;")
        sidebar.addWidget(addTaskButton, alignment=Qt.AlignCenter)
        clock = QLabel("")
        clockFont = QFont()
        clockFont.setPointSize(12)
        clock.setFont(clockFont)
        timer = QTimer(self)
        timer.timeout.connect(partial(self.updateTime, clock))
        timer.start(1000)
        self.updateTime(clock)
        sidebar.addWidget(clock, alignment=Qt.AlignCenter)

        # widget
        # main_layout.addStretch(1)
        main_layout.addLayout(content_layout,  90)

        content_layout.addWidget(scroll_area,  20)
        content_layout.addLayout(sidebar,  10)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)

        self.setCentralWidget(central_widget)

        timertask = QTimer(self)
        timertask.timeout.connect(partial(self.loadTasks, tasks))
        timertask.start(1000)
        self.loadTasks(tasks)


    def timeNow(self):
        now = datetime.datetime.now()
        time = now.strftime("%Y-%m-%d %H:%M:%S")
        return time

    def updateTime(self, label):
        label.setText(self.timeNow())

    def addNewTask(self, tasks):
        dialog = AddNewTaskDialog(self.timeNow(), "Add New Task", "", "")
        if dialog.exec():
            t = dialog.getData()["title"]
            d = dialog.getData()["description"]
            end = dialog.getData()['endTime']
            error = QMessageBox()
            error.setWindowTitle("Error")

            if(t == ""):
                error.setText("Title cannot be empty!")
                error.exec()
            elif(end < datetime.datetime.now()):
                error.setText("End time must be in the future!")
                error.exec()
            else:
                start = datetime.datetime.strptime(self.timeNow(), "%Y-%m-%d %H:%M:%S")
                task = Task(t,d, start, end, 0, 1)
                task.addToDb()
                # tasks.addWidget(task, alignment=Qt.AlignTop)
                self.loadTasks(tasks)
        else:
            print('adding new task canceled')

    def loadTasks(self, tasks):
        conn = sqlite3.connect('data')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks ORDER BY end_time ASC")
        tasksList = cursor.fetchall()

        while tasks.count():
            item = tasks.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for t in tasksList:
            start = datetime.datetime.strptime(t[3], "%Y-%m-%d %H:%M:%S")
            end = datetime.datetime.strptime(t[4], "%Y-%m-%d %H:%M:%S")
            task = Task(t[1], t[2], start, end, t[0], t[5])
            tasks.addWidget(task, alignment=Qt.AlignTop)

        cursor.close()
        conn.close()

class Task(QWidget):
    def __init__(self, t, d, startT, endT, id_, act):
        super().__init__()

        self.id = id_
        label = QLabel()
        layout = QVBoxLayout()

        now = datetime.datetime.now()

        self.active = act

        titleLbl = QLabel(str(t))
        titleFont = QFont()
        titleFont.setBold(True)
        titleLbl.setFont(titleFont)
        if(endT >= now and act == 1):
            titleLbl.setStyleSheet("color: orange;")
        elif(endT < now and act == 1):
            titleLbl = QLabel(str(t) + " DELAY!!!")
            titleLbl.setStyleSheet("color: red;")
        elif(act == 0):
            titleLbl = QLabel(str(t) + " DONE!!!")
            titleLbl.setStyleSheet("color: green;")


        descriptioLbl = QLabel(str(d))
        self.startTime = startT
        self.endTime = endT
        self.title = str(t)
        self.description = str(d)

        time = QLabel("End time: " + endT.strftime("%Y-%m-%d %H:%M:%S"))

        timeFont = QFont()
        timeFont.setItalic(True)
        layout.addWidget(titleLbl)
        layout.addWidget(descriptioLbl)
        layout.addWidget(time)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins around the layout

        editBtn = QPushButton("Edit")
        editBtn.clicked.connect(self.editTask)
        editBtn.setFixedSize(100, 25)
        button_layout.addWidget(editBtn)

        delBtn = QPushButton("Delete")
        delBtn.clicked.connect(self.delFromDb)
        delBtn.setFixedSize(100, 25)
        button_layout.addWidget(delBtn)

        actBtn = QPushButton("Done")
        actBtn.clicked.connect(self.endTask)
        actBtn.setFixedSize(100, 25)
        button_layout.addWidget(actBtn)

        layout.addLayout(button_layout)

        layout.addLayout(button_layout)

        self.setMinimumHeight(160)

        self.setLayout(layout)

    def addToDb(self):
        conn = sqlite3.connect('data')
        cursor = conn.cursor()

        cursor.execute('''INSERT INTO tasks (title, description, start_time, end_time) values (?, ?, ?, ?)
        ''', (self.title, self.description, self.startTime.strftime("%Y-%m-%d %H:%M:%S"), self.endTime.strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()

        cursor.close()
        conn.close()

    def delFromDb(self):
        confirm = QMessageBox()
        confirm.setWindowTitle("Delete")
        confirm.setText("Are you sure?")
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setDefaultButton(QMessageBox.No)
        result = confirm.exec()

        if (result == QMessageBox.Yes):
            conn = sqlite3.connect('data')
            cursor = conn.cursor()

            cursor.execute('DELETE FROM tasks WHERE id = ?', (self.id,))

            conn.commit()

            cursor.close()
            conn.close()

    def editTask(self):
        dialog = AddNewTaskDialog(self.endTime.strftime("%Y-%m-%d %H:%M:%S"), "Edit Task", self.title, self.description)
        if dialog.exec():
            t = dialog.getData()["title"]
            d = dialog.getData()["description"]
            end = dialog.getData()['endTime']
            error = QMessageBox()
            error.setWindowTitle("Error")

            if (t == ""):
                error.setText("Title cannot be empty!")
                error.exec()
            else:
                conn = sqlite3.connect('data')
                cursor = conn.cursor()

                cursor.execute('UPDATE tasks SET title = ?, description = ?, end_time = ? WHERE id = ?', (t,d,end,self.id))

                conn.commit()

                cursor.close()
                conn.close()
        else:
            print('editing task canceled')

    def endTask(self):
        if(self.active == 1):
            confirm = QMessageBox()
            confirm.setWindowTitle("End")
            confirm.setText("Are you sure?")
            confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            confirm.setDefaultButton(QMessageBox.No)
            result = confirm.exec()

            if(result == QMessageBox.Yes):
                conn = sqlite3.connect('data')
                cursor = conn.cursor()

                now = datetime.datetime.now()
                time = now.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('UPDATE tasks SET end_time = ? WHERE id = ?', (time,self.id))
                cursor.execute('UPDATE tasks SET active = ? WHERE id = ?', (0,self.id))

                conn.commit()

                cursor.close()
                conn.close()


app = QApplication()
window = MainWindow()
window.show()
app.exec()