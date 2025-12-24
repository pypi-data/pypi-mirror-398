import urllib.parse
import requests
import random
import aiohttp
import asyncio
from urllib.parse import quote_plus
import os
import webbrowser
from urllib.parse import quote_plus
import re

def generateimage(prompt, save=False):
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            if save:
                with open("generatedimage.png", "wb") as f:
                    f.write(response.content)
                print("Image saved as generatedimage.png")
                return image_url
            return image_url
        else:
            print(f"Failed to fetch image: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching image: {e}")
        return None

def qminiai(geminiapikey):
    import os
    from google import genai
    from google.genai import types
    import webbrowser
    from urllib.parse import quote_plus
    import re
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    import os

    client = genai.Client(api_key=geminiapikey)

    chat_history = []

    def generate():
        try:
            userinput = input()
            if not userinput.strip():
                return
            match = re.match(r"generateimage\((.*?)\)", userinput)
            if match:
                prompt = match.group(1)
                generateimagewithai(prompt)
            match2 = re.match(r"attachfile\((.*?)\)", userinput)
            if match2:
                filepath = match2.group(1).strip('"')
                attachfile(filepath)
                userinput = userinput.replace(match2.group(0), txt)
            match3 = re.match(r"searchforoldwebsite\(([^,]+),\s*([^)]+)\)", userinput)
            if match3:
                website = match3.group(1).strip()
                datetime = match3.group(2).strip()
                replacement = searchforoldwebsite(website, datetime)
                userinput = userinput.replace(match3.group(0), replacement)
            match4 = re.match(r'searchforwebsite\((["\']?https?://[^"\')]+["\']?)\)', userinput)
            if match4:
                website = match4.group(1)
                replacement = searchforwebsite(website)
                userinput = userinput.replace(match4.group(0), replacement)
            match5 = re.match(r"readexcelfile\((.*?)\)", userinput)
            if match5: 
                filepath = match5.group(1)
                replacement = readexcelfile(filepath)
                userinput = userinput.replace(match5.group(0), replacement)
            match6 = re.match(r"runfile\((.*?)\)", userinput)
            if match6:
                file = match6.group(1)
                runfile(file)
            chat_history.append(types.Content(role="user", parts=[types.Part.from_text(text=userinput)]))

            model = "gemini-2.5-flash"
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=-1)
            )

            response_text = ""
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=chat_history,
                config=config,
            ):
                print(chunk.text)
                response_text += chunk.text
            chat_history.append(
                types.Content(role="model", parts=[types.Part.from_text(text=response_text)])
            )

        except Exception as e:
            pass

    def generateimagewithai(prompt):
        encodedprompt = quote_plus(prompt)
        url = f"https://pollinations.ai/prompt/{encodedprompt}"
        webbrowser.open(url)

    def attachfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            globals()["txt"] = f"Attached file content:\n{content}"
        except Exception as e:
            return f"Failed to attach file: {e}"

    def searchforoldwebsite(website, datetime):
        try:
            apiurl = f"https://archive.org/wayback/available?url={website}&timestamp={datetime}"
            resp = requests.get(apiurl)
            if resp.status_code == 200:
                data = resp.json()
                snapshot = data.get("archived_snapshots", {}).get("closest", {})
                if snapshot:
                    return f"{website}'s content in {datetime}: Snapshot found: URL: {snapshot.get('url')} Timestamp: {snapshot.get('timestamp')}"
                else:
                    return f"{website}'s content in {datetime}: No snapshot found."
            else:
                return f"{website}'s content in {datetime}: Request failed with status code {resp.status_code}"
        except Exception as e:
            return f"{website}'s content in {datetime}: [Error] {e}"

    def searchforwebsite(website):
        try:
            url = str(website).strip().strip('"').strip("'")
            resp = requests.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                text = soup.get_text().strip().replace("\n", " ")
                return f"{url}'s content: {text}"
            else:
                return f"{url}'s content: [Error] Status code {resp.status_code}"
        except Exception as e:
            return f"{url}'s content: [Error] {e}"

    def readexcelfile(filepath):
        try:
            filepath = filepath.strip().strip('"').strip("'")
            xls = pd.ExcelFile(filepath)
            if not xls.sheet_names:
                return f"[Error] No worksheets found in '{filepath}'. The file may be empty or corrupted."
            df = xls.parse(xls.sheet_names[0])
            return f"{filepath}'s content:\n{df.to_string(index=False)}"
        except Exception as e:
            return f"[Error reading Excel file: {e}]"

    def runfile(file):
        os.system(file)

    if __name__ == "__main__":
        while True:
            generate()

