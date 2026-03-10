import React from 'react';
import { Box, Text } from 'ink';

export default function SailingInstructions() {
  return (
    <Box flexDirection="column" paddingTop={2}>
      <Text bold color="cyan">Sailing Instructions</Text>
      <Text dimColor>Projects &amp; builds</Text>
      <Text>{'\n'}[projects go here]</Text>
    </Box>
  );
}
