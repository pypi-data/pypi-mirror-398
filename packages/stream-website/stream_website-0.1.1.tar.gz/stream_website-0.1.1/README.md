
# Stream Website (FastAPI Based)

An automated tool to set up a live streaming website using FastAPI and MediaMTX.

## Installation

```bash
pip install stream-website
```

## Usage

Simply run the following command:

```bash
python -m stream-website
```


Then go to:

```
http://localhost:8000
```
in your browser to access the website.



Your stream will be available at:

```
http://localhost:8888/live/stream/index.m3u8
```

## How to Stream with OBS

To start streaming from OBS (Open Broadcaster Software):

1. Open OBS and go to **Settings > Stream**.
2. Set the **Service** to `Custom...`.
3. Set the **Server** (RTMP URL) to:
	```
	rtmp://localhost:1935/live
	```
4. Set the **Stream Key** to:
	```
	stream
	```
5. Click **Start Streaming**.

Your stream will now be available at the m3u8 link above.

## Important: Port Configuration & Public Access

To make your system fully accessible and functional for external users, you must understand the port logic:

- **Website Interface (Port 8000):** Forwarding this port makes the website accessible. However, it only shows the web interface.
- **Live Stream Feed (Port 8888):** This is the default port for MediaMTX data. You must also forward this port to make the actual video broadcast viewable to the public.

> **Note:** Opening only port 8000 will result in a "video not found" or loading error for external users. Both 8000 and 8888 ports must be open.