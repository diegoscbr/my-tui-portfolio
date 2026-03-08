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
