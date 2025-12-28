#!/usr/bin/env node
/**
 * Generate tracking_config.json based on DISABLE_TRACKING environment variable
 * This script is run during the build process to set build-time tracking configuration
 */

const fs = require('fs');
const path = require('path');

const disableTracking = process.env.DISABLE_TRACKING === 'true';

const config = {
  disableTracking: disableTracking
};

const configJson = JSON.stringify(config, null, 2);

// Write to src/Config (source)
const srcConfigPath = path.join(
  __dirname,
  '../src/Config/tracking_config.json'
);
fs.writeFileSync(srcConfigPath, configJson);

// Write to lib/Config (compiled output)
const libConfigPath = path.join(
  __dirname,
  '../lib/Config/tracking_config.json'
);
// Ensure directory exists
const libConfigDir = path.dirname(libConfigPath);
if (!fs.existsSync(libConfigDir)) {
  fs.mkdirSync(libConfigDir, { recursive: true });
}
fs.writeFileSync(libConfigPath, configJson);

console.log(`Tracking ${disableTracking ? 'disabled' : 'enabled'}`);
