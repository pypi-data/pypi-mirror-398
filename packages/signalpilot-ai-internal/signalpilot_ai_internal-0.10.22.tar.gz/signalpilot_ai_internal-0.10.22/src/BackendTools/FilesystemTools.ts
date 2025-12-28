import { AppStateService } from '../AppState';

/**
 * Tools for interacting with the filesystem directly
 */
export class FilesystemTools {
  private dataDir: string = 'data';

  constructor() {
    // No longer need to pass contentManager as parameter
  }

  /**
   * Creates a temporary kernel session for filesystem operations
   * @returns Promise with kernel connection and cleanup function
   */
  private async createTemporaryKernel(): Promise<{
    kernel: any;
    cleanup: () => void;
  }> {
    try {
      console.log('[FilesystemTools] Creating temporary kernel session...');

      const serviceManager = AppStateService.getServiceManager();
      if (!serviceManager) {
        throw new Error('Service manager not available');
      }

      // Create a new session for this operation
      const sessionManager = serviceManager.sessions;
      const kernelspecManager = serviceManager.kernelspecs;

      // Get the default Python kernel spec
      await kernelspecManager.refreshSpecs();
      const specs = kernelspecManager.specs;

      // Find a Python kernel spec (prefer python3, fallback to python)
      let kernelName = 'python3';
      if (!specs?.kernelspecs[kernelName]) {
        kernelName = 'python';
        if (!specs?.kernelspecs[kernelName]) {
          // Use the default kernel if no python kernel is found
          kernelName = specs?.default || 'python3';
        }
      }

      console.log(`[FilesystemTools] Using kernel spec: ${kernelName}`);

      // Create a new session with a unique name
      const sessionId = `filesystem-temp-${Date.now()}-${Math.random().toString(36).substring(7)}`;
      const session = await sessionManager.startNew({
        name: sessionId,
        path: `temp/${sessionId}`,
        type: 'file',
        kernel: {
          name: kernelName
        }
      });

      console.log(`[FilesystemTools] Created temporary session: ${session.id}`);

      // Wait for kernel to be ready
      if (session.kernel) {
        // Wait a moment for the kernel to initialize
        await new Promise(resolve => setTimeout(resolve, 2000));
      }

      console.log('[FilesystemTools] Temporary kernel is ready');

      // Return kernel and cleanup function
      return {
        kernel: session.kernel,
        cleanup: () => {
          console.log(
            `[FilesystemTools] Cleaning up temporary session: ${session.id}`
          );
          sessionManager.shutdown(session.id).catch(error => {
            console.warn(
              `[FilesystemTools] Error shutting down session ${session.id}:`,
              error
            );
          });
        }
      };
    } catch (error) {
      console.error(
        '[FilesystemTools] Error creating temporary kernel:',
        error
      );
      throw error;
    }
  }

