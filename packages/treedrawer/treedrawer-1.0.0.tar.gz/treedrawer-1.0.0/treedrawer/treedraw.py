def draw_tree(n):
    x = int(n)
    if x > 1:
        print()
        print("-" * (x * 2 + 1))
        print()

        print(" " * x + "*")
        for i in range(1, x + 1):
            print(" " * (x - i) + "*" * (2 * i + 1))
        for _ in range(x // 2 + 1):
            print(" " * x + "*")
    else:
        print("Choose a number higher than 2.")
