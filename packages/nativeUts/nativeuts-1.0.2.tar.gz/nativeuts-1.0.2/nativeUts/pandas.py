from forbiddenfruit import curse
import pandas as pd
import unicodedata


#============================  DATAFRAME
def trim_all(self):
    return self.map(lambda x: x.strip() if isinstance(x, str) else x)

def table_query(self,table_name,varchar=255,force_string=False,query_type="postgres"):
    tipos = { "O":f"VARCHAR({varchar})","int64": "BIGINT","q": "BIGINT", "float64": "FLOAT","d": "FLOAT", "object": f"VARCHAR({varchar})", "bool": "BOOLEAN","?": f"VARCHAR({varchar})", "datetime64[ns]": "TIMESTAMP", "timedelta[ns]": "INTERVAL", "category": f"VARCHAR({varchar})", "int32": "INT", "float32": "REAL", "string": "TEXT", "UInt8": "TINYINT", "UInt16": "SMALLINT", "UInt32": "INT", "UInt64": "BIGINT", "Int8": "TINYINT", "Int16": "SMALLINT", "Int32": "INT", "Int64": "BIGINT" }
    
    column_name_format = lambda x:f'[{x}]' if query_type != 'postgres' else f'"{x}"'

    if force_string:
        return f"create table {table_name} (\n" + "\n".join([f"{column_name_format(x)} VARCHAR({varchar})," for x in self.columns])[0:-1] + "\n)"
    else:
        return f"create table {table_name} (\n" + "\n".join([f"{column_name_format(x)} {tipos[self.dtypes[x].char]}," for x in self.columns])[0:-1] + "\n)"


def headers_snake_case(self):
        '''
            Essa função faz:
                espaços para _
                retira espaços extras
                retira acentuacao
        '''
        df_loc = self.copy()

        retira_acentuacao  = lambda titulo:unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode("ascii")
        retira_caracteres  = lambda titulo: "".join([x for x in titulo if x not in "-()/\\'"])
        para_minusculas    = lambda titulo:titulo.lower() 
        retira_espacos_ext = lambda titulo: titulo.replace("  "," ")
        retira_laterais    = lambda titulo: titulo.strip()
        retira_espacos     = lambda titulo: titulo.replace(" ","_")

        df_loc.columns = df_loc.columns.map(retira_acentuacao)
        df_loc.columns = df_loc.columns.map(retira_caracteres)
        df_loc.columns = df_loc.columns.map(para_minusculas)
        df_loc.columns = df_loc.columns.map(retira_espacos_ext)
        df_loc.columns = df_loc.columns.map(retira_laterais)
        df_loc.columns = df_loc.columns.map(retira_espacos)

        return df_loc


curse(pd.DataFrame, "trim_all", trim_all)
curse(pd.DataFrame, "table_query", table_query)
curse(pd.DataFrame, "headers_snake_case", headers_snake_case)
