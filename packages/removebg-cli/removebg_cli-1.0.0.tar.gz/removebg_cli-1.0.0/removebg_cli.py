#!/usr/bin/env python3
"""removebg-cli - 智能图片背景移除工具"""
import argparse, os, sys, time
import requests
from rich.console import Console
from rich.panel import Panel

API_URL = "https://api.remove.bg/v1.0/removebg"
SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")
MAX_RETRIES = 3
LOW_CREDITS_WARN = 10

console = Console()

def log_info(msg): console.print(f"[blue]ℹ[/blue] {msg}")
def log_success(msg): console.print(f"[green]✓[/green] {msg}")
def log_error(msg): console.print(f"[red]✗[/red] {msg}")
def log_warn(msg): console.print(f"[yellow]⚠[/yellow] {msg}")

def get_api_key():
    key = os.environ.get("REMOVE_BG_API_KEY")
    if not key:
        log_error("请设置环境变量 REMOVE_BG_API_KEY")
        console.print("\n[dim]设置方法:[/dim]")
        console.print("  export REMOVE_BG_API_KEY='你的API密钥'")
        console.print("  # 或添加到 ~/.zshrc 或 ~/.bashrc")
        console.print("\n[dim]获取API Key:[/dim] https://www.remove.bg/dashboard#api-key")
        sys.exit(1)
    return key

def is_url(s):
    return s.startswith(("http://", "https://"))

def validate_source(source):
    if is_url(source):
        return True
    if not os.path.exists(source):
        log_error(f"文件不存在: {source}")
        return False
    if not os.path.isfile(source):
        log_error(f"不是文件: {source}")
        return False
    ext = os.path.splitext(source)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        log_error(f"不支持的格式: {ext} (支持: {', '.join(SUPPORTED_FORMATS)})")
        return False
    size_mb = os.path.getsize(source) / (1024 * 1024)
    if size_mb > 22:
        log_error(f"文件过大: {size_mb:.1f}MB (最大22MB)")
        return False
    return True

def get_output_path(source, output, fmt):
    ext = "png" if fmt in ["auto", "png"] else fmt
    if output:
        return output
    if is_url(source):
        from urllib.parse import urlparse, unquote
        path = urlparse(source).path
        base = os.path.splitext(os.path.basename(unquote(path)))[0] or "output"
        return f"{base}-nobg.{ext}"
    else:
        dir_path = os.path.dirname(os.path.abspath(source))
        base = os.path.splitext(os.path.basename(source))[0]
        return os.path.join(dir_path, f"{base}-nobg.{ext}")

def check_remaining_credits(api_key):
    """检查剩余额度，低于阈值时警告"""
    try:
        resp = requests.get("https://api.remove.bg/v1.0/account", headers={"X-Api-Key": api_key}, timeout=5)
        if resp.status_code == 200:
            d = resp.json()["data"]["attributes"]
            free_calls = d["api"]["free_calls"]
            total = d["credits"]["total"]
            remaining = free_calls + total
            if remaining <= LOW_CREDITS_WARN:
                log_warn(f"剩余额度不足: {remaining} (免费{free_calls} + credits{total})")
            return remaining
    except:
        pass
    return None

def remove_bg(api_key, source, output=None, size="auto", fmt="auto", bg_color=None, crop=False, shadow=False):
    if not validate_source(source):
        sys.exit(1)
    
    headers = {"X-Api-Key": api_key}
    data = {"size": size, "format": fmt if fmt != "auto" else "png", "type": "auto"}
    files = None
    
    if crop: data["crop"] = "true"
    if shadow: data["add_shadow"] = "true"
    if bg_color: data["bg_color"] = bg_color
    
    log_info(f"处理中: {source}")
    
    if is_url(source):
        data["image_url"] = source
    else:
        files = {"image_file": open(source, "rb")}
    
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(API_URL, headers=headers, data=data, files=files, timeout=60)
            if resp.status_code == 200:
                break
            elif resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 10))
                log_warn(f"请求过快，{retry_after}秒后重试...")
                time.sleep(retry_after)
                if files: files["image_file"].seek(0)
                continue
            elif resp.status_code >= 500 and attempt < MAX_RETRIES - 1:
                wait = 2 ** attempt
                log_warn(f"服务器错误，{wait}秒后重试...")
                time.sleep(wait)
                if files: files["image_file"].seek(0)
                continue
            else:
                break
        except requests.Timeout:
            log_warn(f"请求超时，重试中... ({attempt + 1}/{MAX_RETRIES})")
            if files: files["image_file"].seek(0)
            continue
        except requests.RequestException as e:
            log_error(f"网络错误: {e}")
            if files: files["image_file"].close()
            sys.exit(1)
    
    if files: files["image_file"].close()
    
    if resp.status_code == 200:
        out_path = get_output_path(source, output, fmt)
        out_dir = os.path.dirname(out_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir)
        with open(out_path, "wb") as f:
            f.write(resp.content)
        credits = resp.headers.get("X-Credits-Charged", "?")
        log_success(f"已保存: {out_path} (消耗 {credits} credits)")
        # 处理后检查剩余额度
        check_remaining_credits(api_key)
    else:
        try:
            err = resp.json().get("errors", [{}])[0].get("title", resp.text)
        except:
            err = resp.text
        log_error(f"API错误 [{resp.status_code}]: {err}")
        sys.exit(1)

