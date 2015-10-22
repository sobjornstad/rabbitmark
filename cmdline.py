# This code was in main.py and should no longer be needed.


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

