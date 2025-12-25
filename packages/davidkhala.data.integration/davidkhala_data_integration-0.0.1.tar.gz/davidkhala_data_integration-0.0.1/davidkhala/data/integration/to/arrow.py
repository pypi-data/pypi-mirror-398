from pyarrow import Table, BufferOutputStream


def fromPandas(df: "pandas.DataFrame") -> Table:
    return Table.from_pandas(df)


def bytesFrom(t: Table) -> bytes:
    buffer = BufferOutputStream()
    from pyarrow.parquet import write_table
    write_table(table, buffer)
    return buffer.getvalue().to_pybytes()
