import {
  INotebookTracker,
  Notebook,
  NotebookPanel
} from '@jupyterlab/notebook';
import { Cell } from '@jupyterlab/cells';
import { NotebookDiffTools } from './NotebookDiffTools';
import { NotebookCellTools } from './NotebookCellTools';
import { TrackingIDUtility } from '../TrackingIDUtility';
import { WaitingUserReplyBoxManager } from './WaitingUserReplyBoxManager';
import { FilesystemTools } from '../BackendTools/FilesystemTools';
import { WebTools } from '../BackendTools/WebTools';
import { DatabaseSearchTools } from '../BackendTools/DatabaseSearchTools';
import { TerminalTools } from '../BackendTools/TerminalTools';
import { AppStateService } from '../AppState';
import {
  DatabaseStateService,
  IDatabaseConfig,
  ISnowflakeCredentials,
  IDatabricksCredentials
} from '../DatabaseStateService';
import { Subscription } from 'rxjs';
import { timeout } from '../utils';
import { v4 as uuidv4 } from 'uuid';

/**
 * Class providing tools for manipulating notebook cells
 */
export class NotebookTools {
  private cellTools: NotebookCellTools;
  private notebookTracker: INotebookTracker;
  private diffTools: NotebookDiffTools;
  private waitingUserReplyBoxManager: WaitingUserReplyBoxManager;
  private filesystemTools: FilesystemTools;
  private webTools: WebTools;
  private terminalTools: TerminalTools;
  private subscriptions: Subscription[] = [];

  /**
   * Create a new NotebookTools instance
   * @param notebooks The notebook tracker from JupyterLab
   */
  constructor(
    notebooks: INotebookTracker,
    waitingUserReplyBoxManager: WaitingUserReplyBoxManager
  ) {
    this.notebookTracker = notebooks;
    this.waitingUserReplyBoxManager = waitingUserReplyBoxManager;
    this.diffTools = new NotebookDiffTools();
    this.filesystemTools = new FilesystemTools();
    this.webTools = new WebTools();
    this.terminalTools = new TerminalTools();
    this.cellTools = new NotebookCellTools(this);

    // Subscribe to notebook change events (no need to track locally)
  }

  /**
   * Get the current active notebook or return null if none
   * @param notebookIdentifier Optional notebook path or ID to specify which notebook to get
   * @returns The current notebook or null
   */
  public getCurrentNotebook(
    _notebookIdentifier?: string | null
  ): { notebook: Notebook; widget: NotebookPanel } | null {
    const notebookIdentifier = _notebookIdentifier?.replace('.ipynb', '');
    // If a specific notebook ID/path is requested, try to resolve it
    if (notebookIdentifier && notebookIdentifier.trim().length > 0) {
      // Try to locate an open notebook matching the identifier (ID or path)
      let matched: NotebookPanel | null = null;
      this.notebookTracker.forEach(panel => {
        if (matched) {
          return;
        }
        try {
          const anyPanel: any = panel as any;
          const idFromMeta =
            anyPanel?.content?.model?.sharedModel?.getMetadata?.()?.sage_ai
              ?.unique_id;
          const path = anyPanel?.context?.path;
          console.log('ID FROM META', idFromMeta);
          console.log('NOTEBOOK IDENTIFIER', notebookIdentifier);
          console.log('PATH', path);
          if (
            (typeof idFromMeta === 'string' &&
              idFromMeta === notebookIdentifier) ||
            (typeof path === 'string' && path === notebookIdentifier)
          ) {
            matched = anyPanel as NotebookPanel;
          }
        } catch {
          // ignore and continue scanning
        }
      });
      if (matched) {
        const matchedAny: any = matched as any;
        return {
          notebook: matchedAny.content as Notebook,
          widget: matchedAny as NotebookPanel
        };
      }
    }

    // Prefer the AppState current notebook when available
    const currentNotebook = AppStateService.getCurrentNotebook();
    if (currentNotebook) {
      return { notebook: currentNotebook.content, widget: currentNotebook };
    }

    // Fallback to active tracker widget
    const current = this.notebookTracker.currentWidget;
    if (!current) {
      console.log('No current notebook');
      return null;
    }
    return { notebook: current.content, widget: current };
  }

  /**
   * Find a cell by its ID in a specific notebook
   * @param cellId The ID of the cell to find
   * @param notebookPath Optional path to the notebook containing the cell
   * @returns The cell or null if not found
   */
  findCellById(
    cellId: string,
    notebookPath?: string | null
  ): { cell: Cell; index: number } | null {
    console.log('Finding cell by ID:', cellId);
    const current = this.getCurrentNotebook(notebookPath);
    if (!current) {
      return null;
    }

    const { notebook } = current;

    for (let i = 0; i < notebook.model!.cells.length; i++) {
      console.log(notebook.widgets[i].id);
      console.log(notebook.widgets[i].model.id);
      console.log(notebook.widgets[i].model.sharedModel.id);
    }

    for (let i = 0; i < notebook.model!.cells.length; i++) {
      const cell = notebook.widgets[i];
      if (cell.model.id === cellId) {
        return { cell, index: i };
      }
    }

    console.log(`Cell with ID ${cellId} not found`);
    return null;
  }

  /**
   * Activate a specific cell in the notebook by index
   * @param index The index of the cell to activate
   * @returns True if successful, false otherwise
   */
  public activateCellByIndex(index: number): boolean {
    const current = this.getCurrentNotebook();
    if (!current) {
      return false;
    }

    const { notebook } = current;

    if (index < 0 || index >= notebook.widgets.length) {
      console.log(`Invalid cell index: ${index}`);
      return false;
    }

    notebook.activeCellIndex = index;
    return true;
  }

