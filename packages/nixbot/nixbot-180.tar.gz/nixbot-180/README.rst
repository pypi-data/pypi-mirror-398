**NAME**


|
| ``nixbot`` - NIXBOT
|


**SYNOPSIS**


|
| ``nixbot <cmd> [key=val] [key==val]``
| ``nixbot -cvaw [init=mod1,mod2]``
| ``nixbot -d`` 
| ``nixbot -s``
|

**DESCRIPTION**


``NIXBOT`` has all you need to program a unix cli program, such as disk
perisistence for configuration files, event handler to handle the
client/server connection, deferred exception handling to not crash
on an error, etc.

``NIXBOT`` contains python3 code to program objects in a functional way.
it provides an "clean namespace" Object class that only has dunder
methods, so the namespace is not cluttered with method names. This
makes storing and reading to/from json possible.

``NIXBOT`` is a python3 IRC bot, it can connect to IRC, fetch and
display RSS feeds, take todo notes, keep a shopping list and log
text. You can run it under systemd for 24/7 presence in a IRC channel.

``NIXBOT`` is Public Domain.


**INSTALL**


installation is done with pipx

|
| ``$ pipx install nixbot``
| ``$ pipx ensurepath``
|
| <new terminal>
|
| ``$ nixbot srv > nixbot.service``
| ``$ sudo mv nixbot.service /etc/systemd/system/``
| ``$ sudo systemctl enable nixbot --now``
|
| joins ``#nixbot`` on localhost
|


**USAGE**


use ``nixbot`` to control the program, default it does nothing

|
| ``$ nixbot``
| ``$``
|

see list of commands

|
| ``$ nixbot cmd``
| ``cfg,cmd,dne,dpl,err,exp,imp,log,mod,mre,nme,``
| ``pwd,rem,req,res,rss,srv,syn,tdo,thr,upt``
|

start console

|
| ``$ nixbot -c``
|

start console and run irc and rss clients

|
| ``$ nixbot -c init=irc,rss``
|

list available modules

|
| ``$ nixbot mod``
| ``err,flt,fnd,irc,llm,log,mbx,mdl,mod,req,rss,``
| ``rst,slg,tdo,thr,tmr,udp,upt``
|

start daemon

|
| ``$ nixbot -d``
| ``$``
|

start service

|
| ``$ nixbot -s``
| ``<runs until ctrl-c>``
|


**COMMANDS**


here is a list of available commands

|
| ``cfg`` - irc configuration
| ``cmd`` - commands
| ``dpl`` - sets display items
| ``err`` - show errors
| ``exp`` - export opml (stdout)
| ``imp`` - import opml
| ``log`` - log text
| ``mre`` - display cached output
| ``pwd`` - sasl nickserv name/pass
| ``rem`` - removes a rss feed
| ``res`` - restore deleted feeds
| ``req`` - reconsider
| ``rss`` - add a feed
| ``syn`` - sync rss feeds
| ``tdo`` - add todo item
| ``thr`` - show running threads
| ``upt`` - show uptime
|

**CONFIGURATION**


irc

|
| ``$ nixbot cfg server=<server>``
| ``$ nixbot cfg channel=<channel>``
| ``$ nixbot cfg nick=<nick>``
|

sasl

|
| ``$ nixbot pwd <nsnick> <nspass>``
| ``$ nixbot cfg password=<frompwd>``
|

rss

|
| ``$ nixbot rss <url>``
| ``$ nixbot dpl <url> <item1,item2>``
| ``$ nixbot rem <url>``
| ``$ nixbot nme <url> <name>``
|

opml

|
| ``$ nixbot exp``
| ``$ nixbot imp <filename>``
|


**PROGRAMMING**

|
| nixbot has it's user modules in the ~/.nixbot/mods directory so for a
| hello world command you would  edit a file in ~/.nixbot/mods/hello.py
| and add the following
|

::

    def hello(event):
        event.reply("hello world !!")


|
| typing the hello command would result into a nice hello world !!
|

::

    $ nixbot hello
    hello world !!


|
| commands run in their own thread and the program borks on exit to enable a
| short debug cycle, output gets flushed on print so exceptions appear in the
| systemd logs. modules can contain your own written python3 code.
|


**FILES**

|
| ``~/.nixbot``
| ``~/.local/bin/nixbot``
| ``~/.local/pipx/venvs/nixbot/*``
|

**AUTHOR**

|
| ``Bart Thate`` <``bthate@dds.nl``>
|

**COPYRIGHT**

|
| ``NIXBOT`` is Public Domain.
|

