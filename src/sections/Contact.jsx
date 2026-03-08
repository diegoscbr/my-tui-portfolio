import React from 'react';
import { Box, Text } from 'ink';

export default function Contact() {
  return (
    <Box flexDirection="column" paddingTop={2}>
      <Text bold color="cyan">Contact</Text>
      <Text>{'\n'}email:   you@diego.boats</Text>
      <Text>github:  github.com/yourhandle</Text>
    </Box>
  );
}
