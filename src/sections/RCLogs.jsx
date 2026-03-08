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
