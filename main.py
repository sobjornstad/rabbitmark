from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from models import Bookmark, Base


def make_Session():
    engine = create_engine('sqlite:///testdb.db')
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine) # will not recreate existing db's
    return Session


if __name__ == '__main__':
    Session = make_Session()
    session = Session()

    while True:
        print "\nBookmark Database"
        print "Would you like to:"
        print "1) Add a bookmark"
        print "2) Search for a bookmark"
        print "0) Quit"
        what_do = raw_input("> ")

        if what_do == "1":
            print "We're going to add a bookmark. Where shall it be?"
            new_name = raw_input("Name: ")
            new_url = raw_input("Url: ")
            new_tags = raw_input("Tags: ")
            new_descr = raw_input("Description: ")
            g_bookmark = Bookmark(name=new_name, url=new_url, tags=new_tags,
                                  description=new_descr)
            session.add(g_bookmark)
            print "Added bookmark with name %s." % new_name
        elif what_do == "2":
            search_for = raw_input("Name (substr search): ")
            search_for = "%" + search_for + "%"
            for bookmark in session.query(Bookmark).filter(
                    Bookmark.name.like(search_for)):
                print "Name: %s" % bookmark.name
                print "URL : %s" % bookmark.url
                print "Tags: %s" % bookmark.tags
                print "Description:"
                print bookmark.description
                print ""
        elif what_do == "0":
            print "Exiting."
            session.commit()
            break
        else:
            print "I didn't get that."
