import { expect, test } from '@jupyterlab/galata';

test('should load the extension without errors', async ({ page }) => {
  const errors: string[] = [];

  page.on('console', message => {
    if (message.type() === 'error') {
      errors.push(message.text());
    }
  });

  await page.goto();

  // Wait for JupyterLab to fully load
  await page.waitForSelector('.jp-FileBrowser');

  // Filter out errors not related to our extension
  const extensionErrors = errors.filter(e =>
    e.includes('jupyterlab_file_browser_sorting_extension')
  );

  expect(extensionErrors).toHaveLength(0);
});

test('should show Unix Style Sorting in context menu', async ({ page }) => {
  await page.goto();

  // Wait for file browser to load
  await page.waitForSelector('.jp-DirListing-content');

  // Right-click on file browser content area
  await page.click('.jp-DirListing-content', { button: 'right' });

  // Check for our menu item
  const menuItem = page.locator('text=Unix Style Sorting');
  await expect(menuItem).toBeVisible();
});
