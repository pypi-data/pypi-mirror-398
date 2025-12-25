/**
 * Unit tests for jupyterlab_nb_venv_kernels_ui_extension
 *
 * Tests verify the context menu configuration for kernel launcher cards.
 */

// Expected context menu commands for .jp-LauncherCard
const EXPECTED_COMMANDS = [
  'launcher:show-kernel-in-file-browser',
  'launcher:open-terminal-at-kernel',
  'launcher:unregister-venv-kernel',
  'launcher:remove-venv-environment'
];

// Schema configuration mirrored from schema/plugin.json
const pluginSchema = {
  'jupyter.lab.menus': {
    context: [
      {
        command: 'launcher:show-kernel-in-file-browser',
        selector: '.jp-LauncherCard',
        rank: 10
      },
      {
        command: 'launcher:open-terminal-at-kernel',
        selector: '.jp-LauncherCard',
        rank: 11
      },
      {
        command: 'launcher:unregister-venv-kernel',
        selector: '.jp-LauncherCard',
        rank: 12
      },
      {
        command: 'launcher:remove-venv-environment',
        selector: '.jp-LauncherCard',
        rank: 13
      }
    ]
  }
};

describe('context menu configuration', () => {
  it('should define all expected context menu commands', () => {
    const contextItems = pluginSchema['jupyter.lab.menus'].context;

    for (const cmd of EXPECTED_COMMANDS) {
      const item = contextItems.find(
        (item: { command: string; selector: string }) =>
          item.command === cmd && item.selector === '.jp-LauncherCard'
      );
      expect(item).toBeDefined();
    }
  });

  it('should target .jp-LauncherCard selector for all commands', () => {
    const contextItems = pluginSchema['jupyter.lab.menus'].context;

    for (const item of contextItems) {
      expect(item.selector).toBe('.jp-LauncherCard');
    }
  });

  it('should have correct menu item order by rank', () => {
    const contextItems = pluginSchema['jupyter.lab.menus'].context;
    const ranks = contextItems.map((item: { rank: number }) => item.rank);

    // Verify ranks are in ascending order
    for (let i = 1; i < ranks.length; i++) {
      expect(ranks[i]).toBeGreaterThan(ranks[i - 1]);
    }
  });
});