  /**
   * Activate a specific cell in the notebook
   * @param indexOrCell The index or cell object to activate
   * @returns True if successful, false otherwise
   */
  public activateCell(indexOrCell: number | Cell): boolean {
    if (typeof indexOrCell === 'number') {
      return this.activateCellByIndex(indexOrCell);
    } else {
      const current = this.getCurrentNotebook();
      if (!current) {
        return false;
      }

      const { notebook } = current;

      // Find the cell index
      let cellIndex = -1;
      for (let i = 0; i < notebook.widgets.length; i++) {
        if (notebook.widgets[i] === indexOrCell) {
          cellIndex = i;
          break;
        }
      }

      if (cellIndex === -1) {
        console.log('Cell not found in notebook');
        return false;
      }

      notebook.activeCellIndex = cellIndex;
      return true;
    }
  }

  public async getNotebookSummary(
    notebookIdentifier: string | null
  ): Promise<any> {
    // Support both notebook paths and IDs for backward compatibility
    const nb = this.getCurrentNotebook(notebookIdentifier);
    const cells = [];
    let index = 0;
    for (const cell of nb?.widget.model?.cells || []) {
      let cellReturn = {
        index: index++,
        id: '',
        cell_type: '',
        summary: '',
        next_step_string: '',
        current_step_string: '',
        empty: true
      };
      const metadata = cell.metadata as any;

      const custom = metadata.custom;
      if (custom) {
        cellReturn = { ...cellReturn, ...custom };
      }
      const tracker = metadata.cell_tracker;
      if (tracker) {
        cellReturn.id = tracker.trackingId;
      }

      cellReturn.empty = cell.sharedModel.getSource().trim() === '';
      cellReturn.cell_type = cell.type;

      cells.push(cellReturn);
    }

    console.log('All Cells', cells);

    return cells;
  }

  /**
   * Activate the cell and scroll to it
   * @param cellId The cell tracking ID cell_x
   */
  public async scrollToCellById(cellId: string): Promise<void> {
    const notebook = this.getCurrentNotebook()?.notebook;
    if (!notebook) {
      return;
    }

    const cellIndex = notebook.widgets.findIndex(
      cell => (cell.model.metadata as any)?.cell_tracker.trackingId === cellId
    );
    const cell = notebook.widgets[cellIndex];
    if (!cell) {
      return;
    }

    notebook.activeCellIndex = cellIndex;

    const exactElement = document.querySelector(`[sage-ai-cell-id=${cellId}]`);
    if (
      exactElement &&
      exactElement.parentElement &&
      exactElement.parentElement.style.display !== 'none'
    ) {
      exactElement.scrollIntoView();
    } else {
      void notebook.scrollToItem(cellIndex, 'center');

      await Promise.resolve(requestAnimationFrame);
      const delayedScroll = (delay: number) => {
        setTimeout(() => {
          document
            .querySelector(`[sage-ai-cell-id=${cellId}]`)
            ?.scrollIntoView();
        }, delay);
      };

      // The notebook scroll doesn't work properly
      // It has issues with the virtualized Notebook
      // This code allows the scroll to be more assertive
      let delay = 100;
      while (delay < 1000) {
        delayedScroll(delay);
        delay += 100;
      }
    }
  }

  /**
   * Scroll to the first plan cell in the notebook
   */
  public async scrollToPlanCell(): Promise<void> {
    const notebook = this.getCurrentNotebook()?.notebook;
    if (!notebook) {
      return;
    }

    const cellIndex = notebook.widgets.findIndex(
      cell => (cell.model.metadata.custom as any)?.sage_cell_type === 'plan'
    );
    const cell = notebook.widgets[cellIndex];
    if (!cell) {
      return;
    }

    void notebook.scrollToItem(cellIndex, 'center');

    notebook.activeCellIndex = cellIndex;

    const cellId = (cell.model.metadata as any)?.cell_tracker.trackingId;
    if (!cellId) {
      return;
    }

    // The notebook scroll doesn't work properly
    // It has issues with the virtualized Notebook
    // This code allows the scroll to be more assertive
    await Promise.resolve(requestAnimationFrame);
    setTimeout(() => {
      document.querySelector(`[sage-ai-cell-id=${cellId}]`)?.scrollIntoView();
    }, 100);
  }

  async waitForScrollEnd(el: HTMLElement): Promise<void> {
    // If the browser supports the event, one-shot-listen for it
    if ('onscrollend' in el) {
      return new Promise(res =>
        el.addEventListener('scrollend', () => res(), { once: true })
      );
    }
    // Fallback to the debounce method (next section)
    return this.waitForScrollIdle(el);
  }

  async waitForScrollIdle(el: HTMLElement, idleMS = 120): Promise<void> {
    return new Promise<void>(resolve => {
      let timer: number;

      const onScroll = () => {
        clearTimeout(timer);
        timer = window.setTimeout(() => {
          el.removeEventListener('scroll', onScroll);
          resolve();
        }, idleMS);
      };

      el.addEventListener('scroll', onScroll, { passive: true });
      onScroll(); // start the timer immediately
    });
  }

  /**
   * Normalize content by trimming whitespace and determining if it's empty
   * @param content The content to normalize
   * @returns The normalized content string
   */
  normalizeContent(content: string): string {
    // Trim the content and check if it's effectively empty
    return content.trim();
  }

  // Forward methods to specialized tools
  display_diff(
    cell: Cell,
    oldText: string,
    newText: string,
    operation: string
  ) {
    return this.diffTools.display_diff(this, cell, oldText, newText, operation);
  }

  apply_diff(cell: Cell, accept: boolean) {
    return this.diffTools.apply_diff(this, cell, accept);
  }

