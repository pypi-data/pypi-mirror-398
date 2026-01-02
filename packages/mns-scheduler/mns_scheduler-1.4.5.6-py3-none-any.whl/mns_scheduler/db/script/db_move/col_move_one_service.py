import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from loguru import logger


def db_export(db, col):
    cmd = 'F:/mongo/bin/mongodump.exe --host ' + db + ' -d patience -c ' + col + ' -o D:/back'
    os.system(cmd)
    logger.info("export finished:{}", col)


def db_import(db, col):
    cmd = 'F:/mongo/bin/mongorestore.exe --host ' + db + ' -d patience -c ' + col + ' D:/back/patience/' + col + '.bson'
    os.system(cmd)

    path = 'D:\\back\\patience\\' + col + '.bson'
    cmd_del = 'del /F /S /Q ' + path
    os.system(cmd_del)

    logger.info("import finished:{}", col)


def handle_one_col(col_name):
    db_export('127.0.0.1:27017', col_name)
    db_import('127.0.0.1:27019', col_name)


if __name__ == '__main__':
    handle_one_col('one_minute_k_line_bfq_h')
