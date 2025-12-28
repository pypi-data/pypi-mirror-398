import { LabIcon } from '@jupyterlab/ui-components';
import reloadIcon from '../../../style/icons/files/reload.svg';
import arrowDownIcon from '../../../style/icons/files/arrow-down.svg';
import openLinkIcon from '../../../style/icons/files/open-link.svg';
import magicIcon from '../../../style/icons/files/magic.svg';
import folderIcon from '../../../style/icons/files/folder.svg';
import fileIcon from '../../../style/icons/files/file.svg';

export const RELOAD_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:reload-icon',
  svgstr: reloadIcon
});

export const ARROW_DOWN_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:arrow-down-icon',
  svgstr: arrowDownIcon
});

export const OPEN_LINK_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:open-link-icon',
  svgstr: openLinkIcon
});

export const MAGIC_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:magic-icon',
  svgstr: magicIcon
});

export const FOLDER_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:folder-icon',
  svgstr: folderIcon
});

export const FILE_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:file-icon',
  svgstr: fileIcon
});