  // Cell manipulation methods
  run_cell(options: {
    cell_id: string;
    notebook_path?: string | null;
    kernel_id?: string | null;
  }) {
    return this.cellTools.run_cell(options);
  }

  /**
   * Find a cell by its ID in a specific notebook
   * If the cellId starts with 'cell_', it is a tracking ID, otherwise it is a model ID
   * @param cellId The ID of the cell to find
   * @param notebookPath Optional path to the notebook containing the cell
   * @returns The cell or null if not found
   */
  findCellByAnyId(
    _cellId: string,
    notebookPath?: string | null
  ): { cell: Cell; index: number } | null {
    const cellId = _cellId || '';
    if (cellId?.startsWith('cell_')) {
      return this.findCellByTrackingId(cellId, notebookPath);
    } else {
      return this.findCellById(cellId, notebookPath);
    }
  }

  // Find a cell by tracking ID in a specific notebook
  findCellByTrackingId(
    trackingId: string,
    notebookPath?: string | null
  ): { cell: Cell; index: number } | null {
    const notebook = this.getCurrentNotebook(notebookPath)?.notebook;
    if (!notebook) {
      return null;
    }

    for (let i = 0; i < notebook.widgets.length; i++) {
      const cell = notebook.widgets[i];
      const metadata: any = cell.model.sharedModel.getMetadata() || {};

      if (
        metadata.cell_tracker &&
        metadata.cell_tracker.trackingId === trackingId
      ) {
        return { cell, index: i };
      }
    }

    return null;
  }

  /**
   * Find a cell by its index in a specific notebook
   * @param index The index of the cell to find
   * @returns The cell or null if not found
   */
  findCellByIndex(index: number): { cell: Cell; index: number } | null {
    const notebook = this.getCurrentNotebook()?.notebook;
    if (!notebook) {
      return null;
    }

    return { cell: notebook.widgets[index], index };
  }

  add_cell(options: {
    cell_type: string;
    source: string;
    summary: string;
    notebook_path?: string | null;
    position?: number | null;
    show_diff?: boolean;
    tracking_id?: string; // Optional tracking ID to reuse
  }): string {
    return this.cellTools.add_cell(options);
  }

  remove_cells(options: {
    cell_ids: string[];
    notebook_path?: string | null;
    remove_from_notebook?: boolean;
    save_checkpoint?: boolean;
  }): boolean {
    return this.cellTools.remove_cells(options);
  }

  edit_cell(options: {
    cell_id: string;
    new_source: string;
    summary: string;
    notebook_path?: string | null;
    show_diff?: boolean;
    is_tracking_id?: boolean; // Indicate if cell_id is a tracking ID
  }): boolean {
    return this.cellTools.edit_cell(options);
  }

  stream_edit_plan(options: {
    partial_plan: string;
    notebook_path?: string | null;
  }): boolean {
    return this.cellTools.stream_edit_plan(options);
  }

  async edit_plan(options: {
    updated_plan_string: string;
    current_step_string?: string;
    next_step_string?: string;
    should_think?: boolean;
    immediate_action?: string;
    notebook_path?: string | null;
  }): Promise<string | { error: true; errorText: string }> {
    return await this.cellTools.edit_plan(options);
  }

  get_cells_info(): {
    cells: Array<{ id: string; type: string; content: string }>;
  } | null {
    return this.cellTools.get_cells_info();
  }

  get_cell_info(options: { cell_id: string }): any {
    return this.cellTools.get_cell_info(options);
  }

  edit_history(options: { limit?: number }): any {
    return this.cellTools.edit_history(options);
  }

  /**
   * Read all cells from the notebook with comprehensive information and metadata
   * @param options Configuration options
   * @param options.notebook_path Path to the notebook file (optional)
   * @param options.include_outputs Whether to include cell outputs (optional, default: true)
   * @param options.include_metadata Whether to include cell metadata (optional, default: true)
   * @returns Array of comprehensive cell information or null if no notebook
   */
  read_cells(
    options: {
      notebook_path?: string | null;
      include_outputs?: boolean;
      include_metadata?: boolean;
    } = {}
  ): {
    cells: Array<{
      id: string;
      index: number;
      type: string;
      content: string;
      trackingId?: string;
      metadata?: any;
      outputs?: any[];
      execution_count?: number;
    }>;
    notebook_path?: string;
    total_cells: number;
  } | null {
    return this.cellTools.read_cells(options);
  }

  refresh_ids(): void {
    new TrackingIDUtility(this.notebookTracker).fixTrackingIDs();
  }

  /**
   * Ensure the first cell of a notebook is a plan cell
   * @param notebookPath Optional notebook path
   */
  public setFirstCellAsPlan(notebookPath?: string | null): void {
    this.cellTools.setFirstCellAsPlan(notebookPath);
  }

  /**
   * Get the plan cell from the notebook
   * @param notebookPath Optional notebook path
   * @returns The plan cell or null if not found
   */
  public getPlanCell(notebookPath?: string | null): Cell | null {
    const current = this.getCurrentNotebook(notebookPath);
    if (!current) {
      return null;
    }

    const { notebook } = current;
    return this.cellTools.findPlanCell(notebook);
  }

