from pyarrow import Table, BufferOutputStream


def fromPandas(df: "pandas.DataFrame") -> Table:
    return Table.from_pandas(df)


def bytesFrom(table: Table) -> bytes:
    from pyarrow.parquet import write_table
    buffer = BufferOutputStream()
    write_table(table, buffer)
    return buffer.getvalue().to_pybytes()
