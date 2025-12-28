/* eslint-disable no-case-declarations */
/**
 * Class to handle the mention dropdown functionality in the chat input
 */
import { Contents } from '@jupyterlab/services';
import { ToolService } from '../../Services/ToolService';
import { ContextCacheService } from './ContextCacheService';
import {
  ChatContextLoaders,
  MENTION_CATEGORIES,
  IMentionContext
} from './ChatContextLoaders';
import { AppStateService } from '../../AppState';
import {
  calculateRelevanceScore,
  createCategoryItemElement,
  createDropdownItemElement,
  createLoadingIndicator,
  getCaretCoordinates,
  getCategoryForType,
  getEmptyMessageForCategory,
  getInputValue,
  getSelectionStart,
  positionDropdown,
  setInputValue,
  setSelectionRange
} from './ChatContextMenuUtils';
import { BACK_CARET_ICON, SEARCH_ICON } from './icons';

// Re-export for backward compatibility
export type { IMentionContext };

export class ChatContextMenu {
  private dropdownElement: HTMLDivElement;
  private searchInput: HTMLInputElement;
  private searchContainer: HTMLDivElement;
  private headerContainer: HTMLDivElement;
  private contentContainer: HTMLDivElement;
  private chatInput: HTMLElement; // Changed from HTMLTextAreaElement to HTMLElement
  private toolService: ToolService;
  private isVisible: boolean = false;
  private mentionTrigger: string = '@';
  private currentMentionStart: number = -1;
  private currentMentionText: string = '';
  private searchText: string = '';
  private contentManager: Contents.IManager;
  private onContextSelected: ((context: IMentionContext) => void) | null = null;
  private contextLoaders: ChatContextLoaders;
  private contextCacheService: ContextCacheService;

  // Navigation state
  private currentView: 'categories' | 'items' = 'categories';
  private selectedCategory: string | null = null;
  private selectedIndex: number = 0;
  private currentDataPath: string = './data'; // Track current directory path for data category

  // Categories and their items
  private categories = MENTION_CATEGORIES;

  private contextItems: Map<string, IMentionContext[]> = new Map();
  private isLoadingContexts: boolean = false;

  constructor(
    chatInput: HTMLElement, // Changed from HTMLTextAreaElement to HTMLElement
    parentElement: HTMLElement,
    contentManager: Contents.IManager,
    toolService: ToolService
  ) {
    this.chatInput = chatInput;
    this.contentManager = contentManager;
    this.toolService = toolService;
    this.contextLoaders = new ChatContextLoaders(contentManager, toolService);
    this.contextCacheService = ContextCacheService.getInstance();

    // Create dropdown element
    this.dropdownElement = document.createElement('div');
    this.dropdownElement.className = 'sage-ai-mention-dropdown';

    // Create header container for category title and search
    this.headerContainer = document.createElement('div');
    this.headerContainer.className = 'sage-ai-mention-header-container';

    // Create search container with icon and input
    this.searchContainer = document.createElement('div');
    this.searchContainer.className = 'sage-ai-mention-search-container';

    // Create search icon
    const searchIcon = SEARCH_ICON.element({
      className: 'sage-ai-mention-search-icon'
    });

    // Create search input
    this.searchInput = document.createElement('input');
    this.searchInput.type = 'text';
    this.searchInput.className = 'sage-ai-mention-search-input';
    this.searchInput.placeholder = 'Search...';

    // Add icon and input to search container
    this.searchContainer.appendChild(searchIcon);
    this.searchContainer.appendChild(this.searchInput);

    // Add search container to header container
    this.headerContainer.appendChild(this.searchContainer);

    // Create content container
    this.contentContainer = document.createElement('div');
    this.contentContainer.className = 'sage-ai-mention-content';

    // Add elements to dropdown
    this.dropdownElement.appendChild(this.headerContainer);
    this.dropdownElement.appendChild(this.contentContainer);

    parentElement.appendChild(this.dropdownElement);

    // Set up event listeners
    this.setupEventListeners();

    // Initialize context items for each category
    void this.initializeContextItems();
  }

  /**
   * Set a callback to be invoked when a context item is selected
   */
  public setContextSelectedCallback(
    callback: (context: IMentionContext) => void
  ): void {
    this.onContextSelected = callback;
  }

  /**
   * Initialize context items for each category
   */
  private async initializeContextItems(): Promise<void> {
    this.contextItems = await this.contextLoaders.initializeContextItems();
  }