  /**
   * Displays a UI component to inform the user that the agent has completed its turn and is now waiting for a user reply.
   *
   * This tool should be called as the final action in an assistant's turn after providing a complete response or asking a question.
   * It signals that the agent is done processing and is awaiting the user's next instruction or answer.
   *
   * **How to use `wait_user_reply`:**
   * 1. **First, send a message** containing your question or the information you want the user to review.
   * 2. **Immediately after**, call the `wait_user_reply` tool.
   * 3. **Generate 1-3 follow up responses** that are relevant to the question or action you are waiting for:
   *    - These should be concise and directly related to the user's potential responses.
   *    - They should not be speculative or unrelated to the current task.
   *    - Create exact responses and examples, not vague responses like "Modify the strategy" which can be interpreted in many ways.
   *    - When asking the user to proceed or continue, only provide one option to continue unless it is extremely relevant to modify the task.
   *    - For extremely simple tasks such as printing hello world or basic debugging tasks do not include any follow up responses.
   *
   * @param options Configuration options
   * @param options.notebook_path Path to the notebook file (optional)
   * @param options.recommended_next_prompts List of recommended prompts to show to the user
   * @returns True if the waiting reply box was shown successfully
   */
  wait_user_reply(options: {
    notebook_path?: string | null;
    recommended_next_prompts?: string[];
  }): boolean {
    try {
      const llmStateDisplay =
        AppStateService.getChatContainerSafe()?.chatWidget.llmStateDisplay;
      if (llmStateDisplay) {
        llmStateDisplay.show('Waiting for your reply...', true);
      }

      // Get the ChatMessages component from the current chat container
      const chatContainer = AppStateService.getState().chatContainer;
      if (chatContainer && chatContainer.chatWidget) {
        const messageComponent = chatContainer.chatWidget.getMessageComponent();

        // Set the continue callback if not already set
        messageComponent.setContinueCallback(() => {
          chatContainer.chatWidget.sendContinueMessage();
        });

        // Show the waiting reply box using the new system with recommended prompts
        messageComponent.showWaitingReplyBox(options.recommended_next_prompts);
        console.log('Waiting for user reply - new system box shown');
        return true;
      } else {
        // Fallback to old system if chat container is not available
        this.waitingUserReplyBoxManager.show(options.recommended_next_prompts);
        console.log('Waiting for user reply - fallback to old system');
        return true;
      }
    } catch (error) {
      console.error('Error showing waiting reply box:', error);
      return false;
    }
  }

  // Filesystem tool wrappers
  /**
   * List datasets in the data directory
   * @param options Configuration options (unused for list_datasets but needed for consistency)
   * @returns JSON string with list of files and their metadata
   */
  async list_datasets(options?: any): Promise<string> {
    return this.filesystemTools.list_datasets(options);
  }

  /**
   * Read a dataset file
   * @param options Configuration options
   * @param options.filepath Path to the file to read
   * @param options.start Starting line number (0-indexed)
   * @param options.end Ending line number (0-indexed)
   * @returns JSON string with file contents or error
   */
  async read_dataset(options: {
    filepath: string;
    start?: number;
    end?: number;
  }): Promise<string> {
    return this.filesystemTools.read_dataset(options);
  }

  /**
   * Delete a dataset file
   * @param options Configuration options
   * @param options.filepath Path to the file to delete
   * @returns JSON string with success or error message
   */
  async delete_dataset(options: { filepath: string }): Promise<string> {
    return this.filesystemTools.delete_dataset(options);
  }

  /**
   * Upload/save a dataset file
   * @param options Configuration options
   * @param options.filepath Path where to save the file
   * @param options.content Content to save
   * @returns JSON string with success or error message
   */
  async save_dataset(options: {
    filepath: string;
    content: string;
  }): Promise<string> {
    return this.filesystemTools.save_dataset(options);
  }

  // Web tool wrappers
  /**
   * Search for tickers matching the query strings
   * @param options Configuration options
   * @param options.queries List of search strings to match against ticker symbols or names
   * @param options.limit Maximum number of results to return (default: 10, max: 10)
   * @returns JSON string with list of matching tickers
   */
  async search_dataset(options: {
    queries: string[];
    limit?: number;
  }): Promise<string> {
    return this.webTools.search_dataset(options);
  }

  // Database tool wrappers
  /**
   * Search database tables using semantic queries
   * @param options Configuration options
   * @param options.queries List of search queries to find relevant tables (required)
   * @param options.database_names Optional list of database names to limit the search scope
   * @returns JSON string with top 5 most relevant tables per query and their metadata
   */
  async search_tables(options: {
    queries: string[];
    database_names: string[];
  }): Promise<string> {
    return DatabaseSearchTools.search_tables(options);
  }

  /**
   * Search the database schemas to find the best matching table schemas (PostgreSQL/MySQL/Snowflake/Databricks).
   * @param options.queries List of search strings to evaluate.
   * @param options.database_names Database configuration names to target (must contain exactly one entry).
   * @param options.limit Optional maximum number of results per query (defaults to 5, capped at 10).
   * @returns JSON string containing the SchemaSearch response payload.
   */
  async schema_search(options: {
    queries: string[];
    database_names: string[];
    limit?: number;
  }): Promise<string> {
    const queries = (options.queries || [])
      .map(query => (typeof query === 'string' ? query.trim() : ''))
      .filter(query => query.length > 0);

    if (queries.length === 0) {
      return JSON.stringify({
        error: 'At least one schema search query is required.'
      });
    }

    const databaseNames = (options.database_names || [])
      .map(name => (typeof name === 'string' ? name.trim() : ''))
      .filter(name => name.length > 0);

    if (databaseNames.length !== 1) {
      return JSON.stringify({
        error: 'Specify exactly one database name for schema search.'
      });
    }

    const connection = this.resolveDatabaseConnection(databaseNames);
    if ('error' in connection) {
      return JSON.stringify({ error: connection.error });
    }

    const { config: targetConfig, url: databaseUrl } = connection;
    if (
      targetConfig.type !== 'postgresql' &&
      targetConfig.type !== 'mysql' &&
      targetConfig.type !== 'snowflake' &&
      targetConfig.type !== 'databricks'
    ) {
      return JSON.stringify({
        error: `Schema search supports PostgreSQL, MySQL, Snowflake, or Databricks databases. Selected configuration '${targetConfig.name}' is type '${targetConfig.type}'.`
      });
    }
    try {
      const { DatabaseTools } = await import('../BackendTools/DatabaseTools');
      const databaseTools = new DatabaseTools();
      const result = await databaseTools.schemaSearch({
        queries,
        limit: options.limit,
        dbUrl: databaseUrl
      });

      return JSON.stringify({
        database: targetConfig.name,
        queries,
        results: result.results ?? []
      });
    } catch (error) {
      return JSON.stringify({
        error: `Failed to search schema: ${error instanceof Error ? error.message : String(error)}`
      });
    }
  }

