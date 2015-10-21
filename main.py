#TODO: It should not be possible to delete a bookmark with none selected.

import sys

from sqlalchemy import create_engine, event, and_, or_
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from PyQt4.QtGui import QApplication, QMainWindow, QItemSelectionModel, \
        QDesktopServices, QShortcut, QKeySequence, QMessageBox
from PyQt4.QtCore import Qt, QAbstractTableModel, SIGNAL, QUrl, QSize, \
        QVariant

from forms.main import Ui_MainWindow
from models import Bookmark, Tag, Base
import utils

NOTAGS = "(no tags)"

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
        if (role == Qt.DisplayRole and orientation == Qt.Horizontal):
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

    def sort(self, column, order=Qt.AscendingOrder):
        rev = (order != Qt.AscendingOrder)

        if column == 0:
            key = lambda i: i.name
        elif column == 1:
            print "DEBUG: Sorting by this column is not supported."
            key = lambda i: None

        self.beginResetModel()
        self.L.sort(key=key, reverse=rev)
        self.endResetModel()


    ### Custom methods ###
    def indexFromPk(self, pk):
        for row, obj in enumerate(self.L):
            if obj.id == pk:
                return self.index(row, 0)
        return None

    def makeNewBookmark(self, url="http://"):
        """
        Create a new bookmark with boilerplate and the provided /url/ or
        'http://' if none. Return the object created.
        """
        new_name = ""
        new_url = url
        new_tags = ""
        new_descr = ""

        g_bookmark = Bookmark(name=new_name, url=new_url, description=new_descr)
        self.session.add(g_bookmark)

        tag_list = [tag.strip() for tag in new_tags.split(',')]
        for tag in tag_list:
            existingTag = self.session.query(Tag).filter(
                    Tag.text == tag).first()
            if existingTag:
                g_bookmark.tags_rel.append(existingTag)
            else:
                new_tag = Tag(text=tag)
                g_bookmark.tags_rel.append(new_tag)
        self.session.flush() # we'll presumably commit as soon as we edit it
        return g_bookmark

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
        tag_query = []
        if NOTAGS in tags:
            tags.remove(NOTAGS)
            tag_query = [Bookmark.tags_rel == None]
        if len(tags) > 0:
            tag_query += [Bookmark.tags_rel.any(Tag.text.in_(allowed_tags))]
        query = self.session.query(Bookmark).filter(
                and_(
                    or_(
                        Bookmark.name.like(nameText),
                        Bookmark.url.like(nameText),
                        Bookmark.description.like(nameText)
                       ),
                    or_(*tag_query)
                ))

        for mark in query:
            self.L.append(mark)
        self.emit(SIGNAL("dataChanged"))
        self.endResetModel()

    def deleteBookmark(self, index):
        """
        Delete the bookmark at /index/ in the table. Return the pk of the entry
        above it to select after deletion (below if the top), or None if this
        is the only entry.
        """
        row = index.row()
        mark = self.L[row]
        try:
            if (row - 1) >= 0:
                nextObj = self.L[row-1]
            else:
                # index was negative, this is the top entry; go below
                nextObj = self.L[row+1]
        except IndexError:
            # there are no other items
            nextObj = None
        self.session.delete(mark)
        self.session.commit()
        self.beginResetModel()
        #TODO: When using beginRemoveRows(), a blank row is left in the table.
        # This is a little inconvenient, but it *works* for now.
        #self.beginRemoveRows(index, row, row)
        del self.L[row]
        self.endResetModel()
        #self.endRemoveRows()
        #self.emit(SIGNAL("dataChanged"))
        return nextObj.id

    def renameTag(self, tag, new):
        """
        Rename tag /tag/ to /new/.

        Return:
            True if tag was renamed.
            False if another tag already existed with name /new/ or it is
                otherwise invalid (there are no other checks currently).
        """
        tag_exists_check = self.session.query(Tag).filter(
                Tag.text == new).one_or_none()
        if tag_exists_check is not None:
            return False

        tag_obj = self.session.query(Tag).filter(Tag.text == tag).one()
        tag_obj.text = new
        self.session.commit()
        return True

    def deleteTag(self, tag):
        """
        Delete the /tag/ from all bookmarks.
        """
        tag_obj = self.session.query(Tag).filter(Tag.text == tag).one()
        self.session.delete(tag_obj)
        self.session.commit()

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
            for tag in mark.tags_rel:
                if tag.text not in new_tags:
                    self.session.delete(tag)
            self.session.commit()
            return True
        return False

    def getObj(self, index):
        try:
            return self.L[index.row()]
        except IndexError:
            return None

    def commit(self):
        """
        Commit all changes. Should be called before quitting or doing anything
        similarly destructive to the memory image to make sure that no
        transactions are still active.
        """
        self.session.commit()


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.form = Ui_MainWindow()
        self.form.setupUi(self)

        self.Session = make_Session()

        # set up actions
        self.form.action_Quit.triggered.connect(self.quit)
        self.form.actionDelete.triggered.connect(self.deleteCurrent)
        self.form.actionNew.triggered.connect(self.onAddBookmark)
        self.form.actionNew_from_clipboard.triggered.connect(
                self.onAddBookmarkFromClipboard)
        self.form.actionRenameTag.triggered.connect(self.onRenameTag)
        self.form.actionDeleteTag.triggered.connect(self.onDeleteTag)

        self.form.tagsAllButton.clicked.connect(lambda: self.tagsSelect('all'))
        self.form.tagsNoneButton.clicked.connect(lambda: self.tagsSelect('none'))
        #self.form.tagsSaveButton.
        #self.form.tagsLoadButton.
        self.form.copyUrlButton.clicked.connect(self.copyUrl)
        self.form.browseUrlButton.clicked.connect(self.openUrl)
        self.form.addButton.clicked.connect(self.onAddBookmark)
        findShortcut = QShortcut(QKeySequence("Ctrl+F"), self.form.searchBox)
        findShortcut.connect(findShortcut, SIGNAL("activated()"),
                             self.form.searchBox.setFocus)

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
        self.tableModel.sort(0)

    def closeEvent(self, event):
        "Catch click of the X button, etc., and properly quit."
        self.quit()

    def quit(self):
        # fake changing focus: the widget name for new is arbitrary,
        # one of the editable boxes is required for old
        self.maybeSaveBookmark(old=self.form.nameBox, new=self.form.nameBox)
        self.tableModel.commit()
        sys.exit(0)

    def onAddBookmarkFromClipboard(self):
        pastedUrl = unicode(QApplication.clipboard().text()).strip()
        if not '://' in pastedUrl:
            utils.warningBox("No protocol (e.g., http://) in URL. Adding "
                             "http:// to beginning. You may wish to check "
                             "the URL.", "URL possibly invalid")
            pastedUrl = 'http://' + pastedUrl
        self.onAddBookmark(urltext=pastedUrl)

    def onAddBookmark(self, urltext="http://"):
        newMark = self.tableModel.makeNewBookmark(urltext)
        self.doUpdateForSearch()
        index = self.tableModel.indexFromPk(newMark.id)
        self.tableView.setCurrentIndex(index)
        self.form.nameBox.setFocus()

    def deleteCurrent(self):
        index = self.tableView.currentIndex()
        nextPk = self.tableModel.deleteBookmark(index)
        index = self.tableModel.indexFromPk(nextPk)
        self.tableView.setCurrentIndex(index)

    def copyUrl(self):
        QApplication.clipboard().setText(self.form.urlBox.text())
    def openUrl(self):
        QDesktopServices.openUrl(QUrl(self.form.urlBox.text()))

    def onRenameTag(self):
        tags = [unicode(i.text())
                for i in self.form.tagList.selectedItems()]
        if len(tags) != 1:
            utils.errorBox("You must select exactly one tag.",
                           "Cannot rename zero or multiple tags")
            return
        tag = tags[0]

        new, ok = utils.inputBox("New name for tag:", "Rename tag", tag)
        if ok:
            if self.tableModel.renameTag(tag, new):
                self.resetTagList()
                self.fillEditPane()
            else:
                utils.errorBox("A tag by that name already exists.",
                               "Cannot rename tag")
        else:
            return


    def onDeleteTag(self):
        tags = [unicode(i.text())
                for i in self.form.tagList.selectedItems()]
        if len(tags) != 1:
            utils.errorBox("Sorry, you currently cannot delete tags in bulk.",
                           "Cannot delete zero or multiple tags")
            return

        tag = tags[0]
        if tag == NOTAGS:
            utils.errorBox("You cannot delete '%s'. It is not a tag; rather, "
                           "it indicates that you would like to search for "
                           "items that do not have any tags." % NOTAGS,
                           "Not deleteable")
            return

        r = utils.questionBox("This will permanently delete the tag '%s' from "
                              "all of your bookmarks. Are you sure you want "
                              "to continue?" % tag, "Delete tag?")
        if r == QMessageBox.Yes:
            self.tableModel.deleteTag(tag)
            self.resetTagList()
            self.fillEditPane()

    def resetTagList(self):
        """
        Update the tag list widget to match the current state of the db.
        """
        # Get updated tag list.
        self.tags = scan_tags(self.Session)

        # Remove tags that no longer exist.
        toRemove = [self.form.tagList.item(i)
                    for i in range(self.form.tagList.count())
                    if self.form.tagList.item(i).text() not in self.tags]
        for i in toRemove:
            self.form.tagList.takeItem(self.form.tagList.row(i))

        # Add new tags and resort list.
        for i in self.tags:
            if not self.form.tagList.findItems(i, Qt.MatchExactly):
                self.form.tagList.addItem(i)
        self.form.tagList.sortItems()

    def maybeSaveBookmark(self, old, new):
        """
        If focus changed away from one of the editable boxes, update state of
        the db object associated with the currently selected bookmark.

        Called by signal set in startQt() when any focus changes, as well as
        before quitting.
        """
        sf = self.form
        if old in (sf.nameBox, sf.urlBox, sf.descriptionBox, sf.tagsBox):
            mark = self.tableModel.getObj(self.tableView.currentIndex())
            QApplication.processEvents()
            if mark is None:
                return # nothing is selected
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
            # If a name or URL is too long to fit in the box, this will make
            # the box show the beginning of it rather than the end.
            for i in (self.form.nameBox, self.form.urlBox, self.form.tagsBox):
                i.setCursorPosition(0)

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
    tag_list.append(NOTAGS)
    return tag_list

def make_Session():
    engine = create_engine('sqlite:///sorenmarks.db')
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine) # will not recreate existing tables/dbs
    return Session

# http://stackoverflow.com/questions/9671490/
# how-to-set-sqlite-pragma-statements-with-sqlalchemy
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

def startQt():
    app = QApplication(sys.argv)
    mw = MainWindow()
    app.focusChanged.connect(mw.maybeSaveBookmark)
    mw.show()
    app.exec_()

if __name__ == '__main__':
    startQt()
