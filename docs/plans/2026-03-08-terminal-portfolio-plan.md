# Terminal Portfolio Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an SSH-accessible terminal portfolio at diego.boats with a sailing-themed interactive TUI, color ASCII video, and five navigable sections.

**Architecture:** A Node.js `ssh2` server handles incoming SSH connections and passes each session's streams directly into an Ink render context — no subprocess spawning needed, one runtime, clean PTY handling. Python pre-renders the 328 sailing frames to ANSI text once at build time; the TUI loads them from disk and loops instantly.

**Tech Stack:** Node.js 20, Ink 5 (React for CLIs), ssh2 (Node SSH server), Python 3.12 + ascii_magic (pre-render only), Hetzner VPS (Ubuntu 22.04), Vercel DNS.

---

## Project Structure

```
videojuego/
  prerender.py              # build-time: converts frames/ -> frames.bin
  frames.bin                # generated (gitignored, built on server)
  frames/                   # existing 328 JPEG frames
  player.py                 # existing reference, not used at runtime
  src/
    server.js               # ssh2 server entry point
    App.jsx                 # root Ink component
    components/
      Layout.jsx            # split-panel (video left, content right)
      VideoPlayer.jsx       # ANSI frame loop, left panel
      TabBar.jsx            # bottom navigation bar
      sections/
        NoticeBoard.jsx     # home: video + bio
        SailingInstructions.jsx
        RCLogs.jsx
        Contact.jsx
        Experience.jsx
  tests/
    VideoPlayer.test.jsx
    TabBar.test.jsx
    Layout.test.jsx
  package.json
  .gitignore
  provision.sh              # VPS setup script
  docs/plans/
```

---

## Task 1: Python Pre-render Script

**Goal:** Convert all 328 frames to ANSI color text once, save to `frames.bin`.

**Files:**
- Create: `prerender.py`
- Creates: `frames.bin` (gitignored)

**Step 1: Write the script**

```python
#!/usr/bin/env python3
"""
Build-time script. Run once on the machine with ascii_magic installed.
Outputs frames.bin (JSON) which the Node TUI reads at runtime.
"""
import json
import sys
from pathlib import Path
from ascii_magic import AsciiArt
from ascii_magic.constants import Modes

FRAMES_DIR = Path(__file__).parent / "frames"
OUTPUT = Path(__file__).parent / "frames.bin"
COLUMNS = 80   # left panel width; ~half a 160-col terminal


def main():
    frame_paths = sorted(FRAMES_DIR.glob("frame_*.jpg"))
    if not frame_paths:
        print(f"No frames found in {FRAMES_DIR}", file=sys.stderr)
        sys.exit(1)

    total = len(frame_paths)
    frames = []
    for i, path in enumerate(frame_paths):
        print(f"\rPre-rendering: {i + 1}/{total}", end="", flush=True)
        art = AsciiArt.from_image(str(path))
        ansi_text = art._img_to_art(columns=COLUMNS, mode=Modes.TERMINAL)
        frames.append(ansi_text)

    OUTPUT.write_text(json.dumps({"fps": 24, "columns": COLUMNS, "frames": frames}))
    print(f"\nWrote {total} frames to {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
```

**Step 2: Run it**

```bash
source .venv/bin/activate
python prerender.py
```

Expected: `Wrote 328 frames to frames.bin (XXXX KB)`

**Step 3: Add to .gitignore**

```
frames.bin
.ssh/
node_modules/
```

**Step 4: Commit**

```bash
git add prerender.py .gitignore
git commit -m "feat: add build-time frame pre-renderer"
```

---

## Task 2: Node.js Project Setup

**Files:**
- Create: `package.json`
- Create: `src/server.js` (empty stub)

**Step 1: Initialize and install dependencies**

```bash
npm init -y
npm install ink@5 react ssh2 ink-use-stdout-dimensions
npm install --save-dev @inkjs/testing jest babel-jest @babel/core @babel/preset-env @babel/preset-react
```

**Step 2: Add babel config for JSX**

Create `babel.config.json`:
```json
{
  "presets": [
    ["@babel/preset-env", { "targets": { "node": "current" } }],
    ["@babel/preset-react", { "runtime": "automatic" }]
  ]
}
```

**Step 3: Add scripts to package.json**

```json
{
  "type": "module",
  "scripts": {
    "start": "node src/server.js",
    "test": "jest"
  },
  "jest": {
    "transform": { "^.+\\.jsx?$": "babel-jest" }
  }
}
```

