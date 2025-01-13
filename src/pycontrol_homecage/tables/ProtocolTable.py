from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView


class ProtocolTable(QTableWidget):

    def __init__(self, tab, nRows: int = None, parent=None):

        super(QTableWidget, self).__init__(1, 6, parent=parent)
        self.set_headers()
        if nRows:
            self.setRowCount(nRows)
            self.nRows = nRows
        else:
            self.nRows = 1

    def set_headers(self):

        self.header_names = ['Stage', 'Task', 'Tracked', 'Threshold(s)', 'Default(s)', 'Delete']
        self.setHorizontalHeaderLabels(self.header_names)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.set_resizemode_for_headers()

    def set_resizemode_for_headers(self):
        for h_ix in range(len(self.header_names)-1):
            self.horizontalHeader().setSectionResizeMode(h_ix, QHeaderView.Stretch)

    def fill_table(self, dat):
        " Here pass prot_dict"

        self.nRows = len(dat)

        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        for i in range(1, len(self.header_names)-1):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        if self.nRows:
            self.setRowCount(self.nRows)

        for k in dat.keys():
            self.fill_row(dat[k], row=int(k))

    def fill_row(self, dat, row=None):
        "Here pass "

        if not row:
            row = 0
            self.reset_()

        for k in dat.keys():
            if ('thresh' in k) or ('default' in k):
                Vtmp = QTableWidgetItem(self._translate(dat[k]))
            else:
                Vtmp = QTableWidgetItem(str(dat[k]))

            if k == 'threshV':
                self.setItem(row, self.header_names.index('Threshold(s)'), Vtmp)
            elif k == 'defaultV':
                self.setItem(row, self.header_names.index('Default(s)'), Vtmp)
            elif k == 'trackV':
                self.setItem(row, self.header_names.index('Tracked'), Vtmp)
            elif k == 'stage_nr':
                self.setItem(row, self.header_names.index('Stage'), Vtmp)
            elif k == 'task':
                self.setItem(row, self.header_names.index('Task'), Vtmp)

        self.resizeRowToContents(row)

    def _translate(self, x):
        ret = ''
        if len(x):
            for x_ in x:
                ret = ret + str(x_[0]) + ': ' + str(x_[1]) + '\n'
        return ret

    def reset_(self):

        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        for i in range(1, len(self.header_names)-1):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        if self.nRows:
            self.setRowCount(self.nRows)
