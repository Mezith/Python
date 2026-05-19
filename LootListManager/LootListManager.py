import os,re,time
from dataclasses import dataclass
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

import customtkinter
from tkinter import (
    Toplevel,
    Label,
    Canvas,
    BOTH,
    YES,
    LEFT,
    SOLID,
    END,
)
from tkinter import filedialog as fd
from tkinter.messagebox import showerror, showinfo, askyesno, askokcancel
from PIL import Image, ImageTk


CONFIG_DIR = "Config"
TOKEN_PATH = "images/token.json"
CREDENTIALS_PATH = "images/credentials.json"
ICON_PATH = "images/icon.ico"
BACKGROUND_PATH = "images/bckrnd.png"
DEFAULT_LUA_PLACEHOLDER = (
    r"File location World of Warcraft\_classic_\WTF\Account\YourAccountName"
    r"\Servername\CharName\SavedVariables\LootListManager.lua"
)
DEFAULT_SHEET_ID_PLACEHOLDER = (
    "Enter your SpreadSheet ID:'1bYkwLwDbMozOVZ01uXrK9xBJ-x24Mtrt1eKEVVC3JrE'"
)
DEFAULT_SHEET_NAME_PLACEHOLDER = "Sheet Name"
DEFAULT_RANGE_PLACEHOLDER = "A:AC "
LIVE_UPDATE_CACHE = os.path.join(CONFIG_DIR, "config5.txt")


@dataclass
class AppConfig:
    lua_path: str
    spreadsheet_id: str
    sheet_name: str
    sheet_range: str


