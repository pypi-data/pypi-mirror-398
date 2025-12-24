import jp_tools


def main():
    jp_tools.download(
        url="https://raw.githubusercontent.com/gitinference/jp-tools/refs/heads/main/LICENSE",
        filename="DELETE.txt",
    )


if __name__ == "__main__":
    main()
