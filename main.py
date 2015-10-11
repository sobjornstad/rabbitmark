import sys

from sqlalchemy import create_engine, event, and_, or_
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from PyQt4.QtGui import QApplication, QMainWindow, QItemSelectionModel
from PyQt4.QtCore import Qt, QAbstractTableModel, SIGNAL

from forms.main import Ui_MainWindow
from models import Bookmark, Tag, Base

class BookmarkTableModel(QAbstractTableModel):
    def __init__(self, parent, Session, *args):
        QAbstractTableModel.__init__(self)
        self.parent = parent
        self.Session = Session
        self.session = self.Session()
        self.headerdata = ("Name", "Tags")
        self.updateForSearch("", [])

    ### Standard reimplemented methods ###
    def rowCount(self, parent):
        return len(self.L)
    def columnCount(self, parent):
        return len(self.headerdata)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, col, orientation, role):
        if (orientation == Qt.Horizontal and role == Qt.DisplayRole):
            return self.headerdata[col]
        else:
            return None

    def data(self, index, role):
        if not index.isValid():
            return None
        if not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None

        col = index.column()
        mark = self.L[index.row()]
        if col == 0:
            return mark.name
        else:
            return ', '.join([i.text for i in mark.tags_rel])

    # def setData(self, index, value, role):
    #     colNum = index.column()
    #     bookmarkNum = index.row()
    #     mark = self.L[bookmarkNum]
    #     value = unicode(value.toString())

    #     if colNum == 0:
    #         pass bla bla
    #     self.emit(QtCore.SIGNAL("dataChanged"))
    #     return True

    ### Custom methods ###
    def indexFromPk(self, pk):
        for row, obj in enumerate(self.L):
            if obj.id == pk:
                return self.index(row, 0)
        return None

    def updateForSearch(self, searchText, tags):
        nameText = "%" + searchText + "%"
        self.beginResetModel()
        self.L = []

        # sqlalchemy doesn't support in_ queries on many-to-many relationships,
        # so it's necessary to get the text of the tags and compare those.
        tag_objs = self.session.query(Tag).filter(
                or_(*[Tag.text.like(t) for t in tags]))
        allowed_tags = [i.text for i in tag_objs]

        # NOTE: without my even having to do anything, this behaves the way I
        # want it to when nothing is selected (equivalent to everything).
        query = self.session.query(Bookmark).filter(
                and_(
                    or_(
                        Bookmark.name.like(nameText),
                        Bookmark.url.like(nameText),
                        Bookmark.description.like(nameText)
                       ),
                    Bookmark.tags_rel.any(Tag.text.in_(allowed_tags))
                ))

        for mark in query:
            self.L.append(mark)
        self.emit(SIGNAL("dataChanged"))
        self.endResetModel()

    def saveIfEdited(self, mark, content):
        """
        If the content in 'content' differs from the data in the db obj
        'mark', update 'mark' to match the contents of 'content'.

        Returns True if an update was made, False if not.
        """
        #currentData = self.L[index.row()]
        if not (mark.name == content['name'] and
                mark.description == content['descr'] and
                mark.url == content['url'] and
                [i.text for i in mark.tags_rel] == content['tags']):
            print "need save!"
            mark.name = content['name']
            mark.description = content['descr']
            mark.url = content['url']

            # add new tags
            new_tags = content['tags']
            for tag in new_tags:
                existingTag = self.session.query(Tag).filter(
                              Tag.text == tag).first()
                if existingTag:
                    mark.tags_rel.append(existingTag)
                else:
                    new_tag = Tag(text=tag)
                    self.session.add(new_tag)
                    mark.tags_rel.append(new_tag)
            # remove tags that are no longer used
            deletedDirty = False
            for tag in mark.tags_rel:
                if tag.text not in new_tags:
                    deletedDirty = True
                    self.session.delete(tag)
            self.session.commit()
            return True
        return False

    def getObj(self, index):
        try:
            return self.L[index.row()]
        except IndexError:
            return None


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.form = Ui_MainWindow()
        self.form.setupUi(self)

        self.Session = make_Session()

        # set up actions
        self.form.action_Quit.triggered.connect(self.quit)
        self.form.tagsAllButton.clicked.connect(lambda: self.tagsSelect('all'))
        self.form.tagsNoneButton.clicked.connect(lambda: self.tagsSelect('none'))
        #self.form.tagsSaveButton.
        #self.form.tagsLoadButton.

        # set up data table
        self.tableView = self.form.bookmarkTable
        self.tableModel = BookmarkTableModel(self, self.Session)
        self.tableView.setModel(self.tableModel)
        self.sm = self.tableView.selectionModel()
        self.sm.selectionChanged.connect(self.fillEditPane)

        # set up tag list
        self.tags = scan_tags(self.Session)
        for i in self.tags:
            self.form.tagList.addItem(i)
        self.form.tagList.sortItems()

        # set up re-search triggers and update for the first time
        self.form.searchBox.textChanged.connect(self.doUpdateForSearch)
        self.form.tagList.itemSelectionChanged.connect(self.doUpdateForSearch)
        self.doUpdateForSearch()

    def closeEvent(self, event):
        "Catch click of the X button, etc., and properly quit."
        self.quit()

    def quit(self):
        # commit? we don't have a session in here
        sys.exit(0)

    def resetTagList(self):
        self.tags = scan_tags(self.Session)
        for i in range(self.form.tagList.count()):
            if self.form.tagList.item(i).text() not in self.tags:
                self.form.tagList.takeItem(i)
        for i in self.tags:
            if not self.form.tagList.findItems(i, Qt.MatchExactly):
                self.form.tagList.addItem(i)
        self.form.tagList.sortItems()

    def maybeSaveBookmark(self, old, new):
        """
        If focus changed away from one of the editable boxes, update state of
        its associated db object.

        Called by signal set in startQt() when any focus changes.
        """
        sf = self.form
        if old in (sf.nameBox, sf.urlBox, sf.descriptionBox, sf.tagsBox):
            mark = self.tableModel.getObj(self.tableView.currentIndex())
            QApplication.processEvents()
            if self.tableModel.saveIfEdited(mark, self.mRepr()):
                self.resetTagList()


    def doUpdateForSearch(self):
        """
        Pass values to the data table model to update its contents for a
        new search.
        """
        tags = [unicode(i.text())
                for i in self.form.tagList.selectedItems()]
        mark = self.tableModel.getObj(self.tableView.currentIndex())
        if mark is None:
            oldId = None
        else:
            oldId = mark.id
        self.tableModel.updateForSearch(
                unicode(self.form.searchBox.text()),
                tags)
        self.reselectItem(oldId) # always have one item selected

    def reselectItem(self, item=None):
        """
        Select the item /item/ if it still exists in the view, or the first
        item in the database if it doesn't or /item/ is None. This is to be
        called after updating the table view through a resetModel().
        """
        if item is None:
            idx = self.tableModel.index(0, 0)
        else:
            idx = self.tableModel.indexFromPk(item)
            if idx is None:
                idx = self.tableModel.index(0, 0)

        self.tableView.setCurrentIndex(idx)
        self.fillEditPane()

    def fillEditPane(self):
        mark = self.tableModel.getObj(self.tableView.currentIndex())
        if not self.sm.selectedRows():
            # nothing selected; hide editor pane
            self.form.splitter.widget(1).setVisible(False)
        else:
            self.form.splitter.widget(1).setVisible(True)
            self.form.nameBox.setText(mark.name)
            self.form.urlBox.setText(mark.url)
            self.form.descriptionBox.setText(mark.description)
            tags = ', '.join([i.text for i in mark.tags_rel])
            self.form.tagsBox.setText(tags)

    def tagsSelect(self, what):
        if what in ('none', 'all'):
            for i in range(self.form.tagList.count()):
                self.form.tagList.item(i).setSelected(
                        False if what == 'none' else True)

    def mRepr(self):
        """
        Short for "mark representation": return a dictionary of the content
        currently in the fields so that the model can compare and/or save it.
        """
        return {
                'name':  unicode(self.form.nameBox.text()),
                'url':   unicode(self.form.urlBox.text()),
                'descr': unicode(self.form.descriptionBox.toPlainText()),
                'tags':  [i.strip() for i in
                          unicode(self.form.tagsBox.text()).split(',')
                          if i.strip() != ''],
               }