def qminiaitwo(geminiapikey):
    import os
    from google import genai
    from google.genai import types
    import webbrowser
    from urllib.parse import quote_plus
    import re
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    import os

    client = genai.Client(api_key=geminiapikey)

    chat_history = []

    def generate():
        try:
            userinput = input()
            if not userinput.strip():
                return
            match = re.match(r"generateimage\((.*?)\)", userinput)
            if match:
                prompt = match.group(1)
                generateimagewithai(prompt)
            match2 = re.match(r"attachfile\((.*?)\)", userinput)
            if match2:
                filepath = match2.group(1).strip('"')
                attachfile(filepath)
                userinput = userinput.replace(match2.group(0), txt)
            match3 = re.match(r"searchforoldwebsite\(([^,]+),\s*([^)]+)\)", userinput)
            if match3:
                website = match3.group(1).strip()
                datetime = match3.group(2).strip()
                replacement = searchforoldwebsite(website, datetime)
                userinput = userinput.replace(match3.group(0), replacement)
            match4 = re.match(r'searchforwebsite\((["\']?https?://[^"\')]+["\']?)\)', userinput)
            if match4:
                website = match4.group(1)
                replacement = searchforwebsite(website)
                userinput = userinput.replace(match4.group(0), replacement)
            match5 = re.match(r"readexcelfile\((.*?)\)", userinput)
            if match5: 
                filepath = match5.group(1)
                replacement = readexcelfile(filepath)
                userinput = userinput.replace(match5.group(0), replacement)
            match6 = re.match(r"runfile\((.*?)\)", userinput)
            if match6:
                file = match6.group(1)
                runfile(file)
            chat_history.append(types.Content(role="user", parts=[types.Part.from_text(text=userinput)]))

            model = "gemini-2.5-flash"
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=-1),
                system_instruction="You are QminiAI."
            )

            response_text = ""
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=chat_history,
                config=config,
            ):
                print(chunk.text)
                response_text += chunk.text
            chat_history.append(
                types.Content(role="model", parts=[types.Part.from_text(text=response_text)])
            )

        except Exception as e:
            pass

    def generateimagewithai(prompt):
        encodedprompt = quote_plus(prompt)
        url = f"https://pollinations.ai/prompt/{encodedprompt}"
        webbrowser.open(url)

    def attachfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            globals()["txt"] = f"Attached file content:\n{content}"
        except Exception as e:
            return f"Failed to attach file: {e}"

    def searchforoldwebsite(website, datetime):
        try:
            apiurl = f"https://archive.org/wayback/available?url={website}&timestamp={datetime}"
            resp = requests.get(apiurl)
            if resp.status_code == 200:
                data = resp.json()
                snapshot = data.get("archived_snapshots", {}).get("closest", {})
                if snapshot:
                    return f"{website}'s content in {datetime}: Snapshot found: URL: {snapshot.get('url')} Timestamp: {snapshot.get('timestamp')}"
                else:
                    return f"{website}'s content in {datetime}: No snapshot found."
            else:
                return f"{website}'s content in {datetime}: Request failed with status code {resp.status_code}"
        except Exception as e:
            return f"{website}'s content in {datetime}: [Error] {e}"

    def searchforwebsite(website):
        try:
            url = str(website).strip().strip('"').strip("'")
            resp = requests.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                text = soup.get_text().strip().replace("\n", " ")
                return f"{url}'s content: {text}"
            else:
                return f"{url}'s content: [Error] Status code {resp.status_code}"
        except Exception as e:
            return f"{url}'s content: [Error] {e}"

    def readexcelfile(filepath):
        try:
            filepath = filepath.strip().strip('"').strip("'")
            xls = pd.ExcelFile(filepath)
            if not xls.sheet_names:
                return f"[Error] No worksheets found in '{filepath}'. The file may be empty or corrupted."
            df = xls.parse(xls.sheet_names[0])
            return f"{filepath}'s content:\n{df.to_string(index=False)}"
        except Exception as e:
            return f"[Error reading Excel file: {e}]"

    def runfile(file):
        os.system(file)

    if __name__ == "__main__":
        while True:
            generate()

