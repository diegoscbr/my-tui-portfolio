import React from 'react';
import { Box, Text, useStdout } from 'ink';
import { DIEGO_LINES, ESCOBAR_LINES } from '../utils/titleArt.js';

const WIDE_THRESHOLD = 120;
const MEDIUM_THRESHOLD = 80;

export default function NoticeBoard() {
  const { stdout } = useStdout();
  const cols = stdout?.columns ?? 80;

  let titleBlock;
  if (cols >= WIDE_THRESHOLD) {
    titleBlock = (
      <>
        {DIEGO_LINES.map((line, i) => <Text key={`d${i}`}>{line}</Text>)}
        {ESCOBAR_LINES.map((line, i) => <Text key={`e${i}`}>{line}</Text>)}
      </>
    );
  } else if (cols >= MEDIUM_THRESHOLD) {
    titleBlock = DIEGO_LINES.map((line, i) => <Text key={`d${i}`}>{line}</Text>);
  } else {
    titleBlock = <Text bold color="cyan">DIEGO ESCOBAR</Text>;
  }

  return (
    <Box flexDirection="column" gap={1} paddingTop={1}>
      {titleBlock}
      <Text dimColor>{'~ ~ ~ ~ ~ ~ ~ ~ ~'}</Text>
      <Text>builder · sailor · maker</Text>
      <Text>
        {'\n'}[your bio here — a few lines about who you are,
        what you build, what you care about.]
      </Text>
    </Box>
  );
}
