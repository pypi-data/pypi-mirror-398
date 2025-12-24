"""
Full TUI/UX example showing forms, menus, dialogs, and input handling
"""
import asyncio
from ConsoleMod import (
    TerminalSplitter, Pane, LayoutMode, PaneLogger,
    Form, InputField, SelectField, CheckboxField, InputType,
    Menu, SelectionList, ConfirmDialog, InputDialog, MenuDialog,
    KeyBindingManager, KeyBindingPreset, KeyCode, LoggerTemplate
)


async def form_example():
    """Example showing form handling"""
    print("Running Form Example..")
    
    logger = LoggerTemplate(name="Form Example")
    
    # Create a form
    form = Form(name="User Registration")
    
    # Add fields
    name_field = InputField("Name", InputType.TEXT, placeholder="Enter your name", required=True)
    email_field = InputField("Email", InputType.EMAIL, placeholder="user@example.com", required=True)
    age_field = InputField("Age", InputType.NUMBER, required=True)
    country_field = SelectField("Country", ["USA", "Canada", "UK", "Australia"], required=True)
    newsletter_field = CheckboxField("Subscribe to newsletter", checked=True)
    
    form.add_field(name_field)
    form.add_field(email_field)
    form.add_field(age_field)
    form.add_field(country_field)
    form.add_field(newsletter_field)
    
    async def process_form():
        await logger.alog("Form created with 5 fields")
        
        # Simulate form filling
        name_field.set_value("John Doe")
        await logger.alog("Name entered")
        await asyncio.sleep(0.3)
        
        email_field.set_value("john@example.com")
        await logger.alog("Email entered")
        await asyncio.sleep(0.3)
        
        age_field.set_value("30")
        await logger.alog("Age entered")
        await asyncio.sleep(0.3)
        
        country_field.set_option(0)
        await logger.alog("Country selected")
        await asyncio.sleep(0.3)
        
        # Validate
        is_valid, errors = form.validate()
        
        if is_valid:
            await logger.alog("✓ Form validated successfully")
            values = form.get_values()
            await logger.alog(f"Submitted values: {values}")
        else:
            await logger.aerror(f"✗ Form validation errors: {errors}")
        
        # Reset form
        await asyncio.sleep(1)
        form.reset()
        await logger.alog("Form reset")
    
    try:
        await asyncio.gather(
            logger.render(),
            process_form(),
        )
    except KeyboardInterrupt:
        await logger.splitter.astop()


async def menu_example():
    """Example showing menu system"""
    print("Running Menu Example..")
    
    logger = LoggerTemplate(name="Menu Example")
    
    # Create menu
    menu = Menu(title="Main Menu")
    
    results = []
    
    def on_file():
        results.append("File selected")
    
    def on_edit():
        results.append("Edit selected")
    
    def on_help():
        results.append("Help selected")
    
    menu.add_item("File", on_file)
    menu.add_item("Edit", on_edit)
    menu.add_item("Help", on_help)
    
    async def process_menu():
        await logger.alog(f"Menu created with {len(menu.items)} items")
        
        # Simulate menu navigation
        for i in range(3):
            menu.next_item()
            item = menu.get_selected_item()
            await logger.alog(f"Selected: {item.label}")
            await asyncio.sleep(0.3)
        
        # Select and activate
        menu.select_item(0)
        await logger.alog("Activating File menu..")
        menu.activate_selected()
        await asyncio.sleep(0.2)
        await logger.alog(f"Result: {results[-1]}")
    
    try:
        await asyncio.gather(
            logger.render(),
            process_menu(),
        )
    except KeyboardInterrupt:
        await logger.splitter.astop()


async def selection_list_example():
    """Example showing selection list"""
    print("Running Selection List Example..")
    
    logger = LoggerTemplate(name="Selection Example")
    
    # Create selection list
    selection = SelectionList(title="Select Items")
    
    items = ["Python", "JavaScript", "Go", "Rust", "C++", "Java"]
    for item in items:
        selection.add_item(item)
    
    async def process_selection():
        await logger.alog(f"Selection list created with {len(items)} items")
        
        # Simulate selection
        for i in range(6):
            if i > 0:
                selection.next_item()
            
            current = selection.get_current_item()
            await logger.alog(f"Current: {current}")
            
            # Toggle selection
            if i % 2 == 0:
                selection.toggle_selection(i)
                await logger.alog(f"  → Selected {current}")
            
            await asyncio.sleep(0.2)
        
        # Show final selection
        selected = selection.get_selected()
        await logger.alog(f"Final selection: {selected}")
    
    try:
        await asyncio.gather(
            logger.render(),
            process_selection(),
        )
    except KeyboardInterrupt:
        await logger.splitter.astop()


