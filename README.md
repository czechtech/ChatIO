# ChatIO
Present a more familiar interface for text-only input and output for introductory programming students.

Implemented by redirecting stdout, stdin, and stderr to display the text output and input of a typical command line python program.  Instead of the typical rudimentary console display, the i/o will be handled in a web browser with a chat-bubble-like interface.

![screenshot](docs/chatio_screenshot.png)

Requires:
 * Flask
 * Flask_socketio
 * Python_QRCode
