/**
 * Centralized file cache service that manages scanned files data
 * Used by both FileExplorerWidget and DataLoaderService to ensure consistency
 */
import { ISignal, Signal } from '@lumino/signaling';
import { IFileEntry } from '../Chat/ChatContextMenu/DataLoaderService';
import { IScannedDirectory } from '../handler';

export interface ICacheState {
  files: IFileEntry[];
  scannedDirectories: IScannedDirectory[];
  workDir: string | null;
  totalFileCount: number;
  lastUpdated: Date | null;
  isLoading: boolean;
}

/**
 * Centralized file cache service
 */
export class FileCacheService {
  private static _instance: FileCacheService | null = null;
  private _cacheState: ICacheState;
  private _cacheUpdated = new Signal<this, ICacheState>(this);

  private constructor() {
    this._cacheState = {
      files: [],
      scannedDirectories: [],
      workDir: null,
      totalFileCount: 0,
      lastUpdated: null,
      isLoading: true
    };
  }

  /**
   * Get the singleton instance
   */
  public static getInstance(): FileCacheService {
    if (!FileCacheService._instance) {
      FileCacheService._instance = new FileCacheService();
    }
    return FileCacheService._instance;
  }

  /**
   * Get the signal that fires when cache is updated
   */
  public get cacheUpdated(): ISignal<this, ICacheState> {
    return this._cacheUpdated;
  }

  /**
   * Get the current cache state
   */
  public getCacheState(): ICacheState {
    return { ...this._cacheState };
  }

  /**
   * Get cached files
   */
  public getFiles(): IFileEntry[] {
    return [...this._cacheState.files];
  }

  /**
   * Get cached scanned directories
   */
  public getScannedDirectories(): IScannedDirectory[] {
    return [...this._cacheState.scannedDirectories];
  }

  /**
   * Get cached work directory
   */
  public getWorkDir(): string | null {
    return this._cacheState.workDir;
  }

  /**
   * Get total file count
   */
  public getTotalFileCount(): number {
    return this._cacheState.totalFileCount;
  }

  /**
   * Check if cache has been initialized
   */
  public isInitialized(): boolean {
    return this._cacheState.lastUpdated !== null;
  }

  /**
   * Check if cache is currently loading
   */
  public isLoading(): boolean {
    return this._cacheState.isLoading;
  }

  /**
   * Update the cache with new file scan data
   * Called by FileExplorerWidget during polling
   */
  public updateCache(data: {
    files: IFileEntry[];
    scannedDirectories: IScannedDirectory[];
    totalFileCount: number;
    workDir?: string | null;
  }): void {
    const oldState = { ...this._cacheState };

    this._cacheState = {
      files: [...data.files],
      scannedDirectories: [...data.scannedDirectories],
      workDir:
        data.workDir !== undefined ? data.workDir : this._cacheState.workDir,
      totalFileCount: data.totalFileCount,
      lastUpdated: new Date(),
      isLoading: false
    };

    // Emit signal if there are changes
    if (this.hasStateChanged(oldState, this._cacheState)) {
      this._cacheUpdated.emit(this._cacheState);
      console.log(
        '[FileCacheService] Cache updated with',
        data.files.length,
        'files'
      );
    }
  }

  /**
   * Set loading state
   */
  public setLoading(isLoading: boolean): void {
    if (this._cacheState.isLoading !== isLoading) {
      this._cacheState.isLoading = isLoading;
      this._cacheUpdated.emit(this._cacheState);
    }
  }

  /**
   * Update work directory
   */
  public updateWorkDir(workDir: string | null): void {
    if (this._cacheState.workDir !== workDir) {
      this._cacheState.workDir = workDir;
      this._cacheUpdated.emit(this._cacheState);
    }
  }

  /**
   * Clear the cache
   */
  public clearCache(): void {
    this._cacheState = {
      files: [],
      scannedDirectories: [],
      workDir: this._cacheState.workDir, // Keep workDir
      totalFileCount: 0,
      lastUpdated: null,
      isLoading: true
    };
    this._cacheUpdated.emit(this._cacheState);
    console.log('[FileCacheService] Cache cleared');
  }

  /**
   * Check if state has changed
   */
  private hasStateChanged(
    oldState: ICacheState,
    newState: ICacheState
  ): boolean {
    return (
      oldState.files.length !== newState.files.length ||
      oldState.scannedDirectories.length !==
        newState.scannedDirectories.length ||
      oldState.totalFileCount !== newState.totalFileCount ||
      oldState.workDir !== newState.workDir ||
      oldState.isLoading !== newState.isLoading ||
      oldState.lastUpdated?.getTime() !== newState.lastUpdated?.getTime()
    );
  }
}