**Step 4: Commit**

```bash
git add package.json babel.config.json
git commit -m "chore: initialize Node.js project with Ink and ssh2"
```

---

## Task 3: SSH Server with Host Key Management

**Files:**
- Create: `src/server.js`

**Step 1: Generate a host key (run once on each machine)**

```bash
mkdir -p .ssh
ssh-keygen -t ed25519 -f .ssh/host_key -N ""
```

This creates `.ssh/host_key` (private) and `.ssh/host_key.pub`. Both are gitignored.

**Step 2: Write the server**

```javascript
// src/server.js
import { readFileSync } from 'fs';
import { Server } from 'ssh2';
import { render } from 'ink';
import React from 'react';
import App from './App.jsx';

const HOST_KEY = readFileSync('.ssh/host_key');
const PORT = 22;

const server = new Server({ hostKeys: [HOST_KEY] }, (client) => {
  client.on('authentication', (ctx) => {
    // Public portfolio — accept all connections, no auth required
    ctx.accept();
  });

  client.on('session', (accept) => {
    const session = accept();
    let rows = 24;
    let cols = 80;

    session.on('pty', (accept, _reject, info) => {
      rows = info.rows;
      cols = info.cols;
      accept();
    });

    session.on('window-change', (_accept, _reject, info) => {
      rows = info.rows;
      cols = info.cols;
    });

    session.on('shell', (accept) => {
      const stream = accept();

      // Ink render into the SSH stream
      const { unmount } = render(
        React.createElement(App, { rows, cols }),
        {
          stdin: stream,
          stdout: stream,
          patchConsole: false,
          exitOnCtrlC: false,
        }
      );

      stream.on('close', () => unmount());
      stream.on('error', () => unmount());
    });
  });

  client.on('error', () => {});
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`SSH server listening on port ${PORT}`);
});
```

**Step 3: Create empty App.jsx stub so server can import it**

```jsx
// src/App.jsx
import React from 'react';
import { Text } from 'ink';

export default function App({ rows, cols }) {
  return <Text>Loading...</Text>;
}
```

**Step 4: Smoke test — start server and connect**

```bash
node src/server.js &
ssh -p 22 -o StrictHostKeyChecking=no localhost
# Should see: Loading...
# ctrl+c / q to disconnect
kill %1
```

**Step 5: Commit**

```bash
git add src/server.js src/App.jsx
git commit -m "feat: add ssh2 server with host key auth and Ink render"
```

---

## Task 4: Layout Component

**Files:**
- Create: `src/components/Layout.jsx`
- Create: `tests/Layout.test.jsx`

**Step 1: Write the failing test**

```jsx
// tests/Layout.test.jsx
import React from 'react';
import { render } from '@inkjs/testing';
import Layout from '../src/components/Layout.jsx';

test('renders left and right panels side by side', () => {
  const { lastFrame } = render(
    <Layout
      cols={80}
      rows={24}
      left={<Text>LEFT</Text>}
      right={<Text>RIGHT</Text>}
    />
  );
  expect(lastFrame()).toContain('LEFT');
  expect(lastFrame()).toContain('RIGHT');
});
```

**Step 2: Run test — expect FAIL**

```bash
npm test -- tests/Layout.test.jsx
```

**Step 3: Implement**

```jsx
// src/components/Layout.jsx
import React from 'react';
import { Box } from 'ink';

const LEFT_RATIO = 0.45;

export default function Layout({ cols, rows, left, right, footer }) {
  const leftWidth = Math.floor(cols * LEFT_RATIO);
  const rightWidth = cols - leftWidth - 1;
  const contentRows = rows - 3; // reserve 3 rows for footer

  return (
    <Box flexDirection="column" width={cols} height={rows}>
      <Box flexDirection="row" height={contentRows}>
        <Box width={leftWidth} height={contentRows} overflow="hidden">
          {left}
        </Box>
        <Box width={1} height={contentRows}>
          <Box borderStyle="single" height={contentRows} />
        </Box>
        <Box width={rightWidth} height={contentRows} overflow="hidden" paddingLeft={1}>
          {right}
        </Box>
      </Box>
      <Box height={3} borderStyle="single" borderTop>
        {footer}
      </Box>
    </Box>
  );
}
```

**Step 4: Run test — expect PASS**

```bash
npm test -- tests/Layout.test.jsx
```

