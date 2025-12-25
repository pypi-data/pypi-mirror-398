# CoMaps Map Distributor

1. [Use cases](#use-cases)
   * [Places with limited connectivity](#places-with-limited-connectivity)
   * [Long-term archival](#long-term-archival)
2. [Installing this tool](#installing-this-tool)
3. [Usage](#usage)
4. [Development](#development)

🗺️A small CLI tool to download and then serve map files for CoMaps via a local network.

![a screenshot of the tool](static/header.png)

[There's also a small video showing how it works](static/intro.webm)

## Use cases

Since the [v2025.12.19-11 Android release](https://codeberg.org/comaps/comaps/releases/tag/v2025.12.19-11) of **CoMaps**, the app allow specifying a remote-server to download maps that is not the default, CoMaps-run *Content Delivery Network* (CDN). So far, [the maps still need to be the *"original"* maps as created by the CoMaps team, as the apps validate the checksums, but there are already some interesting use cases.


### Places with limited connectivity 

A big class of use cases is getting people to install & use CoMaps when they are having a very limited or even no internet connection. As the Android *APK* file can be transferred to devices locally, so can now be the maps. For example, this can be useful if…

* …you are living in a household with multiple devices that use CoMaps and for which you want to download/update maps. So far, each device needed to download the maps from the internet, wasting bandwidth, time and potentially money if you're on metered connections. By using a custom, local map delivery server you just need to download the maps from the internet once.
* …you have friends, family or communities living in remote places with limited or even no connectivity to the internet. You can now deliver the app and all necessary maps from any laptop by opening a WiFi-hot spot to let folks download the maps.
* …you are being deployed in humanitarian situations in places that are disconnected from the internet. By bringing the APK and local maps, a single laptop can be used to rapidly deploy CoMaps & the maps to local teams.

### Long-term archival

So far, older versions of CoMaps could no longer install the maps published along-side them, due to limited space on the CoMaps CDN. Which made long-term archival of older versions, e.g. for academic interest like in national archives or libraries problematic. Now you can archive older maps alongside the APK, and even still install it on devices.

## Installing this tool

Will be packed for PyPI soon, for now you can install via `uv`.

## Usage

The main `comaps-map-distributor` has two main commands: `download-maps` and `serve-maps`. While both have some optional parameters, you do not have to set-up anything, the map-download part can be used interactively and walks you through the process of downloading the maps you are interested in. 

And the map-serving part doesn't need user input if started from the same place the download was initiated. It will automatically display the IP addresses that should be used in the CoMaps app, assuming the devices share a local network (e.g. Wifi)

`comaps-map-distributor download-maps` does allow specifying map versions, allows selecting which maps to download, from which remote CoMaps CDN server and where to save them. If no parameters are given, the latest map version is downloaded from one of the existing CoMaps servers and saved in a default place.
* `comaps-map-distributor serve-maps` allows serving them over the local network with a very basic HTTP server, so that the _CoMaps_ Android app can find and download them without requiring internet connectivity. If a non-standard folder is used for storing the maps, you can specify the correct map folder.

Both commands can be run with `--help` for further help.

## Development

To develop locally, [use `uv`](https://docs.astral.sh/uv/) for managing dependencies etc locally, e.g.:

```
git clone ssh://git@codeberg.org/gedankenstuecke/comaps-map-distributor.git
uv sync
uv run comaps-map-distributor
```