def translate(sourcelanguage, text, targetlanguage):
    from deep_translator import GoogleTranslator
    translated = GoogleTranslator(source=sourcelanguage, target=targetlanguage).translate(text)
    return translated

def guiqminiai(geminiapikey, title, geometry, bg, icon, fullscreen=False):
    import os
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter.scrolledtext import ScrolledText
    from google import genai
    from google.genai import types
    import webbrowser
    from urllib.parse import quote_plus
    import re
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    import platform

    client = genai.Client(api_key=geminiapikey)
    chat_history = []
    
    root = tk.Tk()
    root.title(title)
    root.configure(bg=bg)
    
    if fullscreen:
        root.attributes('-fullscreen', True)
    else:
        root.geometry(geometry)
    
    if platform.system() == "Windows":
        try: root.iconbitmap(icon)
        except: pass
    else:
        try:
            iconimg = tk.PhotoImage(file=icon)
            root.iconphoto(False, iconimg)
        except: pass
    
    output_text = ScrolledText(root, height=20, width=80, state=tk.DISABLED, wrap=tk.WORD)
    output_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    user_input_widget = ScrolledText(root, height=5, width=80, wrap=tk.WORD)
    user_input_widget.pack(pady=(0, 10), padx=10, fill=tk.X)
    
    def generateimagewithai(prompt):
        encodedprompt = quote_plus(prompt)
        url = f"https://pollinations.ai/prompt/{encodedprompt}"
        webbrowser.open(url)
        return f"[Tool: Image generation command sent. Check your browser for '{prompt}']"

    def attachfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return f"\n[Attached file content of '{os.path.basename(filepath)}':\n{content}\n]\n"
        except Exception as e:
            return f"[Tool Error: Failed to attach file: {e}]"

    def searchforoldwebsite(website, datetime):
        try:
            apiurl = f"https://archive.org/wayback/available?url={website}&timestamp={datetime}"
            resp = requests.get(apiurl)
            if resp.status_code == 200:
                data = resp.json()
                snapshot = data.get("archived_snapshots", {}).get("closest", {})
                if snapshot:
                    return f"Website content from Wayback Machine for {website} on {datetime}: Snapshot found at URL: {snapshot.get('url')} Timestamp: {snapshot.get('timestamp')}"
                else:
                    return f"Website content from Wayback Machine for {website} on {datetime}: No snapshot found."
            else:
                return f"Website content from Wayback Machine for {website} on {datetime}: Request failed with status code {resp.status_code}"
        except Exception as e:
            return f"Website content from Wayback Machine for {website} on {datetime}: [Error] {e}"

    def searchforwebsite(website):
        try:
            url = str(website).strip().strip('"').strip("'")
            resp = requests.get(url, timeout=5) 
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for script_or_style in soup(['script', 'style']):
                    script_or_style.decompose()
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk).strip()
                return f"Website content for {url}: {text[:500]}..." 
            else:
                return f"Website content for {url}: [Error] Status code {resp.status_code}"
        except Exception as e:
            return f"Website content for {url}: [Error] {e}"

    def readexcelfile(filepath):
        try:
            filepath = filepath.strip().strip('"').strip("'")
            xls = pd.ExcelFile(filepath)
            if not xls.sheet_names:
                return f"[Tool Error] No worksheets found in '{filepath}'. File may be empty or corrupted."
            df = xls.parse(xls.sheet_names[0])
            return f"Excel content from '{filepath}':\n{df.to_string(index=False)}"
        except Exception as e:
            return f"[Tool Error reading Excel file: {e}]"

    def runfile(file):
        os.system(file)
        return f"[Tool: Executed file '{file}'. Check your system's output/window for results.]"
        
    def display_message(role, text):
        output_text.config(state=tk.NORMAL)
        output_text.insert(tk.END, f"\n{role}: {text}\n")
        output_text.config(state=tk.DISABLED)
        output_text.see(tk.END)

    def onsubmit():
        user_input = user_input_widget.get("1.0", "end-1c").strip()
        user_input_widget.delete("1.0", tk.END)

        if not user_input:
            return

        display_message("You", user_input)
        
        processed_input = user_input
        
        match5 = re.search(r"readexcelfile\((.*?)\)", processed_input)
        if match5:
            filepath = match5.group(1).strip().strip('"').strip("'")
            replacement = readexcelfile(filepath)
            processed_input = processed_input.replace(match5.group(0), replacement)
            display_message("Tool", f"Excel processed. Replacement: {replacement[:50]}...")
            
        match4 = re.search(r'searchforwebsite\((["\']?https?://[^"\')]+["\']?)\)', processed_input)
        if match4:
            website = match4.group(1).strip().strip('"').strip("'")
            replacement = searchforwebsite(website)
            processed_input = processed_input.replace(match4.group(0), replacement)
            display_message("Tool", f"Website scraped. Replacement: {replacement[:50]}...")
            
        match3 = re.search(r"searchforoldwebsite\(([^,]+),\s*([^)]+)\)", processed_input)
        if match3:
            website = match3.group(1).strip().strip('"').strip("'")
            datetime = match3.group(2).strip().strip('"').strip("'")
            replacement = searchforoldwebsite(website, datetime)
            processed_input = processed_input.replace(match3.group(0), replacement)
            display_message("Tool", f"Wayback Machine searched. Replacement: {replacement[:50]}...")
            
        match2 = re.search(r"attachfile\((.*?)\)", processed_input)
        if match2:
            filepath = match2.group(1).strip().strip('"').strip("'")
            replacement = attachfile(filepath)
            processed_input = processed_input.replace(match2.group(0), replacement)
            display_message("Tool", f"File attached. Replacement: {replacement[:50]}...")
            
        match6 = re.search(r"runfile\((.*?)\)", processed_input)
        if match6:
            file_to_run = match6.group(1).strip().strip('"').strip("'")
            log_message = runfile(file_to_run)
            display_message("Tool", log_message)
            
        match = re.search(r"generateimage\((.*?)\)", processed_input)
        if match:
            prompt = match.group(1).strip().strip('"').strip("'")
            log_message = generateimagewithai(prompt)
            display_message("Tool", log_message)

        chat_history.append(types.Content(role="user", parts=[types.Part.from_text(text=processed_input)]))

        model = "gemini-2.5-flash"
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=-1)
        )

        response_text = ""
        output_text.config(state=tk.NORMAL)
        output_text.insert(tk.END, "\nAI: ")
        
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=chat_history,
            config=config,
        ):
            output_text.insert(tk.END, chunk.text)
            output_text.see(tk.END)
            root.update_idletasks()
            
            response_text += chunk.text
        
        output_text.config(state=tk.DISABLED)
        
        chat_history.append(
            types.Content(role="model", parts=[types.Part.from_text(text=response_text)])
        )
    
    submit_button = tk.Button(root, text="Submit", command=onsubmit)
    submit_button.pack(pady=5)
    
    user_input_widget.bind("<Return>", lambda event: onsubmit())

    root.mainloop()

    return root

