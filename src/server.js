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
