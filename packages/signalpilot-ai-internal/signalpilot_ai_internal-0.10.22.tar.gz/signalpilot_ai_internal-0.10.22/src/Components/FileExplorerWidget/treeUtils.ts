import { ISupportedFileEntry, TreeNode, IFolderNode, IFileNode } from './types';

/**
 * Builds a hierarchical tree structure from a flat array of files
 */
export function buildFileTree(
  files: ISupportedFileEntry[],
  baseDirAbsolutePath?: string
): TreeNode[] {
  const rootNodes: TreeNode[] = [];
  const folderMap = new Map<string, IFolderNode>();

  for (const file of files) {
    // Compute a path relative to the provided base directory (if any)
    const normalizedFileAbs = file.absolute_path.replace(/\\/g, '/');
    let relativeForTree = file.relative_path.replace(/\\/g, '/');
    if (baseDirAbsolutePath) {
      const baseNormalized = baseDirAbsolutePath.replace(/\\/g, '/');
      const baseWithSlash = baseNormalized.endsWith('/')
        ? baseNormalized
        : `${baseNormalized}/`;
      if (
        normalizedFileAbs === baseNormalized ||
        normalizedFileAbs.startsWith(baseWithSlash)
      ) {
        relativeForTree = normalizedFileAbs.slice(baseWithSlash.length);
      }
    }

    const pathParts = relativeForTree
      .split('/')
      .filter(part => part.length > 0);

    if (pathParts.length === 1) {
      // File is in root directory
      rootNodes.push({
        type: 'file',
        file: {
          ...file,
          // Ensure relative_path is relative to the dir root
          relative_path: pathParts[0]
        }
      });
    } else {
      // File is in a subdirectory
      const folderPath = pathParts.slice(0, -1);
      const fileName = pathParts[pathParts.length - 1];

      // Build the folder path string
      let currentPath = '';
      let parentPath = '';

      // Create all necessary folders in the path
      for (let i = 0; i < folderPath.length; i++) {
        const folderName = folderPath[i];
        currentPath = currentPath ? `${currentPath}/${folderName}` : folderName;

        if (!folderMap.has(currentPath)) {
          const newFolder: IFolderNode = {
            type: 'folder',
            name: folderName,
            path: currentPath,
            children: [],
            isExpanded: true,
            fileCount: 0
          };
          folderMap.set(currentPath, newFolder);

          // Add to parent or root
          if (i === 0) {
            // This is a root-level folder
            rootNodes.push(newFolder);
          } else {
            // Add to parent folder
            const parentFolder = folderMap.get(parentPath);
            if (parentFolder) {
              parentFolder.children.push(newFolder);
            }
          }
        }

        // Increment file count for this folder
        const folder = folderMap.get(currentPath)!;
        folder.fileCount++;

        parentPath = currentPath;
      }

      // Add the file to the last folder in the path
      const targetFolder = folderMap.get(currentPath);
      if (targetFolder) {
        targetFolder.children.push({
          type: 'file',
          file: {
            ...file,
            relative_path: fileName
          }
        });
      }
    }
  }

  // Sort the tree
  sortTreeNodes(rootNodes);

  return rootNodes;
}

/**
 * Recursively sort tree nodes (folders first, then files, both alphabetically)
 */
function sortTreeNodes(nodes: TreeNode[]): void {
  // Sort the current level
  nodes.sort((a, b) => {
    if (a.type === 'folder' && b.type === 'file') {
      return -1;
    }
    if (a.type === 'file' && b.type === 'folder') {
      return 1;
    }
    return a.type === 'folder'
      ? a.name.localeCompare((b as IFolderNode).name)
      : (a as IFileNode).file.name.localeCompare((b as IFileNode).file.name);
  });

  // Recursively sort children
  for (const node of nodes) {
    if (node.type === 'folder') {
      sortTreeNodes(node.children);
    }
  }
}

/**
 * Count total files in a tree (recursive)
 */
export function countFilesInTree(nodes: TreeNode[]): number {
  let count = 0;
  for (const node of nodes) {
    if (node.type === 'file') {
      count++;
    } else {
      count += countFilesInTree(node.children);
    }
  }
  return count;
}

/**
 * Find a file in the tree by its absolute path
 */
export function findFileInTree(
  nodes: TreeNode[],
  absolutePath: string
): ISupportedFileEntry | null {
  for (const node of nodes) {
    if (node.type === 'file' && node.file.absolute_path === absolutePath) {
      return node.file;
    } else if (node.type === 'folder') {
      const found = findFileInTree(node.children, absolutePath);
      if (found) {
        return found;
      }
    }
  }
  return null;
}
