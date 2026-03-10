import pkg from 'cfonts';
const { render } = pkg;

const OPTIONS = {
  font: 'block',
  colors: ['cyan', '#5f87ff'],
  background: 'transparent',
  letterSpacing: 0,
  lineHeight: 0,
  space: false,
  maxLength: 0,
};

function artLines(text) {
  const output = render(text, { ...OPTIONS, env: 'node' });
  return output.array ?? output.string.split('\n');
}

export const DIEGO_LINES = artLines('DIEGO');
export const ESCOBAR_LINES = artLines('ESCOBAR');
