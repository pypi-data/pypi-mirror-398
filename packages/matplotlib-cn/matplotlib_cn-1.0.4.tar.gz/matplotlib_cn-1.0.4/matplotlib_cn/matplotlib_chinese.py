import os

from matplotlib import rcParams, font_manager


def enable_matplotlib_chinese(verbose=True):
    """
    Enable matplotlib to display Chinese characters and negative signs
    using SimHei.ttf in the same directory as this script.
    """

    def log(msg):
        if verbose:
            print(f"[matplotlib_cn] {msg}")

    # Locate SimHei.ttf in the same directory as this script
    font_path = os.path.join(os.path.dirname(__file__), "SimHei.ttf")
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file '{font_path}' not found. Ensure it exists in the same directory.")

    # Register the font
    font_manager.fontManager.addfont(font_path)
    font_prop = font_manager.FontProperties(fname=font_path)
    font_name = font_prop.get_name()

    # Configure matplotlib
    rcParams["font.sans-serif"] = [font_name]
    rcParams["axes.unicode_minus"] = False

    log(f"matplotlib enabled with Chinese font: {font_name} ")

# alias
plot_chinese = enable_matplotlib_chinese