  /**
   * Refresh context items for a specific category
   */
  private async refreshContextItems(categoryId: string): Promise<void> {
    console.log(
      `[ChatContextMenu] Refreshing context items for category: ${categoryId}`
    );

    try {
      switch (categoryId) {
        case 'data':
          // For data category, we load from cache/JSON file directly (no async waiting)
          const dataItems = await this.contextLoaders.loadDatasets('./data');
          this.contextItems.set('data', dataItems);
          console.log(
            `[ChatContextMenu] Loaded ${dataItems.length} data items from cache`
          );
          break;
        case 'snippets':
          const snippets = await this.contextLoaders.loadSnippets();
          this.contextItems.set('snippets', snippets);
          break;
        case 'variables':
          const variables = await this.contextLoaders.loadVariables();
          this.contextItems.set('variables', variables);
          break;
        case 'cells':
          const cells = await this.contextLoaders.loadCells();
          this.contextItems.set('cells', cells);
          break;
        case 'database':
          const databases = await this.contextLoaders.loadDatabases();
          this.contextItems.set('database', databases);
          break;
        case 'tables':
          const tables = await this.contextLoaders.loadTables();
          this.contextItems.set('tables', tables);
          break;
      }
    } catch (error) {
      console.error(
        `[ChatContextMenu] Error refreshing ${categoryId} category:`,
        error
      );
      // Set empty array as fallback
      this.contextItems.set(categoryId, []);
    }
  }

  /**
   * Set up event listeners for detecting @ mentions and handling selection
   */
  private setupEventListeners(): void {
    // Listen for input to detect @ character and filter dropdown
    this.chatInput.addEventListener('input', this.handleInput);

    // Listen for keydown to handle navigation and selection
    this.chatInput.addEventListener('keydown', this.handleKeyDown);

    // Listen for search input changes
    this.searchInput.addEventListener('input', this.handleSearchInput);
    this.searchInput.addEventListener('keydown', this.handleSearchKeyDown);

    // Close dropdown when clicking outside
    document.addEventListener('click', event => {
      if (
        !this.dropdownElement.contains(event.target as Node) &&
        event.target !== this.chatInput
      ) {
        this.hideDropdown();
      }
    });

    // Handle clicks on dropdown items
    this.dropdownElement.addEventListener('click', this.handleDropdownClick);
  }

  /**
   * Handle input events to detect @ mentions and update dropdown
   */
  private handleInput = async (event: Event): Promise<void> => {
    const cursorPosition = this.getSelectionStart();
    const inputValue = this.getInputValue();

    // Check if we're currently in a mention context
    if (this.isVisible) {
      // Check if cursor moved outside of the current mention
      if (
        cursorPosition < this.currentMentionStart ||
        !inputValue
          .substring(this.currentMentionStart, cursorPosition)
          .startsWith(this.mentionTrigger)
      ) {
        this.hideDropdown();
        return;
      }

      // Update the current mention text and search input to reflect what's being typed
      this.currentMentionText = inputValue.substring(
        this.currentMentionStart + 1,
        cursorPosition
      );

      // Sync the search input with what the user is typing after @
      if (this.searchInput.value !== this.currentMentionText) {
        this.searchInput.value = this.currentMentionText;
        this.searchText = this.currentMentionText;
      }

      // Wait for contexts to finish loading before rendering search results
      if (this.isLoadingContexts) {
        return; // Skip rendering until contexts are loaded
      }

      await this.renderDropdown(this.searchText);
      return;
    }

    // Look for a new mention
    if (inputValue.charAt(cursorPosition - 1) === this.mentionTrigger) {
      // Found a new mention
      this.currentMentionStart = cursorPosition - 1;
      this.currentMentionText = '';
      await this.showDropdown();
    }
  };

  /**
   * Handle search input changes
   */
  private handleSearchInput = async (event: Event): Promise<void> => {
    const target = event.target as HTMLInputElement;
    this.searchText = target.value;
    this.selectedIndex = 0; // Reset selection when search changes
    
    // Wait for contexts to finish loading before rendering search results
    if (this.isLoadingContexts) {
      return; // Skip rendering until contexts are loaded
    }
    
    await this.renderDropdown(this.searchText);
  };

