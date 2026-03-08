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
