import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';
import { SECTIONS } from './sections.js';

export default function App() {
  const [activeIdx, setActiveIdx] = useState(0);

  useInput((input, key) => {
    if (input === 'q' || key.escape) process.exit(0);
    if (key.leftArrow) setActiveIdx((i) => Math.max(0, i - 1));
    if (key.rightArrow) setActiveIdx((i) => Math.min(SECTIONS.length - 1, i + 1));
  });

  return (
    <Box flexDirection="column">
      {/* Main row */}
      <Box flexDirection="row" gap={2} paddingX={2} paddingY={1}>
        {/* Left: video placeholder */}
        <Box flexBasis="45%" flexShrink={0} flexDirection="column" alignItems="center" justifyContent="center" minHeight={20}>
          <Text dimColor>┌──────────────────────┐</Text>
          <Text dimColor>│                      │</Text>
          <Text dimColor>│                      │</Text>
          <Text dimColor>│      [ video ]       │</Text>
          <Text dimColor>│                      │</Text>
          <Text dimColor>│                      │</Text>
          <Text dimColor>└──────────────────────┘</Text>
        </Box>

        {/* Divider */}
        <Text dimColor>│</Text>

        {/* Right: name */}
        <Box flexGrow={1} flexDirection="column" justifyContent="center" paddingLeft={2}>
          <Text bold color="cyan">DIEGO ESCOBAR</Text>
          <Text dimColor>~ ~ ~ ~ ~ ~ ~ ~ ~</Text>
          <Text> </Text>
          <Text>builder · sailor · maker</Text>
        </Box>
      </Box>

      {/* Tab bar */}
      <Box flexDirection="column" borderStyle="single" borderTop paddingX={2}>
        <Box flexDirection="row" gap={2}>
          {SECTIONS.map((s, i) => (
            <Text key={s.id} bold={i === activeIdx} underline={i === activeIdx} color={i === activeIdx ? 'cyan' : 'white'}>
              {s.label}
            </Text>
          ))}
        </Box>
        <Text dimColor>← → to navigate  q to quit</Text>
      </Box>
    </Box>
  );
}
