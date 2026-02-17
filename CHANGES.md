## Changes in v0.3.0

Bugs:

* Make web links in "About RabbitMark" dialog properly open a browser instead of doing nothing.
* Don't move cursor to a different position in the "Description" text box
  when window focus blurs.
* Properly cancel link check when you press "cancel"
  so it doesn't continue to run in the background and block application exit.
* Always show "(no tags)" first in the tag list, even when some tags start with punctuation.


Features:

* Show the number of bookmarks next to each tag name in the tags pane.
* Remove the experimental Pocket integration, as Pocket no longer exists.
* Add a Readwise Reader integration
  (currently only supports sending bookmarks to Readwise;
  I might add a tool to sync items you have read and marked back into RabbitMark in the future).
  Use "Send to Readwise Reader" on the Bookmark menu and paste a Readwise access token.


Internal:

* Switch to build with uv
* Clean up a bunch of linter errors
