import json
import random
import argparse

import requests
from const import *

from mahjong import from_mpsz


def create_yama(enable_reddora=True):
    """
    麻雀の山（136枚）を作成する
    
    Args:
        enable_reddora: 赤ドラを有効にするか
    
    Returns:
        list: 山の牌のリスト（Tile定数のリスト）
    """
    yama = []
    
    # 萬子 (0-8)
    for tile in range(Tile.Manzu1, Tile.Manzu9 + 1):
        if tile == Tile.Manzu5 and enable_reddora:
            # 赤ドラ有効時: 通常5萬を3枚、赤5萬を1枚
            yama.extend([tile] * 3)
            yama.append(Tile.RedManzu5)
        else:
            yama.extend([tile] * 4)
    
    # 筒子 (9-17)
    for tile in range(Tile.Pinzu1, Tile.Pinzu9 + 1):
        if tile == Tile.Pinzu5 and enable_reddora:
            # 赤ドラ有効時: 通常5筒を3枚、赤5筒を1枚
            yama.extend([tile] * 3)
            yama.append(Tile.RedPinzu5)
        else:
            yama.extend([tile] * 4)
    
    # 索子 (18-26)
    for tile in range(Tile.Souzu1, Tile.Souzu9 + 1):
        if tile == Tile.Souzu5 and enable_reddora:
            # 赤ドラ有効時: 通常5索を3枚、赤5索を1枚
            yama.extend([tile] * 3)
            yama.append(Tile.RedSouzu5)
        else:
            yama.extend([tile] * 4)
    
    # 字牌 (27-33)
    for tile in range(Tile.East, Tile.Red + 1):
        yama.extend([tile] * 4)
    
    return yama


def tiles_to_mpsz(tiles):
    """
    牌のリストをMPSZ記法の文字列に変換する
    
    Args:
        tiles: 牌のリスト（Tile定数のリスト）
    
    Returns:
        str: MPSZ記法の文字列
    """
    # 牌を種類ごとに分類
    manzu = []
    pinzu = []
    souzu = []
    jihai = []
    
    for tile in sorted(tiles):
        if Tile.Manzu1 <= tile <= Tile.Manzu9:
            manzu.append(str(tile - Tile.Manzu1 + 1))
        elif Tile.Pinzu1 <= tile <= Tile.Pinzu9:
            pinzu.append(str(tile - Tile.Pinzu1 + 1))
        elif Tile.Souzu1 <= tile <= Tile.Souzu9:
            souzu.append(str(tile - Tile.Souzu1 + 1))
        elif Tile.East <= tile <= Tile.Red:
            jihai.append(str(tile - Tile.East + 1))
        elif tile == Tile.RedManzu5:
            manzu.append("0")
        elif tile == Tile.RedPinzu5:
            pinzu.append("0")
        elif tile == Tile.RedSouzu5:
            souzu.append("0")
    
    # カスタムソート関数：0（赤ドラ）を5の直後に配置
    def sort_mpsz(chars):
        def sort_key(char):
            if char == "0":
                return (5, 1)  # 5の直後
            else:
                return (int(char), 0)  # 通常の数字
        return "".join(sorted(chars, key=sort_key))
    
    # MPSZ記法の文字列を構築
    result = ""
    if manzu:
        result += sort_mpsz(manzu) + "m"
    if pinzu:
        result += sort_mpsz(pinzu) + "p"
    if souzu:
        result += sort_mpsz(souzu) + "s"
    if jihai:
        result += "".join(sorted(jihai)) + "z"
    
    return result


def hand_to_display(hand):
    """
    手牌のリストをDisplay表記（emoji）に変換する
    
    Args:
        hand: 手牌のリスト（Tile定数のリスト）
    
    Returns:
        str: 手牌をemoji表記で表現した文字列
    """
    if not hand:
        return ""
    
    # カスタムソート関数：赤ドラを対応する通常の5牌の直後に配置
    def sort_key(tile):
        if tile == Tile.RedManzu5:
            return (Tile.Manzu5, 1)  # 通常の5萬の直後
        elif tile == Tile.RedPinzu5:
            return (Tile.Pinzu5, 1)  # 通常の5筒の直後
        elif tile == Tile.RedSouzu5:
            return (Tile.Souzu5, 1)  # 通常の5索の直後
        else:
            return (tile, 0)  # 通常の牌
    
    # 手牌をカスタムソートしてから表示
    sorted_hand = sorted(hand, key=sort_key)
    emoji_list = [Tile.Display[tile] for tile in sorted_hand]
    return "".join(emoji_list)


