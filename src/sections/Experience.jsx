import React from 'react';
import { Box, Text } from 'ink';

export default function Experience() {
  return (
    <Box flexDirection="column" paddingTop={2}>
      <Text bold color="cyan">Experience</Text>
      <Text>{'\n'}[work history goes here]</Text>
    </Box>
  );
}
