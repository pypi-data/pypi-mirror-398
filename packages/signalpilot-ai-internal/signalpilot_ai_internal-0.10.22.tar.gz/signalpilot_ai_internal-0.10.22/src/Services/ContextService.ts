import { BehaviorSubject, Observable } from 'rxjs';
import { IMentionContext } from '../Chat/ChatContextMenu/ChatContextLoaders';

/**
 * Service for managing context items across the application
 * Uses RxJS for reactive state management similar to AppState
 */
export class ContextService {
  private static instance: ContextService | null = null;

  // BehaviorSubject to hold the current context items
  private _contextItems = new BehaviorSubject<Map<string, IMentionContext>>(
    new Map()
  );

  private constructor() {}

  public static getInstance(): ContextService {
    if (!ContextService.instance) {
      ContextService.instance = new ContextService();
    }
    return ContextService.instance;
  }

  /**
   * Get the current context items as an Observable
   */
  public getContextItems(): Observable<Map<string, IMentionContext>> {
    return this._contextItems.asObservable();
  }

  /**
   * Get the current context items value synchronously
   */
  public getCurrentContextItems(): Map<string, IMentionContext> {
    return new Map(this._contextItems.value);
  }

  /**
   * Add a context item
   */
  public addContextItem(context: IMentionContext): void {
    const currentItems = new Map(this._contextItems.value);
    currentItems.set(context.id, context);
    this._contextItems.next(currentItems);
  }

  /**
   * Remove a context item by ID
   */
  public removeContextItem(contextId: string): void {
    const currentItems = new Map(this._contextItems.value);
    currentItems.delete(contextId);
    this._contextItems.next(currentItems);
  }

  /**
   * Get a specific context item by ID
   */
  public getContextItem(contextId: string): IMentionContext | undefined {
    return this._contextItems.value.get(contextId);
  }

  /**
   * Set all context items (replaces current state)
   */
  public setContextItems(items: Map<string, IMentionContext>): void {
    this._contextItems.next(new Map(items));
  }

  /**
   * Clear all context items
   */
  public clearContextItems(): void {
    this._contextItems.next(new Map());
  }

  /**
   * Check if a context item exists
   */
  public hasContextItem(contextId: string): boolean {
    return this._contextItems.value.has(contextId);
  }

  /**
   * Get context items by type
   */
  public getContextItemsByType(type: string): IMentionContext[] {
    const items = Array.from(this._contextItems.value.values());
    return items.filter(item => item.type === type);
  }

  /**
   * Subscribe to context changes (helper method)
   */
  public subscribe(
    callback: (items: Map<string, IMentionContext>) => void
  ): () => void {
    const subscription = this._contextItems.subscribe(callback);
    return () => subscription.unsubscribe();
  }
}