class ConfigManager:
    def __init__(self, config_dir: str = CONFIG_DIR):
        self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)

    def _config_path(self, name: str) -> str:
        return os.path.join(self.config_dir, name)

    def load(self) -> AppConfig:
        lua_path = self._read_or_default(
            "config1.txt",
            "/",
        )
        spreadsheet_id = self._read_or_default(
            "config2.txt",
            DEFAULT_SHEET_ID_PLACEHOLDER,
        )
        sheet_name = self._read_or_default(
            "config3.txt",
            DEFAULT_SHEET_NAME_PLACEHOLDER,
        )
        sheet_range = self._read_or_default(
            "config4.txt",
            DEFAULT_RANGE_PLACEHOLDER,
        )
        return AppConfig(
            lua_path=lua_path,
            spreadsheet_id=spreadsheet_id,
            sheet_name=sheet_name,
            sheet_range=sheet_range,
        )

    def save(
        self,
        lua_path: Optional[str],
        spreadsheet_id: Optional[str],
        sheet_name: Optional[str],
        sheet_range: Optional[str],
    ) -> None:
        if lua_path:
            self._write("config1.txt", lua_path)
        if spreadsheet_id and spreadsheet_id not in ("", DEFAULT_SHEET_ID_PLACEHOLDER):
            self._write("config2.txt", spreadsheet_id)
        if sheet_name and sheet_name not in ("", DEFAULT_SHEET_NAME_PLACEHOLDER):
            self._write("config3.txt", sheet_name)
        if sheet_range and sheet_range not in ("", DEFAULT_RANGE_PLACEHOLDER):
            self._write("config4.txt", sheet_range)

    def _read_or_default(self, filename: str, default: str) -> str:
        path = self._config_path(filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                value = f.readline().strip()
                return value if value else default
        return default

    def _write(self, filename: str, value: str) -> None:
        path = self._config_path(filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(value)


class GoogleSheetsClient:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, token_path: str = TOKEN_PATH, credentials_path: str = CREDENTIALS_PATH):
        self.token_path = token_path
        self.credentials_path = credentials_path

    def _ensure_token_fresh(self) -> Optional[Credentials]:
        creds = None
        if os.path.exists(self.token_path):
            now = time.time()
            # 4 hours freshness window
            if os.stat(self.token_path).st_mtime < now - 14400:
                os.remove(self.token_path)
            else:
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                if not askokcancel(
                    title="Loot List Updater",
                    message=(
                        "Before the application can run, it needs access to your Google Spreadsheets.\n"
                        "Verify your Google credentials."
                    ),
                ):
                    return None
                creds = flow.run_local_server(port=0)

            with open(self.token_path, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        return creds

    def get_service(self):
        creds = self._ensure_token_fresh()
        if not creds:
            return None
        try:
            return build("sheets", "v4", credentials=creds)
        except HttpError as err:
            showerror(title="Loot List Manager", message=str(err))
            return None


class LootListManagerCore:
    def __init__(self, sheets_client: GoogleSheetsClient):
        self.sheets_client = sheets_client

    def _fetch_sheet_data(
        self,
        spreadsheet_id: str,
        ranges: List[str],
    ) -> Tuple[List[List[str]], str, List[List[str]]]:
        service = self.sheets_client.get_service()
        if not service:
            raise RuntimeError("Google Sheets service unavailable")

        # Get formatting (strikethrough)
        request = (
            service.spreadsheets()
            .get(
                spreadsheetId=spreadsheet_id,
                ranges=ranges[0],
                includeGridData=True,
                fields="sheets.data.rowData.values.effectiveFormat.textFormat(strikethrough)",
            )
            .execute()
        )

        # Get sheet index
        sheet_index_req = (
            service.spreadsheets()
            .get(
                spreadsheetId=spreadsheet_id,
                ranges=ranges[0],
                includeGridData=True,
                fields="sheets.properties(index)",
            )
            .execute()
        )

        response = request.get("sheets", ["Error No Sheets"])
        sheet_index = sheet_index_req.get("sheets", ["Error No Sheets"])
        sheet_index = re.sub(r"[^0-9]+", "", str(sheet_index))

        # Get values
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=ranges[0])
            .execute()
        )
        values = result.get("values", ["Error No Values"])
        df = pd.DataFrame(values)
        df_replace = df.replace([""], [None])
        processed_dataset = df_replace.values.tolist()

        size = len(processed_dataset)
        bool_ean = list(str(response[0]).split(","))
        s = len(processed_dataset[0])

        strk_bool = []
        full_sheet = []
        combined_sheet = []
        player_list = []

        for x in bool_ean:
            y = re.split(r"\s", x)
            y2 = re.sub(r"[^a-zA-Z]+", "", y[-1])
            strk_bool.append(y2)

        for row in processed_dataset:
            for cell in row:
                full_sheet.append(cell)

        i = 0
        for cell in full_sheet:
            if i < len(strk_bool):
                if strk_bool[i] == "True":
                    combined_sheet.append(str(cell) + "~")
                else:
                    combined_sheet.append(cell)
            i += 1

        for col in range(0, s):
            player_list.append(processed_dataset[0][col])

        new_list = np.reshape(player_list, (s, 1))
        t = new_list.tolist()
        t_player = new_list.tolist()

        i = 0
        n = 0
        for cell in combined_sheet:
            if i >= s:
                if n < s:
                    t[n].append(cell)
                    n += 1
                else:
                    n = 0
                    t[n].append(cell)
                    n += 1
            i += 1

        return t, sheet_index, t_player

    def download_to_lua(
        self,
        spreadsheet_id: str,
        ranges: List[str],
        lua_path: str,
    ) -> bool:
        try:
            t, _, _ = self._fetch_sheet_data(spreadsheet_id, ranges)
            with open(lua_path, "w", encoding="utf-8") as f:
                f.write("\nLootlistTest23 = {\n")

            with open(lua_path, "a", encoding="utf-8") as f:
                size_t = len(t)
                for row_idx in range(1, size_t):
                    cd = len(t[row_idx]) - 1
                    for i, cell in enumerate(t[row_idx]):
                        if i == 0:
                            f.write(f'\t["{cell}"] = {{\n')
                        else:
                            label = t[0][i]
                            f.write(f'\t\t"{label} {cell}", -- [{i}]\n')
                            if i == cd:
                                f.write("\t},\n")
                f.write("}\n")
            return True
        except Exception:
            showerror(
                title="Loot List Updater Error",
                message="Error: Something is wrong with the Google Spreadsheet information.",
            )
            return False

    def update_cell_strikethrough(
        self,
        row_index: int,
        col_index: int,
        sheet_id: int,
        strike: bool,
        spreadsheet_id: str,
    ) -> None:
        service = self.sheets_client.get_service()
        if not service:
            return

        end_row = row_index + 1
        end_col = col_index + 1

        reqs = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startColumnIndex": col_index,
                        "endColumnIndex": end_col,
                        "startRowIndex": row_index,
                        "endRowIndex": end_row,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {"strikethrough": strike}
                        }
                    },
                    "fields": "userEnteredFormat/textFormat/strikethrough",
                }
            }
        ]

        request = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": reqs},
        )
        request.execute()

    def update_from_lua(
        self,
        spreadsheet_id: str,
        ranges: List[str],
        lua_path: str,
    ) -> bool:
        try:
            t, sheet_index, t_player = self._fetch_sheet_data(spreadsheet_id, ranges)
        except RuntimeError:
            return False

        array_z: List[str] = []
        with open(lua_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i <= 1:
                    continue
                m = re.findall(r'"([^"]*)"', line)
                m = re.sub(r"^.{1,2}", "", str(m))
                m = re.sub(r".{2}$", "", str(m))
                if m:
                    array_z.append(m)

        n4 = len(t[0]) - 1

        for row_idx in range(1, len(t_player)):
            n3 = 0
            x_p = re.sub(r"^.{1,2}", "", str(t_player[row_idx]))
            x_p = re.sub(r".{2}$", "", str(x_p))
            for x_p2 in array_z:
                if x_p == x_p2:
                    n3 += 1
                else:
                    if 0 < n3 <= n4:
                        t_player[row_idx].append(x_p2)
                        n3 += 1
                    elif n3 > n4:
                        n3 = 0

        for row_idx in range(1, len(t_player)):
            for col_idx in range(1, n4):
                x = str(t_player[row_idx][col_idx])
                x_1 = str(t[row_idx][col_idx])
                if x[-1] != x_1[-1]:
                    if x[-1] == "~":
                        self.update_cell_strikethrough(
                            row_index=row_idx,
                            col_index=col_idx,
                            sheet_id=int(sheet_index),
                            strike=True,
                            spreadsheet_id=spreadsheet_id,
                        )
                    else:
                        self.update_cell_strikethrough(
                            row_index=row_idx,
                            col_index=col_idx,
                            sheet_id=int(sheet_index),
                            strike=False,
                            spreadsheet_id=spreadsheet_id,
                        )
                        showerror(
                            title="Loot List Updater Error",
                            message="Error: Something is wrong with the Google Spreadsheet information.",
                        )
                        return False
        return True


class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None

    def showtip(self, text: str):
        if self.tipwindow or not text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = Label(
            tw,
            text=text,
            justify=LEFT,
            background="#ffffe0",
            relief=SOLID,
            borderwidth=1,
            font=("Arial", "12", "normal"),
        )
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


def create_tooltip(widget, text: str):
    tooltip = ToolTip(widget)

    def enter(_event):
        tooltip.showtip(text)

    def leave(_event):
        tooltip.hidetip()

    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)


