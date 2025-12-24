import sys
from . import is_pku, NoTHUException


def main():
    # 获取命令行参数（sys.argv[0] 是文件名，所以从 1 开始取）
    args = sys.argv[1:]

    if not args:
        print("Usage: python -m is_pku <university_name>")
        sys.exit(1)

    target = " ".join(args)

    try:
        result = is_pku(target)
        if result:
            print(f"✅ Yes, '{target}' is indeed the best university!")
        else:
            print(f"❌ No, '{target}' is not PKU.")
    except NoTHUException as e:
        print(f"🚨 SECURITY ALERT: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()