**Step 5: Commit**

```bash
git add src/components/Layout.jsx tests/Layout.test.jsx
git commit -m "feat: add split-panel Layout component"
```

---

## Task 5: VideoPlayer Component

**Files:**
- Create: `src/components/VideoPlayer.jsx`
- Create: `tests/VideoPlayer.test.jsx`

**Step 1: Write the failing test**

```jsx
// tests/VideoPlayer.test.jsx
import React from 'react';
import { render } from '@inkjs/testing';
import VideoPlayer from '../src/components/VideoPlayer.jsx';

// Mock frames data
jest.mock('../src/frames.js', () => ({
  frames: ['frame1_ansi', 'frame2_ansi'],
  fps: 24,
}));

test('renders without crashing', () => {
  const { lastFrame } = render(<VideoPlayer width={80} height={20} />);
  expect(lastFrame()).toBeDefined();
});
```

**Step 2: Run test — expect FAIL**

```bash
npm test -- tests/VideoPlayer.test.jsx
```

**Step 3: Create frames loader**

```javascript
// src/frames.js
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const data = JSON.parse(readFileSync(resolve(__dirname, '../frames.bin'), 'utf-8'));

export const { frames, fps, columns } = data;
```

**Step 4: Implement VideoPlayer**

```jsx
// src/components/VideoPlayer.jsx
import React, { useState, useEffect } from 'react';
import { Box, Text } from 'ink';
import { frames, fps } from '../frames.js';

export default function VideoPlayer({ height }) {
  const [frameIdx, setFrameIdx] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setFrameIdx((i) => (i + 1) % frames.length);
    }, 1000 / fps);
    return () => clearInterval(interval);
  }, []);

  // Split frame into lines and show only what fits
  const lines = frames[frameIdx].split('\n').slice(0, height);

  return (
    <Box flexDirection="column">
      {lines.map((line, i) => (
        // eslint-disable-next-line react/no-array-index-key
        <Text key={i}>{line}</Text>
      ))}
    </Box>
  );
}
```

**Step 5: Run test — expect PASS**

```bash
npm test -- tests/VideoPlayer.test.jsx
```

**Step 6: Commit**

```bash
git add src/components/VideoPlayer.jsx src/frames.js tests/VideoPlayer.test.jsx
git commit -m "feat: add VideoPlayer component with pre-rendered ANSI frames"
```

---

## Task 6: TabBar Component

**Files:**
- Create: `src/components/TabBar.jsx`
- Create: `tests/TabBar.test.jsx`

**Step 1: Define sections constant (shared)**

```javascript
// src/sections.js
export const SECTIONS = [
  { id: 'notice-board',          label: 'Notice Board' },
  { id: 'sailing-instructions',  label: 'Sailing Instructions' },
  { id: 'rc-logs',               label: 'R/C Logs' },
  { id: 'contact',               label: 'Contact' },
  { id: 'experience',            label: 'Experience' },
];
```

**Step 2: Write the failing test**

```jsx
// tests/TabBar.test.jsx
import React from 'react';
import { render } from '@inkjs/testing';
import TabBar from '../src/components/TabBar.jsx';
import { SECTIONS } from '../src/sections.js';

test('renders all section labels', () => {
  const { lastFrame } = render(
    <TabBar sections={SECTIONS} activeIdx={0} />
  );
  SECTIONS.forEach(({ label }) => {
    expect(lastFrame()).toContain(label);
  });
});

test('highlights active section', () => {
  const { lastFrame } = render(
    <TabBar sections={SECTIONS} activeIdx={2} />
  );
  expect(lastFrame()).toContain('R/C Logs');
});
```

**Step 3: Run test — expect FAIL**

```bash
npm test -- tests/TabBar.test.jsx
```

**Step 4: Implement**

```jsx
// src/components/TabBar.jsx
import React from 'react';
import { Box, Text } from 'ink';

export default function TabBar({ sections, activeIdx }) {
  return (
    <Box flexDirection="column">
      <Box flexDirection="row" gap={2} paddingX={1}>
        {sections.map((s, i) => (
          <Text
            key={s.id}
            bold={i === activeIdx}
            underline={i === activeIdx}
            color={i === activeIdx ? 'cyan' : 'white'}
          >
            {s.label}
          </Text>
        ))}
      </Box>
      <Box paddingX={1}>
        <Text dimColor>{'<- -> to navigate  enter to open  q to quit'}</Text>
      </Box>
    </Box>
  );
}
```

