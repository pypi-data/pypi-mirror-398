import pandas as pd

def _guide(msg, guidance):
    if guidance == "on":
        print(msg)

def smart_merge(df1, df2, on, guidance="off"):
    """
    Automatically decides the best join type.

    Rules:
    - If both sides have duplicates → outer join
    - If df2 is lookup table → left join
    - If both sides unique → inner join
    """

    dup1 = df1[on].duplicated().any()
    dup2 = df2[on].duplicated().any()

    _guide("🧠 SMART MERGE STARTED", guidance)

    if not dup1 and not dup2:
        _guide("✨ Both keys unique → INNER JOIN chosen.", guidance)
        return df1.merge(df2, how="inner", on=on)

    if dup1 and not dup2:
        _guide("✨ df1 has duplicates, df2 is lookup → LEFT JOIN chosen.", guidance)
        return df1.merge(df2, how="left", on=on)

    if not dup1 and dup2:
        _guide("✨ df2 has duplicates, df1 is lookup → RIGHT JOIN chosen.", guidance)
        return df1.merge(df2, how="right", on=on)

    _guide("⚠️ Both sides have duplicates → FULL OUTER JOIN chosen.", guidance)
    return df1.merge(df2, how="outer", on=on)
