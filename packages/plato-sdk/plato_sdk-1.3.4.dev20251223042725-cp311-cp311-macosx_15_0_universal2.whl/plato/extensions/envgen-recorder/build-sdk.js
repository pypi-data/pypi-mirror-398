const esbuild = require('esbuild');
const path = require('path');

esbuild.build({
  entryPoints: [path.resolve(__dirname, 'sdk-browser-entry.ts')],
  bundle: true,
  outfile: 'plato-sdk-bundle.js',
  format: 'iife',
  globalName: 'PlatoSDK',
  platform: 'browser',
  target: 'es2020',
  sourcemap: true,
  minify: false,
}).then(() => console.log('✅ SDK bundled from sdk/typescript-sdk (browser-compatible)')).catch(err => {
  console.error('❌ Failed:', err);
  process.exit(1);
});
