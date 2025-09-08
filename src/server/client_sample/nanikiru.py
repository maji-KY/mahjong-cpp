from typing import Annotated

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("麻雀何切る問題。東場で、あなたは東家固定です。牌はmpsz形式(m=萬子, p=筒子, s=索子, z=字牌, 0=赤)で表現します。")

@mcp.tool()
def get_hand(
    include_jihai: Annotated[bool, "字牌を含めるかどうか"] = False,
    low_shanten: Annotated[bool, "低シャンテンのみ生成"] = True,
) -> str:
    """
    新しく手牌を開きます。手牌はmpsz形式で、ドラ表示牌も含みます。
    何切る問題では実践的な低いシャンテン数の手牌を生成するため、基本的に字牌を含めないで生成します。
    """
    import subprocess
    import os
    # このファイルのディレクトリに移動
    dir_path = os.path.dirname(os.path.abspath(__file__))
    # コマンドを構築
    cmd = ["uv", "run", "client.py", "-g"]
    if not include_jihai:
        cmd.append("--no-jihai")
    if low_shanten:
        cmd.append("--low-shanten")
    # コマンドを実行
    result = subprocess.run(cmd, cwd=dir_path, capture_output=True, text=True)
    # 標準出力を返す
    return result.stdout.strip()


@mcp.tool()
def analyze_hand(
    input_hand: Annotated[str, "手牌のmpsz形式文字列"],
    dora_indicator: Annotated[str, "ドラ表示牌(一つ)のmpsz形式文字列(1mや0sや4zなど)"],
) -> str:
    """与えられた手牌を分析し、最適な打牌をおすすめ順に返します。"""
    import subprocess
    import os
    # このファイルのディレクトリに移動
    dir_path = os.path.dirname(os.path.abspath(__file__))
    # dora_indicatorがint型なのでstrに変換
    dora_str = str(dora_indicator)
    # コマンドを実行
    result = subprocess.run([
        "uv", "run", "client.py",
        "-a", input_hand,
        "-d", dora_str
    ], cwd=dir_path, capture_output=True, text=True)
    # 標準出力を返す
    return result.stdout.strip()


if __name__ == "__main__":
    mcp.run(transport="stdio")