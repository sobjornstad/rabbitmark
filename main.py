# RabbitMark-devel
# Copyright (c) 2015 Soren Bjornstad.
# All rights reserved (temporary; if you read this and want such, contact me
# for relicensing under some FOSS license).

#TODO: Don't allow rich text in description box.
#TODO: Add a thingy to check if archive.org URL is *already* used, and if so to
#      strip out the non-archive.org part and/or do a new snapshot search.
#TODO: Adding new with tags selected and not (no tags) doesn't work as expected.
#TODO: "Pinned" flag (put at top of display)
#TODO: Clear the search box upon adding an item so that the new item shows up.
#TODO: Add an option to select the tags that the current bookmark has?
#TODO: Add some sort of inter-item linkage function.

import datetime
import requests
import sys

from sqlalchemy import create_engine, event, and_, or_
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from PyQt4.QtGui import QApplication, QMainWindow, QDesktopServices, \
        QShortcut, QKeySequence, QMessageBox, QDialog, QCursor
from PyQt4.QtCore import Qt, QAbstractTableModel, SIGNAL, QUrl

from forms.main import Ui_MainWindow
from forms.archivesearch import Ui_Dialog as Ui_ArchiveDialog
from models import Bookmark, Tag, Base
import utils

NOTAGS = "(no tags)"
TAG_SEARCH_MODES = {'AND': 1, 'OR': 0}
DATE_FORMAT = '%Y-%m-%d'

