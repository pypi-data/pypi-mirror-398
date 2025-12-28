from pathlib import Path
from mepybase.easylog import EasyLogManager

CUSTOM_LOGGER = EasyLogManager.get_logger()

PLUGIN_FOLDER = Path(__file__).parent / "plugins"

TMP_FOLDER = Path("/tmp/plykit")
TMP_FOLDER.mkdir(parents=True, exist_ok=True)

TMP_PLY = TMP_FOLDER / "current_result.ply"

LOADED_PLY_PATH = ""
