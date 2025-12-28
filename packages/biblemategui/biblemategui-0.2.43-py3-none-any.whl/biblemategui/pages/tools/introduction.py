from nicegui import ui, app, run
import os, re, markdown2, asyncio
from biblemategui import BIBLEMATEGUI_DATA, get_translation
from agentmake.plugins.uba.lib.BibleBooks import BibleBooks
from agentmake.plugins.uba.lib.BibleParser import BibleVerseParser
from agentmake import readTextFile

def get_contents(b, lang="eng"):
    parser = BibleVerseParser(False, language=lang)
    def process_content(parser, content):
        # parse content
        content = parser.parseText(content)
        # convert md to html
        content = markdown2.markdown(content, extras=["tables","fenced-code-blocks","toc","codelite"])
        content = content.replace("<h1>", "<h2>").replace("</h1>", "</h2>")
        # convert links
        content = re.sub(r'''(onclick|ondblclick)="(bcv)\((.*?)\)"''', r'''\1="emitEvent('\2', [\3]); return false;"''', content)
        return content
    contents = []
    conversation_file = os.path.join(BIBLEMATEGUI_DATA, "BibleBookStudies", lang, f"{b}.py")
    if os.path.isfile(conversation_file):
        contents = [process_content(parser, i["content"]) for i in eval(readTextFile(conversation_file)) if i.get("role", "") == "assistant" and not i.get("content", "") == "Sure! Let's dive into the analysis process."]
    return contents

def book_introduction(gui=None, b=1, q="", **_):

    # handle book change
    def on_book_change(event):
        nonlocal gui
        app.storage.user['tool_book_number'] = event.value
        gui.load_area_2_content(title="Introduction", sync=False)

    # handle bcv events
    def bcv(event):
        nonlocal gui
        b, c, v, *_ = event.args
        gui.change_area_1_bible_chapter(None, b, c, v)
    ui.on('bcv', bcv)

    # Summary display
    async def load_introduction(b):
        n = ui.notification("Loading ...", timeout=None, spinner=True)
        await asyncio.sleep(0)
        contents = await run.io_bound(get_contents, b, app.storage.user['ui_language'])

        with ui.row().classes('w-full justify-center'):
            book_options = {i: BibleBooks.abbrev["eng"][str(i)][-1] for i in range(1,67)}
            ui.select(
                options=book_options,
                value=b,
                on_change=on_book_change,
            )

        if contents:
            sections = {
                "Overview": "info",
                "Structural Outline": "account_tree",
                "Logical Flow": "low_priority",
                "Historical Setting": "history_edu",
                "Themes": "style",
                "Keywords": "vpn_key",
                "Theology": "auto_stories",
                "Canonical Placement": "format_list_numbered",
                "Practical Living": "volunteer_activism",
                "Summary": "summarize",
            }
            # display content
            index = 0
            for section, icon in sections.items():
                with ui.expansion(get_translation(section), icon=icon, value=(q.lower() == section.lower())) \
                            .classes('w-full border rounded-lg shadow-sm') \
                            .props('header-class="font-bold text-lg text-secondary"'):
                    ui.html(f'<div class="content-text">{contents[index]}</div>', sanitize=False)
                index += 1
        n.dismiss()

    ui.timer(0, lambda: load_introduction(b), once=True)    