def creategemini(geminiapikey, userinput, instructions=None, maxtokens=None):
    client = genai.Client(api_key=geminiapikey)
    if maxtokens < 300:
        maxtokens = 300

    chat_history = []
    chat_history.append(types.Content(role="user", parts=[types.Part.from_text(text=userinput)]))

    model = "gemini-2.5-flash"
    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        system_instruction=instructions if instructions else None,
        max_output_tokens=maxtokens if maxtokens else None
    )

    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=chat_history,
        config=config
    ):
        response_text += chunk.text
    chat_history.append(
        types.Content(role="model", parts=[types.Part.from_text(text=response_text)])
    )
    return response_text

def askai(geminiapikey, prompt):
    client = genai.Client(api_key=geminiapikey)
    model = "gemini-2.5-flash"
    
    response = client.models.generate_content(
        model=model,
        contents=[prompt]
    )
    
    return response.text

def guiqminiaitwo(geminiapikey, title, geometry, bg, icon, fullscreen=False):
    import os
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter.scrolledtext import ScrolledText
    from google import genai
    from google.genai import types
    import webbrowser
    from urllib.parse import quote_plus
    import re
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    import platform

    client = genai.Client(api_key=geminiapikey)
    chat_history = []
    
    root = tk.Tk()
    root.title(title)
    root.configure(bg=bg)
    
    if fullscreen:
        root.attributes('-fullscreen', True)
    else:
        root.geometry(geometry)
    
    if platform.system() == "Windows":
        try: root.iconbitmap(icon)
        except: pass
    else:
        try:
            iconimg = tk.PhotoImage(file=icon)
            root.iconphoto(False, iconimg)
        except: pass
    
    output_text = ScrolledText(root, height=20, width=80, state=tk.DISABLED, wrap=tk.WORD)
    output_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    user_input_widget = ScrolledText(root, height=5, width=80, wrap=tk.WORD)
    user_input_widget.pack(pady=(0, 10), padx=10, fill=tk.X)
    
    def generateimagewithai(prompt):
        encodedprompt = quote_plus(prompt)
        url = f"https://pollinations.ai/prompt/{encodedprompt}"
        webbrowser.open(url)
        return f"[Tool: Image generation command sent. Check your browser for '{prompt}']"

    def attachfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return f"\n[Attached file content of '{os.path.basename(filepath)}':\n{content}\n]\n"
        except Exception as e:
            return f"[Tool Error: Failed to attach file: {e}]"

    def searchforoldwebsite(website, datetime):
        try:
            apiurl = f"https://archive.org/wayback/available?url={website}&timestamp={datetime}"
            resp = requests.get(apiurl)
            if resp.status_code == 200:
                data = resp.json()
                snapshot = data.get("archived_snapshots", {}).get("closest", {})
                if snapshot:
                    return f"Website content from Wayback Machine for {website} on {datetime}: Snapshot found at URL: {snapshot.get('url')} Timestamp: {snapshot.get('timestamp')}"
                else:
                    return f"Website content from Wayback Machine for {website} on {datetime}: No snapshot found."
            else:
                return f"Website content from Wayback Machine for {website} on {datetime}: Request failed with status code {resp.status_code}"
        except Exception as e:
            return f"Website content from Wayback Machine for {website} on {datetime}: [Error] {e}"

    def searchforwebsite(website):
        try:
            url = str(website).strip().strip('"').strip("'")
            resp = requests.get(url, timeout=5) 
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for script_or_style in soup(['script', 'style']):
                    script_or_style.decompose()
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk).strip()
                return f"Website content for {url}: {text[:500]}..." 
            else:
                return f"Website content for {url}: [Error] Status code {resp.status_code}"
        except Exception as e:
            return f"Website content for {url}: [Error] {e}"

    def readexcelfile(filepath):
        try:
            filepath = filepath.strip().strip('"').strip("'")
            xls = pd.ExcelFile(filepath)
            if not xls.sheet_names:
                return f"[Tool Error] No worksheets found in '{filepath}'. File may be empty or corrupted."
            df = xls.parse(xls.sheet_names[0])
            return f"Excel content from '{filepath}':\n{df.to_string(index=False)}"
        except Exception as e:
            return f"[Tool Error reading Excel file: {e}]"

    def runfile(file):
        os.system(file)
        return f"[Tool: Executed file '{file}'. Check your system's output/window for results.]"
        
    def display_message(role, text):
        output_text.config(state=tk.NORMAL)
        output_text.insert(tk.END, f"\n{role}: {text}\n")
        output_text.config(state=tk.DISABLED)
        output_text.see(tk.END)

    def onsubmit():
        user_input = user_input_widget.get("1.0", "end-1c").strip()
        user_input_widget.delete("1.0", tk.END)

        if not user_input:
            return

        display_message("You", user_input)
        
        processed_input = user_input
        
        match5 = re.search(r"readexcelfile\((.*?)\)", processed_input)
        if match5:
            filepath = match5.group(1).strip().strip('"').strip("'")
            replacement = readexcelfile(filepath)
            processed_input = processed_input.replace(match5.group(0), replacement)
            display_message("Tool", f"Excel processed. Replacement: {replacement[:50]}...")
            
        match4 = re.search(r'searchforwebsite\((["\']?https?://[^"\')]+["\']?)\)', processed_input)
        if match4:
            website = match4.group(1).strip().strip('"').strip("'")
            replacement = searchforwebsite(website)
            processed_input = processed_input.replace(match4.group(0), replacement)
            display_message("Tool", f"Website scraped. Replacement: {replacement[:50]}...")
            
        match3 = re.search(r"searchforoldwebsite\(([^,]+),\s*([^)]+)\)", processed_input)
        if match3:
            website = match3.group(1).strip().strip('"').strip("'")
            datetime = match3.group(2).strip().strip('"').strip("'")
            replacement = searchforoldwebsite(website, datetime)
            processed_input = processed_input.replace(match3.group(0), replacement)
            display_message("Tool", f"Wayback Machine searched. Replacement: {replacement[:50]}...")
            
        match2 = re.search(r"attachfile\((.*?)\)", processed_input)
        if match2:
            filepath = match2.group(1).strip().strip('"').strip("'")
            replacement = attachfile(filepath)
            processed_input = processed_input.replace(match2.group(0), replacement)
            display_message("Tool", f"File attached. Replacement: {replacement[:50]}...")
            
        match6 = re.search(r"runfile\((.*?)\)", processed_input)
        if match6:
            file_to_run = match6.group(1).strip().strip('"').strip("'")
            log_message = runfile(file_to_run)
            display_message("Tool", log_message)
            
        match = re.search(r"generateimage\((.*?)\)", processed_input)
        if match:
            prompt = match.group(1).strip().strip('"').strip("'")
            log_message = generateimagewithai(prompt)
            display_message("Tool", log_message)

        chat_history.append(types.Content(role="user", parts=[types.Part.from_text(text=processed_input)]))

        model = "gemini-2.5-flash"
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
            system_instruction="You are QminiAI."
        )

        response_text = ""
        output_text.config(state=tk.NORMAL)
        output_text.insert(tk.END, "\nAI: ")
        
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=chat_history,
            config=config,
        ):
            output_text.insert(tk.END, chunk.text)
            output_text.see(tk.END)
            root.update_idletasks()
            
            response_text += chunk.text
        
        output_text.config(state=tk.DISABLED)
        
        chat_history.append(
            types.Content(role="model", parts=[types.Part.from_text(text=response_text)])
        )
    
    submit_button = tk.Button(root, text="Submit", command=onsubmit)
    submit_button.pack(pady=5)
    
    user_input_widget.bind("<Return>", lambda event: onsubmit())

    root.mainloop()

    return root
