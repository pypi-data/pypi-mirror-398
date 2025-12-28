import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

/**
 * Tools for executing terminal commands
 */
export class TerminalTools {
  /**
   * Execute a shell command in the terminal
   * @param options Configuration options
   * @param options.command Shell command to execute
   * @returns JSON string with command output
   */
  async execute_command(options: { command: string }): Promise<string> {
    try {
      const { command } = options;

      const settings = ServerConnection.makeSettings();
      const url = URLExt.join(
        settings.baseUrl,
        'signalpilot-ai-internal',
        'terminal',
        'execute'
      );

      const response = await ServerConnection.makeRequest(
        url,
        {
          method: 'POST',
          body: JSON.stringify({ command }),
          headers: {
            'Content-Type': 'application/json'
          }
        },
        settings
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          error: `HTTP ${response.status}: ${response.statusText}`
        }));
        return JSON.stringify({
          error: errorData.error || `Request failed: ${response.statusText}`
        });
      }

      const result = await response.json();

      if (result.error) {
        return JSON.stringify({ error: result.error });
      }

      return JSON.stringify({
        stdout: result.stdout,
        stderr: result.stderr,
        exit_code: result.exit_code
      });
    } catch (error) {
      console.error('Error executing terminal command:', error);
      return JSON.stringify({
        error: `Failed to execute command: ${error instanceof Error ? error.message : String(error)}`
      });
    }
  }
}
