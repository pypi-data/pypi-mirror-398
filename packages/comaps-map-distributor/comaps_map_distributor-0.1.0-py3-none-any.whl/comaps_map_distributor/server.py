import os
import glob 

from http.server import HTTPServer
import socket
import netifaces
from RangeHTTPServer import RangeRequestHandler

from functools import partial

class MyRequestHandler(RangeRequestHandler):
    protocol_version = "HTTP/1.1"


def get_available_versions(directory):
    map_dict = {}
    version_numbers = glob.glob(directory+"/maps/*")
    version_numbers = [e.split('/')[-1] for e in version_numbers]
    for v in version_numbers:
        maps = glob.glob(directory+"/maps/{}/*".format(v))
        maps = [m.split('/')[-1].replace('.mwm','') for m in maps]
        map_dict[v] = maps
    return  map_dict

def find_free_port():
    """
    iterate over potential ports and return first free one
    """
    ports =  [80, 8000, 8080] + list(range(4000,5000))
    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('localhost', port))
            s.close()
            return port
        except OSError:
            pass


def get_ips():
    """
    find the IPs from which files will be served
    """
    interfaces = netifaces.interfaces()
    ips = []
    for interface in interfaces:
        if not interface.startswith("docker"): # ignore docker bindings
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                ips.extend([addr['addr'] for addr in addrs[netifaces.AF_INET]])
    return ips


def create_ip_info(directory, ips, port):
    """
    Make nice panel for people to find how to access
    their local map server
    """
    output = "[bold]:exclamation:[green]Serving map files from folder[/green][/bold]:\n"
    output += "[italic]{}[/italic]\n\n".format(directory)
    output += "You can access your map files from the following addresses:\n\n"
              
    for i, ip in enumerate(ips):
        output += "{}. http://{}:{}\n".format(i+1, ip, port)
    output += ("\n[italic]IPs for local connections likely start with [bold]10.x.x.x[/bold]"
                   ", [bold]192.x.x.x[/bold] or [bold]172.x.x.x[/bold][/italic].\n\n"
               ":warning-emoji: [italic]127.0.0.1[/italic] is not accessible outside your computer!"
                   )
    return output

def create_web_server(directory, port):
    '''
    create the webserver based on input
    '''
    handler = partial(MyRequestHandler,directory=directory)
    return HTTPServer(('', port), handler)
