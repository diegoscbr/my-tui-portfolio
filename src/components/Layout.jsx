import React from 'react';
import { Box } from 'ink';

const LEFT_RATIO = 0.45;

export default function Layout({ cols, rows, left, right, footer }) {
  const leftWidth = Math.floor(cols * LEFT_RATIO);
  const rightWidth = cols - leftWidth - 1;
  const contentRows = rows - 3; // reserve 3 rows for footer

  return (
    <Box flexDirection="column" width={cols} height={rows}>
      <Box flexDirection="row" height={contentRows}>
        <Box width={leftWidth} height={contentRows} overflow="hidden">
          {left}
        </Box>
        <Box width={1} height={contentRows}>
          <Box borderStyle="single" height={contentRows} />
        </Box>
        <Box width={rightWidth} height={contentRows} overflow="hidden" paddingLeft={1}>
          {right}
        </Box>
      </Box>
      <Box height={3} borderStyle="single" borderTop>
        {footer}
      </Box>
    </Box>
  );
}
