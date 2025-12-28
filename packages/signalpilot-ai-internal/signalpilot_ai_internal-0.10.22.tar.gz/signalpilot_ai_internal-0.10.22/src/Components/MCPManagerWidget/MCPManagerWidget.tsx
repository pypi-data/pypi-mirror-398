import * as React from 'react';
import { ReactWidget } from '@jupyterlab/ui-components';
import { MCPManagerContent } from './MCPManagerContent';
import { MCP_ICON } from './icons';

/**
 * A widget for managing MCP server connections
 */
export class MCPManagerWidget extends ReactWidget {
  constructor() {
    super();
    this.id = 'signalpilot-mcp-manager';
    this.title.icon = MCP_ICON;
    this.title.label = '';
    this.title.caption = '';
    this.title.closable = true;
    this.addClass('sage-mcp-manager-widget');
  }

  render(): JSX.Element {
    return <MCPManagerContent />;
  }
}
