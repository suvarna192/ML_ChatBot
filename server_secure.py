import websockets
import asyncio
import threading
import logging
import http.server
import socketserver
import os
import signal
from faqengine import FaqEngine
import ssl
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server data
HOST = '192.168.100.37'
PORT = 7890
HTTP_PORT = 8002  # Port for serving HTML file
logger.info("Server listening on Port %d", PORT)

# Dictionary to store session IDs for each WebSocket connection
sessions = {}
context = {}
dialogue_state = {}

guided_flow = {}
guided_flow[' webinar enquire'] = {}
guided_flow[' webinar enquire']["greetings"] = "Welcome to Sumasoft How we may I help you?"
guided_flow[' webinar enquire']['Information'] = "Thanks for sharing your details."
guided_flow[' webinar enquire']['Acknowledgement'] = "Thank you for contacting suma soft pvt. ltd."

# guided_flow = {}
guided_flow['service line Enquire '] = {}
guided_flow['service line Enquire ']["greetings"] = "Welcome to Sumasoft How we may I help you?"
guided_flow['service line Enquire ']['Information'] = "Thanks for sharing your details."
guided_flow['service line Enquire ']['Acknowledgement'] = "Thank you for contacting suma soft pvt. ltd."

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
    logger = logging.getLogger(session_id)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

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
            context[session_id].append(message)
            # Process the message using FAQ engine
            response,_class = faq_model.query(message)
            # print(response,_class)
            if not _class in ["Acknowledgement","greetings","Information","OutOfScope","Exception"] and not _class  in ['job enquiry','Company Enquire','Tech support enquire','Employee Enquire']:
                dialogue_state[session_id] = _class

            print(response,_class)
            
            if response == "Could not understand your query. Please rephrase it again":
                # Log error with session ID and user query in both session log file and error log file
                error_message = f"Session ID: {session_id} - User Query: {message}"
                session_logger.info(f"Bot: {response}")
                error_logger.error(error_message)
                await websocket.send(response)
                context[session_id].append(response)
            else:
                if  _class in ["Acknowledgement","greetings","Information"] and dialogue_state[session_id] != "":
                    print('--->>',dialogue_state[session_id],_class)
                    #import pdb; pdb.set_trace()
                    response = guided_flow[dialogue_state[session_id]][_class]
                else:
                    pass


                session_logger.info(f"Bot: {response}")
                # Send response including session ID and message
                await websocket.send(response)
                context[session_id].append(response)
           
    # Handle disconnecting clients
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"A client with session ID {session_id} disconnected")
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
    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # ssl_context.load_cert_chain(certfile="/home/sadmin/chatbot/newsumabot/src/sumasoft.com.pem", keyfile="/home/sadmin/chatbot/newsumabot/src/sumasoft_key.pem")
    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # localhost_pem = pathlib.Path(__file__).with_name("localhost.pem")
    certfile_path = "/home/sadmin/chatbot/newsumabot/src/sumasoft.com.pem"
    keyfile_path = "/home/sadmin/chatbot/newsumabot/src/sumasoft_key.pem"
    ssl_context.load_cert_chain(certfile=certfile_path, keyfile=keyfile_path)

    ws_server = websockets.serve(echo, HOST, PORT,ssl=ssl_context)
    asyncio.get_event_loop().run_until_complete(ws_server)

# Load FAQs data and initialize FAQ engine
base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
faqs_list = [os.path.join(base_path, "Greetings.csv"), os.path.join(base_path, "sumasoft.csv"),os.path.join(base_path, "Information.csv"),os.path.join(base_path, "Acknowledgement.csv")]
faq_model = FaqEngine(faqs_list, 'sentence-transformers')

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
