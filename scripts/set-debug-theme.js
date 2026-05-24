#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const theme = process.argv[2];
if (!theme) {
	console.error('Usage: set-debug-theme.js <theme-label>');
	process.exit(1);
}

const debugDir = path.join(__dirname, '..', '.vscode-debug');
const userDir = path.join(debugDir, 'user-data', 'User');
fs.mkdirSync(userDir, { recursive: true });

const isLight = theme.includes('Morning');
const bootstrapTheme = isLight ? 'Default Light Modern' : 'Default Dark Modern';

fs.writeFileSync(
	path.join(userDir, 'settings.json'),
	`${JSON.stringify(
		{
			'window.autoDetectColorScheme': false,
			'workbench.colorTheme': bootstrapTheme,
		},
		null,
		2,
	)}\n`,
);

fs.writeFileSync(
	path.join(debugDir, 'theme-target.json'),
	`${JSON.stringify({ theme }, null, 2)}\n`,
);

console.log(`Debug bootstrap: ${bootstrapTheme} → ${theme}`);
