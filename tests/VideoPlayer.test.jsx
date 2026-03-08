import { jest, test, expect } from '@jest/globals';
import React from 'react';
import { render } from 'ink-testing-library';

// Mock frames data using ESM-compatible mock
jest.unstable_mockModule('../src/frames.js', () => ({
  frames: ['frame1_ansi', 'frame2_ansi'],
  fps: 24,
}));

const { default: VideoPlayer } = await import('../src/components/VideoPlayer.jsx');

test('renders without crashing', () => {
  const { lastFrame } = render(<VideoPlayer width={80} height={20} />);
  expect(lastFrame()).toBeDefined();
});