class BookmarkTableModel(QAbstractTableModel):
    """
    Handles the interface to the database. Currently it *also* handles tag
    management, which isn't really part of the description of the model; this
    code should be moved into a TagManager or a set of functions of that
    description soon.
    """
    columns = {'Name': 0, 'Tags': 1}
    def __init__(self, parent, Session, *args):
        QAbstractTableModel.__init__(self)
        self.parent = parent
        self.Session = Session
        self.session = self.Session()
        self.headerdata = ("Name", "Tags")
        self.L = None
        self.updateForSearch("", [], False, TAG_SEARCH_MODES['OR'])

    ### Standard reimplemented methods ###
    def rowCount(self, parent):
        return len(self.L)
    def columnCount(self, parent):
        return len(self.headerdata)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, col, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
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
        if col == self.columns['Name']:
            return mark.name
        elif col == self.columns['Tags']:
            return ', '.join(i.text for i in mark.tags_rel)
        else:
            assert False, "Invalid column %r requested from model's " \
                          "data()" % col

    def sort(self, col, order=Qt.AscendingOrder):
        rev = (order != Qt.AscendingOrder)

        if col == self.columns['Name']:
            key = lambda i: i.name
        elif col == self.columns['Tags']:
            print "DEBUG: Sorting by this column is not supported."
            key = lambda i: None
        else:
            assert False, "Invalid column %r requested from model's " \
                          "sort()" % col

        self.beginResetModel()
        self.L.sort(key=key, reverse=rev)
        self.endResetModel()


    ### Custom methods ###
    def indexFromPk(self, pk):
        for row, obj in enumerate(self.L):
            if obj.id == pk:
                return self.index(row, 0)
        return None

    def makeNewBookmark(self, url="http://", tags=None):
        """
        Create a new bookmark with boilerplate and the provided /url/ or
        'http://' if none. Return the object created.
        """
        new_name = ""
        new_url = url
        if tags is None:
            tags = []
        new_tags = ', '.join(tags)
        new_descr = ""
        new_private = False

        g_bookmark = Bookmark(name=new_name, url=new_url,
                              description=new_descr, private=new_private)
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

    def updateForSearch(self, searchText, tags, showPrivates, searchMode):
        nameText = "%" + searchText + "%"
        self.beginResetModel()
        self.L = []

        # SQLAlchemy doesn't support in_ queries on many-to-many relationships,
        # so it's necessary to get the text of the tags and compare those.
        # NOTE: without my even having to do anything, this behaves the way I
        # want it to for OR when nothing is selected (equivalent to everything).
        # For AND, we explicitly check whether /tags/ is empty and don't do a
        # filter if it is.
        tag_objs = self.session.query(Tag).filter(
                or_(*[Tag.text.like(t) for t in tags]))
        allowed_tags = [i.text for i in tag_objs]

        # TODO: This query uses some unnecessary duplication -- multiple
        # filter()s can be used for the OR query mode too.
        if searchMode == TAG_SEARCH_MODES['OR']:
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

        elif searchMode == TAG_SEARCH_MODES['AND']:
            query = self.session.query(Bookmark).filter(
                    or_(
                        Bookmark.name.like(nameText),
                        Bookmark.url.like(nameText),
                        Bookmark.description.like(nameText)
                       ))
            if NOTAGS in tags:
                query = query.filter(Bookmark.tags_rel == None)
            if len(tags): # don't filter at all if no tags selected
                for tag in allowed_tags:
                    query = query.filter(Bookmark.tags_rel.any(Tag.text == tag))

        else:
            assert False, "in updateForSearch(): Search mode %r " \
                          "unimplemented" % searchMode

        if not showPrivates:
            query = query.filter(Bookmark.private == False)
        for mark in query:
            self.L.append(mark)
        self.sort(0)
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
        tags = mark.tags_rel
        self.session.delete(mark)
        for tag in tags:
            self.maybeExpungeTag(tag)
        self.commit()

        #TODO: When using beginRemoveRows(), a blank row is left in the table.
        # This is a little inconvenient, but it *works* for now.
        #self.beginRemoveRows(index, row, row)
        self.beginResetModel()
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
        self.commit()
        return True

    def deleteTag(self, tag):
        """
        Delete the /tag/ from all bookmarks.
        """
        tag_obj = self.session.query(Tag).filter(Tag.text == tag).one()
        self.session.delete(tag_obj)
        self.commit()

    def maybeExpungeTag(self, tag):
        """
        Delete /tag/ from the tags table if it is no longer referenced by
        any bookmarks.

        Return:
            True if the tag was deleted.
            False if the tag is still referenced and was not deleted.

        WARNING: This method does not call commit() for performance reasons,
        but deletes will not be seen by other operations until a transaction is
        finished. Do not forget to commit after using this method.
        """
        if not len(tag.bookmarks):
            self.session.delete(tag)
            return True
        else:
            return False

    def saveIfEdited(self, mark, content):
        """
        If the content in 'content' differs from the data in the db obj
        'mark', update 'mark' to match the contents of 'content'.

        Returns True if an update was made, False if not.
        """
        if not (mark.name == content['name'] and
                mark.description == content['descr'] and
                mark.url == content['url'] and
                mark.private == content['priv'] and
                [i.text for i in mark.tags_rel] == content['tags']):
            mark.name = content['name']
            mark.description = content['descr']
            mark.url = content['url']
            mark.private = content['priv']

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
                    mark.tags_rel.remove(tag)
                    self.maybeExpungeTag(tag)
            self.commit()
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
        sf = self.form
        sf.action_Quit.triggered.connect(self.quit)
        sf.actionDelete.triggered.connect(self.deleteCurrent)
        sf.actionNew.triggered.connect(self.onAddBookmark)
        sf.actionNew_from_clipboard.triggered.connect(
                self.onAddBookmarkFromClipboard)
        sf.actionRenameTag.triggered.connect(self.onRenameTag)
        sf.actionDeleteTag.triggered.connect(self.onDeleteTag)
        sf.actionWayBack.triggered.connect(self.onWayBackMachine)
        sf.actionShowPrivate.triggered.connect(self.onTogglePrivate)
        self.showPrivates = False

        sf.tagsAllButton.clicked.connect(lambda: self.tagsSelect('all'))
        sf.tagsNoneButton.clicked.connect(lambda: self.tagsSelect('none'))
        sf.tagsInvertButton.clicked.connect(lambda: self.tagsSelect('invert'))
        #self.form.tagsSaveButton.
        #self.form.tagsLoadButton.
        sf.copyUrlButton.clicked.connect(self.copyUrl)
        sf.browseUrlButton.clicked.connect(self.openUrl)
        sf.addButton.clicked.connect(self.onAddBookmark)
        findShortcut = QShortcut(QKeySequence("Ctrl+F"), sf.searchBox)
        findShortcut.connect(findShortcut, SIGNAL("activated()"),
                             sf.searchBox.setFocus)

        # Set up tag mode dropdown.
        # Indexes of these options should match with TAG_SEARCH_MODES.
        sf.tagsModeDropdown.addItem("Require at least one selected tag (OR)")
        sf.tagsModeDropdown.addItem("Require all selected tags (AND)")
        sf.tagsModeDropdown.activated.connect(self.doUpdateForSearch)

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

    def closeEvent(self, evt):
        "Catch click of the X button, etc., and properly quit."
        self.quit()

    def quit(self):
        # fake changing focus: the widget name for new is arbitrary,
        # one of the editable boxes is required for old
        self.maybeSaveBookmark(old=self.form.nameBox, new=self.form.nameBox)
        self.tableModel.commit()
        sys.exit(0)

    def onTogglePrivate(self):
        self.showPrivates = not self.showPrivates
        self.doUpdateForSearch()

    def onAddBookmarkFromClipboard(self):
        pastedUrl = unicode(QApplication.clipboard().text()).strip()
        if not '://' in pastedUrl:
            utils.warningBox("No protocol (e.g., http://) in URL. Adding "
                             "http:// to beginning. You may wish to check "
                             "the URL.", "URL possibly invalid")
            pastedUrl = 'http://' + pastedUrl
        self.onAddBookmark(urltext=pastedUrl)

    def onAddBookmark(self, isChecked=False, urltext="http://"):
        # isChecked is not used
        tags = [unicode(i.text())
                for i in self.form.tagList.selectedItems()]
        newMark = self.tableModel.makeNewBookmark(urltext, tags)
        self.doUpdateForSearch()
        index = self.tableModel.indexFromPk(newMark.id)
        self.tableView.setCurrentIndex(index)
        self.form.nameBox.setFocus()

    def deleteCurrent(self):
        if not self.sm.hasSelection():
            utils.errorBox("Please select a bookmark to delete.",
                           "No bookmark selected")
            return
        index = self.tableView.currentIndex()
        nextPk = self.tableModel.deleteBookmark(index)
        index = self.tableModel.indexFromPk(nextPk)
        self.resetTagList()
        self.tableView.setCurrentIndex(index)

    def copyUrl(self):
        QApplication.clipboard().setText(self.form.urlBox.text())
    def openUrl(self):
        QDesktopServices.openUrl(QUrl(self.form.urlBox.text()))

    def onWayBackMachine(self):
        """
        Find a URL from the WayBackMachine that can replace the current URL
        (presumably if the formerly working URL has stopped working, or perhaps
        if we just want to make sure it will work in the future or save a
        particular version of the page).

        This method requests a list of snapshots from the CDX (more
        complicated) WayBackMachine API on archive.org, then creates a
        WayBackDialog to allow the user to find a snapshot that contains the
        content they were hoping for. Finally, it rewrites the value in the
        URLbox (which will result in it being saved when the focus changes,
        just as when the user edits it) to match the new snapshot.

        No arguments, no return.
        """
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        mark = self.tableModel.getObj(self.tableView.currentIndex())
        site = mark.url
        requestUrl = "http://web.archive.org/cdx/search/cdx?url=%s&output=json"
        result = requests.get(requestUrl % site)
        try:
            # If no results, .json() may raise ValueError or just return None.
            snapshots = result.json()
            if not snapshots:
                raise ValueError
        except ValueError:
            QApplication.restoreOverrideCursor()
            utils.informationBox("Sorry, the WayBackMachine does not have "
                                 "this page archived.", "Page not found")
            return

        archived = []
        for i in snapshots[1:]: # first row is headers
            timestamp, pagePath = i[1], i[2]
            formattedTimestamp = datetime.datetime.strptime(
                    timestamp, '%Y%m%d%H%M%S').strftime(DATE_FORMAT)
            archivedUrl = "http://web.archive.org/web/%s/%s" % (
                    timestamp, pagePath)
            archived.append((formattedTimestamp, timestamp, archivedUrl))

        QApplication.restoreOverrideCursor()
        dlg = WayBackDialog(self, archived)
        snapshotIndex = dlg.exec_()
        if snapshotIndex != -1: # if not cancelled
            self.form.urlBox.setText(archived[snapshotIndex][2])


    def onRenameTag(self):
        tags = [unicode(i.text())
                for i in self.form.tagList.selectedItems()]

        if len(tags) < 1:
            utils.errorBox("Please select a tag to rename.",
                           "No tag selected")
            return
        elif len(tags) > 1:
            utils.errorBox("Tags cannot be renamed in bulk. Please select"
                           "exactly one tag.", "Cannot rename multiple tags")
            return

        tag = tags[0]
        new, doContinue = utils.inputBox("New name for tag:", "Rename tag", tag)
        if doContinue:
            if self.tableModel.renameTag(tag, new):
                self.resetTagList()
                self.fillEditPane()
            else:
                utils.errorBox("A tag by that name already exists.",
                               "Cannot rename tag")

    def onDeleteTag(self):
        tags = [unicode(i.text())
                for i in self.form.tagList.selectedItems()]

        if len(tags) < 1:
            utils.errorBox("Please select a tag to delete.",
                           "No tag selected")
            return
        elif len(tags) > 1:
            utils.errorBox("Sorry, you currently cannot delete tags in bulk.",
                           "Cannot delete multiple tags")
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
        Update the state of the database object associated with the currently
        selected bookmark.

        Arguments:
            old - the widget that previously had focus
            new - the widget that has just gained focus (unused)

        Return:
            None.

        This method is called by the signal set in startQt() when any focus
        changes, as well as before quitting.
        """
        sf = self.form
        if old in (sf.nameBox, sf.urlBox, sf.descriptionBox, sf.tagsBox,
                   sf.privateCheck):
            mark = self.tableModel.getObj(self.tableView.currentIndex())
            QApplication.processEvents()
            if mark is None:
                return # nothing is selected
            if self.tableModel.saveIfEdited(mark, self.mRepr()):
                self.resetTagList()
            self.doUpdateForSearch()

    def doUpdateForSearch(self):
        """
        Call tableModel.updateForSearch() to bring the contents of the
        bookmarks table into sync with the filter and tag selection.

        We determine and pass the text in the filter box and a list of the tags
        selected, and we restore the selection to the currently selected
        bookmark after the view is refreshed if that bookmark is still in the
        new view.

        No arguments, no return.
        """
        selectedTags = [unicode(i.text())
                        for i in self.form.tagList.selectedItems()]
        mark = self.tableModel.getObj(self.tableView.currentIndex())
        oldId = None if mark is None else mark.id
        searchMode = self.form.tagsModeDropdown.currentIndex()
        self.tableModel.updateForSearch(
                unicode(self.form.searchBox.text()),
                selectedTags,
                self.showPrivates,
                searchMode)
        self.reselectItem(oldId)
        self.updateTitleCount(self.tableModel.rowCount(self))

    def reselectItem(self, item=None):
        """
        Select the given /item/ if it still exists in the view, or the first
        item in the view if it doesn't or /item/ is None.

        This method should to be called after updating the table view using a
        resetModel() command, as that causes the loss of the current selection.

        Arguments:
            item (default None) - if not None, attempt to select the item by
                this primary key.
        """
        if item is None:
            idx = self.tableModel.index(0, 0)
        else:
            idx = self.tableModel.indexFromPk(item)
            if idx is None: # provided item isn't in this view
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
            self.form.privateCheck.setChecked(mark.private)
            tags = ', '.join([i.text for i in mark.tags_rel])
            self.form.tagsBox.setText(tags)
            # If a name or URL is too long to fit in the box, this will make
            # the box show the beginning of it rather than the end.
            for i in (self.form.nameBox, self.form.urlBox, self.form.tagsBox):
                i.setCursorPosition(0)

    def tagsSelect(self, what):
        # Block signals so that we only have to call itemSelectionChanged
        # once instead of numTags times -- this *greatly* improves performance.
        oldSigs = self.form.tagList.blockSignals(True)
        for i in range(self.form.tagList.count()):
            if what == 'none':
                self.form.tagList.item(i).setSelected(False)
            elif what == 'all':
                self.form.tagList.item(i).setSelected(True)
            elif what == 'invert':
                currentStatus = self.form.tagList.item(i).isSelected()
                self.form.tagList.item(i).setSelected(not currentStatus)
            else:
                assert False, "Invalid argument to tagsSelect!"
        self.form.tagList.blockSignals(oldSigs)
        self.form.tagList.itemSelectionChanged.emit()

    def mRepr(self):
        """
        Short for "mark representation": return a dictionary of the content
        currently in the fields so that the model can compare and/or save it.
        """
        return {
                'name':  unicode(self.form.nameBox.text()),
                'url':   unicode(self.form.urlBox.text()),
                'descr': unicode(self.form.descriptionBox.toPlainText()),
                'priv':  self.form.privateCheck.isChecked(),
                'tags':  [i.strip() for i in
                          unicode(self.form.tagsBox.text()).split(',')
                          if i.strip() != ''],
               }

    def updateTitleCount(self, count):
        """
        Change the count of matching items that appears in the title bar to
        /count/.
        """
        self.setWindowTitle("RabbitMark - %i match%s" % (
                count, '' if count == 1 else 'es'))


class WayBackDialog(QDialog):
    """
    Allow the user to search through the snapshots provided by the
    WayBackMachine using a binary search algorithm.

    To set up the dialog, snapshotData must be provided to the constructor;
    snapshot data consists of a list of tuples containing a formatted timestamp
    (in whatever format the user should see it), a raw timestamp (format
    '%Y%m%d%H%M%S'), and the full URL to that snapshot on the web.

    When the user has made a selection, exec_() will return an index value into
    the snapshotData list corresponding to the snapshot the user selected, or
    -1 if the user cancelled the dialog.
    """

    state_label_template = "You are at snapshot %i, bisecting %i to %i (%i " \
                           "total snapshots).\nHow do you want to proceed?"
    snapshot_label_template = "The following snapshot is from %s:"

    def __init__(self, parent, snapshotData):
        """
        Set up the dialog as usual.

        Arguments:
            parent - parent widget, as normal
            snapshotData - see the class docstring.
        """
        QDialog.__init__(self)
        self.form = Ui_ArchiveDialog()
        self.form.setupUi(self)
        self.parent = parent

        self.form.useRadio.setChecked(True)
        self.form.okButton.clicked.connect(self.onContinue)
        self.form.copyButton.clicked.connect(self.onCopy)
        self.form.browseButton.clicked.connect(self.onBrowseTo)

        self.sd = snapshotData # list of snapshots
        self.lower = None      # lowest possible target snapshot index
        self.upper = None      # highest possible target snapshot index
        self.curnt = None      # current snapshot index
        self.stack = []        # history of past values of 3 variables above
        self.proceed('start')

    def reject(self):
        """
        0 is a possible return value on accept, meaning to use the first
        snapshot in the list, so we have to redefine reject()'s traditional
        return value of 0 as -1.
        """
        QDialog.done(self, -1)

    def onCopy(self):
        "Copy URL to clipboard -- same as in MainWindow."
        QApplication.clipboard().setText(self.form.urlBox.text())

    def onBrowseTo(self):
        "Browse to shown URL -- same as in MainWindow."
        QDesktopServices.openUrl(QUrl(self.form.urlBox.text()))

    def proceed(self, action):
        """
        Move a step forward in our binary search algorithm.

        The single argument /action/ is one of the following strings:
            'start'   - initialize the algorithm, starting at latest snapshot
            'later'   - say that the target snapshot is more recent than
                        current
            'earlier' - say that the target snapshot is older than current
            'backup'  - pop control vars off the stack and go back one step in
                        the search algorithm
        Other values will raise an AssertionError.

        This method assumes that the action requested is valid with the current
        values of the control variables; the interface is responsible for
        making sure the user cannot select an invalid action. At the end of
        proceed() we call self.checkAllowableActions(), which is responsible
        for disabling options that could result in this method receiving an
        invalid action.
        """

        # Save current search parameters to a stack for later undo before
        # beginning an action that changes them.
        if action in ('earlier', 'later'):
            self.stack.append((self.lower, self.upper, self.curnt))

        # Process the provided action.
        if action == 'start':
            self.lower = 0
            self.upper = len(self.sd) - 1
            self.curnt = self.upper
        elif action == 'later':
            self.lower = self.curnt + 1
            increaseBy = (self.upper - self.curnt + 1) / 2
            # always move by at least 1, to allow taking the final step
            #TODO: With the addition of the +1 above, I'm not sure this 
            #      conditional is required anymore
            self.curnt = self.curnt + (increaseBy if increaseBy > 0 else 1)
        elif action == 'earlier':
            self.upper = self.curnt - 1
            decreaseBy = (self.curnt - self.lower + 1) / 2
            self.curnt = self.curnt - (decreaseBy if decreaseBy > 0 else 1)
        elif action == 'backup':
            self.lower, self.upper, self.curnt = self.stack.pop()
        else:
            assert False, "Invalid action!"
        self.checkAllowableActions()
        self.updateDialogText()

    def updateDialogText(self):
        """
        Update the dialog box to show the user appropriate details about the
        state of the search.

        This method should be called after proceed() is done.
        """
        tstamp, _, url = self.sd[self.curnt]
        self.form.urlBox.setText(url)
        self.form.urlBox.setCursorPosition(0)

        # note: display converted to 1-based indexing for user-friendliness
        if len(self.sd) > 1 and self.curnt+1 == 1:
            state = "This is the oldest of %i snapshots.\n" \
                    "What do you want to do?" % len(self.sd)
        elif len(self.sd) > 1 and self.curnt+1 == len(self.sd):
            state = "This is the most recent of %i snapshots.\n" \
                    "What do you want to do?" % len(self.sd)
        elif len(self.sd) == 1:
            state = "This is the only available snapshot.\n" \
                    "What do you want to do?"
        else:
            state = self.state_label_template % (
                    self.curnt+1, self.lower+1, self.upper+1, len(self.sd))
        self.form.stateLabel.setText(state)
        self.form.snapshotLabel.setText(self.snapshot_label_template % tstamp)

    def checkAllowableActions(self):
        """
        Determine which search actions make sense to allow with the current
        state of the search (for instance, it doesn't make sense to try a newer
        snapshot when the current snapshot is equal to the upper bound), and
        disable those that don't. Additionally, reselect the "use" option.

        This method should be called after proceed() is done.
        """
        sf = self.form
        sf.newerRadio.setEnabled(self.upper > self.curnt)
        sf.olderRadio.setEnabled(self.lower < self.curnt)
        sf.backupRadio.setEnabled(len(self.stack) > 0)
        sf.useRadio.setChecked(True)

    def onContinue(self):
        """
        Runs when "OK" is clicked. If "use" or "cancel" is selected, the dialog
        is accepted or rejected as appropriate; if another option is selected,
        proceed() is called to move another step into the search algorithm.
        """
        if self.form.useRadio.isChecked():
            self.done(self.curnt)
        elif self.form.newerRadio.isChecked():
            self.proceed('later')
        elif self.form.olderRadio.isChecked():
            self.proceed('earlier')
        elif self.form.backupRadio.isChecked():
            self.proceed('backup')
        elif self.form.cancelRadio.isChecked():
            self.reject()
        else:
            assert False, "No radio button selected! This should be " \
                          "impossible."


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
