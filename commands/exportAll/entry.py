import adsk.core
import os, re
import traceback
from pathlib import Path
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

# Set to True to give more verbose debug logging
DEBUG_LOG = False

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdExportAll'
CMD_NAME = 'Export All Components'
CMD_Description = 'Export all components from the current design as STEP or STL files. These can then be imported into a 3D slicer'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidMakePanel'
COMMAND_BESIDE_ID = 'ExportAllCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar.
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    if DEBUG_LOG:
        futil.log(f'{CMD_NAME} Command Created Event')

    args.command.setDialogMinimumSize(317,200)

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    inputs.addTextBoxCommandInput('destination_folder', 'Destination Folder', 'Development/3D Printing', 1, False)

    type_input = inputs.addDropDownCommandInput('destination_type', 'Destination Type', 1)
    type_input_items = type_input.listItems
    type_input_items.add('STL', False)
    type_input_items.add('STEP', True)
    type_input_items.add('3mf', False)

    export_type = inputs.addRadioButtonGroupCommandInput('export_type', 'Export Type')
    export_type_items = export_type.listItems
    export_type_items.add('One file per component', True,)
    export_type_items.add('One file, multiple bodies', False)

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


def exportComponent(exportManager: adsk.fusion.ExportManager, exportFolder: os.PathLike, typeInputItems, component: adsk.fusion.Component, stripVersion: bool):
    futil.log(f'Files will be exported to {exportFolder}')
    sanitizedName = re.sub(r'[\\|/|:|?|.|"|<|>|\|]', '-', component.name)
    if stripVersion:
        sanitizedName = sanitizedName.rsplit(' ', 1)[0]
    for type_item in typeInputItems:
        exportOptions = None
        if type_item.isSelected:
            destinationType = type_item.name
            if destinationType == '3mf':
                exportPath = os.path.join(exportFolder, f'{sanitizedName}.3mf')
                exportOptions = exportManager.createC3MFExportOptions(component, exportPath)
            elif destinationType == 'STEP':
                exportPath = os.path.join(exportFolder, f'{sanitizedName}.step')
                exportOptions = exportManager.createSTEPExportOptions(exportPath, component)
            elif destinationType == 'STL':
                exportPath = os.path.join(exportFolder, f'{sanitizedName}.stl')
                exportOptions = exportManager.createSTLExportOptions(component, exportPath)
        if not exportOptions is None:
            exportManager.execute(exportOptions)
            futil.log(f'Exported {component.name} to {exportPath}')

# This event handler is called when the user clicks the OK button in the command dialog or
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    if DEBUG_LOG:
        futil.log(f'{CMD_NAME} Command Execute Event')

    homeFolder = Path('~').expanduser()

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs
    folderInput: adsk.core.TextBoxCommandInput = inputs.itemById('destination_folder')
    destinationFolder = folderInput.text
    exportTypeInput: adsk.core.addRadioCommandInput = inputs.itemById('export_type')
    exportTypeInputItems = exportTypeInput.listItems
    exportType = exportTypeInput.selectedItem.name
    destTypeInput: adsk.core.addDropDownCommandInput = inputs.itemById('destination_type')
    destTypeInputItems = destTypeInput.listItems

    exportFolder = os.path.join(homeFolder, destinationFolder)
    design = adsk.fusion.Design.cast(app.activeProduct)
    exportManager = design.exportManager
    if not design:
        ui.messageBox('No Active Fusion Design', 'No Design')
        return
    try:
        rootComponent = design.rootComponent
        if exportType == 'One file, multiple bodies':
            futil.log(f'Will export a file with multiple bodies')
            exportComponent(exportManager, exportFolder, destTypeInputItems, rootComponent, True)
        elif rootComponent.occurrences.count == 0:
            futil.log(f'Will export the root component')
            exportComponent(exportManager, exportFolder, destTypeInputItems, rootComponent, True)
        else:
            futil.log(f'Will export {rootComponent.occurrences.count} components')
            if rootComponent.occurrences.count > 1:
                sanitizedRoot = re.sub(r'[\\|/|:|?|.|"|<|>|\|]', '-', rootComponent.name)
                unversionedRoot = sanitizedRoot.rsplit(' ', 1)[0]
                exportRoot = os.path.join(exportFolder, f'{unversionedRoot}')
                if not os.path.isdir(exportRoot):
                    os.mkdir(exportRoot)
                futil.log(f'Files will be exported to {exportRoot}')
                exportFolder = exportRoot
            for occurence in rootComponent.occurrences:
                if not occurence.isLightBulbOn:
                    continue
                component = occurence.component
                if not component:
                    continue
                exportComponent(exportManager, exportFolder, destTypeInputItems, component, False)
    except:  #pylint:disable=bare-except
        # Write the error message to the TEXT COMMANDS window.
        futil.log(f'Failed:\n{traceback.format_exc()}')


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    if DEBUG_LOG:
        futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # General logging for debug.
    if DEBUG_LOG:
        futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    if DEBUG_LOG:
        futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs

    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    folderInput = inputs.itemById('destination_folder')
    args.destinationFolder = folderInput
    args.areInputsValid = True
    # if valueInput.value >= 0:
    #     args.areInputsValid = True
    # else:
    #     args.areInputsValid = False


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    if DEBUG_LOG:
        futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []
