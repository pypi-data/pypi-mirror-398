import { SnippetCreationWidget } from './Components/SnippetCreationWidget';
import { DiffNavigationWidget } from './Components/DiffNavigationWidget';

/**
 * Global widget references that need to be shared across the plugin lifecycle
 */
export let globalSnippetCreationWidget: SnippetCreationWidget | undefined;
export let globalDiffNavigationWidget: DiffNavigationWidget | undefined;

/**
 * Set the global snippet creation widget reference
 */
export function setGlobalSnippetCreationWidget(
  widget: SnippetCreationWidget | undefined
): void {
  globalSnippetCreationWidget = widget;
}

/**
 * Set the global diff navigation widget reference
 */
export function setGlobalDiffNavigationWidget(
  widget: DiffNavigationWidget | undefined
): void {
  globalDiffNavigationWidget = widget;
}

/**
 * Get the global snippet creation widget reference
 */
export function getGlobalSnippetCreationWidget():
  | SnippetCreationWidget
  | undefined {
  return globalSnippetCreationWidget;
}

/**
 * Get the global diff navigation widget reference
 */
export function getGlobalDiffNavigationWidget():
  | DiffNavigationWidget
  | undefined {
  return globalDiffNavigationWidget;
}
