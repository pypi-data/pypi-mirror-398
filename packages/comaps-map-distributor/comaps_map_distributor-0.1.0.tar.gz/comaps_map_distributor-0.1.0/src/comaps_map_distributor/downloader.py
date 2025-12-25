import os
import sys
import requests

from pathlib import Path

from InquirerPy import prompt, inquirer
from InquirerPy.base import Choice
from InquirerPy.validator import PathValidator

from rich import print
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

def get_map_version(url="https://cdn-us-1.comaps.app/servers?allversions"):
    """
    user didn't specify version. Get latest one
    """
    response = requests.get(url)
    return response.json()[-1]


def get_cdn_host(map_version, url="https://cdn-us-1.comaps.app/"):
    """
    User didn't specify server. Get best one
    """
    response = requests.get(url + "servers?version={}".format(map_version))
    return response.json()[0]

def get_map_names(cdn_host, map_version, user_specified_server):
    """
    parse JSON to get names of countries and map version
    """
    print("[bold] Getting list of maps [/bold]")
    response = requests.get("{}/maps/{}/countries.txt".format(cdn_host, map_version))
    try:
        countries = response.json()
    except requests.exceptions.JSONDecodeError:
        if user_specified_server:
            print('[bold][red]Error: requested map version {} does not exist[/red][/bold]'.format(map_version))
            print('This could be due to the map version being wrong, or not existing on the server you manually specified.')
            sys.exit('Try running without --map-version and/or without --download-server to use the latest/defaults')
        else:
            print('[bold][red]Error: requested map version {} does not exist[/red][/bold]'.format(map_version))
            sys.exit('Try running without --map-version to use latest map versions')
    map_version = countries['v']
    country_list = recurse_map_json(countries)
    print("[bold] Got list of all available maps (version [italic]{}[/italic][/bold])".format(map_version))
    return (map_version, country_list)


def recurse_map_json(countries, name_list=[]):
    """
    recursively iterate over keys in countries.txt
    to get all names of actual files that can be 
    downloaded
    """
    if 'g' in countries.keys():
        for entry in countries['g']:
            if 'g' in entry.keys():
                recurse_map_json(entry, name_list)
            else:
                #print(entry['id'])
                name_list.append(entry['id'])
    return name_list


def select_maps(country_list):
    """
    build fuzzy match UI for selecting which maps to download
    """

    # map keys for better usability

    keybindings = {
        "toggle": [
            {"key": "left"},
            {"key": "right"},
            ],
        "toggle-all": [{"key": "c-a"}],
        "toggle-all-false": [{"key": "c-n"}],
}

    # make world map and world coast map selected by default

    country_list = list(map(lambda x: Choice(x, enabled=True) if x == 'World' or x == 'WorldCoasts' else x, country_list))

    questions = [
        {
            "name": "map_names",
            "type": "fuzzy",
            "message": "Select maps to download:",
            "choices": country_list,
            "multiselect": True,
            "validate": lambda result: len(result) > 1,
            "invalid_message": "minimum 2 selection",
            "max_height": "60%",
        },
    ]

    print(Panel("[bold]:question:Select the maps you want to download [/bold]\n\n"
                ":exclamation:You can search/filter for maps by starting to type the name.\n\n"
                "[bold]Available shortcuts:[/bold]\n"
                "1. [italic]<Left> / <Right>[/italic] arrows: toggle select/deselect of map\n"
                "2. [italic]<Ctrl+a>[/italic]: select all maps\n"
                "3. [italic]<Ctrl+n>[/italic]: deselect all maps\n"
                "4. [italic]<Enter>[/italic]: confirm selection\n\n"
                ":warning-emoji: [italic]World[/italic] & [italic]WorldCoast[/italic] are selected by default"
                ))

    result = prompt(questions=questions, keybindings=keybindings)

    return result["map_names"]


def select_download_path(map_version, directory):
    """
    where should the files be downloaded to?
    create folders if not existing yet
    """
    if not directory:
        home_path = os.getcwd()
        dest_path = inquirer.filepath(
            message="Enter path where downloaded files should be stored:",
            default= home_path,
            validate=PathValidator(is_dir=True, message="Input is not a directory"),
            only_directories=True,
        ).execute()
        print(dest_path)
        dest_path = os.path.join(dest_path, "comaps_folder/maps/{}".format(map_version))
    else:
        dest_path = os.path.join(directory, "maps/{}".format(map_version))
    Path(dest_path).mkdir(parents=True, exist_ok=True)
    return dest_path


def create_download_url(base_url, map_version, map_name):
    """
    Structure download URL
    """
    download_url = "{}maps/{}/{}.mwm".format(
            base_url,
            map_version,
            map_name)
    return download_url


def download_maps(selected_maps, base_url, map_version, download_location):
    print("[bold]Downloading maps:[/bold] {}".format(selected_maps))
    download_progress = Progress(transient=True)
    download_progress.start()
    overall_progress = download_progress.add_task("[blue]Downloading files...", total=len(selected_maps))
    for map_name in selected_maps:
        download_url = create_download_url(base_url, map_version, map_name)
        local_filename = "{}/{}.mwm".format(download_location, map_name)
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            per_file_progress = download_progress.add_task(
                    "[yellow]File: {}".format(map_name),
                    total=int(r.headers.get("content-length", 0)))
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    download_progress.update(per_file_progress, advance=8192)
            download_progress.update(per_file_progress, visible=False)
        download_progress.update(overall_progress, advance=1)
        print(":white_check_mark:[bold] Downloaded: [/bold][italic]{}[/italic] from {}".format(
            map_name,
            download_url))
    download_progress.stop()
    print("[bold]:rocket: All files downloaded! [/bold]")