**Step 5: Run test — expect PASS**

```bash
npm test -- tests/TabBar.test.jsx
```

**Step 6: Commit**

```bash
git add src/sections.js src/components/TabBar.jsx tests/TabBar.test.jsx
git commit -m "feat: add sailing-themed TabBar with section navigation"
```

---

## Task 7: Section Components

**Files:**
- Create: `src/sections/NoticeBoard.jsx`
- Create: `src/sections/SailingInstructions.jsx`
- Create: `src/sections/RCLogs.jsx`
- Create: `src/sections/Contact.jsx`
- Create: `src/sections/Experience.jsx`

Each section is a right-panel content component. Placeholder content for now — fill in real content after layout is wired up.

**Step 1: NoticeBoard (bio panel — shown on home screen right side)**

```jsx
// src/sections/NoticeBoard.jsx
import React from 'react';
import { Box, Text } from 'ink';

export default function NoticeBoard() {
  return (
    <Box flexDirection="column" gap={1} paddingTop={2}>
      <Text bold color="cyan">DIEGO ESCOBAR</Text>
      <Text dimColor>{'~ ~ ~ ~ ~ ~ ~ ~ ~'}</Text>
      <Text>{'\n'}builder · sailor · maker</Text>
      <Text>
        {'\n'}[your bio here — a few lines about who you are,
        what you build, what you care about.]
      </Text>
    </Box>
  );
}
```

**Step 2: Remaining sections (stubs — fill in real content later)**

```jsx
// src/sections/SailingInstructions.jsx
import React from 'react';
import { Box, Text } from 'ink';
export default function SailingInstructions() {
  return (
    <Box flexDirection="column" paddingTop={2}>
      <Text bold color="cyan">Sailing Instructions</Text>
      <Text dimColor>Projects & builds</Text>
      <Text>{'\n'}[projects go here]</Text>
    </Box>
  );
}
```

```jsx
// src/sections/RCLogs.jsx
import React from 'react';
import { Box, Text } from 'ink';
export default function RCLogs() {
  return (
    <Box flexDirection="column" paddingTop={2}>
      <Text bold color="cyan">R/C Logs</Text>
      <Text dimColor>Reflections & writing</Text>
      <Text>{'\n'}[writing goes here]</Text>
    </Box>
  );
}
```

```jsx
// src/sections/Contact.jsx
import React from 'react';
import { Box, Text } from 'ink';
export default function Contact() {
  return (
    <Box flexDirection="column" paddingTop={2}>
      <Text bold color="cyan">Contact</Text>
      <Text>{'\n'}email:   you@diego.boats</Text>
      <Text>github:  github.com/yourhandle</Text>
    </Box>
  );
}
```

```jsx
// src/sections/Experience.jsx
import React from 'react';
import { Box, Text } from 'ink';
export default function Experience() {
  return (
    <Box flexDirection="column" paddingTop={2}>
      <Text bold color="cyan">Experience</Text>
      <Text>{'\n'}[work history goes here]</Text>
    </Box>
  );
}
```

**Step 3: Commit**

```bash
git add src/sections/
git commit -m "feat: add section components with placeholder content"
```

---

## Task 8: Wire Up App.jsx

**Files:**
- Modify: `src/App.jsx`

**Step 1: Implement full App**

```jsx
// src/App.jsx
import React, { useState } from 'react';
import { useInput } from 'ink';
import Layout from './components/Layout.jsx';
import VideoPlayer from './components/VideoPlayer.jsx';
import TabBar from './components/TabBar.jsx';
import { SECTIONS } from './sections.js';
import NoticeBoard from './sections/NoticeBoard.jsx';
import SailingInstructions from './sections/SailingInstructions.jsx';
import RCLogs from './sections/RCLogs.jsx';
import Contact from './sections/Contact.jsx';
import Experience from './sections/Experience.jsx';

const SECTION_COMPONENTS = [
  NoticeBoard,
  SailingInstructions,
  RCLogs,
  Contact,
  Experience,
];

export default function App({ rows = 24, cols = 80 }) {
  const [activeIdx, setActiveIdx] = useState(0);

  useInput((input, key) => {
    if (input === 'q' || key.escape) process.exit(0);
    if (key.leftArrow) setActiveIdx((i) => Math.max(0, i - 1));
    if (key.rightArrow) setActiveIdx((i) => Math.min(SECTIONS.length - 1, i + 1));
  });

  const ActiveSection = SECTION_COMPONENTS[activeIdx];
  const contentRows = rows - 3;

  return (
    <Layout
      cols={cols}
      rows={rows}
      left={<VideoPlayer height={contentRows} />}
      right={<ActiveSection />}
      footer={<TabBar sections={SECTIONS} activeIdx={activeIdx} />}
    />
  );
}
```

