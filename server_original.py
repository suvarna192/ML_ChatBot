import websockets
import asyncio
import threading
import logging
import http.server
import socketserver
import os
import signal
from running_bot import running_bot
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server data
HOST = 'localhost'
PORT = 7890
HTTP_PORT = 8002  # Port for serving HTML file
logger.info("Server listening on Port %d", PORT)

# Dictionary to store session IDs for each WebSocket connection
sessions = {}
context = {}
dialogue_state = {}


# Flag to indicate whether the HTTP server should keep serving
http_server_running = True

# Function to handle logging for each session
def setup_logging(session_id):
    log_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    log_file = os.path.join(log_directory, f"{session_id}.log")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    session_logger = logging.getLogger(session_id)
    session_logger.addHandler(handler)
    session_logger.setLevel(logging.INFO)
    return session_logger

# Function to handle logging for errors
def setup_error_logging():
    error_log_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
    if not os.path.exists(error_log_directory):
        os.makedirs(error_log_directory)
    error_log_file = os.path.join(error_log_directory, "error.log")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(error_log_file)
    handler.setFormatter(formatter)
    error_logger = logging.getLogger("error_logger")
    error_logger.addHandler(handler)
    error_logger.setLevel(logging.ERROR)
    return error_logger

# Initialize error logger
error_logger = setup_error_logging()

# The main behavior function for the WebSocket server
async def echo(websocket, path):
    # Generate a unique session ID for the current WebSocket connection
    session_id = str(id(websocket))
    sessions[session_id] = websocket
    session_logger = setup_logging(session_id)
    context[session_id] = []
    dialogue_state[session_id] = ""
    
    logger.info("A client connected with session ID: %s", session_id)

    # Handle incoming messages
    try:
        async for message in websocket:
            session_logger.info(f"User: {message}")
            # context[session_id].append(message)
            # Process the message using running_bot function
            user_input = message
            input_id = session_id
            customer_details = {'balance_transfer': 'balance transfer of 12 lakh', 'topup_offer': 'topup value upto 7 lakhs'}

            customer_details = json.dumps(customer_details)
            response, status = running_bot(user_input, input_id, customer_details)


            if status not in ["Acknowledgement", "greetings", "Information", "OutOfScope", "Exception"] and status not in ['job enquiry', 'Company Enquire', 'Tech support enquire', 'Employee Enquire']:
                dialogue_state[session_id] = status

            print(response, status)
            
            if response == "Could not understand your query. Please rephrase it again":
                # Log error with session ID and user query in both session log file and error log file
                error_message = f"Session ID: {session_id} - User Query: {message}"
                session_logger.info(f"Bot: {response}")
                error_logger.error(error_message)
                await websocket.send(response)
                context[session_id].append(response)
            else:
                if status in ["Acknowledgement", "greetings", "Information"] and dialogue_state[session_id] != "":
                    print('--->>', dialogue_state[session_id], status)
                    response = guided_flow[dialogue_state[session_id]][status]

                session_logger.info(f"Bot: {response}")
                # Send response including session ID and message
                await websocket.send(response)
                context[session_id].append(response)
           
    # Handle disconnecting clients
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"A client with session ID %s disconnected", session_id)
    finally:
        del sessions[session_id]
        session_logger.handlers.clear()  # Remove handler to avoid memory leak

# Function to serve HTML file
def serve_html():
    global http_server
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", HTTP_PORT), Handler)
    logger.info("Serving HTML file at http://%s:%d/client.html", HOST, HTTP_PORT)
    http_server = httpd
    http_server.serve_forever()

# Start the WebSocket server
def start_websocket_server():
    global ws_server
    ws_server = websockets.serve(echo, HOST, PORT)
    asyncio.get_event_loop().run_until_complete(ws_server)

# Function to handle SIGINT (ctrl+c)
def signal_handler(sig, frame):
    global http_server_running
    global ws_server
    global http_server
    
    logger.info('Stopping servers...')
    http_server_running = False
    if http_server:
        http_server.shutdown()
    if ws_server:
        ws_server.close()
    asyncio.get_event_loop().stop()

# Register signal handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)

# Start the HTTP server in a separate thread
html_thread = threading.Thread(target=serve_html)
html_thread.start()

# Start the WebSocket server
start_websocket_server()

# Run the event loop indefinitely
asyncio.get_event_loop().run_forever()
