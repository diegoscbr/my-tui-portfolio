import React, { useState } from 'react';
import { useInput } from 'ink';
import Layout from './components/Layout.jsx';
import VideoPlayer from './components/VideoPlayer.jsx';
import TabBar from './components/TabBar.jsx';
import { SECTIONS } from './sections.js';
import NoticeBoard from './sections/NoticeBoard.jsx';
import SailingInstructions from './sections/SailingInstructions.jsx';
import RCLogs from './sections/RCLogs.jsx';
import Contact from './sections/Contact.jsx';
import Experience from './sections/Experience.jsx';

const SECTION_COMPONENTS = [
  NoticeBoard,
  SailingInstructions,
  RCLogs,
  Contact,
  Experience,
];

export default function App({ rows = 24, cols = 80 }) {
  const [activeIdx, setActiveIdx] = useState(0);

  useInput((input, key) => {
    if (input === 'q' || key.escape) process.exit(0);
    if (key.leftArrow) setActiveIdx((i) => Math.max(0, i - 1));
    if (key.rightArrow) setActiveIdx((i) => Math.min(SECTIONS.length - 1, i + 1));
  });

  const ActiveSection = SECTION_COMPONENTS[activeIdx];
  const contentRows = rows - 3;

  return (
    <Layout
      cols={cols}
      rows={rows}
      left={<VideoPlayer height={contentRows} />}
      right={<ActiveSection />}
      footer={<TabBar sections={SECTIONS} activeIdx={activeIdx} />}
    />
  );
}
