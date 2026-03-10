import { jest } from '@jest/globals';
import React from 'react';

// ESM mocking must happen before dynamic imports
jest.unstable_mockModule('../src/frames.js', () => ({
  frames: ['frame1_ansi\nline2', 'frame2_ansi\nline2'],
  fps: 24,
  columns: 80,
}));

const { render } = await import('ink-testing-library');
const { default: VideoPlayer } = await import('../src/components/VideoPlayer.jsx');

test('renders without crashing', () => {
  const { lastFrame } = render(<VideoPlayer height={20} />);
  expect(lastFrame()).toBeDefined();
});
