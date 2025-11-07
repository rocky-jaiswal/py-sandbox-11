from mod_a.utils import add


def work(a: int, b: int) -> int:
    return add(a, b)


def main():
    res = work(2, 18)
    print(res)
    return res


if __name__ == "__main__":
    main()