  /**
   * Read data from specific database tables found via search
   * @param options Configuration options
   * @param options.table_name Name of the table to read from
   * @param options.schema_name Schema name (optional, defaults to public)
   * @param options.limit Maximum number of rows to return (default: 10)
   * @param options.columns Specific columns to select (optional, defaults to all)
   * @param options.where_clause Optional WHERE clause for filtering
   * @returns JSON string with query results
   */
  async read_databases(options: {
    table_name: string;
    schema_name?: string;
    limit?: number;
    columns?: string[];
    where_clause?: string;
  }): Promise<string> {
    try {
      const limit = options.limit || 10;
      const columns = options.columns || ['*'];
      const schemaName = options.schema_name || 'public';
      const tableName = options.table_name;

      const connection = this.resolveDatabaseConnection();
      if ('error' in connection) {
        return JSON.stringify({ error: connection.error });
      }
      const { config: activeConfig, url: databaseUrl } = connection;

      // Validate table name to prevent SQL injection
      if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(tableName)) {
        return JSON.stringify({
          error:
            'Invalid table name. Table names must contain only letters, numbers, and underscores.'
        });
      }

      // Build the SQL query
      const columnList = columns.includes('*') ? '*' : columns.join(', ');
      let query = `SELECT ${columnList}
                         FROM ${schemaName}.${tableName}`;

      if (options.where_clause) {
        query += ` WHERE ${options.where_clause}`;
      }

      query += ` LIMIT ${limit}`;

      // Execute the query using DatabaseTools
      const { DatabaseTools } = await import('../BackendTools/DatabaseTools');
      const databaseTools = new DatabaseTools();
      const result = await databaseTools.executeQuery(query, databaseUrl);

      // Parse and return the result
      let parsedResult;
      try {
        parsedResult = JSON.parse(result);
      } catch (e) {
        return JSON.stringify({
          error: 'Failed to parse query result.'
        });
      }

      return JSON.stringify({
        database: activeConfig.name,
        table: `${schemaName}.${tableName}`,
        query_executed: query,
        ...parsedResult
      });
    } catch (error) {
      return JSON.stringify({
        error: `Failed to read from database: ${error instanceof Error ? error.message : String(error)}`
      });
    }
  }

  private resolveDatabaseConnection(
    targetDatabaseNames?: string[]
  ): { config: IDatabaseConfig; url: string } | { error: string } {
    const state = DatabaseStateService.getState();
    const configurations = state.configurations || [];

    let selectedConfig: IDatabaseConfig | undefined;

    const normalizedTargets = targetDatabaseNames
      ?.map(name => name.trim())
      .filter(name => name.length > 0);

    if (normalizedTargets && normalizedTargets.length > 0) {
      selectedConfig = configurations.find(config =>
        normalizedTargets.includes(config.name)
      );

      if (!selectedConfig) {
        return {
          error: `No database configuration found matching names: ${normalizedTargets.join(', ')}.`
        };
      }
    } else if (state.activeConfig) {
      selectedConfig = state.activeConfig;
    } else if (configurations.length === 1) {
      selectedConfig = configurations[0];
    }

    if (!selectedConfig) {
      return {
        error:
          'No active database configuration found. Please connect to a database first.'
      };
    }

    let databaseUrl: string | null = null;

    if (
      selectedConfig.connectionType === 'url' &&
      selectedConfig.urlConnection
    ) {
      databaseUrl = selectedConfig.urlConnection.connectionUrl?.trim() || null;
      if (selectedConfig.type === 'snowflake' && databaseUrl) {
        if (!databaseUrl.toLowerCase().startsWith('snowflake://')) {
          return {
            error:
              'Snowflake URL connections must use a snowflake:// connection string that includes credentials.'
          };
        }
      }
    } else if (
      selectedConfig.connectionType === 'credentials' &&
      selectedConfig.credentials
    ) {
      const creds = selectedConfig.credentials as any;
      switch (selectedConfig.type) {
        case 'postgresql':
          databaseUrl = `postgresql://${creds.username}:${creds.password}@${creds.host}:${creds.port}/${creds.database}`;
          break;
        case 'mysql':
          databaseUrl = `mysql+pymysql://${creds.username}:${creds.password}@${creds.host}:${creds.port}/${creds.database}`;
          break;
        case 'snowflake':
          databaseUrl = this.buildSnowflakeSqlAlchemyUrl(
            creds as ISnowflakeCredentials
          );
          if (!databaseUrl) {
            return {
              error:
                'Failed to build Snowflake connection URL. Please verify your credentials.'
            };
          }
          break;
        case 'databricks':
          databaseUrl = this.buildDatabricksSqlAlchemyUrl(
            creds as IDatabricksCredentials
          );
          if (!databaseUrl) {
            return {
              error:
                'Failed to build Databricks connection URL. Please verify your credentials.'
            };
          }
          break;
        default:
          return { error: 'Unsupported database type for query execution' };
      }
    } else {
      return { error: 'Invalid database configuration' };
    }

    if (!databaseUrl) {
      return { error: 'Database connection URL could not be resolved' };
    }

    databaseUrl = databaseUrl.trim();

    return { config: selectedConfig, url: databaseUrl };
  }

  private buildSnowflakeSqlAlchemyUrl(
    creds: ISnowflakeCredentials
  ): string | null {
    try {
      const baseUrl = creds.connectionUrl?.trim();
      if (!baseUrl) {
        return null;
      }

      const normalizedUrl = baseUrl.startsWith('http')
        ? baseUrl
        : `https://${baseUrl}`;
      const url = new URL(normalizedUrl);
      const host = url.hostname.replace(/\.snowflakecomputing\.com$/i, '');

      if (!host) {
        return null;
      }

      const encodedUser = encodeURIComponent(creds.username);
      const encodedPassword = encodeURIComponent(creds.password);

      let path = '';
      if (creds.database) {
        path = `/${encodeURIComponent(creds.database)}`;
      }

      const params = new URLSearchParams();
      if (creds.warehouse) {
        params.set('warehouse', creds.warehouse);
      }
      if (creds.role) {
        params.set('role', creds.role);
      }

      const paramString = params.toString();
      const connection = `snowflake://${encodedUser}:${encodedPassword}@${host}${path}`;
      return paramString ? `${connection}?${paramString}` : connection;
    } catch (error) {
      console.error('[NotebookTools] Failed to build Snowflake URL:', error);
      return null;
    }
  }

  private buildDatabricksSqlAlchemyUrl(
    creds: IDatabricksCredentials
  ): string | null {
    try {
      const host = creds.connectionUrl?.trim();
      if (!host) {
        return null;
      }

      // Remove protocol if present
      const normalizedHost = host.replace(/^https?:\/\//, '');

      // Get token based on auth type
      let token: string;
      if (creds.authType === 'pat' && creds.accessToken) {
        token = creds.accessToken;
      } else if (
        creds.authType === 'service_principal' &&
        creds.clientId &&
        creds.clientSecret
      ) {
        // For service principal, we'll use client_id:client_secret as token
        token = `${creds.clientId}:${creds.clientSecret}`;
      } else {
        console.error(
          '[NotebookTools] Invalid Databricks authentication configuration'
        );
        return null;
      }

      // Get catalog (required field)
      const catalog = creds.catalog;

      // Build http_path from warehouseHttpPath if available
      const httpPath = creds.warehouseHttpPath || '';
      if (!httpPath) {
        console.warn(
          '[NotebookTools] No HTTP path specified for Databricks connection'
        );
      }

      // Encode token for URL
      const encodedToken = encodeURIComponent(token);

      // Build the connection URL following the format:
      // databricks://token:{token}@{host}:443/{catalog}?http_path={http_path}
      let connectionUrl = `databricks://token:${encodedToken}@${normalizedHost}:443/${catalog}`;

      if (httpPath) {
        connectionUrl += `?http_path=${encodeURIComponent(httpPath)}`;
      }

      return connectionUrl;
    } catch (error) {
      console.error('[NotebookTools] Failed to build Databricks URL:', error);
      return null;
    }
  }

  /**
   * Generate a unique ID for a notebook
   * @returns A unique notebook ID in the format 'nb_<uuid>_<timestamp>'
   */
  private generateNotebookUniqueId(): string {
    return 'nb_' + uuidv4() + '_' + Date.now();
  }

  /**
   * Check if a notebook exists at the given path
   * @param path Path to the notebook file
   * @returns True if the notebook exists, false otherwise
   */
  private async checkNotebookExists(path: string): Promise<boolean> {
    const contentManager = AppStateService.getContentManager();
    if (!contentManager) {
      return false;
    }

    try {
      await contentManager.get(path);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get the unique_id from an existing notebook or generate a new one
   * @param notebookPath Path to the notebook file
   * @returns The notebook's unique_id
   */
  private async getOrCreateNotebookUniqueId(
    notebookPath: string
  ): Promise<string> {
    const contentManager = AppStateService.getContentManager();
    if (!contentManager) {
      console.error('Content manager not available');
      return this.generateNotebookUniqueId();
    }

    try {
      const nbFile = await contentManager.get(notebookPath);

      // Check if unique_id already exists in metadata
      if (nbFile?.content?.metadata?.sage_ai?.unique_id) {
        const existingId = nbFile.content.metadata.sage_ai.unique_id;
        console.log(
          `[getOrCreateNotebookUniqueId] Found existing unique_id: ${existingId}`
        );
        return existingId;
      }
    } catch (error) {
      console.log(
        `[getOrCreateNotebookUniqueId] Notebook doesn't exist or error reading: ${error}`
      );
    }

    // Generate new unique_id if none exists
    const newId = this.generateNotebookUniqueId();
    console.log(
      `[getOrCreateNotebookUniqueId] Generated new unique_id: ${newId}`
    );
    return newId;
  }

  /**
   * Create a new notebook with metadata including unique_id
   * @param path Path where the notebook should be created
   * @param uniqueId The unique_id to assign to the notebook
   * @returns True if creation was successful, false otherwise
   */
  private async createNewNotebook(
    path: string,
    uniqueId: string
  ): Promise<boolean> {
    const contentManager = AppStateService.getContentManager();
    if (!contentManager) {
      console.error('Content manager not available');
      return false;
    }

    try {
      const newNotebook = {
        type: 'notebook' as const,
        format: 'json' as const,
        content: {
          cells: [],
          metadata: {
            sage_ai: {
              unique_id: uniqueId
            }
          },
          nbformat: 4,
          nbformat_minor: 5
        }
      };

      await contentManager.save(path, newNotebook);
      console.log(
        `[createNewNotebook] Created notebook at: ${path} with unique_id: ${uniqueId}`
      );
      return true;
    } catch (error) {
      console.error('[createNewNotebook] Error creating notebook:', error);
      return false;
    }
  }

  /**
   * Copy the current launcher thread to the notebook
   * @param notebookPath Path to the notebook
   * @param notebookUniqueId Unique ID of the notebook
   * @returns True if thread was copied successfully
   */
  private async copyThreadToNotebook(
    notebookPath: string,
    notebookUniqueId: string
  ): Promise<boolean> {
    const chatContainer = AppStateService.getState().chatContainer;
    if (!chatContainer) {
      console.log('[copyThreadToNotebook] No chat container available');
      return false;
    }

    const chatHistoryManager = chatContainer.chatWidget.chatHistoryManager;
    const chatMessages = chatContainer.chatWidget.messageComponent;

    console.log('[copyThreadToNotebook] Copying launcher thread to notebook');

    // Get the current messages and contexts
    const currentMessages = chatMessages.messageHistory || [];
    const currentContexts = chatMessages.getMentionContexts();

    console.log(
      '[copyThreadToNotebook] Found',
      currentMessages.length,
      'messages to copy'
    );

    // Add tool result to the message history
    const toolCall = currentMessages[currentMessages.length - 1]?.content?.[0];
    if (toolCall?.id) {
      AppStateService.getState().chatContainer?.chatWidget.messageComponent.addToolResult(
        'open_notebook',
        toolCall.id,
        'Opened notebook ' + notebookPath,
        notebookPath
      );
    }

    // Get the updated message history after adding the tool result
    const updatedMessages = chatMessages.messageHistory || [];

    // Copy the thread to the notebook
    const copiedThread = await chatHistoryManager.copyLauncherThreadToNotebook(
      notebookUniqueId,
      updatedMessages,
      currentContexts
    );

    if (copiedThread) {
      console.log(
        `[copyThreadToNotebook] Successfully copied thread ${copiedThread.id} to notebook ${notebookPath}`
      );
      return true;
    } else {
      console.log(
        '[copyThreadToNotebook] No launcher thread to copy, or copy failed'
      );
      return false;
    }
  }

  /**
   * Open a notebook file in JupyterLab
   * @param path Path to the notebook file
   * @returns True if opened successfully
   */
  private async openNotebookFile(path: string): Promise<boolean> {
    try {
      // Cancel any ongoing LLM message
      AppStateService.getState().chatContainer?.chatWidget.cancelMessage();
      await timeout(100);

      // Open the notebook using document manager
      AppStateService.getState().documentManager?.open(path);

      console.log(`[openNotebookFile] Opened notebook: ${path}`);
      return true;
    } catch (error) {
      console.error('[openNotebookFile] Error opening notebook:', error);
      return false;
    }
  }

  /**
   * Create a new notebook with tracking info, then switch to it
   * This ensures the notebook has its unique_id metadata before opening,
   * avoiding race conditions with notebook switch handlers
   * @param path Path where the notebook should be created
   * @returns Object with success status and notebook unique_id if successful
   */
  async createNotebookWithTracking(path: string): Promise<{
    success: boolean;
    notebookId?: string;
  }> {
    try {
      console.log(`[createNotebookWithTracking] Creating notebook: ${path}`);

      // Step 1: Generate unique_id
      const uniqueId = this.generateNotebookUniqueId();
      console.log(
        `[createNotebookWithTracking] Generated unique_id: ${uniqueId}`
      );

      // Step 2: Create the notebook file with metadata
      const created = await this.createNewNotebook(path, uniqueId);
      if (!created) {
        console.error(
          '[createNotebookWithTracking] Failed to create notebook file'
        );
        return { success: false };
      }

      // Step 3: Set the notebook ID in AppState BEFORE opening
      // This ensures any tracking/switch handlers see the correct ID
      AppStateService.setCurrentNotebookId(uniqueId);
      console.log(
        `[createNotebookWithTracking] Set current notebook ID to: ${uniqueId}`
      );

      // Step 4: Copy launcher thread to the notebook (if applicable)
      await this.copyThreadToNotebook(path, uniqueId);

      // Step 5: Open the notebook file
      const opened = await this.openNotebookFile(path);
      if (!opened) {
        console.error(
          '[createNotebookWithTracking] Failed to open notebook file'
        );
        return { success: false };
      }

      console.log(
        `[createNotebookWithTracking] Successfully created and opened notebook: ${path}`
      );
      return { success: true, notebookId: uniqueId };
    } catch (error) {
      console.error('[createNotebookWithTracking] Error:', error);
      return { success: false };
    }
  }

  /**
   * Open or create a Jupyter notebook file in the workspace
   * @param options Configuration options
   * @param options.notebook_path Path to the notebook file to open or create
   * @param options.create_new Whether to create a new notebook if it doesn't exist (default: false)
   * @returns True if the notebook was successfully opened or created, False otherwise
```   */
  async open_notebook(options: {
    path_of_notebook: string;
    create_new?: boolean;
  }): Promise<boolean> {
    try {
      const { path_of_notebook, create_new = false } = options;

      console.log(
        `[open_notebook] Opening notebook: ${path_of_notebook}, create_new: ${create_new}`
      );

      // Step 1: Check if notebook exists
      const notebookExists = await this.checkNotebookExists(path_of_notebook);

      // Step 2: Handle notebook creation if needed
      if (!notebookExists && create_new) {
        // Generate unique_id before creating the notebook
        const uniqueId = this.generateNotebookUniqueId();
        console.log(
          `[open_notebook] Creating new notebook with unique_id: ${uniqueId}`
        );

        const created = await this.createNewNotebook(
          path_of_notebook,
          uniqueId
        );
        if (!created) {
          console.error('[open_notebook] Failed to create new notebook');
          return false;
        }
      } else if (!notebookExists) {
        console.error(
          `[open_notebook] Notebook does not exist and create_new is false: ${path_of_notebook}`
        );
        return false;
      }

      // Step 3: Get or create the notebook's unique_id
      const notebookUniqueId =
        await this.getOrCreateNotebookUniqueId(path_of_notebook);

      // Step 4: Copy the current launcher thread to the notebook
      await this.copyThreadToNotebook(path_of_notebook, notebookUniqueId);

      // Step 5: Open the notebook file
      const opened = await this.openNotebookFile(path_of_notebook);

      if (opened) {
        console.log(
          `[open_notebook] Successfully opened notebook: ${path_of_notebook}`
        );
      } else {
        console.log(
          `[open_notebook] Notebook exists and can be opened: ${path_of_notebook}`
        );
      }

      // The LLM loop will continue automatically when the notebook loads
      // because the copied thread will be loaded and the conversation service
      // will continue from where it left off
      return true;
    } catch (error) {
      console.error('[open_notebook] Error in open_notebook:', error);
      return false;
    }
  }

  /**
   * Execute a shell command in the terminal
   * @param options Configuration options
   * @param options.command Shell command to execute
   * @returns JSON string with command output
   */
  async execute_command(options: { command: string }): Promise<string> {
    return this.terminalTools.execute_command(options);
  }

  /**
   * Compress chat history by summarizing older messages while keeping recent ones intact
   * @param options Configuration options
   * @param options.notebook_id ID of the notebook whose chat history to compress
   * @param options.keep_recent_count Number of recent messages to keep uncompressed (default: 10)
   * @returns JSON string with compression status
   */
  async compress_history(options: {
    notebook_id?: string | null;
    keep_recent_count?: number;
  }): Promise<string> {
    try {
      const keepRecentCount = options.keep_recent_count || 10;
      const notebookId =
        options.notebook_id || AppStateService.getCurrentNotebookId();

      if (!notebookId) {
        return JSON.stringify({
          success: false,
          error: 'No active notebook ID found'
        });
      }

      const chatContainer = AppStateService.getChatContainerSafe();
      if (!chatContainer || !chatContainer.chatWidget) {
        return JSON.stringify({
          success: false,
          error: 'Chat container not available'
        });
      }

      const chatHistoryManager = chatContainer.chatWidget.chatHistoryManager;
      const currentThread = chatHistoryManager.getCurrentThread();

      if (!currentThread || !currentThread.messages) {
        return JSON.stringify({
          success: false,
          error: 'No active chat thread found'
        });
      }

      const totalMessages = currentThread.messages.length;
      if (totalMessages <= keepRecentCount) {
        return JSON.stringify({
          success: true,
          compressed: false,
          message: `Only ${totalMessages} messages in history. No compression needed.`,
          total_messages: totalMessages,
          kept_recent: totalMessages
        });
      }

      const messagesToCompress = currentThread.messages.slice(
        0,
        totalMessages - keepRecentCount
      );
      const messagesToKeep = currentThread.messages.slice(
        totalMessages - keepRecentCount
      );

      // Get notebook context
      const notebookSummary = await this.getNotebookSummary(notebookId);
      const planCell = this.getPlanCell(notebookId);
      const planContent =
        planCell?.model?.sharedModel?.getSource() || 'No plan available';

      const conversationText = messagesToCompress
        .map(
          msg =>
            `${msg.role === 'user' ? 'User' : 'Assistant'}: ${JSON.stringify(msg.content)}`
        )
        .join('\n\n');

      const chatService = AppStateService.getChatService();
      if (!chatService || !chatService.isInitialized()) {
        return JSON.stringify({
          success: false,
          error: 'Chat service not initialized'
        });
      }

      const compressionSystemPrompt = require('../Config/prompts/chat_compression_prompt.md');
      const compressionPrompt = `# NOTEBOOK CONTEXT

## Current Plan
${planContent}

## Notebook Summary
${JSON.stringify(notebookSummary, null, 2)}

---

# CONVERSATION HISTORY TO COMPRESS

${conversationText}`;

      let summaryContent = '';
      const summaryResponse = await chatService.sendEphemeralMessage(
        compressionPrompt,
        compressionSystemPrompt,
        chatService.getModelName(),
        (chunk: string) => {
          summaryContent += chunk;
        }
      );

      // If sendEphemeralMessage returns the complete text, use that
      if (typeof summaryResponse === 'string') {
        summaryContent = summaryResponse;
      }

      const compressedMessages = [
        {
          role: 'user',
          content: `[Compressed conversation history: ${messagesToCompress.length} messages]`
        },
        {
          role: 'assistant',
          content: summaryContent.trim()
        },
        ...messagesToKeep
      ];

      // Update the stored thread history
      chatHistoryManager.updateCurrentThreadMessages(
        compressedMessages,
        currentThread.contexts
      );

      // Update the active conversation history in ChatMessages
      const messageComponent = chatContainer.chatWidget.getMessageComponent();
      messageComponent.messageHistory = [...compressedMessages];

      // Reload the UI to reflect compressed history
      await messageComponent.loadFromThread({
        ...currentThread,
        messages: compressedMessages
      });

      return JSON.stringify({
        success: true,
        compressed: true,
        original_message_count: totalMessages,
        compressed_message_count: messagesToCompress.length,
        kept_recent_count: keepRecentCount,
        new_total_count: compressedMessages.length,
        summary_preview: summaryContent.substring(0, 200) + '...'
      });
    } catch (error) {
      return JSON.stringify({
        success: false,
        error: `Failed to compress history: ${error instanceof Error ? error.message : String(error)}`
      });
    }
  }
}
