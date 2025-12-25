import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { IFileBrowserFactory, FileBrowser } from '@jupyterlab/filebrowser';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { Contents } from '@jupyterlab/services';

const PLUGIN_ID = 'jupyterlab_file_browser_sorting_extension:plugin';
const COMMAND_TOGGLE_UNIX_SORT = 'filebrowser:toggle-unix-sorting';

/**
 * LC_COLLATE=C (ASCIIbetical) comparison function.
 * Sort order: . -> 0-9 -> A-Z -> _ -> a-z
 */
function cLocaleCompare(a: string, b: string): number {
  const lenA = a.length;
  const lenB = b.length;
  const minLen = Math.min(lenA, lenB);

  for (let i = 0; i < minLen; i++) {
    const charCodeA = a.charCodeAt(i);
    const charCodeB = b.charCodeAt(i);
    if (charCodeA !== charCodeB) {
      return charCodeA - charCodeB;
    }
  }
  return lenA - lenB;
}

/**
 * Default locale comparison (case-insensitive).
 */
function defaultLocaleCompare(a: string, b: string): number {
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
}

// Global settings
let sortNotebooksFirst = false;
let useCLocaleSorting = true;

/**
 * Sort items using the specified comparison function.
 */
function sortItems(
  items: Contents.IModel[],
  state: { direction: 'ascending' | 'descending'; key: string }
): Contents.IModel[] {
  const copy = [...items];
  const reverse = state.direction === 'descending' ? -1 : 1;

  function getPriority(item: Contents.IModel): number {
    if (item.type === 'directory') {
      return 0;
    }
    if (sortNotebooksFirst && item.type === 'notebook') {
      return 1;
    }
    return 2;
  }

  function compareByName(a: Contents.IModel, b: Contents.IModel): number {
    return useCLocaleSorting
      ? cLocaleCompare(a.name, b.name)
      : defaultLocaleCompare(a.name, b.name);
  }

  copy.sort((a, b) => {
    const priorityA = getPriority(a);
    const priorityB = getPriority(b);
    if (priorityA !== priorityB) {
      return priorityA - priorityB;
    }

    let result: number;
    if (state.key === 'last_modified') {
      result =
        new Date(a.last_modified).getTime() -
        new Date(b.last_modified).getTime();
    } else if (state.key === 'file_size') {
      result = (b.size ?? 0) - (a.size ?? 0);
    } else {
      result = compareByName(a, b);
    }
    return result * reverse;
  });

  return copy;
}

const plugin: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  description: 'LC_COLLATE=C file browser sorting',
  autoStart: true,
  requires: [IFileBrowserFactory],
  optional: [ISettingRegistry],
  activate: (
    app: JupyterFrontEnd,
    factory: IFileBrowserFactory,
    settingRegistry: ISettingRegistry | null
  ) => {
    const { commands } = app;
    const { tracker } = factory;
    const patchedListings = new WeakSet<object>();

    /**
     * Force re-sort on a single listing
     */
    function resortListing(listing: any): void {
      if (!listing || !listing.sortState) {
        return;
      }
      // Use patched sort method which handles customSortedItems
      listing.sort(listing.sortState);
    }

    /**
     * Force re-sort on all browsers
     */
    function resortAllBrowsers(): void {
      tracker.forEach((browser: FileBrowser) => {
        const listing = (browser as any).listing;
        resortListing(listing);
      });
    }

    /**
     * Patch a DirListing to use custom sorting.
     */
    function patchListing(listing: any): void {
      if (!listing || patchedListings.has(listing)) {
        return;
      }
      patchedListings.add(listing);

      // Store reference to our custom sorted items
      let customSortedItems: Contents.IModel[] = [];

      // Override sortedItems getter to return our custom sorted items
      Object.defineProperty(listing, 'sortedItems', {
        get: function () {
          return customSortedItems;
        },
        configurable: true
      });

      // Store original sort
      const originalSort = listing.sort.bind(listing);

      // Override sort method
      listing.sort = function (state: {
        direction: 'ascending' | 'descending';
        key: string;
      }): void {
        const model = this.model;
        if (!model) {
          originalSort(state);
          return;
        }

        const itemsArray = Array.from(model.items()) as Contents.IModel[];
        if (itemsArray.length === 0) {
          this._sortState = state;
          customSortedItems = [];
          this._sortedItems = [];
          originalSort(state);
          return;
        }

        const sorted = sortItems(itemsArray, state);
        customSortedItems = sorted;
        this._sortedItems = sorted;
        this._sortState = state;
        this.update();
      };

      // Hook into model refresh to re-sort
      const model = listing.model;
      if (model && model.refreshed) {
        model.refreshed.connect(() => {
          if (listing.sortState) {
            listing.sort(listing.sortState);
          }
        });
      }

      // Trigger initial sort
      if (listing.sortState) {
        listing.sort(listing.sortState);
      }
    }

    function patchFileBrowser(browser: FileBrowser): void {
      const listing = (browser as any).listing;
      if (listing) {
        patchListing(listing);
      }
    }

    // Load settings
    if (settingRegistry) {
      settingRegistry
        .load('@jupyterlab/filebrowser-extension:browser')
        .then(settings => {
          sortNotebooksFirst =
            (settings.get('sortNotebooksFirst').composite as boolean) ?? false;
          settings.changed.connect(() => {
            sortNotebooksFirst =
              (settings.get('sortNotebooksFirst').composite as boolean) ??
              false;
          });
        })
        .catch(() => {});

      settingRegistry
        .load(PLUGIN_ID)
        .then(settings => {
          useCLocaleSorting =
            (settings.get('useCLocaleSorting').composite as boolean) ?? true;

          settings.changed.connect(() => {
            const newValue =
              (settings.get('useCLocaleSorting').composite as boolean) ?? true;
            useCLocaleSorting = newValue;
            resortAllBrowsers();
          });
        })
        .catch(() => {});
    }

    // Register toggle command
    commands.addCommand(COMMAND_TOGGLE_UNIX_SORT, {
      label: 'Unix Style Sorting',
      caption: 'Sort: dot files first, uppercase before lowercase',
      isToggleable: true,
      isToggled: () => useCLocaleSorting,
      execute: async () => {
        if (settingRegistry) {
          const settings = await settingRegistry.load(PLUGIN_ID);
          await settings.set('useCLocaleSorting', !useCLocaleSorting);
        } else {
          useCLocaleSorting = !useCLocaleSorting;
          resortAllBrowsers();
        }
      }
    });

    // Add to context menu at bottom
    app.contextMenu.addItem({
      command: COMMAND_TOGGLE_UNIX_SORT,
      selector: '.jp-DirListing-item',
      rank: 100
    });

    app.contextMenu.addItem({
      command: COMMAND_TOGGLE_UNIX_SORT,
      selector: '.jp-DirListing',
      rank: 100
    });

    // Wait for app to be fully restored before patching
    app.restored.then(() => {
      // Patch existing browsers
      tracker.forEach(patchFileBrowser);

      // Patch new browsers when added
      tracker.widgetAdded.connect((_, browser) => {
        patchFileBrowser(browser);
      });
    });
  }
};

export default plugin;