**Step 2: Test locally (requires frames.bin)**

```bash
# Make sure frames.bin exists first:
source .venv/bin/activate && python prerender.py

# Start server and connect:
node src/server.js &
ssh -p 22 -o StrictHostKeyChecking=no localhost
# Should see full TUI with video on left, Notice Board on right
# <- -> to switch sections, q to quit
kill %1
```

**Step 3: Commit**

```bash
git add src/App.jsx
git commit -m "feat: wire up full App with navigation and section routing"
```

---

## Task 9: VPS Provisioning

**Goal:** Hetzner VPS running the portfolio server.

**Step 1: Create Hetzner account and VPS**

1. Go to hetzner.com, create account
2. New Project → New Server
3. Select: Ubuntu 22.04, CAX11 (ARM, €3.29/mo), any datacenter
4. Add your SSH public key (`~/.ssh/id_ed25519.pub`) during setup
5. Note the server IP (e.g., `1.2.3.4`)

**Step 2: Create provision.sh**

```bash
#!/bin/bash
# Run on the VPS as root: bash provision.sh
set -e

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs python3 python3-pip python3-venv git

# Install Python deps for pre-rendering
python3 -m venv /app/.venv
/app/.venv/bin/pip install ascii_magic pillow

# Clone repo
git clone https://github.com/YOUR_USERNAME/diego-boats.git /app
cd /app

# Pre-render frames (one-time)
/app/.venv/bin/python prerender.py

# Install Node deps
npm install --production

# Generate SSH host key
mkdir -p .ssh
ssh-keygen -t ed25519 -f .ssh/host_key -N ""

# Install as systemd service
cat > /etc/systemd/system/portfolio.service << EOF
[Unit]
Description=diego.boats terminal portfolio
After=network.target

[Service]
WorkingDirectory=/app
ExecStart=/usr/bin/node src/server.js
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable portfolio
systemctl start portfolio

echo "Done. Run: systemctl status portfolio"
```

**Step 3: Run it**

```bash
scp provision.sh root@1.2.3.4:/root/
ssh root@1.2.3.4 "bash provision.sh"
```

**Step 4: Verify**

```bash
ssh -p 22 root@1.2.3.4  # confirm server responds
# From another terminal:
ssh -o StrictHostKeyChecking=no 1.2.3.4
# Should see the TUI
```

**Step 5: Commit provision script**

```bash
git add provision.sh
git commit -m "chore: add VPS provisioning script"
```

---

## Task 10: DNS Configuration

**Goal:** Point `diego.boats` at the VPS so `ssh diego.boats` works.

**Step 1: Add A record in Vercel DNS**

1. Go to vercel.com → your account → Domains → diego.boats
2. Add record:
   - Type: `A`
   - Name: `@`  (root domain)
   - Value: `1.2.3.4`  (your VPS IP)
   - TTL: 300

**Step 2: Verify propagation**

```bash
# Wait 1-5 minutes, then:
dig diego.boats A +short
# Should return: 1.2.3.4
```

**Step 3: Test end-to-end**

```bash
ssh diego.boats
# First connection: terminal will show host key fingerprint, type "yes"
# Should see full TUI
```

---

## Task 11: GitHub Repo

**Step 1: Create and push**

```bash
gh repo create diego-boats --public --source=. --push
```

**Step 2: Add repo URL to Contact section**

Edit `src/sections/Contact.jsx` and update with your real GitHub URL.

```bash
git add src/sections/Contact.jsx
git commit -m "chore: add github repo link to Contact section"
git push
```

---

## Post-Launch: Fill In Real Content

Once the infrastructure works, fill in actual content:

- `src/sections/NoticeBoard.jsx` — your real bio
- `src/sections/SailingInstructions.jsx` — your actual projects
- `src/sections/RCLogs.jsx` — your writing/reflections
- `src/sections/Contact.jsx` — real email, socials
- `src/sections/Experience.jsx` — work history

No structural changes needed — just update the text in each section component.
