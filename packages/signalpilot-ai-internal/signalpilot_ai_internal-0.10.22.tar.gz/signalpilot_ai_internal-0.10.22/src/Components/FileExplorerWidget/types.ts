import { IFileEntry } from '../../Chat/ChatContextMenu/DataLoaderService';
import { IDatasetSchema } from '../../Chat/ChatContextMenu/DataLoaderService';
import { IScannedDirectory } from '../../handler';

export interface IFileExplorerState {
  isVisible: boolean;
  files: IFileEntry[];
  scannedDirectories: IScannedDirectory[];
  workDir: string | null;
  isLoading: boolean;
  error?: string;
  totalFileCount: number;
  isUploading: boolean;
  uploadProgress?: {
    completed: number;
    total: number;
  };
  uploadSuccess?: {
    fileCount: number;
  };
  folderAddedSuccess?: {
    folderPath: string;
  };
}

export type FileType = 'csv' | 'tsv' | 'json' | 'parquet' | 'pkl' | 'ipynb';

export interface ISupportedFileEntry extends IFileEntry {
  displayPath: string;
  fileType: FileType;
  schema?: IDatasetSchema;
  hasSchema: boolean;
  isExpanded?: boolean;
}

// Tree structure types
export interface IFolderNode {
  type: 'folder';
  name: string;
  path: string;
  children: TreeNode[];
  isExpanded: boolean;
  fileCount: number;
}

export interface IFileNode {
  type: 'file';
  file: ISupportedFileEntry;
}

export type TreeNode = IFolderNode | IFileNode;