class BackgroundFrame(customtkinter.CTkFrame):
    def __init__(self, master, lua_placeholder: str, *pargs, **kwargs):
        super().__init__(master, *pargs, **kwargs)
        self.lua_placeholder = lua_placeholder
        self.image = Image.open(BACKGROUND_PATH)
        self.img_copy = self.image.copy()
        self.background_image = ImageTk.PhotoImage(self.image)
        self.background = Canvas(self, bd=0, highlightthickness=0, width=900, height=700)
        self.background.pack(fill=BOTH, expand=True)
        self.background.bind("<Configure>", self._resize_image)
        self.entry_4 = None
        self.entry_4_text = None

    def _resize_image(self, event):
        new_width = event.width
        new_height = event.height
        self.image = self.img_copy.resize((new_width, new_height), Image.LANCZOS)
        self.background_image = ImageTk.PhotoImage(self.image)
        self.background.create_image(0, 0, image=self.background_image, anchor="nw")

        s_width = new_width - 30

        if self.entry_4 is not None:
            self.entry_4.destroy()

        self.entry_4_text = customtkinter.StringVar(self)
        self.entry_4 = customtkinter.CTkEntry(
            master=self,
            width=s_width,
            height=30,
            border_color="#080808",
            corner_radius=2,
            placeholder_text_color="#ffffff",
            textvariable=self.entry_4_text,
        )
        self.entry_4.insert(0, self.lua_placeholder)
        self.entry_4.configure(state="disabled")
        self.entry_4.place(relx=0.5, rely=0.3, anchor="c")

        self.background.create_text(
            20,
            new_height / 4 - 130,
            text="Loot List Manager",
            font=("Impact", 50),
            fill="Gray1",
            anchor="w",
        )
        self.background.create_text(
            20,
            new_height / 4 - 10,
            text="Lootlist.lua File Path",
            font=("Impact", 22),
            fill="Gray1",
            anchor="w",
        )
        self.background.create_text(
            20,
            new_height / 2 - 40,
            text="Google Spreadsheet Information",
            font=("Impact", 22),
            fill="Gray1",
            anchor="w",
        )


