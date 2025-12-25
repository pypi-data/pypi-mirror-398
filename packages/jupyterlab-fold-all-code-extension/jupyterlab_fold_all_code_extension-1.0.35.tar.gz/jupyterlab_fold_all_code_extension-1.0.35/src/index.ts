import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';

const PLUGIN_ID = 'jupyterlab_fold_all_code_extension:plugin';

const CommandIDs = {
  foldAllCode: 'jupyterlab_fold_all_code_extension:fold-all',
  expandAllCode: 'jupyterlab_fold_all_code_extension:expand-all'
};

/**
 * Set the source_hidden metadata on a cell.
 * This ensures the hidden state is persisted in the notebook file
 * and respected during export.
 */
function setSourceHidden(cell: any, hidden: boolean): void {
  // JupyterLab 4.x API: use cell.model.getMetadata/setMetadata
  let jupyter = cell.model.getMetadata('jupyter') as
    | Record<string, any>
    | undefined;

  if (hidden) {
    if (!jupyter) {
      jupyter = {};
    }
    jupyter['source_hidden'] = true;
    cell.model.setMetadata('jupyter', jupyter);
  } else {
    if (jupyter) {
      delete jupyter['source_hidden'];
      if (Object.keys(jupyter).length === 0) {
        cell.model.deleteMetadata('jupyter');
      } else {
        cell.model.setMetadata('jupyter', jupyter);
      }
    }
  }
}

/**
 * Fold all code cells in the given notebook panel.
 */
function foldAllCodeCells(notebookPanel: NotebookPanel): void {
  const notebook = notebookPanel.content;
  const cells = notebook.widgets;

  for (let i = 0; i < cells.length; i++) {
    const cell = cells[i];
    if (cell.model.type === 'code') {
      cell.inputHidden = true;
      setSourceHidden(cell, true);
    }
  }
}

/**
 * Expand all code cells in the given notebook panel.
 */
function expandAllCodeCells(notebookPanel: NotebookPanel): void {
  const notebook = notebookPanel.content;
  const cells = notebook.widgets;

  for (let i = 0; i < cells.length; i++) {
    const cell = cells[i];
    if (cell.model.type === 'code') {
      cell.inputHidden = false;
      setSourceHidden(cell, false);
    }
  }
}

/**
 * Initialization data for the jupyterlab_fold_all_code_extension extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  description:
    'JupyterLab extension to fold and expand all code cells, to help create clean notebooks to share with non-technical audiences',
  autoStart: true,
  requires: [INotebookTracker],
  activate: (app: JupyterFrontEnd, notebookTracker: INotebookTracker) => {
    console.log(
      'JupyterLab extension jupyterlab_fold_all_code_extension is activated!'
    );

    // Add fold all code command
    app.commands.addCommand(CommandIDs.foldAllCode, {
      label: 'Fold All Code',
      caption: 'Collapse all code cells in the notebook',
      execute: () => {
        const currentNotebook = notebookTracker.currentWidget;
        if (currentNotebook) {
          foldAllCodeCells(currentNotebook);
        }
      },
      isEnabled: () => notebookTracker.currentWidget !== null
    });

    // Add expand all code command
    app.commands.addCommand(CommandIDs.expandAllCode, {
      label: 'Expand All Code',
      caption: 'Show all code cells in the notebook',
      execute: () => {
        const currentNotebook = notebookTracker.currentWidget;
        if (currentNotebook) {
          expandAllCodeCells(currentNotebook);
        }
      },
      isEnabled: () => notebookTracker.currentWidget !== null
    });
  }
};

export default plugin;
