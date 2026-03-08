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
        <Text key={i}>{line}</Text>
      ))}
    </Box>
  );
}
