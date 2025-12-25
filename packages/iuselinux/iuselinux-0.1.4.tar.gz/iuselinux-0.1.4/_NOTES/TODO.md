- About should be a tab in settings, not just something on the bottom of the page. Also include a link to www.iuselinux.com
- When i press start service just now i saw "Service Not Installed. Run `iuselinux service install`". Detect if service is installed. If not installed, there is no reason for service status or start server, do install service instead.


- cache and slow load. dynamic update. paginate
- background service?


- All permissions (request and stats) in settings


----

- unread icon?

- urls?

Some more issues:

- Multiple images

----

- is there auto resume connection
- what does default chats to return default chat limit in api do?
- what about message limit?
- where is advanced?

----

The install/uninstall logic of this application must be flawless. I never want it to be the case that a user struggles to get rid of this application, or struggles to update it. Audit every single component related to install/uninstall, including for tailscale and including the auto-update. Do each component you find independently in a sub agent. Merge the results back to a report "installables_audit.md" including bugs/issues sorted by critical. After creating that report, you may verify things by running commands to install/uninstall. However, since there are sub agents those shouldn't since they may interfere with each other.

Look through all operations that can affect this the users operating system (sqlite operations, sending things, etc). Create a list of all of them. Then with sub agents audit each one to make sure nothing dangerous is being done that could *break* other applications or the operating sytem. Write back findings to dangerous_audit.md
