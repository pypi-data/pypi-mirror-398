def sample_rows(df, n=None, frac=None, random_state=42, guidance="on"):
    df2 = df.sample(n=n, frac=frac, random_state=random_state)

    if guidance == "on":
        print(f"🎲 Sampled rows: {len(df2)}")

    return df2


def shuffle_rows(df, random_state=42, guidance="on"):
    df2 = df.sample(frac=1, random_state=random_state).reset_index(drop=True)

    if guidance == "on":
        print(f"🔀 Shuffled dataset (rows randomized)")

    return df2