  /**
   * Handle keydown events in the search input
   */
  private handleSearchKeyDown = (event: KeyboardEvent): void => {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        this.navigateDropdown('down');
        break;
      case 'ArrowUp':
        event.preventDefault();
        this.navigateDropdown('up');
        break;
      case 'Tab':
        event.preventDefault();
        void this.selectCurrentItem();
        break;
      case 'Enter':
        event.preventDefault();
        void this.selectCurrentItem();
        break;
      case 'Escape':
        event.preventDefault();
        this.hideDropdown();
        break;
    }
  };

  /**
   * Get the current selection start position
   */
  private getSelectionStart(): number {
    return getSelectionStart(this.chatInput);
  }

  /**
   * Get the current input value
   */
  private getInputValue(): string {
    return getInputValue(this.chatInput);
  }

  /**
   * Set the input value
   */
  private setInputValue(value: string): void {
    setInputValue(this.chatInput, value);
  }

  /**
   * Set selection range
   */
  private setSelectionRange(start: number, end: number): void {
    setSelectionRange(this.chatInput, start, end);
  }

  /**
   * Get caret coordinates for positioning the dropdown
   */
  private getCaretCoordinates(): { top: number; left: number; height: number } {
    return getCaretCoordinates(this.chatInput);
  }

  /**
   * Position the dropdown relative to the current cursor position
   */
  private positionDropdown(): void {
    if (!this.isVisible) {
      return;
    }

    const coords = this.getCaretCoordinates();
    console.log('Caret coordinates:', coords); // Debug log

    positionDropdown(this.dropdownElement, coords);
  }

  /**
   * Update the category header based on current view
   */
  private updateCategoryHeader(): void {
    // Remove existing category header if present
    const existingHeader = this.headerContainer.querySelector(
      '.sage-ai-mention-category-header'
    );
    if (existingHeader) {
      existingHeader.remove();
    }

    // Add category header only when in items view
    if (this.currentView === 'items' && this.selectedCategory) {
      const categoryHeader = document.createElement('div');
      categoryHeader.className = 'sage-ai-mention-category-header';

      // Create back caret icon
      const backIcon = BACK_CARET_ICON.element({
        className: 'sage-ai-mention-back-icon'
      });

      // Create category title
      const categoryTitle = document.createElement('span');
      categoryTitle.className = 'sage-ai-mention-category-title';

      // Find the category name and handle directory path for data category
      const category = this.categories.find(
        cat => cat.id === this.selectedCategory
      );
      let displayTitle = category?.name || this.selectedCategory;

      // For data category, show current directory path
      if (
        this.selectedCategory === 'data' &&
        this.currentDataPath !== './data'
      ) {
        const pathParts = this.currentDataPath.split('/');
        const currentDir = pathParts[pathParts.length - 1];
        displayTitle = `${category?.name || 'Data'} / ${currentDir}`;
      }

      categoryTitle.textContent = displayTitle;

      // Add click handler for navigation back
      categoryHeader.addEventListener('click', async () => {
        // If we're in a subdirectory of data, go back to parent
        if (
          this.selectedCategory === 'data' &&
          this.currentDataPath !== './data'
        ) {
          const pathParts = this.currentDataPath.split('/');
          pathParts.pop(); // Remove last part
          this.currentDataPath = pathParts.join('/') || './data';
          await this.refreshContextItems('data');
          void this.renderDropdown(this.searchText);
        } else {
          // Go back to categories view
          this.currentView = 'categories';
          this.selectedCategory = null;
          this.selectedIndex = 0;
          // Reset data path when leaving data category
          this.currentDataPath = './data';
          void this.renderDropdown(this.searchText);
        }
      });

      categoryHeader.appendChild(backIcon);
      categoryHeader.appendChild(categoryTitle);

      // Insert at the beginning of header container
      this.headerContainer.insertBefore(categoryHeader, this.searchContainer);
    }
  }

  /**
   * Render the dropdown based on current view and search text
   */
  private async renderDropdown(searchText: string): Promise<void> {
    this.contentContainer.innerHTML = '';

    // Update the category header based on current view
    this.updateCategoryHeader();

    if (this.currentView === 'categories') {
      // Always show database schema first if available
      const hasDbSchema = this.renderDatabaseSchema(searchText);

      // If there's search text, show matching items next
      if (searchText && searchText.length > 0) {
        const hasMatchingItems = this.renderMatchingItems(searchText);

        // Add a separator before categories if we have database schema or matching items
        if ((hasDbSchema || hasMatchingItems) && searchText.length < 2) {
          const separator = document.createElement('div');
          separator.className = 'sage-ai-mention-separator';
          separator.textContent = 'Categories';
          this.contentContainer.appendChild(separator);
        }

        // Only show categories if we don't have good matches or search is very short
        if (!hasMatchingItems || searchText.length < 2) {
          this.renderCategories();
        }
      } else {
        // No search text - add separator before categories if we have database schema
        if (hasDbSchema) {
          const separator = document.createElement('div');
          separator.className = 'sage-ai-mention-separator';
          separator.textContent = 'Categories';
          this.contentContainer.appendChild(separator);
        }
        this.renderCategories();
      }
    } else if (this.currentView === 'items' && this.selectedCategory) {
      // Show items in the category with filtering if there's search text
      await this.renderCategoryItems(this.selectedCategory, searchText);
    }

    // Reset to first item and highlight it
    this.selectedIndex = 0;
    this.highlightItem(this.selectedIndex);
    this.positionDropdown();
  }

  /**
   * Calculate a relevance score for an item based on search text
   */
  private calculateRelevanceScore(
    item: IMentionContext,
    searchText: string
  ): number {
    return calculateRelevanceScore(item, searchText);
  }

  /**
   * Render items that match the search text across all categories
   * @returns true if matching items were found and rendered, false otherwise
   */
  private renderMatchingItems(searchText: string): boolean {
    const matchingItems: Array<{ item: IMentionContext; score: number }> = [];

    // Collect matching items from all categories with scores
    for (const [categoryId, items] of this.contextItems.entries()) {
      let itemsToSearch = items;

      // For data category, when searching, include ALL files (not just top-level)
      // to ensure search works across subdirectories
      if (categoryId === 'data') {
        // Filter out directories, but include all files regardless of location
        itemsToSearch = items.filter((item: IMentionContext) => !item.isDirectory);
      }

      for (const item of itemsToSearch) {
        const score = this.calculateRelevanceScore(item, searchText);
        if (score > 500) {
          // Filter out items with too little relevance
          matchingItems.push({ item, score });
        }
      }
    }

    // Sort by score (highest first), then by name
    matchingItems.sort((a, b) => {
      if (a.score !== b.score) {
        return b.score - a.score;
      }
      return a.item.name.localeCompare(b.item.name);
    });

    if (matchingItems.length > 0) {
      // Limit to maximum 10 matching items
      matchingItems.slice(0, 10).forEach(({ item }) => {
        const itemElement = createDropdownItemElement(
          item,
          'sage-ai-mention-item sage-ai-mention-subcategory',
          getCategoryForType(item.type)
        );
        this.contentContainer.appendChild(itemElement);
      });

      return true;
    }

    return false;
  }

  /**
   * Get category ID for a given item type
   */
  private getCategoryForType(type: string): string {
    return getCategoryForType(type);
  }

  /**
   * Render the categories view
   */
  private renderCategories(): void {
    console.log(
      '[ChatContextMenu] Rendering categories:',
      this.categories.map(c => c.id)
    );
    this.categories.forEach(category => {
      console.log(
        `[ChatContextMenu] Creating element for category: ${category.id} - ${category.name}`
      );
      const itemElement = createCategoryItemElement(category);
      this.contentContainer.appendChild(itemElement);
    });
  }

  /**
   * Filter items to only show those that belong to the current directory level
   */
  private filterItemsForCurrentDirectory(
    items: IMentionContext[],
    currentPath: string
  ): IMentionContext[] {
    // Normalize the current path
    const normalizedCurrentPath = currentPath.replace(/\\/g, '/');

    // For the root data directory, show items that are either:
    // 1. Database schema (special case)
    // 2. Files directly in the data directory (no subdirectory in path)
    // 3. Directories that are direct children of the data directory
    if (normalizedCurrentPath === './data') {
      return items.filter(item => {
        // Always show database schema at root level
        if (item.id === 'database-schema') {
          return true;
        }

        // Skip items that don't have a path (shouldn't happen, but safety check)
        if (!item.path) {
          return false;
        }

        const itemPath = item.path.replace(/\\/g, '/');

        // Remove the './data/' prefix to get the relative path
        const relativePath = itemPath
          .replace('./data/', '')
          .replace('./data', '');

        // If no relative path or empty, it's in the root
        if (!relativePath || relativePath === item.name) {
          return true;
        }

        // For directories, show only direct children (no '/' in the relative path)
        if (item.isDirectory) {
          return (
            !relativePath.includes('/') || relativePath.split('/').length === 1
          );
        }

        // For files, show only those directly in the data folder (no '/' in relative path)
        return !relativePath.includes('/');
      });
    }

    // For subdirectories, show items that are direct children of the current directory
    return items.filter(item => {
      // Skip database schema in subdirectories
      if (item.id === 'database-schema') {
        return false;
      }

      // Skip items that don't have a path
      if (!item.path) {
        return false;
      }

      const itemPath = item.path.replace(/\\/g, '/');

      // Check if the item's parent path matches the current path
      if (item.parentPath) {
        const normalizedParentPath = item.parentPath.replace(/\\/g, '/');
        return normalizedParentPath === normalizedCurrentPath;
      }

      // Fallback: check if the item path starts with current path
      const expectedPrefix =
        normalizedCurrentPath === './data'
          ? './data/'
          : `${normalizedCurrentPath}/`;
      if (!itemPath.startsWith(expectedPrefix)) {
        return false;
      }

      // Get the remainder after removing the current path prefix
      const remainder = itemPath.substring(expectedPrefix.length);

      // Show only direct children (no additional '/' in the remainder)
      return !remainder.includes('/');
    });
  }

  /**
   * Render items for a specific category
   */
  private async renderCategoryItems(
    categoryId: string,
    searchText: string = ''
  ): Promise<void> {
    // For data category, ensure we have the latest cached data available
    if (categoryId === 'data') {
      // Just refresh context items synchronously (loads from cache)
      await this.refreshContextItems('data');
    }

    const items = this.contextItems.get(categoryId) || [];
    console.log(`Rendering items for category ${categoryId}:`, items); // Debug log

    if (items.length === 0) {
      const emptyElement = document.createElement('div');
      emptyElement.className = 'sage-ai-mention-empty';
      emptyElement.textContent = getEmptyMessageForCategory(categoryId);
      this.contentContainer.appendChild(emptyElement);
      return;
    }

    // For data category, show all files in a flattened structure
    if (categoryId === 'data') {
      // Filter items to only show files (not directories)
      const files = items.filter((item: IMentionContext) => !item.isDirectory);

      // Filter based on search text
      let displayFiles = files;

      if (searchText) {
        const matchingFiles: Array<{ item: IMentionContext; score: number }> =
          [];

        for (const item of files) {
          const score = this.calculateRelevanceScore(item, searchText);
          if (score > 500) {
            matchingFiles.push({ item, score });
          }
        }

        // Sort by score (highest first), then by name
        matchingFiles.sort((a, b) => {
          if (a.score !== b.score) {
            return b.score - a.score;
          }
          return a.item.name.localeCompare(b.item.name);
        });

        displayFiles = matchingFiles.slice(0, 15).map(({ item }) => item);
      } else {
        // Sort files alphabetically when no search
        displayFiles = files.sort((a, b) => a.name.localeCompare(b.name));
      }

      // Render all files in a flat list
      displayFiles.forEach((item: IMentionContext) => {
        const itemElement = createDropdownItemElement(
          item,
          'sage-ai-mention-item sage-ai-mention-subcategory'
        );
        this.contentContainer.appendChild(itemElement);
      });
    } else {
      // Handle other categories as before
      let displayItems = items;
      if (searchText) {
        const matchingItems: Array<{ item: IMentionContext; score: number }> =
          [];

        for (const item of items) {
          const score = this.calculateRelevanceScore(item, searchText);
          if (score > 500) {
            matchingItems.push({ item, score });
          }
        }

        matchingItems.sort((a, b) => {
          if (a.score !== b.score) {
            return b.score - a.score;
          }
          return a.item.name.localeCompare(b.item.name);
        });

        displayItems = matchingItems.slice(0, 10).map(({ item }) => item);
      }

      // Show filtered/sorted items
      displayItems.forEach(item => {
        const itemElement = createDropdownItemElement(
          item,
          'sage-ai-mention-item sage-ai-mention-subcategory'
        );
        this.contentContainer.appendChild(itemElement);
      });
    }
  }

  /**
   * Render database schema item if available
   * @param searchText Optional search text to filter database schema
   * @returns true if database schema was rendered, false otherwise
   */
  private renderDatabaseSchema(searchText: string = ''): boolean {
    // Look for database schema in the data category
    const dataItems = this.contextItems.get('data') || [];
    const dbSchemaItem = dataItems.find(item => item.id === 'database-schema');

    if (!dbSchemaItem) {
      return false;
    }

    // If there's search text, check if database schema matches
    if (searchText && searchText.length > 0) {
      const score = this.calculateRelevanceScore(dbSchemaItem, searchText);
      if (score <= 500) {
        return false; // Don't show if relevance is too low
      }
    }

    // Create and append the database schema item
    const itemElement = createDropdownItemElement(
      dbSchemaItem,
      'sage-ai-mention-item sage-ai-mention-subcategory sage-ai-mention-database-schema',
      'data'
    );
    this.contentContainer.appendChild(itemElement);

    return true;
  }

  /**
   * Handle clicks on dropdown items
   */
  private handleDropdownClick = async (event: Event): Promise<void> => {
    event.preventDefault();
    event.stopPropagation();

    const target = event.target as Element;

    // Handle category selection
    const categoryItem = target.closest('.sage-ai-mention-category-main');
    if (categoryItem) {
      const categoryId = categoryItem.getAttribute('data-category');
      if (categoryId) {
        this.selectedCategory = categoryId;
        this.currentView = 'items';
        // Reset data path when entering data category
        if (categoryId === 'data') {
          this.currentDataPath = './data';
        }
        // Clear search when entering a category
        this.searchInput.value = '';
        this.searchText = '';
        this.updateSearchPlaceholder();

        // For data category, just render - data is already loaded from cache
        void this.renderDropdown(this.searchText);
        this.positionDropdown(); // Reposition after content change
        // Focus search input
        setTimeout(() => this.searchInput.focus(), 0);
      }
      return;
    }

    // Handle item selection
    const mentionItem = target.closest('.sage-ai-mention-subcategory');
    if (mentionItem) {
      const itemId = mentionItem.getAttribute('data-id');
      const categoryId = mentionItem.getAttribute('data-category');
      const itemType = mentionItem.getAttribute('data-type');

      if (itemId) {
        // Check if this is a directory in the data category
        if (itemType === 'directory' && this.selectedCategory === 'data') {
          // Navigate into the directory
          this.currentDataPath = itemId; // itemId contains the full path for directories
          await this.refreshContextItems('data');
          void this.renderDropdown(this.searchText);
          this.positionDropdown();
          return;
        }

        // If we're selecting from the matching items section and have a category
        if (this.currentView === 'categories' && categoryId) {
          this.selectedCategory = categoryId;
        }

        void this.selectItem(itemId);
      }
    }
  };

  /**
   * Highlight a specific item in the dropdown
   */
  private highlightItem(index: number): void {
    // Remove active class from all items
    const items = this.contentContainer.querySelectorAll(
      '.sage-ai-mention-item, .sage-ai-mention-subcategory'
    );
    items.forEach(item => item.classList.remove('active'));

    // Add active class to the specified item
    if (items.length > 0 && index >= 0 && index < items.length) {
      items[index].classList.add('active');

      // Scroll to the item if needed
      const itemElement = items[index] as HTMLElement;
      const contentRect = this.contentContainer.getBoundingClientRect();
      const itemRect = itemElement.getBoundingClientRect();

      if (itemRect.bottom > contentRect.bottom) {
        this.contentContainer.scrollTop += itemRect.bottom - contentRect.bottom;
      } else if (itemRect.top < contentRect.top) {
        this.contentContainer.scrollTop -= contentRect.top - itemRect.top;
      }
    }
  }

  /**
   * Select an item from the dropdown and insert it into the input
   */
  private async selectItem(itemId: string): Promise<void> {
    // Find the selected item
    let selectedItem: IMentionContext | undefined;

    if (this.selectedCategory) {
      // Search in the specific category
      const categoryItems = this.contextItems.get(this.selectedCategory) || [];
      selectedItem = categoryItems.find(item => item.id === itemId);
    } else {
      // Search across all categories
      for (const [, items] of this.contextItems.entries()) {
        selectedItem = items.find(item => item.id === itemId);
        if (selectedItem) {
          break;
        }
      }
    }

    if (!selectedItem) {
      return;
    }

    // Replace the mention with the selected item
    const beforeMention = this.getInputValue().substring(
      0,
      this.currentMentionStart
    );
    // Calculate the end of the current mention: start + '@' + current typed text
    const currentMentionEnd =
      this.currentMentionStart + 1 + this.currentMentionText.length;
    const afterMention = this.getInputValue().substring(currentMentionEnd);

    // Format: @{item name} - replace spaces with non-breaking spaces for valid mention syntax
    const displayName = selectedItem.name.replace(/\s+/g, '_');
    const replacement = `@${displayName} `;

    // Update the input value
    this.setInputValue(beforeMention + replacement + afterMention);

    // Set cursor position after the inserted mention
    const newCursorPosition = this.currentMentionStart + replacement.length;
    this.setSelectionRange(newCursorPosition, newCursorPosition);

    // Hide the dropdown
    this.hideDropdown();

    // Focus the input
    this.chatInput.focus();

    // Load content if needed and invoke callback
    if (this.onContextSelected) {
      const contextWithContent = { ...selectedItem };

      // Snippets already have their content loaded, so no need to fetch it separately
      this.onContextSelected(contextWithContent);
    }
  }

  /**
   * Update search placeholder based on current view
   */
  private updateSearchPlaceholder(): void {
    if (this.currentView === 'categories') {
      this.searchInput.placeholder = 'Search all items...';
    } else if (this.selectedCategory) {
      const categoryName =
        this.categories.find(cat => cat.id === this.selectedCategory)?.name ||
        'items';
      this.searchInput.placeholder = `Search ${categoryName.toLowerCase()}...`;
    }
  }

  /**
   * Show loading indicator in the dropdown
   */
  private showLoadingState(message: string = 'Loading contexts...'): void {
    // Remove any existing loading indicator first
    const existingLoader = this.contentContainer.querySelector(
      '.sage-ai-mention-loading'
    );
    if (existingLoader) {
      existingLoader.remove();
    }

    // Create and append the loading element at the bottom
    const loadingElement = createLoadingIndicator(message);
    this.contentContainer.appendChild(loadingElement);
  }

  /**
   * Hide loading indicator from the dropdown
   */
  private hideLoadingState(): void {
    const existingLoader = this.contentContainer.querySelector(
      '.sage-ai-mention-loading'
    );
    if (existingLoader) {
      existingLoader.remove();
    }
  }

  /**
   * Show the dropdown
   */
  async showDropdown() {
    this.isVisible = true;
    this.currentView = 'categories';
    this.selectedCategory = null;
    this.selectedIndex = 0;
    this.dropdownElement.classList.add('visible');

    // Clear and setup search input for categories view
    this.searchInput.value = '';
    this.searchText = '';
    this.updateSearchPlaceholder();

    // Position dropdown first so it appears
    this.positionDropdown();

    // Trigger async data refresh in the background (non-blocking)
    this.contextLoaders.triggerAsyncDataRefresh();

    // Check if contexts are currently being loaded
    if (AppStateService.isContextLoading()) {
      // First render the existing content, then show loading at bottom
      await this.loadContextsAndRender();
      this.showLoadingState('Refreshing contexts...');
      // Wait for loading to complete, then refresh
      const checkLoading = setInterval(async () => {
        if (!AppStateService.isContextLoading()) {
          clearInterval(checkLoading);
          this.hideLoadingState();
          await this.loadContextsAndRender();
        }
      }, 100);
      return;
    }

    await this.loadContextsAndRender();
  }

  /**
   * Load contexts and render the dropdown
   */
  private async loadContextsAndRender(): Promise<void> {
    // Set loading flag to prevent premature renders during typing
    this.isLoadingContexts = true;
    
    // Get contexts from cache (this will load them if not available)
    try {
      const cachedContexts = await this.contextCacheService.getContexts();

      // Update context items with cached data
      this.contextItems = cachedContexts;

      console.log(
        '[ChatContextMenu] Using cached contexts:',
        Array.from(this.contextItems.entries()).map(
          ([key, items]) => `${key}: ${items.length} items`
        )
      );
    } catch (error) {
      console.warn(
        '[ChatContextMenu] Failed to get cached contexts, falling back to direct loading:',
        error
      );

      // Fallback: Load contexts directly if cache fails
      const snippetContexts = await this.contextLoaders.loadSnippets();
      const variableContexts = await this.contextLoaders.loadVariables();
      const datasetContexts = await this.contextLoaders.loadDatasets();
      const cellContexts = await this.contextLoaders.loadCells();
      const databaseContexts = await this.contextLoaders.loadDatabases();

      this.contextItems.set('snippets', snippetContexts);
      this.contextItems.set('data', datasetContexts);
      this.contextItems.set('variables', variableContexts);
      this.contextItems.set('cells', cellContexts);

      const tableContexts = await this.contextLoaders.loadTables();
      this.contextItems.set('tables', tableContexts);
      this.contextItems.set('database', databaseContexts);
    } finally {
      // Clear loading flag - contexts are now available
      this.isLoadingContexts = false;
    }

    // Render with current search text (which might have been typed while loading)
    await this.renderDropdown(this.searchText);

    // Focus the search input for immediate typing
    setTimeout(() => this.searchInput.focus(), 0);
  }

  /**
   * Hide the dropdown
   */
  hideDropdown(): void {
    this.isVisible = false;
    this.dropdownElement.classList.remove('visible');
    this.currentMentionStart = -1;
    this.currentMentionText = '';
    this.currentView = 'categories';
    this.selectedCategory = null;
  }

  /**
   * Handle keydown events for navigation and selection
   */
  private handleKeyDown = (event: KeyboardEvent): void => {
    if (!this.isVisible) {
      return;
    }

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        this.navigateDropdown('down');
        break;
      case 'ArrowUp':
        event.preventDefault();
        this.navigateDropdown('up');
        break;
      case 'Tab':
        event.preventDefault();
        void this.selectCurrentItem();
        break;
      case 'Enter':
        event.preventDefault();
        void this.selectCurrentItem();
        break;
      case 'Escape':
        event.preventDefault();
        this.hideDropdown();
        break;
    }
  };

  /**
   * Navigate through dropdown items
   */
  private navigateDropdown(direction: 'up' | 'down'): void {
    const items = this.contentContainer.querySelectorAll(
      '.sage-ai-mention-item, .sage-ai-mention-subcategory'
    );

    if (items.length === 0) {
      return;
    }

    if (direction === 'down') {
      this.selectedIndex = (this.selectedIndex + 1) % items.length;
    } else {
      this.selectedIndex =
        this.selectedIndex <= 0 ? items.length - 1 : this.selectedIndex - 1;
    }

    this.highlightItem(this.selectedIndex);
  }

  /**
   * Select the currently highlighted item
   */
  private async selectCurrentItem(): Promise<void> {
    const items = this.dropdownElement.querySelectorAll(
      '.sage-ai-mention-item, .sage-ai-mention-subcategory'
    );

    if (
      items.length === 0 ||
      this.selectedIndex < 0 ||
      this.selectedIndex >= items.length
    ) {
      return;
    }

    const selectedElement = items[this.selectedIndex] as HTMLElement;

    // Handle category selection
    if (selectedElement.classList.contains('sage-ai-mention-category-main')) {
      const categoryId = selectedElement.getAttribute('data-category');
      if (categoryId) {
        this.selectedCategory = categoryId;
        this.currentView = 'items';
        this.selectedIndex = 0;
        // Reset data path when entering data category
        if (categoryId === 'data') {
          this.currentDataPath = './data';
        }
        // Clear search when entering a category
        this.searchInput.value = '';
        this.searchText = '';
        this.updateSearchPlaceholder();

        // Refresh context items for this category
        await this.refreshContextItems(categoryId);
        await this.renderDropdown(this.searchText);
        this.positionDropdown();
        // Focus search input
        setTimeout(() => this.searchInput.focus(), 0);
      }
      return;
    }

    // Handle item selection
    if (selectedElement.classList.contains('sage-ai-mention-subcategory')) {
      const itemId = selectedElement.getAttribute('data-id');
      const categoryId = selectedElement.getAttribute('data-category');
      const itemType = selectedElement.getAttribute('data-type');

      if (itemId) {
        // Check if this is a directory in the data category
        if (itemType === 'directory' && this.selectedCategory === 'data') {
          // Navigate into the directory
          this.currentDataPath = itemId; // itemId contains the full path for directories
          await this.refreshContextItems('data');
          await this.renderDropdown(this.searchText);
          this.positionDropdown();
          return;
        }

        // If we're selecting from the matching items section and have a category
        if (this.currentView === 'categories' && categoryId) {
          this.selectedCategory = categoryId;
        }

        void this.selectItem(itemId);
      }
    }
  }

  /**
   * Trigger selection of the currently highlighted item (public method)
   */
  public selectHighlightedItem(): void {
    void this.selectCurrentItem();
  }

  /**
   * Check if dropdown is visible (public method)
   */
  public getIsVisible(): boolean {
    return this.isVisible;
  }
}
