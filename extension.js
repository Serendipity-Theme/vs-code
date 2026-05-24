const fs = require('fs');
const path = require('path');
const vscode = require('vscode');

function readTargetTheme() {
	const targetPath = path.join(__dirname, '.vscode-debug', 'theme-target.json');
	try {
		const { theme } = JSON.parse(fs.readFileSync(targetPath, 'utf8'));
		return typeof theme === 'string' ? theme : undefined;
	} catch {
		return process.env.SERENDIPITY_DEBUG_THEME;
	}
}

/**
 * VS Code extension dev host auto-picks a dev theme by type and ignores
 * launch.json colorTheme. Bootstrap with a built-in light/dark theme first,
 * then switch to the requested Serendipity variant once themes are registered.
 */
function activate(context) {
	const theme = readTargetTheme();
	if (!theme) {
		return;
	}

	const config = vscode.workspace.getConfiguration();
	const applyTheme = () => {
		if (config.get('workbench.colorTheme') !== theme) {
			void config.update(
				'workbench.colorTheme',
				theme,
				vscode.ConfigurationTarget.Global,
			);
		}
	};

	for (const delay of [0, 100, 300, 700, 1500, 3000]) {
		const handle = setTimeout(applyTheme, delay);
		context.subscriptions.push({ dispose: () => clearTimeout(handle) });
	}
}

function deactivate() {}

module.exports = { activate, deactivate };
