import sqlite3
import MySQLdb
from tqdm import tqdm
from contextlib import closing
import secrets as s

tcrd = s.tcrd


def dropTable(cursor, tableName):
    cursor.execute(f"""DROP TABLE IF EXISTS {tableName}""")


def main():
    localdb = sqlite3.connect('tinxapi/metadata.sqlite3')
    remotedb = MySQLdb.connect(host=tcrd['host'], user=tcrd['user'],
                               password=tcrd['password'], database="tcrd")

    try:
        with closing(localdb.cursor()) as localCursor:
            with closing(remotedb.cursor()) as remoteCursor:
                try:
                    print("Setting up Disease Metadata table")
                    disease_metadata(localCursor, remoteCursor)
                    print("Setting up Protein Metadata table")
                    protein_metadata(localCursor, remoteCursor)
                    print("Setting up Disease Ancestors Metadata table")
                    disease_ancestors_metadata(localCursor, remoteCursor)
                except Exception as err:
                    print(err)
    except Exception as err:
        print(err)

    localdb.commit()
    localdb.close()
    remotedb.close()


def disease_metadata(cursor, remoteCursor):
    tableName = 'tinx_disease_metadata'
    dropTable(cursor, tableName)
    cursor.execute(
        f"""
            CREATE TABLE IF NOT EXISTS {tableName}
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT, tinx_disease_id VARCHAR NOT NULL,
                num_important_targets INTEGER NOT NULL, category VARCHAR
            )
         """
    )
    query = """
        SELECT tinx_disease.doid as tinx_disease_id, COUNT(tinx_importance.doid) as num_important_targets
        FROM tinx_disease LEFT JOIN tinx_importance ON tinx_importance.doid = tinx_disease.doid
        GROUP BY tinx_disease.doid
    """
    remoteCursor.execute(query)

    for row in tqdm(remoteCursor.fetchall()):
        cursor.execute(f"INSERT INTO {tableName} (tinx_disease_id, num_important_targets) VALUES (?,?)", row)


def protein_metadata(cursor, remoteCursor):
    tableName = 'tinx_protein_metadata'
    dropTable(cursor, tableName)
    cursor.execute(
        f"""
            CREATE TABLE IF NOT EXISTS {tableName}
            (id INTEGER PRIMARY KEY AUTOINCREMENT, protein_id INTEGER, num_important_targets INTEGER)
        """
    )
    query = """
        SELECT protein.id as protein_id, COUNT(tinx_importance.doid) as num_important_targets
        FROM protein LEFT JOIN tinx_importance ON tinx_importance.protein_id = protein.id
        GROUP BY protein.id
    """
    remoteCursor.execute(query)

    for row in tqdm(remoteCursor.fetchall()):
        cursor.execute(f"INSERT INTO {tableName} (protein_id, num_important_targets) VALUES (?,?)", row)


def disease_ancestors_metadata(cursor, remoteCursor):
    tableName = 'tinx_disease_ancestors'
    remoteTableName = 'do_parent'
    maxParents = 14
    dropTable(cursor, tableName)
    cursor.execute(
        f"""
            CREATE TABLE IF NOT EXISTS {tableName} 
            (doid VARCHAR PRIMARY KEY, max_ancestor VARCHAR, ancestor_path VARCHAR)
        """
    )

    coalesce_query = ','.join(f"p{i}.doid" for i in range(maxParents, 0, -1))
    concat_query = ','.join(f"p{i}.doid" for i in range(maxParents, 0, -1))

    query = f"""
        SELECT p1.doid AS doid, COALESCE({coalesce_query}) AS max_ancestor,
            CONCAT_WS(' / ', {concat_query}) AS ancestor_path
        FROM {remoteTableName} p1 
    """
    query = query + " ".join(
        f"LEFT JOIN {remoteTableName} p{i} ON p{i}.doid = p{i - 1}.parent_id" for i in range(2, maxParents + 1)
    )
    remoteCursor.execute(query)

    for row in tqdm(remoteCursor.fetchall()):
        cursor.execute(f"INSERT OR REPLACE INTO {tableName} (doid, max_ancestor, ancestor_path) VALUES (?,?,?)", row)


if __name__ == '__main__':
    main()
