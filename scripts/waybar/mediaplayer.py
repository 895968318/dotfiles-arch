#!/usr/bin/env python3

import json
import sys
import logging
import traceback
from gi.repository import GLib

# --- 配置 ---
MAX_LENGTH = 40
PLAYER_ICONS = {
    "spotify": "",
    "firefox": "",
    "chrome": "",
    "vlc": "󰕼",
}
DEFAULT_ICON = "🎵"

# --- 日志配置 ---
logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG 级别以获取更多信息
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

def get_bus():
    """获取 D-Bus 连接"""
    try:
        import pydbus
        return pydbus.SessionBus()
    except ImportError:
        logging.error("pydbus module not found. Install with: pip install pydbus")
        return None
    except Exception as e:
        logging.error(f"Failed to connect to D-Bus: {e}")
        return None

def get_player_service_name(service_name):
    """从服务名获取播放器服务名"""
    if service_name.startswith("org.mpris.MediaPlayer2."):
        return service_name
    return f"org.mpris.MediaPlayer2.{service_name}"

def get_player_from_service(bus, service_name):
    """从服务名获取播放器对象"""
    try:
        full_service_name = get_player_service_name(service_name)
        player = bus.get(full_service_name, "/org/mpris/MediaPlayer2")
        logging.debug(f"Successfully connected to player: {service_name}")
        return player, service_name
    except Exception as e:
        logging.debug(f"Failed to connect to {service_name}: {e}")
        return None, None

def get_all_players(bus):
    """获取所有可用的媒体播放器"""
    players = []
    try:
        services = bus.dbus.ListNames()
        logging.debug(f"Found {len(services)} D-Bus services")
        
        for service in services:
            if service.startswith("org.mpris.MediaPlayer2."):
                player_name = service.split('.')[-1]
                player, name = get_player_from_service(bus, player_name)
                if player:
                    try:
                        status = player.PlaybackStatus
                        players.append((player, name, status))
                        logging.debug(f"Player {name}: {status}")
                    except Exception as e:
                        logging.debug(f"Failed to get status for {name}: {e}")
        
        logging.info(f"Found {len(players)} active media players")
        return players
    except Exception as e:
        logging.error(f"Failed to list players: {e}")
        return []

def choose_best_player(players):
    """选择最佳播放器（优先播放中的，其次暂停的）"""
    playing_players = [p for p in players if p[2] == "Playing"]
    if playing_players:
        return playing_players[0][0], playing_players[0][1]
    
    paused_players = [p for p in players if p[2] == "Paused"]
    if paused_players:
        return paused_players[0][0], paused_players[0][1]
    
    return None, None

def get_metadata_info(player):
    """从播放器获取元数据信息"""
    try:
        metadata = player.Metadata
        status = player.PlaybackStatus
        
        if not metadata or status == "Stopped":
            return None
        
        # 安全地获取艺术家信息
        artist_list = metadata.get("xesam:artist", [])
        if isinstance(artist_list, list) and artist_list:
            artist = artist_list[0]
        elif isinstance(artist_list, str):
            artist = artist_list
        else:
            artist = ""
        
        title = metadata.get("xesam:title", "")
        album = metadata.get("xesam:album", "")
        
        logging.debug(f"Metadata - Artist: {artist}, Title: {title}, Status: {status}")
        
        return {
            "artist": artist,
            "title": title,
            "album": album,
            "status": status
        }
    except Exception as e:
        logging.error(f"Failed to get metadata: {e}")
        return None

def format_display_text(info):
    """格式化显示文本"""
    if info["artist"] and info["title"]:
        text = f"{info['artist']} - {info['title']}"
    elif info["title"]:
        text = info["title"]
    elif info["artist"]:
        text = info["artist"]
    else:
        text = "Unknown Track"
    
    if len(text) > MAX_LENGTH:
        text = text[:MAX_LENGTH-1] + "…"
    
    return text

def get_player_icon(player_name):
    """获取播放器图标"""
    return PLAYER_ICONS.get(player_name.lower(), DEFAULT_ICON)

def main():
    """主函数，用于获取媒体信息并输出为 JSON"""
    try:
        logging.info("Starting media player script")
        
        # 获取 D-Bus 连接
        bus = get_bus()
        if not bus:
            print_json({})
            return
        
        # 获取所有播放器
        players = get_all_players(bus)
        if not players:
            logging.info("No media players found")
            print_json({})
            return
        
        # 选择最佳播放器
        best_player, player_name = choose_best_player(players)
        if not best_player:
            logging.info("No active players found")
            print_json({})
            return
        
        # 获取元数据
        info = get_metadata_info(best_player)
        if not info:

            logging.info("No valid metadata found")
            print_json({})
            return
        
        # 格式化输出
        text = format_display_text(info)
        icon = get_player_icon(player_name)
        
        tooltip = f"{info['artist']} - {info['title']}"
        if info['album']:
            tooltip += f"\nAlbum: {info['album']}"
        tooltip += f"\nStatus: {info['status']}"
        tooltip += f"\nPlayer: {player_name}"
        
        result = {
            "text": text,
            "tooltip": tooltip,
            "class": f"player-{player_name.lower()}",
            "alt": player_name,
            "percentage": 0  # 可以根据需要添加进度信息
        }
        
        # 如果需要在 Waybar 配置中使用图标，可以添加
        if icon != DEFAULT_ICON:
            result["icon"] = icon
        
        logging.info(f"Output: {text} ({info['status']})")
        print_json(result)

    except KeyboardInterrupt:
        logging.info("Script interrupted by user")
        print_json({})
    except Exception as e:
        logging.error(f"Unexpected error in main(): {e}")
        logging.error(f"Traceback:\n{traceback.format_exc()}")
        print_json({})

def print_json(data):
    """安全地打印 JSON 到标准输出"""
    try:
        output = json.dumps(data, ensure_ascii=False)
        sys.stdout.write(output + "\n")
        sys.stdout.flush()
    except Exception as e:
        logging.error(f"Failed to output JSON: {e}")
        sys.stdout.write("{}\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()