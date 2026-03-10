// src/server.js
process.on('uncaughtException', (err) => console.error('[uncaught]', err));

import { readFileSync } from 'fs';
import ssh2pkg from 'ssh2';
const { Server } = ssh2pkg;
import { render } from 'ink';
import React from 'react';
import App from './App.jsx';

const HOST_KEY = readFileSync('.ssh/host_key');
const PORT = 2222;

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

    session.on('shell', (accept) => {
      const stream = accept();

      // Ink requires isTTY + setRawMode on stdin.
      stream.isTTY = true;
      stream.setRawMode = () => {};
      stream.ref = () => {};
      stream.unref = () => {};
      stream.columns = cols;
      stream.rows = rows;

      session.on('window-change', (_accept, _reject, info) => {
        stream.columns = info.cols;
        stream.rows = info.rows;
        stream.emit('resize');
      });

      // Ink render into the SSH stream
      let unmount;
      try {
        ({ unmount } = render(
          React.createElement(App),
          {
            stdin: stream,
            stdout: stream,
            patchConsole: false,
            exitOnCtrlC: false,
            onError: (err) => console.error('[ink error]', err),
          }
        ));
      } catch (err) {
        console.error('[render error]', err);
        stream.end();
        return;
      }

      stream.on('close', () => unmount?.());
      stream.on('error', (err) => { console.error('[stream error]', err); unmount?.(); });
    });
  });

  client.on('error', () => {});
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`SSH server listening on port ${PORT}`);
});
