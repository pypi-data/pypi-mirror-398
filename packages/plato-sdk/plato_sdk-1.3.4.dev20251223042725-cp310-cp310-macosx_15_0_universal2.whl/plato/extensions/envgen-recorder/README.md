# EnvGen Recorder Chrome Extension

A Chrome extension for recording browser sessions with UI event capture and automatic cloud upload via Plato API.

## Features

- **Video Recording**: Captures full tab video using Chrome's tabCapture API
- **Pause Markers**: Add pause/resume markers with keyboard shortcut (Cmd+Shift+Space) - recording continues, markers added to data
- **UI Event Tracking**: Records all user interactions (clicks, scrolls, typing, etc.) with precise timestamps
- **Network Monitoring**: Captures all HTTP requests/responses with headers, timing, and status codes
- **Auto-Upload**: Automatically uploads recordings to S3 via Plato API (no AWS credentials needed)
- **Session Management**: Store and replay recordings locally
- **Export to JSON**: Download recordings in structured JSON format for processing

## Installation

### Option 1: Via Plato CLI (Easiest)

```bash
# Install extension and get setup instructions
uv run plato install-extension

# Follow the printed instructions to load in Chrome
```

### Option 2: Manual Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Navigate to `~/.plato/envgen-recorder` (if using CLI)
   - Or select this directory directly
5. The extension icon should appear in your toolbar

## Configuration

### Plato API Setup (for Auto-Upload)

1. Click the extension icon → Click ⚙️ Settings
2. Enter your **Plato API Key** (contact your organization admin)
3. Click "Save Settings"

**Note:** All recordings automatically upload to `plato.so` (hardcoded).

**Without API Key:**
- Recordings still work and are saved locally
- You can manually download them later
- Auto-upload will be disabled

## Usage

### Recording a Session

1. Navigate to the page you want to record
2. Click the EnvGen extension icon
3. Click "Start Recording"
   - Chrome will start recording the tab video + UI events
4. Perform your actions on the page
5. **Pause Markers** (optional): Press **Cmd+Shift+Space** to add pause/resume markers
   - A small orange indicator appears in top-right corner when pause marker is active
   - **Recording continues** - video, events, and network are still captured
   - Markers are added to the event data for post-processing segmentation
   - Press the shortcut again to add a resume marker
   - Useful for marking sections of interest or skippable segments
6. Click the extension icon again and click "Stop Recording"
7. The extension will save the session internally (video + events + network)
8. Click **"View Sessions"** to see all your saved recordings
9. Click **"Download"** on any session to export the files:
   - `envgen_recording_[UUID].webm` - Video recording
   - `envgen_recording_[UUID]_events.json` - UI & network events (includes pause/resume markers)

### Viewing Sessions

Click "View Sessions" in the popup to open the sessions manager where you can:
- View all saved recordings with metadata (duration, event count, file size)
- Play videos directly in the browser
- Download individual sessions (video + events JSON)
- Delete old sessions

All sessions are stored locally in:
- **Chrome Storage**: Session metadata and UI events
- **IndexedDB**: Video files

### Processing the Recording

The downloaded JSON file contains all UI events with timestamps. You can process it with the envgen workflow:

```bash
# Create a config file with your recording details
cat > config/video_processor.yaml << EOF
workflow_type: video_processor
video_file: path/to/envgen_recording_TIMESTAMP.webm
events_file: path/to/envgen_recording_TIMESTAMP_events.json
output_file: output/actions.json
extract_frames: true
frames_output_dir: output/frames

storage:
  type: s3
  s3:
    bucket_name: plato-envgen-artifacts
    region: us-west-1

logging:
  level: INFO
  logfire_enabled: true
EOF

# Run the workflow
uv run python scripts/run_workflow.py -c config/video_processor.yaml
```

## Event Format

The extension captures events in the following format (including pause/resume markers):

```json
{
  "recording_start": 1699564800000,
  "recording_end": 1699564900000,
  "stats": {
    "ui_event_count": 42,
    "network_event_count": 128,
    "duration_ms": 100000
  },
  "ui_events": [
    {
      "seq_id": 0,
      "timestamp": 1699564801234,
      "type": "click",
      "url": "https://example.com",
      "target": {
        "tagName": "BUTTON",
        "id": "submit-btn",
        "className": "btn btn-primary",
        "xpath": "/html[1]/body[1]/div[1]/button[1]",
        "cssPath": "button.btn.btn-primary",
        "text": "Submit",
        "value": ""
      },
      "mouse": {
        "x": 150,
        "y": 200,
        "pageX": 150,
        "pageY": 500,
        "button": 0
      }
    },
    {
      "seq_id": 1,
      "timestamp": 1699564805000,
      "type": "pause_marker",
      "url": "",
      "target": {},
      "metadata": {
        "marker_number": 1,
        "description": "User toggled pause marker - recording continues"
      }
    },
    {
      "seq_id": 2,
      "timestamp": 1699564810000,
      "type": "resume_marker",
      "url": "",
      "target": {},
      "metadata": {
        "marker_number": 1,
        "description": "User toggled resume marker - recording was never stopped"
      }
    }
  ],
  "network_events": [
    {
      "requestId": "12345",
      "timestamp": 1699564801000,
      "url": "https://api.example.com/data",
      "method": "POST",
      "type": "xmlhttprequest",
      "initiator": "https://example.com",
      "requestHeaders": [
        {"name": "Content-Type", "value": "application/json"}
      ],
      "requestBody": {"formData": {}},
      "status": "completed",
      "statusCode": 200,
      "responseHeaders": [
        {"name": "Content-Type", "value": "application/json"}
      ],
      "completedTimestamp": 1699564801234,
      "duration": 234,
      "ip": "1.2.3.4",
      "fromCache": false
    }
  ]
}
```

## Development

### Files

- `manifest.json` - Extension manifest
- `content.js` - Content script that captures UI events
- `background.js` - Service worker that manages recording state
- `popup.html` - Extension popup UI
- `popup.js` - Popup UI controller

### Event Types Captured

- Mouse: `click`, `dblclick`, `mousedown`, `mouseup`, `mousemove`, `wheel`
- Keyboard: `keydown`, `keyup`
- Input: `input`, `change`, `submit`
- Focus: `focus`, `blur`
- Scroll: `scroll`
- Markers: `pause_marker`, `resume_marker` (recording continues, used for segmentation)

## Troubleshooting

**Events not being captured**: Make sure the extension is enabled and the content script is injected. Check the browser console for errors.

**Recording not starting**: Ensure you have the necessary permissions. Try reloading the extension.

**Missing events**: Some events may be throttled (like `mousemove`) to prevent overwhelming the system. This is normal.