def scan_tags(Session):
    session = Session()
    tag_list = [unicode(i) for i in session.query(Tag).all()]
    return tag_list

def make_Session():
    engine = create_engine('sqlite:///testdb.db')
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine) # will not recreate existing db's
    return Session

# http://stackoverflow.com/questions/9671490/
# how-to-set-sqlite-pragma-statements-with-sqlalchemy
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def dbTest():
    Session = make_Session()
    session = Session()

    while True:
        print "\nBookmark Database"
        print "Would you like to:"
        print "1) Add a bookmark"
        print "2) Search for a bookmark"
        print "3) Delete a bookmark"
        print "4) Test tag editing"
        print "0) Quit"
        what_do = raw_input("> ")

        if what_do == "1":
            print "We're going to add a bookmark. Where shall it be?"
            new_name = raw_input("Name: ")
            new_url = raw_input("Url: ")
            new_tags = raw_input("Tags: ")
            new_descr = raw_input("Description: ")

            g_bookmark = Bookmark(name=new_name, url=new_url, description=new_descr)
            session.add(g_bookmark)

            tag_list = [tag.strip() for tag in new_tags.split(',')]
            for tag in tag_list:
                existingTag = session.query(Tag).filter(Tag.text == tag).first()
                if existingTag:
                    g_bookmark.tags_rel.append(existingTag)
                else:
                    new_tag = Tag(text=tag)
                    g_bookmark.tags_rel.append(new_tag)
            print "Added bookmark with name %s." % new_name

        elif what_do == "2":
            search_for = raw_input("Name (substr search): ")
            search_for = "%" + search_for + "%"
            for bookmark in session.query(Bookmark).filter(
                    Bookmark.name.like(search_for)):
                print "Name: %s" % bookmark.name
                print "URL : %s" % bookmark.url
                print "Tags: %r" % [i.text for i in bookmark.tags_rel]
                print "Description:"
                print bookmark.description
                print ""

        elif what_do == "3":
            search_for = raw_input("Delete name (substr search): ")
            search_for = "%" + search_for + "%"
            for bookmark in session.query(Bookmark).filter(
                    Bookmark.name.like(search_for)):
                print "Deleting name '%s'...sure?" % bookmark.name
                try:
                    raw_input("(^C to cancel)")
                except KeyboardInterrupt:
                    break
                session.delete(bookmark)

        elif what_do == "4":
            print 'Adjusting tags for "Lillian".'
            mark = session.query(Bookmark).filter(Bookmark.name == 'Lillian').one()
            new_tags_raw = raw_input("New tags: ")
            new_tags = [i.strip() for i in new_tags_raw.split(',')]

            for tag in new_tags:
                existingTag = session.query(Tag).filter(Tag.text == tag).first()
                if existingTag:
                    mark.tags_rel.append(existingTag)
                else:
                    new_tag = Tag(text=tag)
                    mark.tags_rel.append(new_tag)
            for tag in mark.tags_rel:
                if tag.text not in new_tags:
                    session.delete(tag)


            #for tag in new_tags:
                #existingTag = session.query(Tag).filter(Tag.text == tag).first()
                ##if not existingTag:
                    #session



            for tag in mark.tags_rel:
                print tag.text


        elif what_do == "0":
            print "Exiting."
            session.commit()
            break
        else:
            print "I didn't get that."

def startQt():
    app = QApplication(sys.argv)
    mw = MainWindow()
    app.focusChanged.connect(mw.maybeSaveBookmark)
    mw.show()
    app.exec_()

if __name__ == '__main__':
    #dbTest()
    startQt()
