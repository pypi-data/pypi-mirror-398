import asyncio
import threading
from ConsoleMod import TerminalSplitter, Pane

splitter = TerminalSplitter(fps=10)

pane1 = Pane("logs", color="green")
pane2 = Pane("errors", color="red")

splitter.add_pane(pane1)
splitter.add_pane(pane2)

# Thread writing to pane1
def log_writer():
    for i in range(10):
        pane1.write(f"Log {i}")
        import time; time.sleep(0.3)

threading.Thread(target=log_writer, daemon=True).start()

# Async writing to pane2
async def error_writer():
    for i in range(5):
        await pane2.awrite(f"Error {i}")
        await asyncio.sleep(0.5)

async def main():
    await asyncio.gather(splitter.render_loop(), error_writer())

asyncio.run(main())