def check_account(api_key):
    log_info("查询账户信息...")
    try:
        resp = requests.get("https://api.remove.bg/v1.0/account", headers={"X-Api-Key": api_key}, timeout=10)
    except requests.RequestException as e:
        log_error(f"网络错误: {e}")
        sys.exit(1)
    
    if resp.status_code == 200:
        d = resp.json()["data"]["attributes"]
        c = d["credits"]
        free = d["api"]["free_calls"]
        total = c["total"]
        remaining = free + total
        
        status = "[green]充足[/green]" if remaining > LOW_CREDITS_WARN else "[red]不足[/red]"
        console.print(Panel(
            f"[bold]总 Credits:[/bold] {total}\n"
            f"  ├─ 订阅: {c['subscription']}\n"
            f"  └─ 按量: {c['payg']}\n"
            f"[bold]免费调用:[/bold] {free}/月\n"
            f"[bold]剩余额度:[/bold] {remaining} {status}",
            title="账户余额", border_style="green" if remaining > LOW_CREDITS_WARN else "red"))
    elif resp.status_code == 403:
        log_error("API Key 无效")
        sys.exit(1)
    else:
        log_error(f"查询失败: {resp.status_code}")
        sys.exit(1)

def main():
    p = argparse.ArgumentParser(
        prog="removebg",
        description="智能图片背景移除工具 (remove.bg API)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  removebg photo.jpg                  # 处理本地图片
  removebg https://example.com/a.jpg  # 处理网络图片 (自动识别URL)
  removebg photo.jpg -o result.png    # 指定输出文件名
  removebg photo.jpg -s full          # 高清输出 (最高25MP)
  removebg photo.jpg -b white         # 白色背景
  removebg photo.jpg -c               # 裁剪空白区域
  removebg --account                  # 查看API余额

环境变量:
  REMOVE_BG_API_KEY                   # 必须设置，获取: https://www.remove.bg/dashboard#api-key
""")
    p.add_argument("source", nargs="?", help="图片路径或URL (自动识别http://或https://开头为URL)")
    p.add_argument("-o", "--output", help="输出文件路径 (默认: 本地文件→同目录, URL→当前目录)")
    p.add_argument("-s", "--size", default="auto", choices=["auto", "preview", "full", "50MP"],
                   help="输出尺寸: auto=自动(默认), preview=0.25MP预览, full=25MP高清, 50MP=最高清晰度")
    p.add_argument("-f", "--format", default="auto", dest="fmt", choices=["auto", "png", "jpg", "webp", "zip"],
                   help="输出格式: auto/png=透明PNG(默认), jpg=无透明, webp=透明+小体积, zip=最快处理")
    p.add_argument("-b", "--bg", help="背景颜色: 颜色名(white)或十六进制(ff0000), 不设置则透明")
    p.add_argument("-c", "--crop", action="store_true", help="裁剪掉空白区域")
    p.add_argument("--shadow", action="store_true", help="添加阴影效果 (适合汽车/产品图)")
    p.add_argument("--account", action="store_true", help="查看API账户余额和免费额度")
    p.add_argument("-v", "--version", action="version", version="%(prog)s 1.0.0")
    
    args = p.parse_args()
    api_key = get_api_key()
    
    if args.account:
        return check_account(api_key)
    if not args.source:
        p.print_help()
        sys.exit(1)
    
    remove_bg(api_key, args.source, args.output, args.size, args.fmt, args.bg, args.crop, args.shadow)

if __name__ == "__main__":
    main()