def generate_random_hand(enable_reddora=True):
    """
    ランダムな14枚の手牌とドラ表示牌を生成する
    
    Args:
        enable_reddora: 赤ドラを有効にするか
    
    Returns:
        tuple: (hand_mpsz_string, dora_indicator_tile)
        - hand_mpsz_string: 14枚の手牌をMPSZ記法で表現した文字列
        - dora_indicator_tile: 山から取ったドラ表示牌（Tile定数）
    """
    # 山を作成してシャッフル
    yama = create_yama(enable_reddora)
    random.shuffle(yama)
    
    # 手牌14枚を取る
    hand_tiles = yama[:14]
    
    # ドラ表示牌を1枚取る（手牌の後から）
    dora_indicator = yama[14]
    
    # 手牌をMPSZ記法に変換
    hand_mpsz = tiles_to_mpsz(hand_tiles)
    
    return hand_mpsz, dora_indicator


def is_agari_hand(hand, dora_indicator):
    """
    手牌が和了形かどうかをサーバーに問い合わせてチェックする
    
    Args:
        hand: 手牌のリスト（Tile定数のリスト）
        dora_indicator: ドラ表示牌
    
    Returns:
        bool: 和了形の場合True、そうでなければFalse
    """
    req_data = {
        "enable_reddora": True,
        "enable_uradora": True,
        "enable_shanten_down": True,
        "enable_tegawari": True,
        "enable_riichi": True,
        "round_wind": Tile.East,
        "dora_indicators": [dora_indicator],
        "hand": hand,
        "melds": [],
        "seat_wind": Tile.East,
        "version": "0.9.1",
    }

    try:
        res = requests.post(
            "http://localhost:50000",
            json.dumps(req_data),
            headers={"Content-Type": "application/json"},
        )
        res_data = res.json()
        
        if not res_data["success"]:
            return False
            
        result = res_data["response"]
        return result.get("agari", False)
    except:
        return False


def generate_non_agari_hand(enable_reddora=True, max_retries=1):
    """
    和了形以外の手牌を生成する（最大1回まで再試行）
    
    Args:
        enable_reddora: 赤ドラを有効にするか
        max_retries: 最大再試行回数
    
    Returns:
        tuple: (hand_mpsz, dora_indicator) 和了形以外の手牌とドラ表示牌、失敗時は(None, None)
    """
    for attempt in range(max_retries + 1):
        hand_mpsz, dora_indicator = generate_random_hand(enable_reddora)
        hand = from_mpsz(hand_mpsz)
        
        if not is_agari_hand(hand, dora_indicator):
            return hand_mpsz, dora_indicator
        
        if attempt < max_retries:
            print(f"和了形が生成されました。再生成します... (試行{attempt + 1}/{max_retries + 1})")
    
    # 最大試行回数に達した場合、最後に生成された手牌を返す（和了形でも）
    print("警告: 最大試行回数に達しました。和了形の可能性がある手牌を返します。")
    return hand_mpsz, dora_indicator


