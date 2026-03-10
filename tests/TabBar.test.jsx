import React from 'react';
import { render } from 'ink-testing-library';
import TabBar from '../src/components/TabBar.jsx';
import { SECTIONS } from '../src/sections.js';

test('renders all section labels', () => {
  const { lastFrame } = render(
    <TabBar sections={SECTIONS} activeIdx={0} />
  );
  SECTIONS.forEach(({ label }) => {
    expect(lastFrame()).toContain(label);
  });
});

test('highlights active section', () => {
  const { lastFrame } = render(
    <TabBar sections={SECTIONS} activeIdx={2} />
  );
  expect(lastFrame()).toContain('R/C Logs');
});
