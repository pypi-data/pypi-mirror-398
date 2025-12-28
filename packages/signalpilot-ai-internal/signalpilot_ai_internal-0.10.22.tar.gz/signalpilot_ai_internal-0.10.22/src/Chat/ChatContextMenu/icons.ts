import { LabIcon } from '@jupyterlab/ui-components';
import variableIcon from '../../../style/icons/context_menu/variable.svg';
import snippetsIcon from '../../../style/icons/context_menu/snippets.svg';
import dataIcon from '../../../style/icons/context_menu/data.svg';
import databaseIcon from '../../../style/icons/context_menu/database.svg';
import cellIcon from '../../../style/icons/context_menu/cell.svg';
import searchIcon from '../../../style/icons/context_menu/search.svg';
import insertIcon from '../../../style/icons/context_menu/insert.svg';
// Context menu icons
export const VARIABLE_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:context-variable-icon',
  svgstr: variableIcon
});

export const SNIPPETS_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:context-snippets-icon',
  svgstr: snippetsIcon
});

export const DATA_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:context-data-icon',
  svgstr: dataIcon
});

export const DATABASE_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:context-database-icon',
  svgstr: databaseIcon
});

export const CELL_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:context-cell-icon',
  svgstr: cellIcon
});

export const SEARCH_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:search-icon',
  svgstr: searchIcon
});

export const BACK_CARET_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:back-caret-icon',
  svgstr: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="15" viewBox="0 0 14 15" fill="none">
    <path d="M8.75 11L5.25 7.5L8.75 4" stroke="#E7E7E7" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>`
});

export const INSERT_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:insert-icon',
  svgstr: insertIcon
});

export const TABLE_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:table-icon',
  svgstr:
    '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="currentColor"><path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-507h560v-133H200v133Zm0 214h560v-134H200v134Zm0 213h560v-133H200v133Zm40-454v-80h80v80h-80Zm0 214v-80h80v80h-80Zm0 214v-80h80v80h-80Z"/></svg>'
});

export const FOLDER_ICON = new LabIcon({
  name: 'signalpilot-ai-internal:folder-icon',
  svgstr: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
    <path d="M2 3.5C2 2.67157 2.67157 2 3.5 2H6.79289C7.15482 2 7.50207 2.14365 7.76777 2.40934L9.70711 4.34868C9.97281 4.61438 10.32 4.75803 10.682 4.75803H12.5C13.3284 4.75803 14 5.4296 14 6.25803V12.5C14 13.3284 13.3284 14 12.5 14H3.5C2.67157 14 2 13.3284 2 12.5V3.5Z" fill="currentColor"/>
  </svg>`
});