def analyze_hand(hand_mpsz, dora_indicator_mpsz="1z"):
    """
    指定された手牌を分析して結果を表示する
    
    Args:
        hand_mpsz: 手牌のMPSZ記法文字列
        dora_indicator_mpsz: ドラ表示牌のMPSZ記法文字列（デフォルト: 東）
    """
    try:
        hand = from_mpsz(hand_mpsz)
        
        # ドラ表示牌をMPSZ記法から変換
        dora_indicator = from_mpsz(dora_indicator_mpsz)[0] if dora_indicator_mpsz else Tile.East
        
        print(f"手牌: {hand_mpsz}")
        print(f"手牌: {hand_to_display(hand)}")
        print(f"ドラ表示牌: {Tile.Name[dora_indicator]} {Tile.Display[dora_indicator]}")
        
    except Exception as e:
        print(f"エラー: 手牌の解析に失敗しました。({e})")
        return
    
    req_data = {
        "enable_reddora": True,
        "enable_uradora": True,
        "enable_shanten_down": True,
        "enable_tegawari": True,
        "enable_riichi": True,
        "round_wind": Tile.East,
        "dora_indicators": [dora_indicator],
        "hand": hand,
        "melds": [],
        "seat_wind": Tile.East,
        "version": "0.9.1",
    }

    try:
        res = requests.post(
            "http://localhost:50000",
            json.dumps(req_data),
            headers={"Content-Type": "application/json"},
        )
        res_data = res.json()
        
        if not res_data["success"]:
            print(f"Failed to calculate. ({res_data['err_msg']})")
            return

        result = res_data["response"]
        if result.get("agari"):
            print(f"和了です")
            print_points(result)
            return

        print_result(result)
        
    except Exception as e:
        print(f"エラー: サーバーとの通信に失敗しました。({e})")


def random_hand_calc():
    # ランダムな手牌とドラ表示牌を生成
    hand_mpsz, dora_indicator = generate_random_hand(enable_reddora=True)
    print(f"Generated hand: {hand_mpsz}")
    print(f"Dora indicator: {Tile.Name[dora_indicator]}")
    
    # 例: 222567m34p33667s北（固定手牌を使いたい場合）
    # hand = from_mpsz("222567m34p33667s4z")
    
    # 13枚手牌でエラーハンドリングをテスト
    # hand = from_mpsz("147m258p369s1234z")  # 13枚の手牌
    
    # ランダム生成した手牌を使用
    hand = from_mpsz(hand_mpsz)
    print(hand)
    print(f"手牌: {hand_to_display(hand)}")

    req_data = {
        "enable_reddora": True,
        "enable_uradora": True,
        "enable_shanten_down": True,
        "enable_tegawari": True,
        "enable_riichi": True,
        "round_wind": Tile.East,
        "dora_indicators": [dora_indicator],  # 生成したドラ表示牌を使用
        "hand": hand,
        "melds": [],
        "seat_wind": Tile.East,
        "version": "0.9.1",
    }

    # Send request to the server
    res = requests.post(
        "http://localhost:50000",
        json.dumps(req_data),
        headers={"Content-Type": "application/json"},
    )
    res_data = res.json()
    # print(res_data)

    # Print result.
    if not res_data["success"]:
        print(f"Failed to calculate. ({res_data['err_msg']})")
        return

    result = res_data["response"]
    if result.get("agari"):
        print(f"和了です")
        print_points(result)
        return

    print_result(result)


def print_points(ret):
    print(json.dumps(ret))
    for yaku in ret["yaku_list"]:
        print(f"{yaku['name']} {yaku['han']} 翻")
    if ret["han"] == 0:
        print("役満")
    else:
        print(f"{ret["han"]} 翻 {ret["fu"]} 符")
    print(f"{ret["score"]} 点")
    print(ret.get("detail"))

