import os
import click 

from rich import print
from rich.panel import Panel
from rich.table import Table

from .downloader import get_map_names, select_maps, select_download_path, download_maps, get_map_version, get_cdn_host
from .server import get_available_versions, find_free_port, get_ips, create_ip_info, MyRequestHandler, create_web_server

@click.group()
def app():
    """
    Download and serve map files for use with the CoMaps android app.
    """
    pass

@app.command("download-maps")
@click.option('--directory',
              required=False,
              help='path to folder into which maps will be downloaded. If not provided, will be asked for interactively in script',
              type=click.Path())
@click.option('--map-version',
              required=False,
              help="Optional: Specify which map release you want to download. Defaults to latest")
@click.option("--download-server",
              required=False,
              help="Optional: Specify from which server to download maps. If not provided, get server from Comaps CDN")
def cli_download_maps(directory, map_version, download_server):
    """
    CLI command to download map files
    """
    print(Panel(":world_map: [bold] Welcome to the CoMaps map distributor [/bold] :world_map:"))
    if not map_version:
        map_version = get_map_version()
    if not download_server:
        download_server = get_cdn_host(map_version)
        user_specified_server = False
    else:
        user_specified_server = True
    map_version, country_list = get_map_names(download_server,
                                              map_version,
                                              user_specified_server)
    selected_maps = select_maps(country_list)
    download_location = select_download_path(map_version,directory)
    download_maps(selected_maps,
                  download_server,
                  map_version,
                  download_location)



@app.command("serve-maps")
@click.option('--directory',
              default=os.getcwd() + "/comaps_folder",
              help='path to folder in which the maps are organized. Default: <CWD>/comaps_folder',
              type=click.Path())
@click.option("--port",
              required=False,
              type=int,
              help="Optional: A port for the server. If not specified, find free port automatically.")
def cli_serve_maps(directory,port=None):
    """
    Serve map files with a small webserver.
    
    Useful for quickly distributing files in the local network
    """
    if not port:
        port = find_free_port()
    ips = get_ips()
    httpd = create_web_server(directory, port)
    print(Panel(create_ip_info(directory, ips, port)))
    # create table of versions 
    available_versions = get_available_versions(directory)
    table = Table(title="Available versions/maps",expand=True)
    table.add_column("Version", justify="right", style="cyan", no_wrap=True)
    table.add_column("Maps", justify='left', style='green')
    for k,v in available_versions.items():
        table.add_row(k, ",".join(v))
    print(table)
    httpd.serve_forever()



