import React from 'react';
import { render } from 'ink-testing-library';
import { Text } from 'ink';
import Layout from '../src/components/Layout.jsx';

test('renders left and right panels side by side', () => {
  const { lastFrame } = render(
    <Layout
      cols={80}
      rows={24}
      left={<Text>LEFT</Text>}
      right={<Text>RIGHT</Text>}
    />
  );
  expect(lastFrame()).toContain('LEFT');
  expect(lastFrame()).toContain('RIGHT');
});