def print_result(ret):
    # print(json.dumps(ret))
    
    # 手牌枚数をチェック
    hand_size = ret["config"]["num_tiles"]
    if hand_size != 14:
        print(f"エラー: 手牌が{hand_size}枚です。14枚である必要があります。")
        return
    
    # シャンテン数を取得
    shanten = ret["shanten"]["all"]
    
    # 統計情報を取得
    stats = ret["stats"]
    t_min = ret["config"]["t_min"]
    
    # 無効な打牌候補をチェック
    invalid_tiles = [stat for stat in stats if stat["tile"] == -1]
    if invalid_tiles:
        print("警告: 無効な打牌候補が検出されました。手牌の状態を確認してください。")
        return
    
    # ソート条件を決定
    if shanten >= 4:
        # 4シャンテン以上：シャンテン戻しでない打牌を有効牌総数降順でソート
        # まずシャンテン戻しでない打牌のみを抽出
        non_backtrack_stats = [stat for stat in stats if stat["shanten"] <= shanten]
        sorted_stats = sorted(non_backtrack_stats, key=lambda x: sum([tile["count"] for tile in x["necessary_tiles"]]), reverse=True)
        print("=== 打牌候補（有効牌総数順） ===")
    else:
        # 3シャンテン以下：期待値降順でソート
        sorted_stats = sorted(stats, key=lambda x: x["exp_score"][t_min] if ret["config"]["calc_stats"] else 0, reverse=True)
        print("=== 打牌候補（期待値順） ===")
    
    # 打牌ごとに情報を表示（上位3択のみ）
    for i, stat in enumerate(sorted_stats[:3], 1):
        tile_id = stat["tile"]
            
        tile = Tile.Name[tile_id]
        tile_emoji = Tile.Display[tile_id]
        num_types = len(stat["necessary_tiles"])
        num_tiles = sum([x["count"] for x in stat["necessary_tiles"]])
        tiles = "".join(
            f"{Tile.Name[x['tile']]}({x['count']}枚) " for x in stat["necessary_tiles"]
        )
        
        print(f"\n{i}. 打牌: {tile} {tile_emoji}")
        print(f"   有効牌: {num_types}種類 {num_tiles}枚")
        print(f"   詳細: {tiles}")
        
        # 確率統計が計算されている場合のみ表示
        if ret["config"]["calc_stats"] and len(stat["tenpai_prob"]) > t_min:
            tenpai_prob = stat["tenpai_prob"][t_min]
            win_prob = stat["win_prob"][t_min]
            exp_score = stat["exp_score"][t_min]
            print(f"   聴牌確率: {tenpai_prob:.2%}")
            print(f"   和了確率: {win_prob:.2%}")
            print(f"   期待値: {exp_score:.2f}点")

    
    print("\n=== 情報 ===")
    print(
        f"向聴数: {ret['shanten']['all']} "
        f"(通常手: {ret['shanten']['regular']}, "
        f"七対子: {ret['shanten']['seven_pairs']}, "
        f"国士無双: {ret['shanten']['thirteen_orphans']})"
    )

    def time_to_str(us):
        if us < 1000:
            return f"{us} us"
        ms = us / 1000
        if ms < 1000:
            return f"{ms:.2f} ms"
        s = ms / 1000

        return f"{s:.2f} s"

    print(f"計算時間: {time_to_str(ret['time'])}")
    print(f"探索数: {ret['searched']} 手")


def main():
    parser = argparse.ArgumentParser(description='麻雀何切る問題ツール')
    
    # 互いに排他的なグループを作成
    mode_group = parser.add_mutually_exclusive_group()
    
    mode_group.add_argument(
        '-g', '--generate',
        action='store_true',
        help='和了形以外の手牌をMPSZ形式で生成する'
    )
    
    mode_group.add_argument(
        '-a', '--analyze',
        type=str,
        metavar='MPSZ',
        help='指定された手牌（MPSZ形式）を分析する'
    )
    
    parser.add_argument(
        '-d', '--dora',
        type=str,
        default='1z',
        metavar='DORA_MPSZ',
        help='ドラ表示牌（MPSZ形式、デフォルト: 1z=東）'
    )
    
    args = parser.parse_args()
    
    if args.generate:
        # 生成モード: 和了形以外の手牌を生成
        result = generate_non_agari_hand(enable_reddora=True, max_retries=1)
        if result[0]:  # hand_mpsz が None でない場合
            hand_mpsz, dora_indicator = result
            print(f"生成された手牌: {hand_mpsz}")
            print(f"ドラ表示牌: {Tile.Name[dora_indicator]} {Tile.Display[dora_indicator]}")
            # emoji表示も追加
            hand = from_mpsz(hand_mpsz)
            print(f"手牌Emoji: {hand_to_display(hand)}")
        else:
            print("エラー: 和了形以外の手牌の生成に失敗しました。")
            
    elif args.analyze:
        # 分析モード: 指定された手牌を分析
        analyze_hand(args.analyze, args.dora)
        
    else:
        # デフォルトモード: 既存の動作（ランダム生成+分析）
        print("=== ランダム手牌生成+分析モード ===")
        random_hand_calc()


if __name__ == "__main__":
    main()
