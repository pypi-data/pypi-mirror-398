import typescript from '@rollup/plugin-typescript';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import json from '@rollup/plugin-json';

export default {
  input: './ui/ts/main.ts', // Your main TypeScript entry file
  output: {
    file: './ui/js/components.js', // Output bundle file
    format: 'es', // ES module format (works with import maps!)
    sourcemap: true // Optional: Generate source map
  },
  external: [
    // Keep Lit external (loaded via import map)
    'lit',
    'lit/decorators.js',
    'lit/directives/unsafe-html.js',
    // Keep Plotly external (too large to bundle, ~3MB)
    'plotly.js-dist-min'
    // tex-to-svg and mathjax-full will be BUNDLED
  ],
  plugins: [
    json(), // Handle JSON files with BOM
    typescript({
      tsconfig: './tsconfig.json',
      sourceMap: true,
      inlineSources: true,
      module: 'esnext'
    }), // Transpile TypeScript
    nodeResolve({
      browser: true,
      preferBuiltins: false
      // No resolveOnly - bundle everything except external
    }), // Resolve node_modules
    commonjs() // Convert CommonJS to ES6 (for tex-to-svg + mathjax-full)
  ],
  onwarn(warning, warn) {
    // Suppress certain warnings
    if (warning.code === 'THIS_IS_UNDEFINED') return;
    if (warning.code === 'CIRCULAR_DEPENDENCY') return;
    if (warning.code === 'MODULE_LEVEL_DIRECTIVE') return;
    if (warning.code === 'EVAL') return;
    warn(warning);
  }
};