  /**
   * Execute Python code in the temporary kernel and return the result
   * @param kernel The kernel connection
   * @param code The Python code to execute
   * @returns Promise with the execution result
   */
  private async executeKernelCode(kernel: any, code: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const future = kernel.requestExecute({
        code: code,
        silent: false
      });

      let output = '';
      let hasError = false;

      future.onIOPub = (msg: any) => {
        const msgType = msg.header.msg_type;

        if (msgType === 'stream' && msg.content.name === 'stdout') {
          output += msg.content.text;
        } else if (msgType === 'error') {
          hasError = true;
          output += `Error: ${msg.content.ename}: ${msg.content.evalue}`;
        } else if (msgType === 'execute_result' || msgType === 'display_data') {
          if (msg.content.data && msg.content.data['text/plain']) {
            output += msg.content.data['text/plain'];
          }
        }
      };

      future.done
        .then(() => {
          if (hasError) {
            reject(new Error(output));
          } else {
            resolve(output);
          }
        })
        .catch((error: any) => {
          reject(error);
        });
    });
  }

  /**
   * List datasets in the data directory
   * @param args Arguments (unused for list_datasets but needed for consistency)
   * @returns JSON string with list of files and their metadata
   */
  async list_datasets(args?: any): Promise<string> {
    let kernelSession: { kernel: any; cleanup: () => void } | null = null;

    try {
      // Create temporary kernel for this operation
      kernelSession = await this.createTemporaryKernel();
      const { kernel } = kernelSession;

      // Python code to list datasets with metadata
      const pythonCode = `
import os
import json
from pathlib import Path

def list_datasets(data_dir='data'):
    """List all files in the data directory with metadata"""
    results = []
    data_path = Path(data_dir)
    
    # Create data directory if it doesn't exist
    data_path.mkdir(exist_ok=True)
    
    if not data_path.exists() or not data_path.is_dir():
        return []
    
    try:
        for item in data_path.iterdir():
            if item.is_file():
                stat_info = item.stat()
                results.append({
                    'name': item.name,
                    'path': str(item),
                    'size': stat_info.st_size,
                    'modified': stat_info.st_mtime
                })
    except Exception as e:
        print(f"Error listing directory: {e}")
        return []
    
    return results

# Execute the function and print results
files = list_datasets()
print(json.dumps(files))
`;

      // Execute the Python code
      const output = await this.executeKernelCode(kernel, pythonCode);

      // Parse the JSON output
      try {
        const files = JSON.parse(output.trim());
        return JSON.stringify(files);
      } catch (parseError) {
        console.error('Error parsing kernel output:', parseError);
        return JSON.stringify({
          error: 'Failed to parse file listing results'
        });
      }
    } catch (error) {
      console.error('Error listing datasets:', error);
      return JSON.stringify({
        error: `Failed to list datasets: ${error instanceof Error ? error.message : String(error)}`
      });
    } finally {
      // Always cleanup the kernel session
      if (kernelSession) {
        kernelSession.cleanup();
      }
    }
  }

  /**
   * Read a dataset file
   * @param args Configuration options
   * @param args.filepath Path to the file to read
   * @param args.start Starting line number (0-indexed)
   * @param args.end Ending line number (0-indexed)
   * @returns JSON string with file contents or error
   */
  async read_dataset(args: {
    filepath: string;
    start?: number;
    end?: number;
  }): Promise<string> {
    let kernelSession: { kernel: any; cleanup: () => void } | null = null;

    try {
      const { filepath, start = 0, end = 5 } = args;

      // Ensure filepath is within data directory
      const safePath = this.getSafeFilePath(filepath);

      // Create temporary kernel for this operation
      kernelSession = await this.createTemporaryKernel();
      const { kernel } = kernelSession;

      // Python code to read file with character and line limits
      const pythonCode = `
import os
import json
from pathlib import Path

def read_dataset_content(filepath, start_line=0, end_line=5, max_chars=5000):
    """Read file content with line and character limits"""
    try:
        file_path = Path(filepath)
        
        if not file_path.exists():
            return {"error": f"File not found: {filepath}"}
        
        if not file_path.is_file():
            return {"error": f"Path is not a file: {filepath}"}
        
        # Read file line by line to handle large files efficiently
        lines = []
        char_count = 0
        truncated = False
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            total_lines = len(all_lines)
            
            # Apply line range limits
            actual_start = max(0, start_line)
            actual_end = min(end_line, total_lines)
            
            # Limit to maximum 5 lines from start
            max_lines = min(actual_start + 5, actual_end)
            
            selected_lines = all_lines[actual_start:max_lines]
            
            # Apply character limit
            for i, line in enumerate(selected_lines):
                line_stripped = line.rstrip('\\n\\r')
                if char_count + len(line_stripped) + 1 > max_chars:  # +1 for newline
                    truncated = True
                    actual_end = actual_start + i
                    break
                lines.append(line_stripped)
                char_count += len(line_stripped) + 1  # +1 for newline
            
            if not truncated and max_lines < actual_end:
                truncated = True
                actual_end = max_lines
        
        return {
            "content": lines,
            "start": actual_start,
            "end": actual_end,
            "path": filepath,
            "total_lines": total_lines,
            "truncated": truncated,
            "character_count": char_count
        }
        
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}

# Execute the function and print results
result = read_dataset_content('${safePath.replace(/\\/g, '\\\\')}', ${start}, ${end})
print(json.dumps(result))
`;

      // Execute the Python code
      const output = await this.executeKernelCode(kernel, pythonCode);

      // Parse the JSON output
      try {
        const result = JSON.parse(output.trim());
        return JSON.stringify(result);
      } catch (parseError) {
        console.error('Error parsing kernel output:', parseError);
        return JSON.stringify({
          error: 'Failed to parse file reading results'
        });
      }
    } catch (error) {
      console.error('Error reading dataset:', error);
      return JSON.stringify({
        error: `Failed to read dataset: ${error instanceof Error ? error.message : String(error)}`
      });
    } finally {
      // Always cleanup the kernel session
      if (kernelSession) {
        kernelSession.cleanup();
      }
    }
  }

  /**
   * Delete a dataset file
   * @param args Configuration options
   * @param args.filepath Path to the file to delete
   * @returns JSON string with success or error message
   */
  async delete_dataset(args: { filepath: string }): Promise<string> {
    let kernelSession: { kernel: any; cleanup: () => void } | null = null;

    try {
      const { filepath } = args;

      // Ensure filepath is within data directory
      const safePath = this.getSafeFilePath(filepath);

      // Create temporary kernel for this operation
      kernelSession = await this.createTemporaryKernel();
      const { kernel } = kernelSession;

      // Python code to delete file
      const pythonCode = `
import os
import json
from pathlib import Path

def delete_file(filepath):
    """Delete a file safely"""
    try:
        file_path = Path(filepath)
        
        if not file_path.exists():
            return {"error": f"File not found: {filepath}"}
        
        if not file_path.is_file():
            return {"error": f"Path is not a file: {filepath}"}
        
        # Delete the file
        file_path.unlink()
        
        return {
            "success": True,
            "path": filepath,
            "message": "File deleted successfully"
        }
        
    except Exception as e:
        return {"error": f"Failed to delete file: {str(e)}"}

# Execute the function and print results
result = delete_file('${safePath.replace(/\\/g, '\\\\')}')
print(json.dumps(result))
`;

      // Execute the Python code
      const output = await this.executeKernelCode(kernel, pythonCode);

      // Parse the JSON output
      try {
        const result = JSON.parse(output.trim());
        return JSON.stringify(result);
      } catch (parseError) {
        console.error('Error parsing kernel output:', parseError);
        return JSON.stringify({
          error: 'Failed to parse file deletion results'
        });
      }
    } catch (error) {
      console.error('Error deleting dataset:', error);
      return JSON.stringify({
        error: `Failed to delete dataset: ${error instanceof Error ? error.message : String(error)}`
      });
    } finally {
      // Always cleanup the kernel session
      if (kernelSession) {
        kernelSession.cleanup();
      }
    }
  }

  /**
   * Upload/save a dataset file
   * @param args Configuration options
   * @param args.filepath Path where to save the file
   * @param args.content Content to save (will be truncated to 5000 characters)
   * @returns JSON string with success or error message
   */
  async save_dataset(args: {
    filepath: string;
    content: string;
  }): Promise<string> {
    let kernelSession: { kernel: any; cleanup: () => void } | null = null;

    try {
      const { filepath, content } = args;

      // Ensure filepath is within data directory
      const safePath = this.getSafeFilePath(filepath);

      // Apply 5000 character limit to content
      const limitedContent =
        content.length > 5000 ? content.substring(0, 5000) : content;
      const wasTruncated = content.length > 5000;

      // Create temporary kernel for this operation
      kernelSession = await this.createTemporaryKernel();
      const { kernel } = kernelSession;

      // Python code to save file with proper directory creation
      const pythonCode = `
import os
import json
from pathlib import Path

def save_file(filepath, content):
    """Save content to a file, creating directories as needed"""
    try:
        file_path = Path(filepath)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "path": filepath,
            "message": "File saved successfully",
            "bytes_written": len(content.encode('utf-8'))
        }
        
    except Exception as e:
        return {"error": f"Failed to save file: {str(e)}"}

# Prepare content (escape for JSON)
content = ${JSON.stringify(limitedContent)}

# Execute the function and print results
result = save_file('${safePath.replace(/\\/g, '\\\\')}', content)
print(json.dumps(result))
`;

      // Execute the Python code
      const output = await this.executeKernelCode(kernel, pythonCode);

      // Parse the JSON output
      try {
        const result = JSON.parse(output.trim());

        // Add truncation info if content was truncated
        if (wasTruncated) {
          result.content_truncated = true;
          result.original_length = content.length;
          result.saved_length = limitedContent.length;
          result.message += ' (Content was truncated to 5000 characters)';
        }

        return JSON.stringify(result);
      } catch (parseError) {
        console.error('Error parsing kernel output:', parseError);
        return JSON.stringify({ error: 'Failed to parse file saving results' });
      }
    } catch (error) {
      console.error('Error saving dataset:', error);
      return JSON.stringify({
        error: `Failed to save dataset: ${error instanceof Error ? error.message : String(error)}`
      });
    } finally {
      // Always cleanup the kernel session
      if (kernelSession) {
        kernelSession.cleanup();
      }
    }
  }

  /**
   * Ensure the file path is safe and within the data directory
   * @param filepath The file path to validate
   * @returns Safe file path
   * @private
   */
  private getSafeFilePath(filepath: string): string {
    // Remove any path traversal attempts
    const cleanPath = filepath.replace(/\.\./g, '').replace(/^\/+/, '');

    // If the path already starts with data directory, use it as is
    if (cleanPath.startsWith(this.dataDir + '/')) {
      return cleanPath;
    }

    // Otherwise, prepend the data directory
    return `${this.dataDir}/${cleanPath}`;
  }
}