async def dialog_example():
    """Example showing dialogs"""
    print("Running Dialog Example..")
    
    logger = LoggerTemplate(name="Dialog Example")
    
    async def process_dialogs():
        # Info dialog
        await logger.alog("Showing info dialog..")
        info_dialog = Dialog("Information", "Welcome to ConsoleMod TUI System!")
        info_dialog.open()
        await logger.alog(f"Dialog result: {info_dialog.get_result()}")
        await asyncio.sleep(0.5)
        
        # Confirm dialog
        await logger.alog("Showing confirm dialog..")
        confirm = ConfirmDialog("Confirm", "Do you want to continue?")
        confirm.open()
        await asyncio.sleep(0.3)
        confirm.confirm()
        await logger.alog(f"Confirmed: {confirm.is_confirmed()}")
        await asyncio.sleep(0.5)
        
        # Input dialog
        await logger.alog("Showing input dialog..")
        input_dlg = InputDialog("Input", "Enter your name:")
        input_dlg.open()
        input_dlg.set_input("John Doe")
        await asyncio.sleep(0.3)
        input_dlg.submit()
        await logger.alog(f"Input: {input_dlg.get_result()}")
        await asyncio.sleep(0.5)
        
        # Menu dialog
        await logger.alog("Showing menu dialog..")
        menu_dlg = MenuDialog("Choose", ["Option 1", "Option 2", "Option 3"])
        menu_dlg.open()
        menu_dlg.next_option()
        await asyncio.sleep(0.2)
        menu_dlg.next_option()
        await asyncio.sleep(0.3)
        result = menu_dlg.select_current()
        await logger.alog(f"Selected: {result}")
    
    try:
        await asyncio.gather(
            logger.render(),
            process_dialogs(),
        )
    except KeyboardInterrupt:
        await logger.splitter.astop()


async def keybinding_example():
    """Example showing keybinding system"""
    print("Running Keybinding Example..")
    
    logger = LoggerTemplate(name="Keybinding Example")
    
    # Create keybinding manager
    kb_manager = KeyBindingManager()
    
    # Register bindings
    async def handle_up():
        await logger.alog("↑ Up arrow pressed")
    
    async def handle_down():
        await logger.alog("↓ Down arrow pressed")
    
    async def handle_enter():
        await logger.alog("✓ Enter pressed")
    
    kb_manager.bind(KeyCode.UP, handle_up, "Move up")
    kb_manager.bind(KeyCode.DOWN, handle_down, "Move down")
    kb_manager.bind(KeyCode.ENTER, handle_enter, "Submit")
    
    async def process_keybindings():
        await logger.alog("Keybinding system initialized")
        
        bindings = kb_manager.get_bindings()
        for key, descriptions in bindings.items():
            for desc in descriptions:
                await logger.alog(f"  {key.value}: {desc}")
        
        await asyncio.sleep(0.3)
        await logger.alog("Simulating key events..")
        
        # Simulate key events
        key_events = [
            (KeyCode.UP, "up"),
            (KeyCode.DOWN, "down"),
            (KeyCode.ENTER, "enter"),
        ]
        
        for key_code, _ in key_events:
            from ConsoleMod import KeyEvent
            event = KeyEvent(key=key_code)
            triggered = await kb_manager.trigger(event)
            if not triggered:
                await logger.alog(f"No binding for {key_code.value}")
            await asyncio.sleep(0.3)
    
    try:
        await asyncio.gather(
            logger.render(),
            process_keybindings(),
        )
    except KeyboardInterrupt:
        await logger.splitter.astop()


async def main():
    """Run all TUI examples"""
    examples = [
        ("Form", form_example),
        ("Menu", menu_example),
        ("Selection List", selection_list_example),
        ("Dialog", dialog_example),
        ("Keybindings", keybinding_example),
    ]
    
    print("ConsoleMod TUI/UX Examples")
    print("=" * 40)
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    
    choice = input("\nSelect example (1-5): ").strip()
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(examples):
            await examples[idx][1]()
        else:
            print("Invalid choice")
    except ValueError:
        print("Invalid input")


if __name__ == "__main__":
    asyncio.run(main())
