import io, sys, builtins, contextlib
import threading
from time import sleep
from traceback import format_tb
from socket import gethostbyname, gethostname
from flask import Flask, cli
from flask_socketio import SocketIO, emit
import logging
import qrcode


######################################################################
# FLASK
host = gethostbyname(gethostname())
port = "5000" # Flask's default port
app = Flask("chatio")
socketio = SocketIO(app) #, logger=False, engineio_logger=False)
connected = False

# Quiet:
logging.getLogger("werkzeug").setLevel(logging.ERROR)
cli.show_server_banner = lambda *args: None

@app.route("/")
def index():
  return html # defined at the end of this file


######################################################################
# SOCKET.IO
@socketio.on('connect')
def client_connected():
  global connected, print_buffer, input_buffer
  connected = True
  # Send buffered output
  for msg in print_buffer:
    socketio.emit("print", msg)
  print_buffer.clear()
  input_buffer.clear()

@socketio.on('disconnect')
def client_disconnected():
  global connected, print_buffer, input_buffer
  connected = False

@socketio.on('input')
def handle_input(i):
  global input_buffer
  input_buffer.append(i)


######################################################################
# I/O REDIRECTS
print_buffer = []
input_buffer = []

def redirected_print(*objs, sep='', end='\n', file=sys.stdout, flush=False):
  global so
  if connected:
    socketio.emit("print", "".join([str(s) + " " for s in objs]))
  else:
    print_buffer.append(objs)
    #sys_print(*objs, end=end, file=file, flush=flush)
  sleep(0.5)
  return

def redirected_input(prompt=None):
  if prompt != None:
    print(prompt)
  while len(input_buffer) < 1:
    socketio.emit("waiting for input")
    sleep(0.5)
  return input_buffer.pop(0)
  #return sys_input("sys_input():")

def redirect_except(typ, value, tracebac):
  if connected:
    socketio.emit("error", typ.__name__)
    socketio.emit("error", str(value))
    socketio.emit("error", format_tb(tracebac))
    sleep(2.0)
  sys_except(typ, value, tracebac)


sys_print  = builtins.print
sys_input  = builtins.input
sys_except = sys.excepthook

builtins.print = redirected_print
builtins.input = redirected_input
sys.excepthook = redirect_except


######################################################################
# THREAD
threading.Thread(target=lambda : socketio.run(app,host=host,port=port,log_output=False,debug=False), daemon=True).start()
# daemon threads are automatically terminated when the main thread exits
sleep(2)


######################################################################
# QR
url = "".join(["http://",host,":",port])
sys_print(url)
qr = qrcode.QRCode()
qr.add_data(url)
qr.print_ascii() # outputs to sys.out


######################################################################
# CSS
css = """
  html, body {
    background-color: gray;
    font-size: 18pt;
  }
  #display {
	  background-color: white;
	  box-shadow: 10px 10px 5px black;
    max-width: 30em;
    padding: 1em;
    margin: auto;
    max-height: 90%;
  }
  #chat-logs {
    min-height: 30em;
    /*overflow-y: scroll;*/
  }
	.chat {
		border-top: solid;
	}
  #send-bar {
		border-top: solid;
  }
  #send-bar #compose-text {
    font-size: 18pt;
    width: 97%;
  }
  .chat > div {
    color: white;
    max-width: 66%;
    width: fit-content;
    border-radius: 1em;
    padding-left: 0.5em;
    padding-right: 0.5em;
  }
  div.chat > div.right {
    background-color: #4590f6; /* blue */
    border-bottom-right-radius: 0.25em;
    margin-left: auto;
  }
  div.chat > div.left {
    background-color: #73e174; /* green */
    border-bottom-left-radius: 0.25em;
    margin-right: auto;
  }
  div.chat > div.error {
    background-color: red;
    border-bottom-left-radius: 0.25em;
    margin-right: auto;
  }
"""

######################################################################
# JAVASCRIPT
javascript = """
	const socket = io({'reconnection': true,'reconnectionDelayMax': 500});
	socket.on("connect", function() {
		console.log("Connected");
		document.getElementById("compose-text").disabled = true;
		document.getElementById("send").disabled = true;
		document.getElementById("processing").hidden = false;
	});
	socket.on("disconnect", function() {
		console.log("Disconnected");
		document.getElementById("compose-text").disabled = true;
		document.getElementById("send").disabled = true;
		document.getElementById("processing").hidden = true;
		chat_logs = document.getElementById("chat-logs")
		old_chat  = document.getElementById("active-chat")
		new_chat  = document.createElement('div');
		old_chat.removeAttribute('id');
		new_chat.setAttribute('class', 'chat')
		new_chat.setAttribute('id','active-chat')
		chat_logs.appendChild(new_chat);
		new_chat.appendChild(document.getElementById("processing"));
	});
	socket.on("print", function(msg) {
		console.log("Got a websocket message:", msg);
		addMessage(msg, "left");
	});
	socket.on("error", function(msg) {
		console.log("Got a websocket message:", msg);
		addMessage(msg, "error");
	});
	socket.on("waiting for input", function() {
		console.log("Socket Waiting for Input");
		document.getElementById("send").disabled = false;
		document.getElementById("compose-text").disabled = false;
		document.getElementById("compose-text").focus();
		document.getElementById("processing").hidden = true;
	});
	document.getElementById("send").addEventListener("click", function() {
		textbox = document.getElementById("compose-text");
		console.log("Sending:" + textbox.value);
		socket.emit("input", textbox.value);
		addMessage(textbox.value, "right");
		textbox.value = "";
		document.getElementById("send").disabled = true;
		document.getElementById("compose-text").disabled = true;
		document.getElementById("processing").hidden = false;
	});
	function addMessage(msg, side) {
		chat = document.getElementById("active-chat");
		div  = document.createElement("div");
		p    = document.createElement("p");
		txt  = document.createTextNode(msg);
		div.setAttribute("class", side);
		p.appendChild(txt);
		div.appendChild(p);
		chat.appendChild(div);
		chat.insertBefore(div, document.getElementById("processing"));
		chat.scrolltop = chat.scrollHeight;
	}
"""

######################################################################
# HTML
html = """
	<!DOCTYPE html>
	<html lang="en">
		<head>
			<meta charset="utf-8">
			<meta name="viewport" content="width=device-width, initial-scale=1.0">
			<title>ChatIO</title>
			<style>
				"""+css+"""
			</style>
		</head>
		<body>
			<div id="display">
			  <div id="chat-logs">
  				<div class="chat" id="active-chat">
	  				<div id="processing" class="left" hidden="true"><p>...</p></div>
		  		</div>
		  	</div>
				<div id="send-bar">
					<form>
						<input type="text" id="compose-text" />
						<input type="submit" id="send" value="Send" />
					</form>
				</div>
			</div>
			<script src="https://cdn.socket.io/4.7.5/socket.io.min.js" crossorigin="anonymous"></script>
			<script>
				"""+javascript+"""
			</script>
		</body>
	</html>
"""