class LootListGUI:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.app_config = self.config_manager.load()
        self.sheets_client = GoogleSheetsClient()
        self.core = LootListManagerCore(self.sheets_client)

        self.root = customtkinter.CTk()
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")
        self.root.iconbitmap(ICON_PATH)
        self.root.title("Loot List Manager")
        self.root.geometry("900x700")
        self.root.minsize(900, 700)

        self.running = False
        self.progressbar = None
        self.lua_path_current = self.app_config.lua_path

        self.background_frame = BackgroundFrame(
            self.root,
            lua_placeholder=self._lua_placeholder_text(),
        )
        self.background_frame.pack(fill=BOTH, expand=YES)

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _lua_placeholder_text(self) -> str:
        if self.app_config.lua_path == "/":
            return DEFAULT_LUA_PLACEHOLDER
        return self.app_config.lua_path

    def _select_file(self):
        filetypes = (("Lua files", "*.lua"), ("All files", "*.*"))
        filename = fd.askopenfilename(
            title="Loot List variable file location",
            initialdir=os.path.dirname(self.app_config.lua_path)
            if self.app_config.lua_path not in ("/", DEFAULT_LUA_PLACEHOLDER)
            else "/",
            filetypes=filetypes,
        )
        if filename:
            self.lua_path_current = filename
            entry = self.background_frame.entry_4
            entry.configure(state="normal")
            entry.delete(0, END)
            entry.insert(0, filename)
            entry.configure(state="disabled")

    def _validate_inputs(self, on_fail=None):
        lua_path = self.lua_path_current
        if not lua_path or lua_path == DEFAULT_LUA_PLACEHOLDER:
            if on_fail:
                on_fail()
            showerror(
                title="Loot List Manager Error",
                message="Error: No file path selected!",
            )
            return None

        spreadsheet_id = self.entry_1_text.get()
        if not spreadsheet_id or spreadsheet_id == DEFAULT_SHEET_ID_PLACEHOLDER:
            if on_fail:
                on_fail()
            showerror(
                title="Loot List Manager Error",
                message="Error: No Spreadsheet ID entered!",
            )
            return None

        sheet_name = self.entry_2_text.get()
        sheet_range = self.entry_3_text.get()
        if not sheet_name or sheet_name == DEFAULT_SHEET_NAME_PLACEHOLDER:
            if on_fail:
                on_fail()
            showerror(
                title="Loot List Manager Error",
                message="Error: No Sheet Name entered!",
            )
            return None

        if not sheet_range or sheet_range == DEFAULT_RANGE_PLACEHOLDER:
            if on_fail:
                on_fail()
            showerror(
                title="Loot List Manager Error",
                message="Error: No Range entered!",
            )
            return None

        ranges = [f"{sheet_name}!{sheet_range}"]
        return spreadsheet_id, ranges, lua_path

    def _before_download(self):
        if not self.sheets_client.get_service():
            return
        validated = self._validate_inputs()
        if not validated:
            return
        spreadsheet_id, ranges, lua_path = validated
        if askyesno(
            title="Loot List Manager",
            message="Download the spreadsheet to the Loot List addon?",
        ):
            if self.core.download_to_lua(spreadsheet_id, ranges, lua_path):
                showinfo(
                    title="Loot List Manager",
                    message=(
                        "You have downloaded the Google spreadsheet and overwritten "
                        "the Lootlist.lua addon."
                    ),
                )

    def _before_manual_update(self):
        if not self.sheets_client.get_service():
            return
        validated = self._validate_inputs()
        if not validated:
            return
        spreadsheet_id, ranges, lua_path = validated
        if askyesno(
            title="Loot List Manager",
            message="Manually update the spreadsheet from the addon?",
        ):
            if self.core.update_from_lua(spreadsheet_id, ranges, lua_path):
                showinfo(
                    title="Loot List Manager",
                    message=(
                        "You have updated the Google spreadsheet from the Lootlist.lua addon."
                    ),
                )

    def _before_live_update(self):
        if not self.sheets_client.get_service():
            return
        validated = self._validate_inputs()
        if not validated:
            return
        _, _, lua_path = validated

        self.running = True
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(LIVE_UPDATE_CACHE, "w", encoding="utf-8") as f:
            f.write(str(os.stat(lua_path).st_mtime))

        self.button_live.configure(text="Click to Stop!", command=self._on_stop_live)
        self.progressbar = customtkinter.CTkProgressBar(
            master=self.root,
            mode="indeterminate",
        )
        self.progressbar.place(
            in_=self.background_frame,
            relx=0.99,
            rely=0.92,
            anchor="se",
        )
        self.progressbar.start()
        self.root.after(1000, self._live_update_loop)

    def _live_update_loop(self):
        validated = self._validate_inputs(on_fail=self._on_stop_live)
        if not validated:
            return
        spreadsheet_id, ranges, lua_path = validated

        if not self.running:
            return

        with open(LIVE_UPDATE_CACHE, "r", encoding="utf-8") as f:
            cached_stamp = f.readline().strip()

        current_stamp = str(os.stat(lua_path).st_mtime)
        if current_stamp != cached_stamp:
            with open(LIVE_UPDATE_CACHE, "w", encoding="utf-8") as f:
                f.write(current_stamp)
            if not self.core.update_from_lua(spreadsheet_id, ranges, lua_path):
                self._on_stop_live()
                return

        self.root.after(1000, self._live_update_loop)

    def _on_stop_live(self):
        self.running = False
        if self.progressbar:
            self.progressbar.destroy()
            self.progressbar = None
        if os.path.exists(LIVE_UPDATE_CACHE):
            os.remove(LIVE_UPDATE_CACHE)
        self.button_live.configure(text="Live Update", command=self._before_live_update)
        showinfo(title="Loot List Manager", message="Live Update is now off")

    def _build_ui(self):
        # File path button
        open_button = customtkinter.CTkButton(
            self.background_frame,
            corner_radius=1,
            width=20,
            height=20,
            text="Choose File Path",
            font=("Helvetica", 12),
            fg_color="#706f6f",
            hover_color="#3d3d3d",
            command=self._select_file,
        )
        open_button.place(
            in_=self.background_frame,
            relx=0.923,
            rely=0.3,
            anchor="c",
        )

        # Buttons
        self.button_live = customtkinter.CTkButton(
            master=self.root,
            text="Live Update",
            corner_radius=2,
            font=("Helvetica", 18),
            fg_color="#3d3d3d",
            hover_color="#706f6f",
            command=self._before_live_update,
        )
        self.button_live.place(
            in_=self.background_frame,
            relx=0.99,
            rely=0.99,
            anchor="se",
        )
        create_tooltip(
            self.button_live,
            text="Live update the Google Spreadsheet from the Lootlist.lua addon.",
        )

        button_manual = customtkinter.CTkButton(
            master=self.root,
            text="Manual Update",
            corner_radius=2,
            font=("Helvetica", 18),
            fg_color="#3d3d3d",
            hover_color="#706f6f",
            command=self._before_manual_update,
        )
        button_manual.place(
            in_=self.background_frame,
            relx=0.25,
            rely=0.99,
            anchor="s",
        )
        create_tooltip(
            button_manual,
            text="Manually update the Google Spreadsheet from the Lootlist.lua addon.",
        )

        button_download = customtkinter.CTkButton(
            master=self.root,
            text="Download",
            corner_radius=2,
            font=("Helvetica", 18),
            fg_color="#3d3d3d",
            hover_color="#706f6f",
            command=self._before_download,
        )
        button_download.place(
            in_=self.background_frame,
            relx=0.01,
            rely=0.99,
            anchor="sw",
        )
        create_tooltip(
            button_download,
            text="Download the Google spreadsheet and update the Lootlist.lua addon.",
        )

        # Spreadsheet inputs
        self.entry_1_text = customtkinter.StringVar(self.root)
        entry_1 = customtkinter.CTkEntry(
            master=self.root,
            width=500,
            height=25,
            border_color="#080808",
            corner_radius=2,
            textvariable=self.entry_1_text,
        )
        entry_1.insert(0, self.app_config.spreadsheet_id)
        entry_1.place(
            in_=self.background_frame,
            relx=0.01,
            rely=0.5,
            anchor="w",
        )
        create_tooltip(
            entry_1,
            text=(
                "Enter the ID of your spreadsheet.\n"
                "Example: 1bYkwLwDbMozOVZ01uXrK9xBJ-x24Mtrt1eKEVVC3JrE\n"
                "If your spreadsheet link is:\n"
                "https://docs.google.com/spreadsheets/d/1bYkwLwDbMozOVZ01uXrK9xBJ-x24Mtrt1eKEVVC3JrE"
            ),
        )

        self.entry_2_text = customtkinter.StringVar(self.root)
        entry_2 = customtkinter.CTkEntry(
            master=self.root,
            width=90,
            height=25,
            border_color="#080808",
            corner_radius=2,
            textvariable=self.entry_2_text,
        )
        entry_2.insert(0, self.app_config.sheet_name)
        entry_2.place(
            in_=self.background_frame,
            relx=0.01,
            rely=0.55,
            anchor="w",
        )
        create_tooltip(
            entry_2,
            text="Enter the name of the sheet on your Google spreadsheet. Default is Sheet1.",
        )

        self.entry_3_text = customtkinter.StringVar(self.root)
        entry_3 = customtkinter.CTkEntry(
            master=self.root,
            width=50,
            height=25,
            border_color="#080808",
            corner_radius=2,
            textvariable=self.entry_3_text,
        )
        entry_3.insert(0, self.app_config.sheet_range)
        entry_3.place(
            in_=self.background_frame,
            relx=0.01,
            rely=0.6,
            anchor="w",
        )
        create_tooltip(
            entry_3,
            text="Enter the first and last column letters of your spreadsheet, e.g. A:AZ (include the colon).",
        )

    def _on_closing(self):
        # Persist config
        self.config_manager.save(
            lua_path=self.lua_path_current if self.lua_path_current else None,
            spreadsheet_id=self.entry_1_text.get(),
            sheet_name=self.entry_2_text.get(),
            sheet_range=self.entry_3_text.get(),
        )
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = LootListGUI()
    app.run()
